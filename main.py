import streamlit as st

st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

from components.sidebar import render_sidebar
from components.charts import render_price_charts, render_dominance_chart
from components.metrics import render_market_metrics
from components.sentiment import render_sentiment_analysis
from utils.data_fetcher import get_crypto_data
from styles.theme import apply_custom_theme
import plotly.io as pio

def main():
    # Apply custom theme
    apply_custom_theme()
    
    # Render sidebar and get selected options
    selected_coins, timeframe, selected_indicators = render_sidebar()
    
    # Main content
    st.title("Cryptocurrency Analysis Platform")
    
    try:
        # Fetch data for BTC as the primary reference
        df_btc = get_crypto_data("bitcoin", timeframe)
        
        if not df_btc.empty:
            # Market metrics section
            col1, col2, col3 = st.columns(3)
            render_market_metrics(df_btc, col1, col2, col3)
        else:
            st.warning("Unable to fetch market data. Please try again later.")
    except Exception as e:
        st.error(f"Error fetching market data: {str(e)}")
    
    # Sentiment Analysis section
    try:
        render_sentiment_analysis(selected_coins)
    except Exception as e:
        st.error(f"Error in sentiment analysis: {str(e)}")
        st.info("Please try refreshing the page or selecting fewer coins to analyze.")
    
    # Technical Analysis section
    st.subheader("Price Analysis")
    try:
        if not df_btc.empty:
            render_price_charts(df_btc, selected_indicators)
    except Exception as e:
        st.error(f"Error rendering price charts: {str(e)}")
    
    # Bitcoin dominance
    st.subheader("Bitcoin Dominance Trend")
    try:
        render_dominance_chart(timeframe)
    except Exception as e:
        st.error(f"Error rendering dominance chart: {str(e)}")
    
    # Phase Analysis
    st.subheader("Market Phase Analysis")
    phase_col1, phase_col2 = st.columns(2)
    
    with phase_col1:
        st.markdown("""
        ### Current Phase Indicators
        - Bitcoin Price Action
        - Market Sentiment
        - Volume Analysis
        """)
    
    with phase_col2:
        st.markdown("""
        ### Strategy Recommendations
        - Focus on large-cap assets
        - Monitor volume triggers
        - Watch for altcoin momentum
        """)

if __name__ == "__main__":
    main()
