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
                'supported_exchanges': ['kraken', 'kucoin', 'binance'],
                'selected_timeframe': '1d',
                'selected_view': 'real-time'
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

        # Render sidebar with error handling
        try:
            sidebar_config = render_sidebar()
            if not sidebar_config:
                st.warning("Please configure analysis settings in the sidebar")
                return
        except Exception as e:
            logger.error(f"Error rendering sidebar: {str(e)}")
            st.error("Error loading configuration interface")
            return
        
        # Create main navigation tabs
        main_tabs = st.tabs([
            "📊 Market Analysis",
            "📈 Historical Analysis",
            "⚙️ Strategy Builder"
        ])
        
        # Market Analysis Tab (consolidated with momentum)
        with main_tabs[0]:
            try:
                render_altcoin_analysis(view_mode="real-time")
            except Exception as e:
                logger.error(f"Error rendering market analysis: {str(e)}")
                st.error("Unable to load market analysis. Please try refreshing the page.")
        
        # Historical Analysis Tab
        with main_tabs[1]:
            try:
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", datetime.now().date())
                with col2:
                    end_date = st.date_input("End Date", datetime.now().date())
                render_altcoin_analysis(view_mode="historical")
            except Exception as e:
                logger.error(f"Error rendering historical analysis: {str(e)}")
                st.error("Unable to load historical analysis. Please try refreshing the page.")
        
        # Strategy Builder Tab
        with main_tabs[2]:
            try:
                render_backtesting_section()
            except Exception as e:
                logger.error(f"Error rendering strategy builder: {str(e)}")
                st.error("Unable to load strategy builder. Please try refreshing the page.")
            
    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    main()
