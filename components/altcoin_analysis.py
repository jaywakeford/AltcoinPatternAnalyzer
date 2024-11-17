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

SECTORS = {
    'DeFi': ['UNI', 'AAVE', 'COMP', 'MKR', 'SNX'],
    'GameFi': ['AXS', 'SAND', 'MANA', 'ENJ', 'GALA'],
    'RWA': ['RNDR', 'OCEAN', 'FILE', 'AR', 'HNT'],
    'AI': ['AGIX', 'FET', 'OCEAN', 'GRT', 'RLC'],
    'Memecoins': ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK'],
    'Institutional': ['BTC', 'ETH', 'LINK', 'GRT', 'MKR'],
    'Layer-1': ['ETH', 'SOL', 'ADA', 'AVAX', 'DOT']
}

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
            df = df.fillna(0)  # Handle NaN values after conversion
            
            # Add sector classification
            df['sector'] = df['symbol'].apply(lambda x: next(
                (sector for sector, coins in SECTORS.items() if x in coins), 'Other'
            ))
            
            # Add filtering options
            selected_pairs = st.multiselect(
                "Select Trading Pairs",
                options=df['symbol'].unique(),
                default=['BTC'],
                help="Search and select multiple trading pairs"
            )
            
            selected_sectors = st.multiselect(
                "Select Sectors",
                options=df['sector'].unique(),
                help="Filter by market sectors"
            )
            
            # Filter data based on selection
            df_filtered = df
            if selected_pairs:
                df_filtered = df[df['symbol'].isin(selected_pairs)]
            elif selected_sectors:
                df_filtered = df[df['sector'].isin(selected_sectors)]
            
            # Calculate volatility using rolling standard deviation
            df_filtered['volatility'] = (
                df_filtered.groupby('symbol')['change_24h']
                .transform(lambda x: x.rolling(window=24, min_periods=1).std())
                .fillna(0)
            )
            
            # Create market overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                _render_momentum_gauge(df_filtered['momentum'].mean())
            with col2:
                _render_volatility_gauge(df_filtered['volatility'].mean())
            with col3:
                _render_health_gauge(50 + df_filtered['change_24h'].mean())
            with col4:
                _render_correlation_gauge(df_filtered)
            
            # Market structure
            st.subheader("Market Structure")
            col1, col2 = st.columns(2)
            with col1:
                _render_market_dominance(df_filtered)
            with col2:
                _render_volume_distribution(df_filtered)
            
            # Sector analysis
            st.subheader("Sector Performance")
            _render_sector_analysis(df_filtered)
            
            # Risk assessment
            st.subheader("Risk Assessment")
            _render_risk_assessment(df_filtered)
            
    except Exception as e:
        logger.error(f"Error in altcoin analysis: {str(e)}")
        st.error("An error occurred while analyzing market data. Please try again.")

def _render_momentum_gauge(momentum: float) -> None:
    """Render momentum gauge."""
    try:
        # Normalize momentum to 0-100 scale
        momentum_normalized = min(100, max(0, float(50 + momentum)))
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=momentum_normalized,
            title={'text': "Market Momentum", 'font': {'color': THEME['text']}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': THEME['muted']},
                'bar': {'color': THEME['primary']},
                'bgcolor': THEME['card_bg'],
                'bordercolor': THEME['muted'],
                'steps': [
                    {'range': [0, 30], 'color': THEME['accent2']},
                    {'range': [30, 70], 'color': THEME['accent1']},
                    {'range': [70, 100], 'color': THEME['secondary']}
                ],
                'threshold': {
                    'line': {'color': THEME['text'], 'width': 4},
                    'thickness': 0.75,
                    'value': momentum_normalized
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            font={'color': THEME['text']}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering momentum gauge: {str(e)}")
        st.warning("Unable to display momentum gauge")

def _render_volatility_gauge(volatility: float) -> None:
    """Render volatility gauge."""
    try:
        # Scale volatility to 0-100
        volatility_normalized = min(100, max(0, float(volatility * 5)))
        
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
                ],
                'threshold': {
                    'line': {'color': THEME['text'], 'width': 4},
                    'thickness': 0.75,
                    'value': volatility_normalized
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            font={'color': THEME['text']}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering volatility gauge: {str(e)}")
        st.warning("Unable to display volatility gauge")

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
                ],
                'threshold': {
                    'line': {'color': THEME['text'], 'width': 4},
                    'thickness': 0.75,
                    'value': health_normalized
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            font={'color': THEME['text']}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering health gauge: {str(e)}")
        st.warning("Unable to display health gauge")

def _render_correlation_gauge(df: pd.DataFrame) -> None:
    """Render BTC correlation gauge."""
    try:
        # Get BTC price changes
        btc_changes = df[df['symbol'] == 'BTC']['change_24h'].values
        if len(btc_changes) == 0:
            raise ValueError("No BTC data available")
            
        # Calculate correlations with proper validation
        correlations = []
        for symbol in df['symbol'].unique():
            if symbol != 'BTC':
                coin_changes = df[df['symbol'] == symbol]['change_24h'].values
                if len(coin_changes) == len(btc_changes) and len(coin_changes) > 1:
                    corr = np.corrcoef(btc_changes, coin_changes)[0, 1]
                    if not np.isnan(corr):
                        correlations.append(corr)
        
        # Calculate average correlation with validation
        avg_correlation = np.mean(correlations) if correlations else 0
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
                ],
                'threshold': {
                    'line': {'color': THEME['text'], 'width': 4},
                    'thickness': 0.75,
                    'value': correlation_normalized
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            font={'color': THEME['text']}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering correlation gauge: {str(e)}")
        st.warning("Unable to display correlation gauge")

def _render_market_dominance(df: pd.DataFrame) -> None:
    """Render market dominance pie chart."""
    try:
        # Get top 5 by market cap
        top_5 = df.nlargest(5, 'market_cap')
        others_market_cap = df.nsmallest(len(df)-5, 'market_cap')['market_cap'].sum()
        
        # Create data for pie chart
        data = pd.concat([
            top_5,
            pd.DataFrame([{
                'symbol': 'Others',
                'market_cap': others_market_cap
            }])
        ])
        
        fig = go.Figure(data=[
            go.Pie(
                labels=data['symbol'],
                values=data['market_cap'],
                hole=0.4,
                textinfo='label+percent',
                marker=dict(colors=[
                    THEME['primary'],
                    THEME['secondary'],
                    THEME['accent1'],
                    THEME['accent2'],
                    THEME['accent3'],
                    THEME['muted']
                ])
            )
        ])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Market Dominance",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering market dominance: {str(e)}")
        st.warning("Unable to display market dominance")

def _render_volume_distribution(df: pd.DataFrame) -> None:
    """Render volume distribution chart."""
    try:
        top_10 = df.nlargest(10, 'volume_24h')
        
        fig = go.Figure(data=[
            go.Bar(
                x=top_10['symbol'],
                y=top_10['volume_24h'],
                text=top_10['volume_24h'].apply(lambda x: f"${x:,.0f}"),
                textposition='auto',
                marker_color=THEME['primary']
            )
        ])
        
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

def _render_sector_analysis(df: pd.DataFrame) -> None:
    """Render sector analysis."""
    try:
        # Calculate sector performance
        sector_performance = df.groupby('sector').agg({
            'change_24h': 'mean',
            'market_cap': 'sum',
            'volume_24h': 'sum'
        }).reset_index()
        
        # Ensure numeric values
        for col in ['change_24h', 'market_cap', 'volume_24h']:
            sector_performance[col] = pd.to_numeric(sector_performance[col], errors='coerce')
        
        fig = go.Figure(data=[
            go.Bar(
                x=sector_performance['sector'],
                y=sector_performance['change_24h'],
                text=sector_performance['change_24h'].apply(lambda x: f"{x:.2f}%"),
                textposition='auto',
                marker_color=sector_performance['change_24h'].apply(
                    lambda x: THEME['accent2'] if x > 0 else THEME['secondary']
                )
            )
        ])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Sector Performance",
            xaxis_title="Sector",
            yaxis_title="Average 24h Change (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering sector analysis: {str(e)}")
        st.warning("Unable to display sector analysis")

def _render_risk_assessment(df: pd.DataFrame) -> None:
    """Render risk assessment."""
    try:
        # Calculate risk scores
        df['risk_score'] = (
            df['volatility'] * 0.4 +
            abs(df['change_24h']) * 0.3 +
            (df['market_cap'].rank(ascending=True) / len(df)) * 0.3
        ) * 100
        
        # Get top coins by market cap
        top_coins = df.nlargest(6, 'market_cap')
        
        # Create columns for metrics
        cols = st.columns(3)
        
        # Display risk metrics
        for i, (_, coin) in enumerate(top_coins.iterrows()):
            with cols[i % 3]:
                st.metric(
                    label=f"{coin['symbol']} Risk Score",
                    value=f"{coin['risk_score']:.1f}",
                    delta=f"{coin['change_24h']:.1f}%",
                    delta_color="normal"
                )
                
    except Exception as e:
        logger.error(f"Error rendering risk assessment: {str(e)}")
        st.warning("Unable to display risk assessment")
