from typing import Dict, List, Optional, Union
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from utils.altcoin_analyzer import AltcoinAnalyzer

logger = logging.getLogger(__name__)

# Constants for styling
THEME = {
    'background': '#1a1a2e',
    'card_bg': '#16213e',
    'primary': '#0f3460',
    'secondary': '#e94560',
    'accent1': '#f0a500',
    'accent2': '#00af91',
    'accent3': '#0a81ab',
    'text': '#ffffff',
    'muted': '#a0aec0'
}

# Updated SECTORS with new categories
SECTORS = {
    'Memecoins': ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK'],
    'Real-World Assets (RWA)': ['RNDR', 'OCEAN', 'FILE', 'AR', 'HNT'],
    'Artificial Intelligence (AI)': ['AGIX', 'FET', 'OCEAN', 'GRT', 'RLC'],
    'Decentralized Finance (DeFi)': ['UNI', 'AAVE', 'COMP', 'MKR', 'SNX'],
    'Blockchain Gaming': ['AXS', 'SAND', 'MANA', 'ENJ', 'GALA'],
    'Regulatory Compliance': ['BNB', 'XRP', 'ADA', 'XLM', 'ALGO'],
    'Institutional': ['BTC', 'ETH', 'LINK', 'GRT', 'MKR']
}

def render_altcoin_analysis(view_mode: Optional[str] = None):
    """Main function to render altcoin analysis."""
    try:
        # Initialize analyzer
        analyzer = AltcoinAnalyzer()
        
        # Fetch initial data
        df = analyzer.fetch_top_50_cryptocurrencies()
        
        if df.empty:
            st.error("Unable to fetch cryptocurrency data. Please try again later.")
            return
        
        # Convert numeric columns
        numeric_columns = ['market_cap', 'volume_24h', 'change_24h', 'momentum']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.fillna(0)
        
        # Add sector classification
        df['sector'] = df['symbol'].apply(lambda x: next(
            (sector for sector, coins in SECTORS.items() if x in coins), 'Other'
        ))
        
        # Market Overview Section
        st.subheader("Market Overview")
        
        # Three-column layout for gauges
        col1, col2, col3 = st.columns(3)
        
        with col1:
            _render_health_gauge(50 + df['change_24h'].mean())
        with col2:
            _render_volatility_gauge(df['momentum'].mean() if 'momentum' in df.columns else 0)
        with col3:
            _render_correlation_gauge(df)
        
        # Market Analysis Section
        st.subheader("Market Analysis")
        
        # Two-column layout for visualizations
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            _render_volume_distribution(df)
        
        with viz_col2:
            _render_market_dominance(df)
        
        # Sector Analysis Section
        st.subheader("Sector Analysis")
        _render_sector_performance(df)
        
    except Exception as e:
        logger.error(f"Error in altcoin analysis: {str(e)}")
        st.error("An error occurred while analyzing market data. Please try again.")

def _render_health_gauge(health: float) -> None:
    """Render market health gauge."""
    try:
        health_normalized = min(100, max(0, float(health)))
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_normalized,
            title={'text': "Market Health", 'font': {'color': THEME['text']}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': THEME['muted']},
                'bar': {'color': THEME['primary']},
                'bgcolor': THEME['card_bg'],
                'bordercolor': THEME['muted'],
                'steps': [
                    {'range': [0, 30], 'color': THEME['accent2']},
                    {'range': [30, 70], 'color': THEME['accent1']},
                    {'range': [70, 100], 'color': THEME['secondary']}
                ]
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=300,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering health gauge: {str(e)}")
        st.warning("Unable to display health gauge")

def _render_volatility_gauge(volatility: float) -> None:
    """Render volatility gauge."""
    try:
        volatility_normalized = min(100, max(0, float(volatility)))
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=volatility_normalized,
            title={'text': "Market Volatility", 'font': {'color': THEME['text']}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': THEME['muted']},
                'bar': {'color': THEME['primary']},
                'bgcolor': THEME['card_bg'],
                'bordercolor': THEME['muted'],
                'steps': [
                    {'range': [0, 30], 'color': THEME['accent2']},
                    {'range': [30, 70], 'color': THEME['accent1']},
                    {'range': [70, 100], 'color': THEME['secondary']}
                ]
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=300,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering volatility gauge: {str(e)}")
        st.warning("Unable to display volatility gauge")

def _render_correlation_gauge(df: pd.DataFrame) -> None:
    """Render BTC correlation gauge."""
    try:
        # Calculate average correlation with BTC
        btc_data = df[df['symbol'] == 'BTC']
        if btc_data.empty:
            st.warning("BTC data not available for correlation calculation")
            return
            
        correlations = []
        for symbol in df['symbol'].unique():
            if symbol != 'BTC':
                correlation = df[df['symbol'] == symbol]['change_24h'].corr(btc_data['change_24h'])
                if not pd.isna(correlation):
                    correlations.append(correlation)
        
        if not correlations:
            st.warning("Insufficient data for correlation calculation")
            return
            
        avg_correlation = np.mean(correlations)
        correlation_normalized = (avg_correlation + 1) * 50  # Scale from [-1,1] to [0,100]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=correlation_normalized,
            title={'text': "BTC Correlation", 'font': {'color': THEME['text']}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': THEME['muted']},
                'bar': {'color': THEME['primary']},
                'bgcolor': THEME['card_bg'],
                'bordercolor': THEME['muted'],
                'steps': [
                    {'range': [0, 30], 'color': THEME['accent2']},
                    {'range': [30, 70], 'color': THEME['accent1']},
                    {'range': [70, 100], 'color': THEME['secondary']}
                ]
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=300,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering correlation gauge: {str(e)}")
        st.warning("Unable to display correlation gauge")

def _render_market_dominance(df: pd.DataFrame) -> None:
    """Render market dominance pie chart."""
    try:
        top_5 = df.nlargest(5, 'market_cap')
        others_market_cap = df.nsmallest(len(df)-5, 'market_cap')['market_cap'].sum()
        
        data = pd.concat([
            top_5,
            pd.DataFrame([{
                'symbol': 'Others',
                'market_cap': others_market_cap
            }])
        ])
        
        fig = go.Figure(data=[go.Pie(
            labels=data['symbol'],
            values=data['market_cap'],
            hole=0.4,
            textinfo='label+percent'
        )])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Market Dominance"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering market dominance: {str(e)}")
        st.warning("Unable to display market dominance")

def _render_volume_distribution(df: pd.DataFrame) -> None:
    """Render volume distribution chart."""
    try:
        top_10 = df.nlargest(10, 'volume_24h')
        
        fig = go.Figure(data=[go.Bar(
            x=top_10['symbol'],
            y=top_10['volume_24h'],
            text=top_10['volume_24h'].apply(lambda x: f"${x:,.0f}"),
            textposition='auto'
        )])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Volume Distribution",
            xaxis_title="Symbol",
            yaxis_title="24h Volume (USD)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering volume distribution: {str(e)}")
        st.warning("Unable to display volume distribution")

def _render_sector_performance(df: pd.DataFrame) -> None:
    """Render sector performance analysis."""
    try:
        # Calculate sector metrics
        sector_metrics = df.groupby('sector').agg({
            'change_24h': 'mean',
            'market_cap': 'sum',
            'volume_24h': 'sum'
        }).round(2)
        
        # Create sector performance visualization
        fig = go.Figure(data=[
            go.Bar(
                x=sector_metrics.index,
                y=sector_metrics['change_24h'],
                text=sector_metrics['change_24h'].apply(lambda x: f"{x:,.2f}%"),
                textposition='auto',
                marker_color=sector_metrics['change_24h'].apply(
                    lambda x: THEME['accent2'] if x > 0 else THEME['secondary']
                )
            )
        ])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Sector Performance (24h Change)",
            xaxis_title="Sector",
            yaxis_title="Average 24h Change (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering sector performance: {str(e)}")
        st.warning("Unable to display sector performance")
