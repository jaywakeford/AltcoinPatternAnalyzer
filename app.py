import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
import pytz
import sys
import traceback
import asyncio
import nest_asyncio
from utils.data_fetcher import exchange_manager
from utils.websocket_manager import websocket_manager

# Enable nested asyncio support
nest_asyncio.apply()

# Set page configuration first
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import components
from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.backtesting import render_backtesting_section
from utils.data_fetcher import get_crypto_data, get_exchange_status, detect_region
from utils.ui_components import show_error, show_warning, show_data_source_info
from utils.technical_analysis import calculate_advanced_metrics

def initialize_session_state():
    """Initialize session state variables."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        
    required_states = {
        'exchange_status': None,
        'error_shown': False,
        'selected_region': detect_region(),
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
        'initialized': True
    }
    
    for key, default_value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
            logger.info(f"Initialized {key} in session state")
    
    return True

async def handle_websocket_message(message: dict):
    """Handle incoming websocket messages."""
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
                price = float(data.get('price', 0))
                volume = float(data.get('volume', 0))
                
        if symbol and price and price > 0:
            if symbol not in st.session_state.real_time_data:
                st.session_state.real_time_data[symbol] = []

            st.session_state.real_time_data[symbol].append({
                'timestamp': timestamp,
                'price': price,
                'volume': volume if volume and volume > 0 else None
            })

            # Keep last 1000 data points
            if len(st.session_state.real_time_data[symbol]) > 1000:
                st.session_state.real_time_data[symbol].pop(0)

            # Update websocket status
            st.session_state.websocket_status[symbol] = {
                'status': 'connected',
                'last_update': timestamp
            }

            # Force Streamlit to update
            st.experimental_rerun()

    except Exception as e:
        logger.error(f"Error handling websocket message: {str(e)}")
        if symbol:
            st.session_state.websocket_status[symbol] = {
                'status': 'error',
                'error': str(e)
            }

def render_real_time_chart(symbol: str):
    """Render real-time price chart."""
    try:
        # Show websocket connection status
        ws_status = st.session_state.websocket_status.get(symbol, {})
        status = ws_status.get('status', 'initializing')
        
        if status == 'connected':
            st.success(f"🟢 Connected to {symbol} websocket feed")
        elif status == 'error':
            st.error(f"🔴 Error in websocket connection: {ws_status.get('error', 'Unknown error')}")
        else:
            st.info("🔵 Initializing websocket connection...")

        if symbol in st.session_state.real_time_data and st.session_state.real_time_data[symbol]:
            data = st.session_state.real_time_data[symbol]
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)

            fig = go.Figure()
            
            # Price line
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['price'],
                name="Price",
                line=dict(color='#17C37B', width=2)
            ))

            # Volume bars if available
            if 'volume' in df.columns and not df['volume'].isnull().all():
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name="Volume",
                    yaxis="y2",
                    marker_color='rgba(23, 195, 178, 0.2)'
                ))

            fig.update_layout(
                title=f"Real-time {symbol} Price",
                yaxis=dict(
                    title="Price",
                    titlefont=dict(color="#17C37B"),
                    tickfont=dict(color="#17C37B")
                ),
                yaxis2=dict(
                    title="Volume",
                    overlaying="y",
                    side="right",
                    titlefont=dict(color="rgba(23, 195, 178, 0.6)"),
                    tickfont=dict(color="rgba(23, 195, 178, 0.6)")
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
                ),
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for real-time data...")
            
    except Exception as e:
        logger.error(f"Error rendering chart: {str(e)}")
        st.error("Unable to render real-time chart")

async def setup_websocket_connection(symbol: str) -> bool:
    """Set up websocket connection with improved error handling."""
    try:
        if symbol not in st.session_state.ws_connections:
            st.session_state.websocket_status[symbol] = {
                'status': 'initializing'
            }
            
            # Initialize exchange connection if needed
            if not exchange_manager.active_exchange:
                exchange_manager._initialize_exchange()
            
            # Enable websocket
            await exchange_manager.enable_websocket(
                symbol=symbol,
                callback=handle_websocket_message
            )
            
            st.session_state.ws_connections[symbol] = True
            st.session_state.websocket_status[symbol] = {
                'status': 'connected',
                'last_update': datetime.now()
            }
            
            logger.info(f"Established websocket connection for {symbol}")
            return True
            
        return True  # Connection already exists
            
    except Exception as e:
        logger.error(f"Error setting up websocket connection: {str(e)}")
        st.session_state.websocket_status[symbol] = {
            'status': 'error',
            'error': str(e)
        }
        return False

async def main_async():
    """Async main application entry point."""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Set up page
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Real-time cryptocurrency analysis with advanced metrics and market insights.
        """)
        
        # Render sidebar
        sidebar_config = render_sidebar()
        if sidebar_config:
            st.session_state.sidebar_config = sidebar_config
        else:
            st.error("Unable to load configuration. Please refresh the page.")
            return

        # Main content tabs
        tab1, tab2, tab3 = st.tabs([
            "📈 Price Analysis",
            "🔄 Altcoin Analysis",
            "⚙️ Strategy Builder"
        ])
        
        # Price Analysis Tab
        with tab1:
            if sidebar_config.get('selected_coins'):
                with st.spinner("Loading price analysis..."):
                    coin = sidebar_config['selected_coins'][0]
                    symbol = f"{coin.upper()}/USDT"
                    
                    # Set up websocket connection
                    connection_success = await setup_websocket_connection(symbol)
                    if connection_success:
                        # Render real-time chart
                        render_real_time_chart(symbol)
                        
                        # Display historical data
                        data = get_crypto_data(coin, sidebar_config['timeframe'])
                        if not data.empty:
                            st.markdown("### Historical Analysis")
                            metrics = calculate_advanced_metrics(data)
                            
                            cols = st.columns(3)
                            with cols[0]:
                                st.metric("Volatility", f"{metrics['volatility']:.2f}%")
                            with cols[1]:
                                st.metric("Momentum", f"{metrics['momentum']:.2f}%")
                            with cols[2]:
                                st.metric("Market Strength", f"{metrics['market_strength']:.2f}")
                        else:
                            st.info("Historical data temporarily unavailable")
                    else:
                        st.error("Failed to establish websocket connection. Please try again.")
        
        # Altcoin Analysis Tab
        with tab2:
            render_altcoin_analysis()
        
        # Strategy Builder Tab
        with tab3:
            render_backtesting_section()
        
        # Footer
        st.sidebar.markdown("---")
        show_data_source_info(
            source=st.session_state.get('data_source', 'unknown'),
            details={
                'Last Updated': st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S'),
                'Real-time Connections': len(st.session_state.ws_connections)
            }
        )
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An error occurred. Please refresh the page and try again.")

def main():
    """Main entry point that runs the async main function."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
