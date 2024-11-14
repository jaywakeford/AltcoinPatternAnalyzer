import streamlit as st
import pandas as pd
import logging
import pytz
from datetime import datetime

from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.predictions import render_prediction_section
from components.backtesting import render_backtesting_section
from utils.data_fetcher import get_crypto_data, get_exchange_status, detect_region
from utils.ui_components import show_error, show_warning, show_data_source_info
from styles.theme import apply_custom_theme

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page configuration first, before any Streamlit commands
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/issues',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': 'Cryptocurrency Analysis Platform - Version 1.0'
    }
)

# Apply custom theme immediately after page config
apply_custom_theme()

def initialize_session_state():
    """Initialize session state variables with enhanced error handling."""
    try:
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
        
        required_states = {
            'exchange_status': None,
            'error_shown': False,
            'selected_region': detect_region(),
            'selected_timezone': 'UTC',
            'data_source': None,
            'sidebar_config': None,
            'last_update': datetime.now()
        }
        
        for key, default_value in required_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.info(f"Initialized {key} in session state")
        
        st.session_state.initialized = True
        logger.info("Session state initialized successfully")
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

def main():
    """Main application entry point with enhanced error handling and layout optimization."""
    try:
        # Initialize session state first
        if not initialize_session_state():
            st.stop()

        # Create main layout with proper spacing
        st.markdown("""
            <style>
                .main-header {
                    text-align: center;
                    padding: 2rem 0;
                    margin-bottom: 2rem;
                    background: rgba(0,0,0,0.2);
                    border-radius: 10px;
                }
                .content-section {
                    padding: 1rem;
                    margin: 1rem 0;
                    background: rgba(0,0,0,0.1);
                    border-radius: 10px;
                }
            </style>
            <div class="main-header">
                <h1>Cryptocurrency Analysis Platform</h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Render sidebar with error boundary
        with st.sidebar:
            sidebar_config = render_sidebar()
            if sidebar_config:
                st.session_state.sidebar_config = sidebar_config
            else:
                sidebar_config = st.session_state.sidebar_config

        if not sidebar_config:
            show_error(
                "Configuration Error",
                "Unable to load sidebar configuration",
                "Please refresh the page"
            )
            st.stop()
        
        # Create main content tabs with proper spacing
        tabs = st.tabs([
            "📈 Price Analysis",
            "🔄 Altcoin Analysis",
            "⚙️ Strategy Builder"
        ])
        
        # Price Analysis Tab
        with tabs[0]:
            if sidebar_config.get('selected_coins'):
                with st.spinner("Loading price analysis..."):
                    coin = sidebar_config['selected_coins'][0]
                    data = get_crypto_data(coin, sidebar_config['timeframe'])
                    
                    if not data.empty:
                        with st.container():
                            st.markdown('<div class="content-section">', unsafe_allow_html=True)
                            render_prediction_section(data)
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("Please select a cryptocurrency or try again later")
        
        # Altcoin Analysis Tab
        with tabs[1]:
            with st.spinner("Loading altcoin analysis..."):
                with st.container():
                    st.markdown('<div class="content-section">', unsafe_allow_html=True)
                    render_altcoin_analysis()
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Strategy Builder Tab
        with tabs[2]:
            with st.spinner("Loading strategy builder..."):
                with st.container():
                    st.markdown('<div class="content-section">', unsafe_allow_html=True)
                    render_backtesting_section()
                    st.markdown('</div>', unsafe_allow_html=True)
        
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
