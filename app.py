import streamlit as st
from components.sidebar import render_sidebar
from components.charts import render_price_charts, render_dominance_chart
from components.metrics import render_market_metrics
from components.sentiment import render_sentiment_analysis
from utils.data_fetcher import get_crypto_data
from styles.theme import apply_custom_theme
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            st.info("""
            💡 The analysis will continue with available sources.
            Try refreshing in a few minutes if the issue persists.
            """)
        
        # Technical Analysis section
        if selected_coins and df is not None and not df.empty:
            try:
                st.subheader("Price Analysis")
                render_price_charts(df, selected_indicators)
                
                st.subheader("Bitcoin Dominance Trend")
                render_dominance_chart(timeframe)
            except Exception as e:
                logger.error(f"Error rendering charts: {str(e)}")
                st.error("Unable to render charts. Please try again later.")
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page or try again later.")

if __name__ == "__main__":
    main()
