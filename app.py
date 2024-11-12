import streamlit as st
import logging
from datetime import datetime
import sys

# Configure logging with more detailed error tracking
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
from components.strategy_builder import StrategyBuilder
from utils.data_fetcher import get_crypto_data
from styles.theme import apply_custom_theme
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def handle_websocket_error():
    """Handle WebSocket connection errors."""
    st.warning("Connection issue detected. Trying to reconnect...")
    try:
        st.experimental_rerun()
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
                if not df.empty:
                    # Market metrics section
                    col1, col2, col3 = st.columns(3)
                    render_market_metrics(df, col1, col2, col3)
                else:
                    st.warning("No market data available. Please try again later.")
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            st.error("Unable to fetch market data. Please try again later.")
        
        # Strategy Builder section
        try:
            st.markdown("---")  # Visual separator
            strategy_builder = StrategyBuilder()
            strategy_config = strategy_builder.render()
            
            if strategy_config:
                st.success("Strategy configured successfully!")
                logger.info("New strategy created")
        except Exception as e:
            logger.error(f"Error in strategy builder: {str(e)}")
            st.error("Error in strategy builder. Please try again.")
            st.info("""
            💡 Troubleshooting tips:
            - Check your strategy parameters
            - Ensure all required fields are filled
            - Try simplifying your strategy rules
            """)
        
        # Technical Analysis section
        if selected_coins and df is not None and not df.empty:
            try:
                st.subheader("Price Analysis")
                render_price_charts(df, selected_indicators)
                
                # Add prediction section here
                render_prediction_section(df)
                
                st.subheader("Bitcoin Dominance Trend")
                render_dominance_chart(timeframe)
            except Exception as e:
                logger.error(f"Error rendering charts: {str(e)}")
                st.error("Unable to render charts. Please try again later.")
        
        # Altcoin Analysis Section
        try:
            render_altcoin_analysis()
        except Exception as e:
            logger.error(f"Error in altcoin analysis: {str(e)}")
            st.error("Error in altcoin analysis. Some features might be temporarily unavailable.")
        
        # Sentiment Analysis section
        try:
            if selected_coins:
                st.subheader("Social Media & News Sentiment Analysis")
                st.caption("""
                Sentiment analysis combines data from multiple sources including social media, news feeds, and market data.
                The analysis provides real-time insights into market sentiment across different platforms.
                """)
                render_sentiment_analysis(selected_coins)
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            st.error("Error in sentiment analysis. Some data sources might be temporarily unavailable.")
        
        # Backtesting section with improved error handling
        st.markdown("---")  # Visual separator
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