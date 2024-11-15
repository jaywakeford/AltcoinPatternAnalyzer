import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
import pytz
import sys
import traceback

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Log import attempts
try:
    logger.info("Importing components...")
    from components.sidebar import render_sidebar, get_exchange_config
    from components.altcoin_analysis import render_altcoin_analysis
    from components.predictions import render_prediction_section
    from components.backtesting import render_backtesting_section
    from utils.data_fetcher import get_crypto_data, get_exchange_status, detect_region
    from utils.ui_components import show_error, show_warning, show_data_source_info
    from utils.technical_analysis import calculate_advanced_metrics
    from styles.theme import apply_custom_theme
    logger.info("All components imported successfully")
except Exception as e:
    logger.error(f"Error importing components: {str(e)}")
    logger.error(traceback.format_exc())
    raise

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
            'last_update': datetime.now(),
            'current_tab': None,
            'refresh_interval': 15,  # Default refresh interval in seconds
            'auto_refresh': True,    # Auto-refresh enabled by default
            'advanced_metrics': {}   # Store advanced metrics calculations
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
        logger.error(traceback.format_exc())
        if not st.session_state.get('error_shown'):
            show_error(
                "Initialization Error",
                "Failed to initialize application state",
                "Please refresh the page"
            )
            st.session_state.error_shown = True
        return False

def render_advanced_metrics(data: pd.DataFrame):
    """Render advanced metrics visualization."""
    try:
        metrics = calculate_advanced_metrics(data)
        
        # Create metrics layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Volatility Gauge
            fig_vol = go.Figure(go.Indicator(
                mode="gauge+number",
                value=metrics['volatility'],
                title={'text': "Volatility Index"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "rgba(255, 140, 0, 0.8)"},
                    'steps': [
                        {'range': [0, 30], 'color': 'rgba(0, 255, 0, 0.3)'},
                        {'range': [30, 70], 'color': 'rgba(255, 255, 0, 0.3)'},
                        {'range': [70, 100], 'color': 'rgba(255, 0, 0, 0.3)'}
                    ]
                }
            ))
            st.plotly_chart(fig_vol, use_container_width=True)
        
        with col2:
            # Momentum Score
            fig_mom = go.Figure(go.Indicator(
                mode="gauge+number",
                value=metrics['momentum'],
                title={'text': "Momentum Score"},
                gauge={
                    'axis': {'range': [-100, 100]},
                    'bar': {'color': "rgba(0, 128, 255, 0.8)"},
                    'steps': [
                        {'range': [-100, -30], 'color': 'rgba(255, 0, 0, 0.3)'},
                        {'range': [-30, 30], 'color': 'rgba(128, 128, 128, 0.3)'},
                        {'range': [30, 100], 'color': 'rgba(0, 255, 0, 0.3)'}
                    ]
                }
            ))
            st.plotly_chart(fig_mom, use_container_width=True)
        
        with col3:
            # Market Strength
            fig_strength = go.Figure(go.Indicator(
                mode="gauge+number",
                value=metrics['market_strength'],
                title={'text': "Market Strength"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "rgba(0, 255, 128, 0.8)"},
                    'steps': [
                        {'range': [0, 40], 'color': 'rgba(255, 0, 0, 0.3)'},
                        {'range': [40, 60], 'color': 'rgba(255, 255, 0, 0.3)'},
                        {'range': [60, 100], 'color': 'rgba(0, 255, 0, 0.3)'}
                    ]
                }
            ))
            st.plotly_chart(fig_strength, use_container_width=True)
        
        # Volume Profile
        st.subheader("Volume Profile")
        fig_vol_profile = go.Figure()
        fig_vol_profile.add_trace(go.Bar(
            x=data.index,
            y=data['volume'],
            name="Volume",
            marker_color='rgba(0, 128, 255, 0.5)'
        ))
        fig_vol_profile.update_layout(
            title="Trading Volume Distribution",
            xaxis_title="Time",
            yaxis_title="Volume",
            height=300
        )
        st.plotly_chart(fig_vol_profile, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering advanced metrics: {str(e)}")
        st.error("Unable to display advanced metrics. Please try again later.")

def main():
    """Main application entry point with enhanced error handling and layout optimization."""
    try:
        logger.info("Starting main application...")
        # Initialize session state first
        if not initialize_session_state():
            logger.error("Failed to initialize session state")
            st.stop()

        # Refresh interval control in sidebar
        st.sidebar.subheader("Real-time Settings")
        st.session_state.refresh_interval = st.sidebar.slider(
            "Refresh Interval (seconds)",
            min_value=5,
            max_value=60,
            value=st.session_state.refresh_interval,
            step=5
        )
        st.session_state.auto_refresh = st.sidebar.checkbox(
            "Auto Refresh",
            value=st.session_state.auto_refresh
        )

        # Auto-refresh logic
        if st.session_state.auto_refresh:
            time_since_update = (datetime.now() - st.session_state.last_update).total_seconds()
            if time_since_update >= st.session_state.refresh_interval:
                st.session_state.last_update = datetime.now()
                st.experimental_rerun()

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
        
        logger.info("Rendering sidebar...")
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
            logger.error("Failed to load sidebar configuration")
            st.stop()
        
        logger.info("Creating main content tabs...")
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
                    logger.info(f"Fetching data for {coin}...")
                    data = get_crypto_data(coin, sidebar_config['timeframe'])
                    
                    if not data.empty:
                        with st.container():
                            st.markdown('<div class="content-section">', unsafe_allow_html=True)
                            # Add advanced metrics visualization
                            render_advanced_metrics(data)
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
        logger.error(traceback.format_exc())
        show_error(
            "Application Error",
            str(e),
            "Please refresh the page"
        )

if __name__ == "__main__":
    main()
