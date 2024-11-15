import streamlit as st
import pandas as pd
import numpy as np
import logging
import sys
import asyncio
import nest_asyncio
from datetime import datetime
import plotly.graph_objects as go

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Enable nested asyncio support
nest_asyncio.apply()

# Set page configuration
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import local modules
from styles.theme import apply_custom_theme
from utils.data_fetcher import ExchangeManager
from utils.websocket_manager import websocket_manager
from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.backtesting import render_backtesting_section

# Apply custom theme
apply_custom_theme()

def initialize_session_state():
    """Initialize session state variables."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        
    required_states = {
        'exchange_status': None,
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
        'initialized': True
    }
    
    for key, default_value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def render_realtime_chart(symbol: str):
    """Render real-time price chart."""
    try:
        if symbol in st.session_state.real_time_data and st.session_state.real_time_data[symbol]:
            data = st.session_state.real_time_data[symbol]
            df = pd.DataFrame(data)
            
            # Create price chart
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['price'],
                name="Price",
                line=dict(color='#17C37B', width=2)
            ))
            
            # Add volume bars if available
            if 'volume' in df.columns and not df['volume'].isnull().all():
                fig.add_trace(go.Bar(
                    x=df['timestamp'],
                    y=df['volume'],
                    name="Volume",
                    yaxis="y2",
                    marker_color='rgba(23, 195, 178, 0.2)'
                ))
            
            fig.update_layout(
                title=f"{symbol} Real-time Price",
                yaxis=dict(
                    title="Price (USD)",
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
            
            # Calculate price change
            if symbol not in st.session_state.last_price:
                st.session_state.last_price[symbol] = price
                price_change = 0
            else:
                last_price = st.session_state.last_price[symbol]
                price_change = ((price - last_price) / last_price) * 100 if last_price > 0 else 0
                st.session_state.last_price[symbol] = price

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
            st.session_state.websocket_status[symbol] = {
                'status': 'connected',
                'last_update': timestamp,
                'last_price': price,
                'price_change': price_change
            }

    except Exception as e:
        logger.error(f"Error handling websocket message: {str(e)}")
        if symbol:
            st.session_state.websocket_status[symbol] = {
                'status': 'error',
                'error': str(e),
                'last_update': datetime.now()
            }

async def setup_websocket_connection(exchange_manager: ExchangeManager, symbol: str) -> bool:
    """Set up websocket connection with improved error handling."""
    try:
        if symbol not in st.session_state.ws_connections:
            st.session_state.websocket_status[symbol] = {
                'status': 'initializing'
            }
            
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
        
        # Initialize exchange manager
        exchange_manager = ExchangeManager()
        
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
                    connection_success = await setup_websocket_connection(exchange_manager, symbol)
                    if connection_success:
                        # Show connection status
                        ws_status = st.session_state.websocket_status.get(symbol, {})
                        if ws_status.get('status') == 'connected':
                            st.success(f"🟢 Connected to {symbol} websocket feed")
                        elif ws_status.get('status') == 'error':
                            st.error(f"🔴 Websocket error: {ws_status.get('error', 'Unknown error')}")
                        else:
                            st.info("🔵 Initializing websocket connection...")
                        
                        # Display real-time metrics
                        if symbol in st.session_state.real_time_data and st.session_state.real_time_data[symbol]:
                            data = st.session_state.real_time_data[symbol]
                            latest = data[-1]
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Current Price",
                                    f"${latest['price']:,.2f}",
                                    f"{latest['price_change']:.2f}%"
                                )
                            with col2:
                                st.metric(
                                    "24h Volume",
                                    f"${latest['volume']:,.2f}" if latest['volume'] else "N/A"
                                )
                            with col3:
                                st.metric(
                                    "Last Update",
                                    latest['timestamp'].strftime('%H:%M:%S')
                                )
                        
                        # Render real-time chart
                        render_realtime_chart(symbol)

        # Altcoin Analysis Tab
        with tab2:
            render_altcoin_analysis()
        
        # Strategy Builder Tab
        with tab3:
            render_backtesting_section()
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An error occurred. Please refresh the page and try again.")

def main():
    """Main entry point."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
