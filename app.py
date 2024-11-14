import streamlit as st
import pandas as pd
import logging
import pytz
from datetime import datetime

from components.sidebar import render_sidebar_content
from components.altcoin_analysis import render_altcoin_analysis
from components.predictions import render_prediction_section
from components.backtesting import render_backtesting_section
from components.charts import render_price_charts
from utils.data_fetcher import get_crypto_data
from utils.ui_components import show_error
from styles.theme import apply_custom_theme

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.page = "Price Analysis"
        st.session_state.selected_coins = ["bitcoin"]
        st.session_state.timeframe = "30"
        st.session_state.indicators = {
            "SMA": True,
            "EMA": False,
            "RSI": False,
            "MACD": False
        }
        st.session_state.analysis_state = {
            'start_date': (datetime.now() - pd.Timedelta(days=30)).date(),
            'end_date': datetime.now().date(),
            'selected_cohort': "Market Cap",
            'selected_subcohorts': [],
            'show_tooltips': True,
            'show_guidance': True
        }
        st.session_state.initialized = True
        logger.info("Session state initialized successfully")
    return True

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
        
        # Apply custom theme
        apply_custom_theme()
        
        # Initialize session state
        initialize_session_state()
        
        # Render sidebar
        with st.sidebar:
            sidebar_config = render_sidebar_content()
            if not sidebar_config:
                st.error("Failed to load sidebar configuration")
                return
        
        # Main content area
        st.title("Cryptocurrency Analysis Platform")
        
        # Navigation tabs
        tab1, tab2, tab3 = st.tabs([
            "📈 Price Analysis",
            "🔄 Altcoin Analysis",
            "⚙️ Strategy Builder"
        ])
        
        with tab1:
            if sidebar_config.get('selected_coins'):
                with st.spinner("Loading price analysis..."):
                    coin = sidebar_config['selected_coins'][0]
                    data = get_crypto_data(coin, sidebar_config['timeframe'])
                    if not data.empty:
                        render_prediction_section(data)
                    else:
                        st.info("Please select a cryptocurrency to analyze")
        
        with tab2:
            with st.spinner("Loading altcoin analysis..."):
                render_altcoin_analysis()
        
        with tab3:
            with st.spinner("Loading strategy builder..."):
                render_backtesting_section()
        
        logger.info("Application rendered successfully")
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        show_error(
            "Application Error",
            str(e),
            "Please refresh the page"
        )

if __name__ == "__main__":
    main()
