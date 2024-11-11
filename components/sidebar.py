import streamlit as st

def render_sidebar():
    """Render the sidebar with filtering options."""
    st.sidebar.title("Analysis Settings")
    
    # Coin selection
    selected_coins = st.sidebar.multiselect(
        "Select Cryptocurrencies",
        ["bitcoin", "ethereum", "binancecoin", "cardano", "solana"],
        default=["bitcoin"]
    )
    
    # Timeframe selection
    timeframe = st.sidebar.selectbox(
        "Select Timeframe",
        ["7", "30", "90", "365"],
        index=1,
        format_func=lambda x: f"{x} days"
    )
    
    # Technical indicators
    st.sidebar.subheader("Technical Indicators")
    selected_indicators = {
        "SMA": st.sidebar.checkbox("Simple Moving Average", value=True),
        "EMA": st.sidebar.checkbox("Exponential Moving Average"),
        "RSI": st.sidebar.checkbox("Relative Strength Index"),
        "MACD": st.sidebar.checkbox("MACD")
    }
    
    # Help section
    with st.sidebar.expander("Help & Information"):
        st.markdown("""
        ### How to use this platform:
        1. Select cryptocurrencies to analyze
        2. Choose your preferred timeframe
        3. Enable technical indicators
        4. Use the charts to analyze patterns
        """)
    
    return selected_coins, timeframe, selected_indicators
