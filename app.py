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
from typing import Optional, Dict, Any, Tuple, List
import re
import time

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
from utils.data_fetcher import ExchangeManager
from styles.theme import apply_custom_theme
from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.backtesting import render_backtesting_section
from utils.websocket_manager import WebSocketManager, ConnectionState

# Initialize WebSocket manager globally
websocket_manager = WebSocketManager()

def initialize_session_state():
    """Initialize session state variables with enhanced websocket and symbol validation support."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.update({
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
            'validation_errors': {},
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
        })
        logger.info("Session state initialized successfully")

def validate_symbol_format(symbol: str) -> Tuple[bool, str]:
    """Validate symbol format with comprehensive checks."""
    try:
        if not symbol or not isinstance(symbol, str):
            return False, "Symbol must be a non-empty string"
            
        # Check format using regex
        if not re.match(r'^[A-Z0-9]+/[A-Z0-9]+$', symbol):
            return False, f"Invalid symbol format: {symbol} - Must be in BASE/QUOTE format (e.g., BTC/USDT)"
            
        base, quote = symbol.split('/')
        
        # Validate base currency
        valid_base = websocket_manager.valid_base_currencies
        if base not in valid_base:
            return False, f"Invalid base currency: {base} - Must be one of {', '.join(sorted(valid_base))}"
            
        # Validate quote currency
        valid_quote = websocket_manager.valid_quote_currencies
        if quote not in valid_quote:
            return False, f"Invalid quote currency: {quote} - Must be one of {', '.join(sorted(valid_quote))}"
            
        return True, "Symbol validation successful"
            
    except Exception as e:
        logger.error(f"Error in symbol validation: {str(e)}")
        return False, f"Validation error: {str(e)}"

def get_trading_symbol(coin: str) -> Optional[str]:
    """Convert coin name to proper trading symbol format."""
    try:
        if not coin:
            return None
            
        coin_lower = coin.lower()
        symbol = st.session_state.symbol_mapping.get(coin_lower)
        
        if not symbol:
            logger.error(f"Symbol mapping not found for coin: {coin}")
            return None
        
        trading_pair = f"{symbol}/USDT"
        is_valid, _ = validate_symbol_format(trading_pair)
        
        if not is_valid:
            return None
            
        logger.info(f"Successfully converted {coin} to trading pair {trading_pair}")
        return trading_pair
        
    except Exception as e:
        logger.error(f"Error converting trading symbol: {str(e)}")
        return None

async def setup_websocket_connection(exchange_manager: ExchangeManager, symbol: str) -> bool:
    """Set up websocket connection with validation."""
    try:
        # Validate symbol format
        is_valid, validation_message = validate_symbol_format(symbol)
        if not is_valid:
            st.error(validation_message)
            logger.error(f"Symbol validation failed: {validation_message}")
            return False

        # Update connection status
        st.session_state.websocket_status[symbol] = {
            'status': 'connecting',
            'last_update': datetime.now(),
            'connection_healthy': False
        }

        # Enable websocket connection
        await exchange_manager.enable_websocket(
            symbol=symbol,
            callback=handle_websocket_message
        )
        
        # Update status on successful connection
        st.session_state.ws_connections[symbol] = True
        st.session_state.websocket_status[symbol].update({
            'status': 'connected',
            'last_update': datetime.now(),
            'connection_healthy': True
        })
        
        logger.info(f"Successfully established websocket connection for {symbol}")
        return True
            
    except Exception as e:
        error_msg = f"Error in websocket setup: {str(e)}"
        logger.error(error_msg)
        st.session_state.websocket_status[symbol] = {
            'status': 'error',
            'error': error_msg,
            'last_update': datetime.now(),
            'connection_healthy': False
        }
        return False

def handle_websocket_message(message: Dict[str, Any]) -> None:
    """Handle incoming websocket messages."""
    try:
        if not isinstance(message, dict):
            return

        symbol = None
        timestamp = datetime.now()
        price = None
        volume = None

        # Extract data based on exchange format
        if 'pair' in message:
            symbol = message['pair'][0] if isinstance(message['pair'], list) else message['pair']
            if 'price' in message:
                price = float(message['price'][0]) if isinstance(message['price'], list) else float(message['price'])
                volume = float(message.get('volume', [0])[0]) if isinstance(message.get('volume'), list) else float(message.get('volume', 0))
        elif 'symbol' in message:
            symbol = message['symbol']
            data = message.get('data', {})
            if isinstance(data, dict):
                price = float(data.get('price', 0))
                volume = float(data.get('volume', 0))

        if symbol and price and price > 0:
            # Initialize data structure if needed
            if symbol not in st.session_state.real_time_data:
                st.session_state.real_time_data[symbol] = []

            # Calculate price change
            last_price = st.session_state.last_price.get(symbol, price)
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

            # Maintain data window
            if len(st.session_state.real_time_data[symbol]) > 100:
                st.session_state.real_time_data[symbol].pop(0)

            # Update connection status
            st.session_state.websocket_status[symbol] = {
                'status': 'connected',
                'last_update': timestamp,
                'last_price': price,
                'price_change': price_change,
                'connection_healthy': True
            }

    except Exception as e:
        logger.error(f"Error handling websocket message: {str(e)}")
        if symbol:
            st.session_state.websocket_status[symbol] = {
                'status': 'error',
                'error': str(e),
                'last_update': datetime.now(),
                'connection_healthy': False
            }

def main():
    """Main application entry point with streamlined structure."""
    try:
        # Apply custom theme
        apply_custom_theme()
        
        # Initialize session state
        initialize_session_state()
        
        # Initialize exchange manager
        exchange_manager = ExchangeManager()
        
        # Page title and description
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Real-time cryptocurrency analysis with advanced metrics and market insights.
        Select a cryptocurrency from the sidebar to begin analysis.
        """)
        
        # Render sidebar
        sidebar_config = render_sidebar()
        if not sidebar_config:
            st.error("Unable to load configuration. Please refresh the page.")
            return

        # Store sidebar configuration
        st.session_state.sidebar_config = sidebar_config
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs([
            "📈 Price Analysis",
            "🔄 Altcoin Analysis",
            "⚙️ Strategy Builder"
        ])
        
        # Price Analysis Tab
        with tab1:
            if sidebar_config.get('selected_coins'):
                coin = sidebar_config['selected_coins'][0]
                
                # Validation Section
                st.markdown("### Trading Pair Validation")
                
                # Get and validate trading symbol
                symbol = get_trading_symbol(coin)
                if not symbol:
                    st.error("Invalid cryptocurrency selected. Please choose a supported coin.")
                    return
                
                # Show validation status
                is_valid, validation_message = validate_symbol_format(symbol)
                if not is_valid:
                    st.error(validation_message)
                    return
                
                st.success(f"Trading pair validated successfully: {symbol}")
                
                # WebSocket Connection Section
                st.markdown("### Real-time Data Connection")
                
                # Setup WebSocket connection
                if symbol not in st.session_state.ws_connections:
                    with st.spinner(f"Establishing connection to {symbol}..."):
                        connection_success = asyncio.run(
                            setup_websocket_connection(exchange_manager, symbol)
                        )
                        
                        if connection_success:
                            st.success(f"Successfully connected to {symbol}")
                        else:
                            st.error("Failed to establish connection. Please try again.")
                            return
                
                # Display real-time data if available
                if symbol in st.session_state.real_time_data:
                    data = st.session_state.real_time_data[symbol]
                    if data:
                        last_data = data[-1]
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric(
                                "Price",
                                f"${last_data['price']:,.2f}",
                                f"{last_data.get('price_change', 0):.2f}%"
                            )
                        
                        with col2:
                            if last_data.get('volume'):
                                st.metric(
                                    "Volume",
                                    f"${last_data['volume']:,.2f}"
                                )
                
            else:
                st.warning("Please select a cryptocurrency from the sidebar")
                
            # Add other tabs content
            with tab2:
                render_altcoin_analysis()
            
            with tab3:
                render_backtesting_section()
                
    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page.")

if __name__ == "__main__":
    main()