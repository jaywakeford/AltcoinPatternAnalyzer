import plotly.graph_objects as go
import streamlit as st
from utils.technical_analysis import calculate_sma, calculate_ema, calculate_rsi, calculate_macd
from utils.data_fetcher import get_bitcoin_dominance

def render_price_charts(df, selected_indicators):
    """Render price charts with optimized layout and sizing."""
    with st.container():
        # Main price chart with increased height and responsive sizing
        fig = go.Figure()
        
        # Add price candlesticks with improved styling
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['price'],
            name="Price",
            line=dict(color='#17C37B', width=2)
        ))
        
        # Add technical indicators with improved visibility
        if selected_indicators['SMA']:
            sma = calculate_sma(df, 20)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=sma,
                name="SMA (20)",
                line=dict(color='#FF9900', width=1.5, dash='dot')
            ))
        
        if selected_indicators['EMA']:
            ema = calculate_ema(df, 20)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=ema,
                name="EMA (20)",
                line=dict(color='#00FFFF', width=1.5, dash='dot')
            ))
        
        # Optimize chart layout
        fig.update_layout(
            title={
                'text': "Price Chart",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20)
            },
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            template="plotly_dark",
            height=600,  # Increased height
            margin=dict(l=60, r=60, t=80, b=60),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=1,
                font=dict(size=12)
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(255,255,255,0.1)'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Create two columns for additional indicators
        if selected_indicators['RSI'] or selected_indicators['MACD']:
            col1, col2 = st.columns(2)
            
            if selected_indicators['RSI']:
                with col1:
                    render_rsi_chart(df)
            
            if selected_indicators['MACD']:
                with col2:
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
    
    # Add overbought/oversold lines with annotations
    fig.add_hline(
        y=70,
        line_color="red",
        line_dash="dash",
        annotation_text="Overbought (70)",
        annotation_position="right"
    )
    fig.add_hline(
        y=30,
        line_color="green",
        line_dash="dash",
        annotation_text="Oversold (30)",
        annotation_position="right"
    )
    
    fig.update_layout(
        title={
            'text': "RSI Indicator",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        yaxis_title="RSI Value",
        template="plotly_dark",
        height=350,  # Increased height
        margin=dict(l=50, r=50, t=50, b=50),  # Increased margins
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div style="padding: 20px 0;"></div>', unsafe_allow_html=True)

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
        title={
            'text': "MACD Indicator",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        yaxis_title="Value",
        template="plotly_dark",
        height=350,  # Increased height
        margin=dict(l=50, r=50, t=50, b=50),  # Increased margins
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div style="padding: 20px 0;"></div>', unsafe_allow_html=True)

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
            title={
                'text': "Bitcoin Market Dominance",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            yaxis_title="Dominance (%)",
            template="plotly_dark",
            height=350,  # Increased height
            margin=dict(l=50, r=50, t=50, b=50),  # Increased margins
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=1
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div style="padding: 20px 0;"></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error rendering dominance chart: {str(e)}")