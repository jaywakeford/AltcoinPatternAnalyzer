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
    from components.sidebar import render_sidebar
    from components.altcoin_analysis import render_altcoin_analysis
    from components.backtesting import render_backtesting_section
    from utils.data_fetcher import get_crypto_data, get_exchange_status, detect_region
    from utils.ui_components import show_error, show_warning, show_data_source_info
    from utils.technical_analysis import calculate_advanced_metrics
    logger.info("All components imported successfully")
except Exception as e:
    logger.error(f"Error importing components: {str(e)}")
    logger.error(traceback.format_exc())
    st.error("Failed to import required components. Please check the logs.")
    sys.exit(1)

# Set page configuration
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables with enhanced error handling."""
    try:
        required_states = {
            'exchange_status': None,
            'error_shown': False,
            'selected_region': detect_region(),
            'selected_timezone': 'UTC',
            'data_source': None,
            'sidebar_config': None,
            'last_update': datetime.now(),
            'current_tab': None,
            'refresh_interval': 15,
            'auto_refresh': True,
            'advanced_metrics': {}
        }
        
        for key, default_value in required_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.info(f"Initialized {key} in session state")
        
        logger.info("Session state initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("Failed to initialize application state. Please refresh the page.")
        return False

def render_advanced_metrics(data: pd.DataFrame):
    """Render advanced metrics visualization."""
    try:
        metrics = calculate_advanced_metrics(data)
        
        # Create metrics layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Volatility",
                f"{metrics['volatility']:.2f}%",
                help="Market volatility indicator"
            )
        
        with col2:
            st.metric(
                "Momentum",
                f"{metrics['momentum']:.2f}%",
                help="Price momentum indicator"
            )
        
        with col3:
            st.metric(
                "Market Strength",
                f"{metrics['market_strength']:.2f}",
                help="Overall market strength indicator"
            )
        
        # Create visualizations
        fig = go.Figure()
        
        # Price Chart
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['close'],
            name="Price",
            line=dict(color='#17C37B', width=2)
        ))
        
        # Volume Chart
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['volume'],
            name="Volume",
            yaxis="y2",
            marker_color='rgba(23, 195, 178, 0.2)'
        ))
        
        # Update layout with improved styling
        fig.update_layout(
            title="Price and Volume Analysis",
            yaxis=dict(
                title="Price",
                titlefont=dict(color="#17C37B"),
                tickfont=dict(color="#17C37B")
            ),
            yaxis2=dict(
                title="Volume",
                overlaying="y",
                side="right",
                titlefont=dict(color="rgba(23, 195, 178, 0.6)"),
                tickfont=dict(color="rgba(23, 195, 178, 0.6)")
            ),
            height=500,
            template="plotly_dark",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add auto-refresh functionality
        if st.session_state.auto_refresh:
            time_since_update = (datetime.now() - st.session_state.last_update).total_seconds()
            if time_since_update >= st.session_state.refresh_interval:
                st.session_state.last_update = datetime.now()
                st.experimental_rerun()
        
    except Exception as e:
        logger.error(f"Error rendering advanced metrics: {str(e)}")
        st.error("Unable to display advanced metrics. Please try again later.")

def main():
    """Main application entry point with enhanced error handling."""
    try:
        # Initialize session state
        if not initialize_session_state():
            st.stop()
        
        # Render title and description
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Real-time cryptocurrency analysis with advanced metrics and market insights.
        """)
        
        # Render sidebar
        sidebar_config = render_sidebar()
        if not sidebar_config:
            st.error("Unable to load configuration. Please refresh the page.")
            st.stop()
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs([
            "📈 Price Analysis",
            "🔄 Altcoin Analysis",
            "⚙️ Strategy Builder"
        ])
        
        # Price Analysis Tab
        with tab1:
            if sidebar_config.get('selected_coins'):
                with st.spinner("Loading price analysis..."):
                    coin = sidebar_config['selected_coins'][0]
                    data = get_crypto_data(coin, sidebar_config['timeframe'])
                    
                    if not data.empty:
                        render_advanced_metrics(data)
                    else:
                        st.info("Please select a cryptocurrency to analyze.")
        
        # Altcoin Analysis Tab
        with tab2:
            with st.spinner("Loading altcoin analysis..."):
                render_altcoin_analysis()
        
        # Strategy Builder Tab
        with tab3:
            with st.spinner("Loading strategy builder..."):
                render_backtesting_section()
        
        # Show data source info
        st.sidebar.markdown("---")
        show_data_source_info(
            source=st.session_state.get('data_source', 'unknown'),
            details={'Last Updated': st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}
        )
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"An error occurred: {str(e)}")
        st.error("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
