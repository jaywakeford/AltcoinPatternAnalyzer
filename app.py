import streamlit as st
import logging
from datetime import datetime
import sys

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

# Must be the first Streamlit command
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Cryptocurrency Analysis Platform"
    }
)

from components.sidebar import render_sidebar
from components.charts import render_price_charts, render_dominance_chart
from components.metrics import render_market_metrics
from components.sentiment import render_sentiment_analysis
from components.backtesting import render_backtesting_section
from components.predictions import render_prediction_section
from components.altcoin_analysis import render_altcoin_analysis
from utils.data_fetcher import get_crypto_data
from styles.theme import apply_custom_theme
from dotenv import load_dotenv

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

def main():
    try:
        # Apply custom theme
        apply_custom_theme()
        
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

        # Create main tabs
        tabs = st.tabs([
            "Price Analysis & Predictions",
            "Altcoin Analysis & Strategy",
            "Strategy Builder & Testing"
        ])

        with tabs[0]:
            if df is not None and not df.empty:
                # Market metrics in first tab
                col1, col2, col3 = st.columns(3)
                render_market_metrics(df, col1, col2, col3)
                
                # Price Analysis section
                st.subheader("Price Analysis")
                render_price_charts(df, selected_indicators)
                
                # Predictions section
                render_prediction_section(df)
                
                # Bitcoin dominance
                st.subheader("Bitcoin Dominance Trend")
                render_dominance_chart(timeframe)
                
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