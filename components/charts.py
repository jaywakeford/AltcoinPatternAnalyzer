import plotly.graph_objects as go
import streamlit as st
from utils.technical_analysis import calculate_sma, calculate_ema, calculate_rsi, calculate_macd
from utils.data_fetcher import get_bitcoin_dominance

def render_price_charts(df, selected_indicators):
    """Render price charts with selected technical indicators."""
    fig = go.Figure()
    
    # Add price candlesticks
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['price'],
        name="Price",
        line=dict(color='#17C37B')
    ))
    
    # Add technical indicators
    if selected_indicators['SMA']:
        sma = calculate_sma(df, 20)
        fig.add_trace(go.Scatter(
            x=df.index,
            y=sma,
            name="SMA (20)",
            line=dict(color='#FF9900')
        ))
    
    if selected_indicators['EMA']:
        ema = calculate_ema(df, 20)
        fig.add_trace(go.Scatter(
            x=df.index,
            y=ema,
            name="EMA (20)",
            line=dict(color='#00FFFF')
        ))
    
    # Update layout
    fig.update_layout(
        title="Price Chart",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional indicators in separate charts
    if selected_indicators['RSI']:
        render_rsi_chart(df)
    
    if selected_indicators['MACD']:
        render_macd_chart(df)

def render_rsi_chart(df):
    """Render RSI indicator chart."""
    rsi = calculate_rsi(df)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=rsi,
        name="RSI",
        line=dict(color='#17C37B')
    ))
    
    # Add overbought/oversold lines
    fig.add_hline(y=70, line_color="red", line_dash="dash")
    fig.add_hline(y=30, line_color="green", line_dash="dash")
    
    fig.update_layout(
        title="RSI Indicator",
        yaxis_title="RSI Value",
        template="plotly_dark",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_macd_chart(df):
    """Render MACD indicator chart."""
    macd, signal = calculate_macd(df)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=macd,
        name="MACD",
        line=dict(color='#17C37B')
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=signal,
        name="Signal",
        line=dict(color='#FF9900')
    ))
    
    fig.update_layout(
        title="MACD Indicator",
        yaxis_title="Value",
        template="plotly_dark",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_dominance_chart(timeframe):
    """Render Bitcoin dominance chart."""
    dominance_df = get_bitcoin_dominance(timeframe)
    
    # Check if DataFrame is empty or missing required column
    if dominance_df.empty:
        st.warning("Unable to fetch Bitcoin dominance data. Please try again later.")
        return
    
    if 'btc_dominance' not in dominance_df.columns:
        st.error("Invalid data format: Bitcoin dominance data is not available.")
        return
    
    try:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dominance_df.index,
            y=dominance_df['btc_dominance'],
            name="BTC Dominance",
            fill='tozeroy',
            line=dict(color='#F7931A')
        ))
        
        fig.update_layout(
            title="Bitcoin Market Dominance",
            yaxis_title="Dominance (%)",
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering dominance chart: {str(e)}")
