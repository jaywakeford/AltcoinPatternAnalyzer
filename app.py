import streamlit as st
# Set page configuration first - must be the first Streamlit command
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import logging
import sys
import asyncio
import nest_asyncio
from datetime import datetime
import plotly.graph_objects as go
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Enable nested asyncio support
nest_asyncio.apply()

# Import local modules after Streamlit configuration
from utils.data_fetcher import ExchangeManager, ConnectionState
from styles.theme import apply_custom_theme
from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.backtesting import render_backtesting_section

def run_async(coroutine):
    """Helper function to run async code with proper task cleanup."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        # Create and run task with proper cleanup
        task = loop.create_task(coroutine)
        return loop.run_until_complete(task)
    finally:
        # Clean up pending tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        
        # Run loop again to handle cancellations
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

async def setup_websocket_connection(exchange_manager: ExchangeManager, symbol: str) -> bool:
    """Set up websocket connection with enhanced error handling and retry logic."""
    try:
        # Check if we need to reconnect
        ws_status = st.session_state.websocket_status.get(symbol, {})
        last_update = ws_status.get('last_update')
        current_time = datetime.now()
        
        needs_reconnect = (
            symbol not in st.session_state.ws_connections or
            (last_update and (current_time - last_update).total_seconds() > 30) or
            not ws_status.get('connection_healthy', False) or
            exchange_manager.get_websocket_status(symbol) != ConnectionState.CONNECTED
        )

        if needs_reconnect:
            # Update status to initializing
            st.session_state.websocket_status[symbol] = {
                'status': 'initializing',
                'last_update': current_time,
                'connection_healthy': False
            }
            
            try:
                # Enable websocket with the exchange
                await exchange_manager.enable_websocket(
                    symbol=symbol,
                    callback=handle_websocket_message
                )
                
                # Reset retry counter on successful connection
                st.session_state.connection_retries[symbol] = 0
                st.session_state.ws_connections[symbol] = True
                st.session_state.websocket_status[symbol].update({
                    'status': 'connected',
                    'last_update': current_time,
                    'connection_healthy': True
                })
                
                logger.info(f"Successfully established websocket connection for {symbol}")
                return True
                
            except Exception as e:
                # Handle connection failure
                st.session_state.connection_retries[symbol] = st.session_state.connection_retries.get(symbol, 0) + 1
                max_retries = 3
                
                if st.session_state.connection_retries[symbol] >= max_retries:
                    logger.error(f"Failed to establish websocket connection for {symbol} after {max_retries} attempts")
                    st.session_state.websocket_status[symbol].update({
                        'status': 'error',
                        'error': f"Connection failed after {max_retries} attempts: {str(e)}",
                        'connection_healthy': False
                    })
                    return False
                
                # Wait before retry (exponential backoff)
                await asyncio.sleep(2 ** st.session_state.connection_retries[symbol])
                return await setup_websocket_connection(exchange_manager, symbol)
        
        return True  # Connection is already established and healthy
            
    except Exception as e:
        logger.error(f"Error in websocket setup: {str(e)}")
        st.session_state.websocket_status[symbol] = {
            'status': 'error',
            'error': str(e),
            'last_update': datetime.now(),
            'connection_healthy': False
        }
        return False

async def handle_websocket_message(message: Dict[str, Any]) -> None:
    """Handle incoming websocket messages with improved error handling."""
    try:
        # Extract symbol and data from message
        symbol = None
        timestamp = datetime.now()
        price = None
        volume = None

        if isinstance(message, dict):
            # Handle Kraken format
            if 'pair' in message:
                symbol = message['pair'][0] if isinstance(message['pair'], list) else message['pair']
                if 'price' in message:
                    price = float(message['price'][0]) if isinstance(message['price'], list) else float(message['price'])
                    volume = float(message.get('volume', [0])[0]) if isinstance(message.get('volume'), list) else float(message.get('volume', 0))
            # Handle KuCoin format
            elif 'symbol' in message:
                symbol = message['symbol']
                data = message.get('data', {})
                if isinstance(data, dict):
                    price = float(data.get('price', 0))
                    volume = float(data.get('volume', 0))

        if symbol and price and price > 0:
            # Initialize data structures if needed
            if symbol not in st.session_state.real_time_data:
                st.session_state.real_time_data[symbol] = []
            
            # Calculate price change
            last_price = st.session_state.last_price.get(symbol, price)
            price_change = ((price - last_price) / last_price) * 100 if last_price > 0 else 0
            st.session_state.last_price[symbol] = price
            
            # Update price changes
            if symbol not in st.session_state.price_changes:
                st.session_state.price_changes[symbol] = []
            st.session_state.price_changes[symbol].append(price_change)
            
            # Keep only last 100 price changes
            if len(st.session_state.price_changes[symbol]) > 100:
                st.session_state.price_changes[symbol].pop(0)

            # Update real-time data
            data_point = {
                'timestamp': timestamp,
                'price': price,
                'volume': volume if volume and volume > 0 else None,
                'price_change': price_change
            }
            
            st.session_state.real_time_data[symbol].append(data_point)
            
            # Keep last 1000 data points
            if len(st.session_state.real_time_data[symbol]) > 1000:
                st.session_state.real_time_data[symbol].pop(0)

            # Update websocket status
            if symbol in st.session_state.websocket_status:
                st.session_state.websocket_status[symbol].update({
                    'status': 'connected',
                    'last_update': timestamp,
                    'last_price': price,
                    'price_change': price_change,
                    'connection_healthy': True
                })

    except Exception as e:
        logger.error(f"Error handling websocket message: {str(e)}")
        if symbol and symbol in st.session_state.websocket_status:
            st.session_state.websocket_status[symbol].update({
                'status': 'error',
                'error': str(e),
                'last_update': datetime.now(),
                'connection_healthy': False
            })

def initialize_session_state():
    """Initialize session state variables with improved logging."""
    try:
        logger.info("Initializing session state...")
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
            
        required_states = {
            'exchange_status': {},
            'error_shown': False,
            'selected_region': None,
            'selected_timezone': 'UTC',
            'data_source': None,
            'sidebar_config': None,
            'last_update': datetime.now(),
            'current_tab': None,
            'refresh_interval': 15,
            'auto_refresh': True,
            'advanced_metrics': {},
            'ws_connections': {},
            'real_time_data': {},
            'websocket_status': {},
            'last_price': {},
            'price_changes': {},
            'connection_retries': {},
            'symbol_mapping': {
                'bitcoin': 'BTC',
                'ethereum': 'ETH',
                'litecoin': 'LTC',
                'ripple': 'XRP',
                'cardano': 'ADA',
                'polkadot': 'DOT',
                'solana': 'SOL',
                'binancecoin': 'BNB'
            }
        }
        
        for key, default_value in required_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.info(f"Initialized {key} in session state")
        
        st.session_state.initialized = True
        logger.info("Session state initialization completed")
        
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        raise

def get_trading_symbol(coin: str) -> str:
    """Convert coin name to proper trading symbol format with validation."""
    try:
        # Convert to lowercase for consistent comparison
        coin_lower = coin.lower()
        
        # Symbol mapping for standardization
        symbol = st.session_state.symbol_mapping.get(coin_lower)
        if not symbol:
            logger.warning(f"Symbol not found for {coin}, using uppercase version")
            symbol = coin.upper()
        
        trading_pair = f"{symbol}/USDT"
        logger.info(f"Converted {coin} to trading pair {trading_pair}")
        return trading_pair
        
    except Exception as e:
        logger.error(f"Error converting trading symbol: {str(e)}")
        raise

def validate_trading_symbol(symbol: str) -> bool:
    """Validate trading symbol format with improved logging."""
    try:
        if not symbol or not isinstance(symbol, str):
            logger.warning("Invalid symbol: empty or not string")
            return False
            
        parts = symbol.split('/')
        if len(parts) != 2:
            logger.warning(f"Invalid symbol format {symbol}: missing separator")
            return False
            
        base, quote = parts
        if not base or not quote:
            logger.warning(f"Invalid symbol {symbol}: empty base or quote")
            return False
            
        valid_quotes = ['USDT', 'USD', 'EUR', 'BTC']
        if quote not in valid_quotes:
            logger.warning(f"Invalid quote currency {quote} for symbol {symbol}")
            return False
            
        logger.info(f"Symbol {symbol} validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error validating trading symbol: {str(e)}")
        return False

def main():
    """Main entry point with enhanced error handling and logging."""
    try:
        # Apply custom theme
        apply_custom_theme()
        
        # Initialize session state
        initialize_session_state()
        
        # Initialize exchange manager
        exchange_manager = ExchangeManager()
        
        # Set up page
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Real-time cryptocurrency analysis with advanced metrics and market insights.
        """)
        
        # Render sidebar first
        sidebar_config = render_sidebar()
        if sidebar_config:
            st.session_state.sidebar_config = sidebar_config
            logger.info("Sidebar configuration loaded successfully")
        else:
            st.error("Unable to load configuration. Please refresh the page.")
            logger.error("Failed to load sidebar configuration")
            return

        # Main content tabs
        tab1, tab2, tab3 = st.tabs([
            "📈 Real-time Price Analysis",
            "🔄 Altcoin Analysis",
            "⚙️ Strategy Builder"
        ])
        
        # Price Analysis Tab
        with tab1:
            if sidebar_config.get('selected_coins'):
                with st.spinner("Loading price analysis..."):
                    coin = sidebar_config['selected_coins'][0]
                    logger.info(f"Processing selected coin: {coin}")
                    
                    # Get and validate trading symbol
                    symbol = get_trading_symbol(coin)
                    logger.info(f"Generated trading symbol: {symbol}")
                    
                    if not validate_trading_symbol(symbol):
                        st.error(f"Invalid trading symbol format: {symbol}")
                        logger.error(f"Symbol validation failed for {symbol}")
                        return
                    
                    # Set up websocket connection using the async helper
                    logger.info(f"Setting up websocket connection for {symbol}")
                    connection_success = run_async(
                        setup_websocket_connection(exchange_manager, symbol)
                    )
                    
                    if connection_success:
                        # Show connection status
                        ws_status = st.session_state.websocket_status.get(symbol, {})
                        status_msg = ws_status.get('status', '')
                        
                        if status_msg == 'connected':
                            st.success(f"🟢 Connected to {symbol} websocket feed")
                            logger.info(f"Successfully connected to {symbol} websocket")
                        elif status_msg == 'error':
                            error_msg = ws_status.get('error', 'Unknown error')
                            st.error(f"🔴 Websocket error: {error_msg}")
                            logger.error(f"Websocket error for {symbol}: {error_msg}")
                            if st.button("Retry Connection"):
                                st.experimental_rerun()
                        else:
                            st.info("🔵 Initializing websocket connection...")
                        
                        # Display real-time metrics if available
                        if symbol in st.session_state.real_time_data and st.session_state.real_time_data[symbol]:
                            data = st.session_state.real_time_data[symbol]
                            latest = data[-1]
                            
                            # Display metrics in columns
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric(
                                    "Current Price",
                                    f"${latest['price']:,.2f}",
                                    f"{latest.get('price_change', 0):.2f}%"
                                )
                            
                            with col2:
                                st.metric(
                                    "24h Volume",
                                    f"${latest.get('volume', 0):,.2f}" if latest.get('volume') else "N/A"
                                )
                                
                            with col3:
                                st.metric(
                                    "Last Update",
                                    latest['timestamp'].strftime('%H:%M:%S')
                                )
                            
                            # Create real-time chart
                            if len(data) > 1:
                                df = pd.DataFrame(data)
                                
                                fig = go.Figure()
                                
                                # Add price line
                                fig.add_trace(go.Scatter(
                                    x=df['timestamp'],
                                    y=df['price'],
                                    mode='lines',
                                    name='Price',
                                    line=dict(color='#17C37B', width=2)
                                ))
                                
                                # Add volume bars if available
                                if 'volume' in df.columns and not df['volume'].isnull().all():
                                    fig.add_trace(go.Bar(
                                        x=df['timestamp'],
                                        y=df['volume'],
                                        name='Volume',
                                        yaxis='y2',
                                        marker_color='rgba(23, 195, 178, 0.2)'
                                    ))
                                
                                # Update layout
                                fig.update_layout(
                                    title=f"{symbol} Real-time Price and Volume",
                                    xaxis_title="Time",
                                    yaxis_title="Price (USD)",
                                    yaxis2=dict(
                                        title="Volume",
                                        overlaying="y",
                                        side="right"
                                    ),
                                    height=500,
                                    template="plotly_dark",
                                    showlegend=True,
                                    legend=dict(
                                        orientation="h",
                                        yanchor="bottom",
                                        y=1.02,
                                        xanchor="right",
                                        x=1
                                    )
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Update and show refresh time
                        st.caption(f"Last data update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                    else:
                        st.error("Failed to establish websocket connection")
                        logger.error("Websocket connection failed")
                        if st.button("Retry Connection"):
                            st.experimental_rerun()
            
        # Altcoin Analysis Tab
        with tab2:
            render_altcoin_analysis()
            
        # Strategy Builder Tab
        with tab3:
            render_backtesting_section()
            
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        if st.button("Restart Application"):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
