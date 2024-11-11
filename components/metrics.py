import streamlit as st
import pandas as pd

def render_market_metrics(df: pd.DataFrame, col1, col2, col3):
    """Render key market metrics."""
    current_price = df['price'].iloc[-1]
    price_change = ((df['price'].iloc[-1] / df['price'].iloc[0]) - 1) * 100
    avg_volume = df['volume'].mean()
    
    with col1:
        st.metric(
            label="Current Price",
            value=f"${current_price:,.2f}",
            delta=f"{price_change:.2f}%"
        )
    
    with col2:
        st.metric(
            label="24h Volume",
            value=f"${avg_volume:,.0f}"
        )
    
    with col3:
        volatility = df['price'].pct_change().std() * 100
        st.metric(
            label="Volatility",
            value=f"{volatility:.2f}%"
        )
