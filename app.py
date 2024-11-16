import streamlit as st
import pandas as pd
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from utils.data_fetcher import ExchangeManager
from styles.theme import apply_custom_theme
from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.backtesting import render_backtesting_section
from utils.symbol_converter import SymbolConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables."""
    if 'initialized' not in st.session_state:
        try:
            st.session_state.update({
                'initialized': True,
                'sidebar_config': None,
                'symbol_cache': {},
                'conversion_log': [],
                'last_update': datetime.now(),
                'exchange_manager': None,
                'symbol_converter': SymbolConverter()
            })
            logger.info("Session state initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing session state: {str(e)}")
            st.error("Failed to initialize application state. Please refresh the page.")
            raise

def convert_and_validate_symbol(coin: str, exchange_manager: ExchangeManager) -> Optional[Dict[str, Any]]:
    """Convert and validate symbol with comprehensive error handling."""
    try:
        if not coin:
            logger.warning("No coin provided for conversion")
            return None

        # Get symbol converter from session state
        symbol_converter = st.session_state.get('symbol_converter')
        if not symbol_converter:
            symbol_converter = SymbolConverter()
            st.session_state.symbol_converter = symbol_converter
        
        # Check cache first
        cache_key = coin.lower()
        if cache_key in st.session_state.symbol_cache:
            logger.info(f"Using cached conversion for {coin}")
            return st.session_state.symbol_cache[cache_key]
        
        # Convert coin name to trading symbol
        trading_symbol = symbol_converter.convert_from_coin_name(coin)
        if not trading_symbol:
            logger.warning(f"Failed to convert {coin} to trading symbol")
            return None
        
        # Validate the trading symbol format
        is_valid, validation_message = symbol_converter.validate_symbol(trading_symbol)
        if not is_valid:
            logger.warning(f"Invalid trading symbol format: {validation_message}")
            return None
        
        # Get exchange-specific format if exchange is available
        exchange_symbol = None
        if exchange_manager and exchange_manager.current_exchange:
            exchange_symbol = symbol_converter.get_exchange_format(
                trading_symbol,
                exchange_manager.current_exchange
            )
            logger.info(f"Generated exchange-specific format: {exchange_symbol}")
        
        # Create conversion result
        result = {
            'original': coin,
            'trading_symbol': trading_symbol,
            'exchange_symbol': exchange_symbol,
            'validation_message': validation_message,
            'timestamp': datetime.now()
        }
        
        # Cache the result
        st.session_state.symbol_cache[cache_key] = result
        logger.info(f"Successfully converted {coin} to {trading_symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error in symbol conversion: {str(e)}")
        st.error(f"Error converting symbol: {str(e)}")
        return None

def render_symbol_conversion_section(coin: str, exchange_manager: ExchangeManager):
    """Render symbol conversion section for a given coin."""
    st.markdown(f"### Symbol Conversion for {coin}")
    
    with st.expander("Symbol Conversion Process", expanded=True):
        st.info("Converting cryptocurrency name to trading pair...")
        
        conversion_result = convert_and_validate_symbol(coin, exchange_manager)
        
        if conversion_result:
            st.success(f"Successfully converted {coin} to trading pair: {conversion_result['trading_symbol']}")
            st.success(f"Validation: {conversion_result['validation_message']}")
            
            if conversion_result['exchange_symbol']:
                st.success(f"Exchange-specific format: {conversion_result['exchange_symbol']}")
            
            # Log successful conversion
            if conversion_result not in st.session_state.conversion_log:
                st.session_state.conversion_log.append(conversion_result)
            
            # Display conversion history
            if st.session_state.conversion_log:
                st.markdown("#### Recent Conversions")
                for log in st.session_state.conversion_log[-5:]:
                    timestamp = log['timestamp'].strftime('%H:%M:%S')
                    exchange_format = f" → {log['exchange_symbol']}" if log['exchange_symbol'] else ""
                    st.info(f"{timestamp} - {log['original']} → {log['trading_symbol']}{exchange_format}")
                    
            return conversion_result
        else:
            st.error(f"Failed to convert {coin} to a valid trading pair")
            st.info("Please check if the cryptocurrency name is correct and try again.")
            return None

def main():
    """Main application entry point."""
    try:
        # Set page config first
        st.set_page_config(
            page_title="Crypto Analysis Platform",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        initialize_session_state()
        
        # Apply custom theme
        apply_custom_theme()
        
        # Initialize exchange manager if not already done
        if 'exchange_manager' not in st.session_state or not st.session_state.exchange_manager:
            st.session_state.exchange_manager = ExchangeManager()
        exchange_manager = st.session_state.exchange_manager
        
        # Page title and description
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Welcome to the Cryptocurrency Analysis Platform! 
        Select a cryptocurrency from the sidebar to begin analysis.
        """)
        
        # Render sidebar and get configuration
        sidebar_config = render_sidebar()
        st.session_state.sidebar_config = sidebar_config
        
        # Main content area
        if sidebar_config and sidebar_config.get('selected_coins'):
            # Process each selected coin
            conversion_results = {}
            for coin in sidebar_config['selected_coins']:
                result = render_symbol_conversion_section(coin, exchange_manager)
                if result:
                    conversion_results[coin] = result
            
            if conversion_results:
                # Display tabs for different analysis sections
                tab1, tab2, tab3 = st.tabs([
                    "📈 Market Analysis",
                    "🔄 Altcoin Analysis",
                    "⚙️ Strategy Builder"
                ])
                
                with tab1:
                    for coin, result in conversion_results.items():
                        st.markdown(f"### Market Analysis for {result['trading_symbol']}")
                        st.markdown("Market analysis components will be added in the next phase.")
                        
                with tab2:
                    render_altcoin_analysis()
                    
                with tab3:
                    render_backtesting_section()
        else:
            st.info("👈 Please select a cryptocurrency from the sidebar to begin analysis.")
            
    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page and try again.")
        st.error(str(e))

if __name__ == "__main__":
    main()
