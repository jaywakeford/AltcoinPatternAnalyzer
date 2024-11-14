import streamlit as st
import pandas as pd
import logging
import pytz
import time
from datetime import datetime

from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.predictions import render_prediction_section
from components.backtesting import render_backtesting_section
from utils.data_fetcher import get_crypto_data, get_exchange_status, detect_region
from utils.ui_components import show_error, show_warning, show_data_source_info, show_exchange_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables with error handling."""
    try:
        # Basic state variables
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
        if 'exchange_status' not in st.session_state:
            st.session_state.exchange_status = None
        if 'error_shown' not in st.session_state:
            st.session_state.error_shown = False
        if 'selected_region' not in st.session_state:
            st.session_state.selected_region = detect_region()
        if 'selected_timezone' not in st.session_state:
            st.session_state.selected_timezone = 'UTC'
        if 'data_source' not in st.session_state:
            st.session_state.data_source = None
        if 'fallback_active' not in st.session_state:
            st.session_state.fallback_active = False
        if 'startup_complete' not in st.session_state:
            st.session_state.startup_complete = False
        if 'initialization_attempts' not in st.session_state:
            st.session_state.initialization_attempts = 0
            
        return True
            
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        if not st.session_state.get('error_shown'):
            show_error(
                "Initialization Error",
                "Failed to initialize application state",
                "Please refresh the page"
            )
            st.session_state.error_shown = True
        return False

def initialize_exchanges():
    """Initialize exchanges with proper error handling and retry logic."""
    try:
        if st.session_state.initialization_attempts >= 3:
            show_warning(
                "Exchange Connection Limited",
                "Maximum initialization attempts reached",
                "Using CoinGecko as fallback data source"
            )
            st.session_state.fallback_active = True
            return True
            
        st.session_state.initialization_attempts += 1
        max_retries = 3
        retry_count = 0
        exchange_status = None
        
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        while retry_count < max_retries:
            try:
                progress_text.text(f"🔄 Initializing exchange connections (Attempt {retry_count + 1}/{max_retries})...")
                progress_bar.progress((retry_count + 1) / max_retries)
                
                exchange_status = get_exchange_status()
                if exchange_status:
                    break
            except Exception as e:
                retry_count += 1
                logger.warning(f"Exchange connection attempt {retry_count} failed: {str(e)}")
                if retry_count < max_retries:
                    progress_text.text(f"⏳ Retrying exchange connection ({retry_count}/{max_retries})")
                    time.sleep(1)
                continue
                
        progress_text.empty()
        progress_bar.empty()
        
        if not exchange_status:
            show_warning(
                "Exchange Connection Limited",
                "Unable to connect to primary exchanges",
                "Using CoinGecko as fallback data source"
            )
            st.session_state.fallback_active = True
            return True

        available_count = len([x for x in exchange_status.values() if x['status'] == 'available'])
        st.session_state.exchange_status = exchange_status
        st.session_state.initialized = True

        if available_count > 0:
            st.success(f"✅ Successfully connected to {available_count} exchanges!")
            show_exchange_status(exchange_status)
            st.session_state.fallback_active = False
            return True
        else:
            show_warning(
                "Limited Exchange Access",
                "No exchanges are currently available in your region",
                "Using CoinGecko as fallback data source"
            )
            st.session_state.fallback_active = True
            return True

    except Exception as e:
        logger.error(f"Exchange initialization error: {str(e)}")
        show_warning(
            "Exchange Connection Error",
            str(e),
            "Using CoinGecko as fallback data source"
        )
        st.session_state.fallback_active = True
        return True

def fetch_crypto_data(coin: str, timeframe: str) -> pd.DataFrame:
    """Fetch cryptocurrency data with enhanced fallback handling."""
    try:
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        progress_text.text(f"📊 Fetching data for {coin.upper()}...")
        progress_bar.progress(0.3)
        
        data = get_crypto_data(coin, timeframe)
        progress_bar.progress(0.7)
        
        if isinstance(data, pd.DataFrame) and not data.empty:
            source_info = {
                "Asset": coin.upper(),
                "Timeframe": f"{timeframe} days",
                "Region": st.session_state.selected_region,
                "Status": "🟢 Live" if not st.session_state.fallback_active else "🟡 Fallback"
            }
            
            if st.session_state.fallback_active:
                source_info["Note"] = "Using CoinGecko as fallback data source"
                source_info["Status"] = "🟡 Fallback Mode"
                
            progress_bar.progress(1.0)
            progress_text.empty()
            progress_bar.empty()
            
            show_data_source_info(
                st.session_state.data_source or "CoinGecko",
                source_info
            )
            return data
        
        progress_text.empty()
        progress_bar.empty()
        
        show_warning(
            "Data Source Warning",
            f"Unable to fetch data for {coin.upper()}",
            "Please try a different asset or timeframe"
        )
        return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching crypto data: {str(e)}")
        progress_text.empty()
        progress_bar.empty()
        
        show_warning(
            "Data Fetch Error",
            str(e),
            "Please try a different asset or timeframe"
        )
        return pd.DataFrame()

def main():
    """Main application entry point with enhanced error handling."""
    try:
        # Initialize session state
        if not initialize_session_state():
            st.stop()

        # Create main layout
        st.title("🚀 Cryptocurrency Analysis Platform")
        
        # Initialize exchanges if not already done
        if not st.session_state.initialized:
            if not initialize_exchanges():
                st.stop()
            st.session_state.startup_complete = True
        
        # Show connection status in sidebar
        if st.session_state.fallback_active:
            st.sidebar.warning("⚠️ Using CoinGecko as fallback data source")
            st.sidebar.info("💡 Click 'Retry Connection' to attempt reconnecting to exchanges")
            if st.sidebar.button("🔄 Retry Connection"):
                st.session_state.initialized = False
                st.session_state.initialization_attempts = 0
                st.experimental_rerun()
        elif st.session_state.exchange_status:
            show_exchange_status(st.session_state.exchange_status)
        
        # Render sidebar with regional optimization
        sidebar_config = render_sidebar()
        
        if not sidebar_config:
            show_error(
                "Configuration Error",
                "Failed to load sidebar configuration",
                "Please refresh the page"
            )
            st.stop()
        
        # Create tabs for different sections
        tabs = st.tabs(["📈 Price Analysis", "🔄 Altcoin Analysis", "⚙️ Strategy Builder"])
        
        # Price Analysis Tab
        with tabs[0]:
            if sidebar_config.get('selected_coins'):
                coin = sidebar_config['selected_coins'][0]
                data = fetch_crypto_data(coin, sidebar_config['timeframe'])
                
                if not data.empty:
                    render_prediction_section(data)
                else:
                    st.info("🔄 Please select a different cryptocurrency or try again later")
            else:
                st.info("🎯 Please select a cryptocurrency to analyze")
        
        # Altcoin Analysis Tab
        with tabs[1]:
            render_altcoin_analysis()
        
        # Strategy Builder Tab
        with tabs[2]:
            render_backtesting_section()
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        show_error(
            "Application Error",
            str(e),
            "Please refresh the page"
        )

if __name__ == "__main__":
    main()
