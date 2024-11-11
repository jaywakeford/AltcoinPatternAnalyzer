import streamlit as st
from components.sidebar import render_sidebar
from components.charts import render_price_charts, render_dominance_chart
from components.metrics import render_market_metrics
from utils.data_fetcher import get_crypto_data
from styles.theme import apply_custom_theme
import plotly.io as pio

# Set page config
st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Apply custom theme
    apply_custom_theme()
    
    # Render sidebar and get selected options
    selected_coins, timeframe, selected_indicators = render_sidebar()
    
    # Main content
    st.title("Cryptocurrency Analysis Platform")
    
    # Fetch data
    df_btc = get_crypto_data("bitcoin", timeframe)
    
    # Market metrics section
    col1, col2, col3 = st.columns(3)
    render_market_metrics(df_btc, col1, col2, col3)
    
    # Charts section
    st.subheader("Price Analysis")
    render_price_charts(df_btc, selected_indicators)
    
    # Bitcoin dominance
    st.subheader("Bitcoin Dominance Trend")
    render_dominance_chart(timeframe)
    
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
