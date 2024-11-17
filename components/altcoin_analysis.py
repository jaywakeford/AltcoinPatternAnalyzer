import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from utils.altcoin_analyzer import AltcoinAnalyzer

logger = logging.getLogger(__name__)

def render_altcoin_analysis():
    """Main function to render altcoin analysis."""
    try:
        st.markdown("## Market Analysis")
        
        # Initialize analyzer
        analyzer = AltcoinAnalyzer()
        
        # Fetch initial data
        with st.spinner("Fetching market data..."):
            df = analyzer.fetch_top_50_cryptocurrencies()
            
            if df.empty:
                st.error("Unable to fetch cryptocurrency data. Please try again later.")
                return
            
            # Convert numeric columns
            numeric_columns = ['market_cap', 'volume_24h', 'change_24h', 'momentum']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Drop any rows with invalid numeric data
            df = df.dropna(subset=numeric_columns)
            
            if df.empty:
                st.warning("No valid market data available")
                return
        
        # Create tabs for different analysis sections
        tabs = st.tabs([
            "📊 Market Overview",
            "📈 Market Structure"
        ])
        
        # Market Overview Tab - Now includes both market metrics and price analysis
        with tabs[0]:
            _render_market_overview(df)
            _render_price_analysis(df)
            
        # Market Structure Tab
        with tabs[1]:
            _render_market_structure(df)
            
    except Exception as e:
        logger.error(f"Error in altcoin analysis: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

def _render_market_overview(df: pd.DataFrame) -> None:
    """Render comprehensive market overview including gauges and visualizations."""
    try:
        # Calculate market metrics
        total_market_cap = df['market_cap'].sum()
        total_volume = df['volume_24h'].sum()
        avg_change = df['change_24h'].mean()
        volatility = df['change_24h'].std()
        avg_momentum = df['momentum'].mean()
        market_health = min(100, max(0, 50 + (avg_change * 2)))
        
        # Display market metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Market Cap", f"${total_market_cap:,.0f}", delta=f"{avg_change:.2f}%")
        with col2:
            st.metric("24h Volume", f"${total_volume:,.0f}", delta=None)
        with col3:
            st.metric("Market Health", f"{market_health:.1f}%", delta=f"{avg_change:.2f}%")
        with col4:
            st.metric("Volatility", f"{volatility:.2f}", delta=None)
        
        # Market Indicators - Four gauges in a row
        st.subheader("Market Indicators")
        gauge_col1, gauge_col2, gauge_col3, gauge_col4 = st.columns(4)
        
        with gauge_col1:
            _render_momentum_gauge(avg_momentum)
        with gauge_col2:
            _render_volatility_gauge(volatility)
        with gauge_col3:
            _render_health_gauge(market_health)
        with gauge_col4:
            _render_correlation_gauge(df)
        
        # Volume Distribution
        st.subheader("Volume Analysis")
        _render_volume_distribution(df)
            
    except Exception as e:
        logger.error(f"Error rendering market overview: {str(e)}")
        st.error("Unable to display market overview")

def _render_correlation_gauge(df: pd.DataFrame) -> None:
    """Render correlation gauge showing BTC correlation with market."""
    try:
        # Calculate BTC correlation
        btc_data = df[df['symbol'] == 'BTC']
        if not btc_data.empty:
            other_coins = df[df['symbol'] != 'BTC']
            correlations = []
            for _, coin_data in other_coins.iterrows():
                correlation = np.corrcoef(btc_data['change_24h'], coin_data['change_24h'])[0, 1]
                correlations.append(correlation)
            avg_correlation = np.mean(correlations) if correlations else 0
            
            # Scale correlation to 0-100 for gauge
            correlation_score = (avg_correlation + 1) * 50  # Scale from [-1,1] to [0,100]
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=correlation_score,
                title={'text': "BTC Correlation"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 20], 'color': "red"},
                        {'range': [20, 40], 'color': "orange"},
                        {'range': [40, 60], 'color': "yellow"},
                        {'range': [60, 80], 'color': "lightgreen"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': correlation_score
                    }
                }
            ))
            
            fig.update_layout(
                template="plotly_dark",
                height=300,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        logger.error(f"Error rendering correlation gauge: {str(e)}")
        st.error("Unable to display correlation gauge")

def _render_price_analysis(df: pd.DataFrame) -> None:
    """Render price analysis visualizations."""
    try:
        # Price Changes Section
        st.subheader("24h Price Changes")
        fig = go.Figure(data=[
            go.Scatter(
                x=df.nlargest(15, 'change_24h')['symbol'],
                y=df.nlargest(15, 'change_24h')['change_24h'],
                mode='markers+text',
                text=df.nlargest(15, 'change_24h')['symbol'],
                marker=dict(
                    size=df.nlargest(15, 'change_24h')['volume_24h'] / df['volume_24h'].max() * 50,
                    color=df.nlargest(15, 'change_24h')['change_24h'],
                    colorscale='RdYlGn',
                    showscale=True
                )
            )
        ])
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
            yaxis_title="24h Change (%)",
            xaxis_title="Symbol",
            title="Top Price Movers"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Price Correlations
        st.subheader("Price Change Correlations")
        correlation_matrix = df[['symbol', 'change_24h']].set_index('symbol')
        fig = px.imshow(
            correlation_matrix.corr(),
            color_continuous_scale='RdBu',
            title="Price Change Correlation Matrix"
        )
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering price analysis: {str(e)}")
        st.error("Unable to display price analysis")

def _render_market_structure(df: pd.DataFrame) -> None:
    """Render market structure visualizations."""
    try:
        # Market Cap Distribution
        st.subheader("Market Structure Analysis")
        
        # Bitcoin Dominance Flow
        btc_data = df[df['symbol'] == 'BTC'].iloc[0]
        market_phases = {
            'Bitcoin': btc_data['market_cap'],
            'Large Caps': df[(df['rank'] > 1) & (df['rank'] <= 10)]['market_cap'].sum(),
            'Mid Caps': df[(df['rank'] > 10) & (df['rank'] <= 25)]['market_cap'].sum(),
            'Small Caps': df[df['rank'] > 25]['market_cap'].sum()
        }
        
        fig = go.Figure(go.Waterfall(
            name="Market Flow",
            orientation="v",
            measure=["relative"] * len(market_phases),
            x=list(market_phases.keys()),
            y=list(market_phases.values()),
            text=[f"${val:,.0f}" for val in market_phases.values()],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "green"}},
            decreasing={"marker": {"color": "red"}}
        ))
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
            yaxis_title="Market Cap (USD)",
            xaxis_title="Market Segments",
            title="Market Cap Distribution Flow"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Market Share Pie Chart
        fig = go.Figure(data=[
            go.Pie(
                labels=df.nlargest(5, 'market_cap')['symbol'],
                values=df.nlargest(5, 'market_cap')['market_cap'],
                hole=0.4,
                textinfo='label+percent',
                marker=dict(colors=px.colors.qualitative.Set3)
            )
        ])
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
            showlegend=True,
            title="Top 5 Market Share Distribution",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering market structure: {str(e)}")
        st.error("Unable to display market structure")

def _render_momentum_gauge(momentum: float) -> None:
    """Render momentum gauge."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=momentum,
        title={'text': "Market Momentum"},
        gauge={
            'axis': {'range': [-40, 40]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [-40, -20], 'color': "red"},
                {'range': [-20, 0], 'color': "orange"},
                {'range': [0, 20], 'color': "lightgreen"},
                {'range': [20, 40], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': momentum
            }
        }
    ))
    fig.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

def _render_volatility_gauge(volatility: float) -> None:
    """Render volatility gauge."""
    volatility_normalized = min(100, max(-100, volatility * 10))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=volatility_normalized,
        title={'text': "Volatility Index"},
        gauge={
            'axis': {'range': [-100, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [-100, -60], 'color': "red"},
                {'range': [-60, -20], 'color': "orange"},
                {'range': [-20, 20], 'color': "yellow"},
                {'range': [20, 60], 'color': "lightgreen"},
                {'range': [60, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': volatility_normalized
            }
        }
    ))
    fig.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

def _render_health_gauge(health: float) -> None:
    """Render health gauge."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health,
        title={'text': "Market Health"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 20], 'color': "red"},
                {'range': [20, 40], 'color': "orange"},
                {'range': [40, 60], 'color': "yellow"},
                {'range': [60, 80], 'color': "lightgreen"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': health
            }
        }
    ))
    fig.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

def _render_volume_distribution(df: pd.DataFrame) -> None:
    """Render volume distribution chart."""
    try:
        top_10 = df.nlargest(10, 'volume_24h')
        fig = go.Figure(data=[
            go.Bar(
                x=top_10['symbol'],
                y=top_10['volume_24h'],
                marker=dict(
                    color=top_10['change_24h'],
                    colorscale='RdYlGn',
                    showscale=True
                ),
                text=top_10['change_24h'].apply(lambda x: f"{x:.2f}%"),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
            yaxis_title="24h Volume (USD)",
            xaxis_title="Symbol",
            showlegend=False,
            title="Top 10 Volume Distribution"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering volume distribution: {str(e)}")
        st.error("Unable to display volume distribution")