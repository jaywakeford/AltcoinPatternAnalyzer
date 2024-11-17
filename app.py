import streamlit as st
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
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def initialize_session_state() -> bool:
    """Initialize session state variables."""
    try:
        if 'initialized' not in st.session_state:
            logger.info("Starting session state initialization")
            
            # Initialize symbol converter
            st.session_state.symbol_converter = SymbolConverter()
            
            # Initialize other session state variables
            st.session_state.update({
                'initialized': True,
                'exchange_manager': None,
                'last_update': datetime.now(),
                'supported_exchanges': ['kraken', 'kucoin', 'binance']
            })
            
            logger.info("Session state initialized successfully")
            return True
            
        return True
        
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        st.error(f"Error initializing application: {str(e)}")
        return False

def display_exchange_formats():
    """Display exchange-specific symbol formats with enhanced error handling."""
    try:
        st.markdown("### Exchange Format Guide")
        
        symbol_converter = st.session_state.symbol_converter
        
        # Create three columns for better layout
        cols = st.columns(3)
        
        # Display formats for each exchange in columns
        for idx, exchange in enumerate(st.session_state.supported_exchanges):
            with cols[idx % 3]:
                with st.expander(f"{exchange.capitalize()} Format Guide", expanded=True):
                    format_info = symbol_converter.get_exchange_format_info(exchange)
                    if format_info:
                        st.markdown(f"**Description**: {format_info['description']}")
                        st.markdown(f"**Example**: `{format_info['example']}`")
                        
                        if format_info.get('validation_rules'):
                            st.markdown("**Validation Rules:**")
                            for rule in format_info['validation_rules']:
                                st.markdown(f"- {rule}")
                        
                        if format_info.get('special_cases'):
                            st.markdown("**Special Cases:**")
                            for original, special in format_info['special_cases'].items():
                                st.code(f"{original} → {special}")
                                
                        # Add symbol validation example
                        example_symbol = format_info['example']
                        is_valid, message = symbol_converter.validate_symbol(example_symbol, exchange)
                        st.markdown("**Validation Example:**")
                        if is_valid:
                            st.success(f"`{example_symbol}` - Valid format")
                        else:
                            st.error(f"`{example_symbol}` - {message}")
        
        logger.debug("Exchange formats displayed successfully")
        
    except Exception as e:
        logger.error(f"Error displaying exchange formats: {str(e)}")
        st.error("Error displaying format examples")

def show_symbol_conversions(coins: list):
    """Display symbol conversion examples with validation."""
    try:
        st.markdown("### Symbol Conversion Examples")
        
        symbol_converter = st.session_state.symbol_converter
        
        # Create columns for the conversion examples
        cols = st.columns(2)
        
        for idx, coin in enumerate(coins):
            with cols[idx % 2]:
                with st.expander(f"{coin.capitalize()} Format Examples", expanded=True):
                    # Get standard symbol
                    standard_symbol = symbol_converter.convert_from_coin_name(coin)
                    if standard_symbol:
                        st.markdown(f"**Standard Format**: `{standard_symbol}`")
                        
                        # Show exchange-specific formats
                        for exchange in st.session_state.supported_exchanges:
                            st.markdown(f"\n**{exchange.capitalize()}**:")
                            exchange_symbol = symbol_converter.convert_to_exchange_format(
                                standard_symbol, exchange
                            )
                            if exchange_symbol:
                                is_valid, message = symbol_converter.validate_symbol(exchange_symbol, exchange)
                                st.code(exchange_symbol)
                                if is_valid:
                                    st.success("✓ Valid format")
                                else:
                                    st.warning(f"⚠ {message}")
                            else:
                                st.error(f"Could not convert to {exchange} format")
                    else:
                        st.warning(f"Could not convert {coin} to standard format")
                    
    except Exception as e:
        logger.error(f"Error showing symbol conversions: {str(e)}")
        st.error("Error displaying symbol conversions")

def main():
    """Main application entry point with enhanced error handling."""
    try:
        # Set page config
        st.set_page_config(
            page_title="Crypto Analysis Platform",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply custom theme
        apply_custom_theme()
        
        # Initialize session state
        if not initialize_session_state():
            return
        
        # Initialize exchange manager if needed
        if not st.session_state.get('exchange_manager'):
            st.session_state.exchange_manager = ExchangeManager()
        
        # Page title and description
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Welcome to the Cryptocurrency Analysis Platform!
        This platform provides real-time analysis with custom symbol format support for multiple exchanges.
        """)
        
        # Get sidebar configuration
        sidebar_config = render_sidebar()
        
        # Main content area
        if sidebar_config and sidebar_config.get('selected_coins'):
            tabs = st.tabs([
                "📈 Symbol Formats",
                "🔄 Market Analysis",
                "⚙️ Strategy Builder"
            ])
            
            with tabs[0]:
                # Display exchange formats and symbol conversion examples
                display_exchange_formats()
                show_symbol_conversions(sidebar_config['selected_coins'])
            
            with tabs[1]:
                render_altcoin_analysis()
            
            with tabs[2]:
                render_backtesting_section()
        
        else:
            st.info("👈 Please select cryptocurrencies from the sidebar to begin analysis.")
            
    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    main()
