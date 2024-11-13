import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.predictions import render_prediction_section
from components.backtesting import render_backtesting_section
from utils.data_fetcher import get_crypto_data, get_exchange_status, detect_region, exchange_manager
from utils.ui_components import show_error, show_warning, show_data_source_info
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

def initialize_session_state():
    """Initialize session state variables with error handling."""
    try:
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
        if 'exchange_status' not in st.session_state:
            st.session_state.exchange_status = None
        if 'error_shown' not in st.session_state:
            st.session_state.error_shown = False
        if 'selected_region' not in st.session_state:
            st.session_state.selected_region = detect_region()
        if 'sidebar_config' not in st.session_state:
            st.session_state.sidebar_config = None
        if 'data_source' not in st.session_state:
            st.session_state.data_source = None
        
        return True
            
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        show_error(
            "Initialization Error",
            "Failed to initialize application state",
            str(e)
        )
        return False

def initialize_exchanges():
    """Initialize exchanges with proper error handling and retry logic."""
    try:
        with st.spinner("Connecting to exchanges..."):
            # Get exchange status
            exchange_status = get_exchange_status()
            available_count = len([x for x in exchange_status.values() if x['status'] == 'available'])
            
            # Update session state
            st.session_state.exchange_status = exchange_status
            st.session_state.initialized = True
            
            if available_count > 0:
                st.success(f"Successfully connected to {available_count} exchanges!")
                show_data_source_info(
                    "Primary Exchange",
                    {"Available": f"{available_count} exchanges", "Region": st.session_state.selected_region}
                )
                return True
            else:
                show_warning(
                    "Limited Exchange Access",
                    "No exchanges are currently available in your region. Using fallback data sources.",
                    "Data will be fetched from CoinGecko API"
                )
                show_data_source_info(
                    "Fallback Source",
                    {"Source": "CoinGecko API", "Region": "Global"}
                )
                return True
        
    except Exception as e:
        logger.error(f"Exchange initialization error: {str(e)}")
        show_error(
            "Exchange Connection Error",
            "Unable to connect to cryptocurrency exchanges",
            "Using fallback data sources. Please check your internet connection or try using a VPN"
        )
        st.session_state.initialized = False
        return False

def fetch_crypto_data(coin: str, timeframe: str) -> pd.DataFrame:
    """Synchronous wrapper for getting crypto data with fallback handling."""
    try:
        with st.spinner(f"Fetching data for {coin}..."):
            data = get_crypto_data(coin, timeframe)
            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)
            
            if not data.empty:
                st.session_state.data_source = data.get('source', 'unknown')
                return data
            else:
                show_warning(
                    "Data Fetch Error",
                    f"Unable to fetch data for {coin}",
                    "Trying fallback data sources"
                )
                return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching crypto data: {str(e)}")
        show_error("Data Error", str(e))
        return pd.DataFrame()

def main():
    """Main application entry point with enhanced error handling."""
    try:
        # Initialize session state
        if not initialize_session_state():
            return
        
        # Initialize exchanges first
        if not st.session_state.initialized:
            if not initialize_exchanges():
                return
        
        # Create main layout
        st.title("Cryptocurrency Analysis Platform")
        
        # Render sidebar with regional optimization
        sidebar_config = render_sidebar()
        st.session_state.sidebar_config = sidebar_config
        
        if not sidebar_config:
            show_error(
                "Configuration Error",
                "Failed to load sidebar configuration",
                "Please refresh the page and try again"
            )
            return
        
        # Create tabs
        tabs = st.tabs(["Price Analysis", "Altcoin Analysis & Strategy", "Strategy Builder & Testing"])
        
        # Price Analysis Tab
        with tabs[0]:
            try:
                if sidebar_config.get('selected_coins'):
                    coin = sidebar_config['selected_coins'][0]
                    data = fetch_crypto_data(coin, sidebar_config['timeframe'])
                    if not data.empty:
                        show_data_source_info(
                            st.session_state.data_source,
                            {"Asset": coin, "Timeframe": f"{sidebar_config['timeframe']} days"}
                        )
                        render_prediction_section(data)
                    else:
                        show_warning(
                            "Data Unavailable",
                            "Unable to fetch market data. Please try again later.",
                            "Check your internet connection or try a different asset"
                        )
                else:
                    st.info("Please select a cryptocurrency to analyze")
                    
            except Exception as e:
                show_error(
                    "Analysis Error",
                    str(e),
                    "Please try different settings or refresh the page"
                )
        
        # Altcoin Analysis Tab
        with tabs[1]:
            try:
                render_altcoin_analysis()
            except Exception as e:
                show_error(
                    "Analysis Error",
                    str(e),
                    "Please try different settings or refresh the page"
                )
        
        # Strategy Builder Tab
        with tabs[2]:
            try:
                render_backtesting_section()
            except Exception as e:
                show_error(
                    "Strategy Error",
                    str(e),
                    "Please try different settings or refresh the page"
                )
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        show_error(
            "Application Error",
            "An unexpected error occurred",
            "Please refresh the page or contact support"
        )

if __name__ == "__main__":
    main()
