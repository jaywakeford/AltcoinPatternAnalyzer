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
    """Initialize session state variables with enhanced error handling."""
    try:
        if 'initialized' not in st.session_state:
            logger.info("Starting session state initialization")
            
            # Initialize symbol converter
            st.session_state.symbol_converter = SymbolConverter()
            
            # Initialize other session state variables
            st.session_state.update({
                'initialized': True,
                'exchange_manager': ExchangeManager(),
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

def main():
    """Main application entry point with enhanced error handling."""
    try:
        # Set page config first
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
            st.error("Failed to initialize application. Please refresh the page.")
            return
        
        # Page title and description
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Welcome to the Cryptocurrency Analysis Platform!
        This platform provides real-time analysis with custom symbol format support for multiple exchanges.
        """)
        
        # Render sidebar first to ensure configuration is available
        sidebar_config = render_sidebar()
        
        if not sidebar_config:
            st.warning("Please configure analysis settings in the sidebar")
            return
        
        # Create main tabs - Removed duplicate momentum tab
        tabs = st.tabs([
            "📊 Market Analysis",
            "⚙️ Strategy Builder"
        ])
        
        # Market Analysis Tab
        with tabs[0]:
            render_altcoin_analysis()
        
        # Strategy Builder Tab
        with tabs[1]:
            render_backtesting_section()
            
    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    main()
