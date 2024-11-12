# Must be the first Streamlit command
import streamlit as st
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Cryptocurrency Analysis Platform"
    }
)

import logging
from datetime import datetime
import sys
from typing import Optional, Union, Any, Generator, ContextManager
from utils.data_fetcher import get_crypto_data
from utils.backtesting import Backtester
from styles.theme import apply_custom_theme
from components.sidebar import render_sidebar
from components.charts import render_price_charts, render_dominance_chart
from components.metrics import render_market_metrics
from components.sentiment import render_sentiment_analysis
from components.backtesting import render_backtesting_section
from components.predictions import render_prediction_section
from components.altcoin_analysis import render_altcoin_analysis
from utils.ui_components import show_error, show_warning, group_elements
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def handle_websocket_error():
    """Handle WebSocket connection errors."""
    st.warning("Connection issue detected. Trying to reconnect...")
    try:
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to reconnect: {str(e)}")
        st.error("Unable to establish connection. Please refresh the page.")

def show_screenshot_help():
    """Display screenshot help message."""
    with st.expander("📸 How to Take Screenshots"):
        st.info('''
        To take a screenshot:
        1. Press 'Print Screen' on your keyboard to capture the entire webpage
        2. Or use your browser's built-in screenshot tool (usually Ctrl+Shift+S)
        3. Alternatively, use your operating system's screenshot utility:
           - Windows: Windows + Shift + S
           - macOS: Command + Shift + 3 (full screen) or 4 (selection)
           - Linux: PrtScr or use your distribution's screenshot tool
        
        For best results:
        - Ensure all charts are fully visible
        - Expand any collapsed sections you want to capture
        - Use full-screen mode for better quality
        ''')

def main():
    try:
        # Apply custom theme
        apply_custom_theme()
        
        # Add screenshot help at the top of the page
        show_screenshot_help()
        
        # Render sidebar and get selected options
        selected_coins, timeframe, selected_indicators = render_sidebar()
        
        # Main content
        st.title("Cryptocurrency Analysis Platform")
        
        # Initialize df as None
        df = None
        
        try:
            # Fetch data for the first selected coin
            if selected_coins:
                df = get_crypto_data(selected_coins[0], timeframe)
                if df.empty:
                    st.warning("No market data available. Please try again later.")
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            st.error("Unable to fetch market data. Please try again later.")
            return

        # Create main tabs with optimized spacing
        tabs = st.tabs([
            "Price Analysis & Predictions",
            "Altcoin Analysis & Strategy",
            "Strategy Builder & Testing"
        ])

        with tabs[0]:
            if df is not None and not df.empty:
                # Add padding for better visual separation
                st.markdown('<div style="padding: 10px 0;"></div>', unsafe_allow_html=True)
                
                # Market metrics in first tab with optimized columns
                col1, col2, col3 = st.columns([1, 1, 1], gap="medium")
                render_market_metrics(df, col1, col2, col3)
                
                # Add spacing between sections
                st.markdown('<div style="padding: 20px 0;"></div>', unsafe_allow_html=True)
                
                # Price Analysis section
                st.subheader("Price Analysis")
                render_price_charts(df, selected_indicators)
                
                # Add spacing between sections
                st.markdown('<div style="padding: 20px 0;"></div>', unsafe_allow_html=True)
                
                # Predictions section
                render_prediction_section(df)
                
                # Add spacing between sections
                st.markdown('<div style="padding: 20px 0;"></div>', unsafe_allow_html=True)
                
                # Bitcoin dominance
                st.subheader("Bitcoin Dominance Trend")
                render_dominance_chart(timeframe)
                
                # Add spacing between sections
                st.markdown('<div style="padding: 20px 0;"></div>', unsafe_allow_html=True)
                
                # Sentiment Analysis
                if selected_coins:
                    st.subheader("Market Sentiment Analysis")
                    st.caption("""
                    Sentiment analysis combines data from multiple sources including news feeds, 
                    price movements, and social media. Hover over the metrics to see more details 
                    about confidence scores and data sources.
                    """)
                    render_sentiment_analysis(selected_coins)

        with tabs[1]:
            try:
                render_altcoin_analysis()
            except Exception as e:
                logger.error(f"Error in altcoin analysis: {str(e)}")
                st.error("Error in altcoin analysis. Some features might be temporarily unavailable.")

        with tabs[2]:
            try:
                render_backtesting_section()
            except Exception as e:
                logger.error(f"Error in backtesting module: {str(e)}")
                st.error("Backtesting error:")
                st.error(str(e))
                st.info("""
                💡 Troubleshooting tips:
                - Check if selected timeframe has enough historical data
                - Verify strategy parameters
                - Try a different asset or time period
                """)
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page or try again later.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if "WebSocket" in str(e):
            handle_websocket_error()
        else:
            st.error(f"Application error: {str(e)}")
            logger.error(f"Unhandled error: {str(e)}")