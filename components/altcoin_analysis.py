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

SECTORS = {
    'DeFi': ['UNI', 'AAVE', 'COMP', 'MKR', 'SNX'],
    'GameFi': ['AXS', 'SAND', 'MANA', 'ENJ', 'GALA'],
    'RWA': ['RNDR', 'OCEAN', 'FILE', 'AR', 'HNT'],
    'AI': ['AGIX', 'FET', 'OCEAN', 'GRT', 'RLC'],
    'Memecoins': ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK'],
    'Institutional': ['BTC', 'ETH', 'LINK', 'GRT', 'MKR'],
    'Layer-1': ['ETH', 'SOL', 'ADA', 'AVAX', 'DOT']
}

def render_altcoin_analysis(view_mode: Optional[str] = None):
    """Main function to render altcoin analysis."""
    try:
        # Generate unique keys based on view mode
        pairs_key = f"trading_pairs_select_{view_mode or 'default'}"
        sectors_key = f"sectors_select_{view_mode or 'default'}"
        
        # Initialize session state for selections if not exists
        if pairs_key not in st.session_state:
            st.session_state[pairs_key] = ['BTC']
        if sectors_key not in st.session_state:
            st.session_state[sectors_key] = []

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
            df = df.fillna(0)
            
            # Add sector classification
            df['sector'] = df['symbol'].apply(lambda x: next(
                (sector for sector, coins in SECTORS.items() if x in coins), 'Other'
            ))
            
            # Add filtering options
            col1, col2 = st.columns(2)
            with col1:
                selected_pairs = st.multiselect(
                    "Select Trading Pairs",
                    options=df['symbol'].unique(),
                    default=['BTC'],
                    key=pairs_key,
                    help="Search and select multiple trading pairs"
                )
            
            with col2:
                selected_sectors = st.multiselect(
                    "Select Sectors",
                    options=df['sector'].unique(),
                    key=sectors_key,
                    help="Filter by market sectors"
                )
            
            # Filter data based on selection
            df_filtered = df.copy()  # Create a copy to avoid SettingWithCopyWarning
            if selected_pairs:
                if 'BTC' not in selected_pairs:
                    selected_pairs = ['BTC'] + selected_pairs
                df_filtered = df_filtered[df_filtered['symbol'].isin(selected_pairs)]
            elif selected_sectors:
                df_filtered = df_filtered[df_filtered['sector'].isin(selected_sectors)]
                if 'BTC' not in df_filtered['symbol'].values:
                    btc_data = df[df['symbol'] == 'BTC']
                    if not btc_data.empty:
                        df_filtered = pd.concat([btc_data, df_filtered])
            
            # Calculate rolling volatility based on view mode
            window = 24 if view_mode == "historical" else 4
            df_filtered.loc[:, 'volatility'] = df_filtered.groupby('symbol')['change_24h'].transform(
                lambda x: x.rolling(window=window, min_periods=1).std()
            ).fillna(0)
            
            # Market Overview Section
            st.subheader("Market Overview")
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                _render_market_health(df_filtered)
            
            with metrics_col2:
                _render_volatility_gauge(df_filtered['volatility'].mean())
            
            # Market Analysis Section
            st.subheader("Market Analysis")
            analysis_col1, analysis_col2 = st.columns(2)
            
            with analysis_col1:
                _render_volume_distribution(df_filtered)
                _render_correlation_gauge(df_filtered)
            
            with analysis_col2:
                _render_market_dominance(df_filtered)
                _render_sector_analysis(df_filtered)
            
    except Exception as e:
        logger.error(f"Error in altcoin analysis: {str(e)}")
        st.error("An error occurred while analyzing market data. Please try again.")

def _render_market_health(df: pd.DataFrame) -> None:
    """Render consolidated market health metrics."""
    try:
        # Calculate health metrics
        momentum = df['momentum'].mean()
        change_24h = df['change_24h'].mean()
        health_score = 50 + (momentum + change_24h) / 2
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=min(100, max(0, health_score)),
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
                    'value': health_score
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
        
        # Add additional metrics below
        col1, col2 = st.columns(2)
        with col1:
            st.metric("24h Change", f"{change_24h:.2f}%")
        with col2:
            st.metric("Momentum", f"{momentum:.2f}")
            
    except Exception as e:
        logger.error(f"Error rendering market health: {str(e)}")
        st.warning("Unable to display market health")

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

def _render_correlation_gauge(df: pd.DataFrame) -> None:
    """Render BTC correlation gauge with enhanced error handling for single coin selection."""
    try:
        # Check if BTC data is available
        btc_data = df[df['symbol'] == 'BTC']
        if btc_data.empty:
            raise ValueError("BTC data is required for correlation calculations")
            
        btc_changes = btc_data['change_24h'].values
        
        # Calculate correlations with proper validation
        correlations = []
        for symbol in df['symbol'].unique():
            if symbol != 'BTC':
                coin_changes = df[df['symbol'] == symbol]['change_24h'].values
                if len(coin_changes) == len(btc_changes) and len(coin_changes) > 1:
                    corr = np.corrcoef(btc_changes, coin_changes)[0, 1]
                    if not np.isnan(corr):
                        correlations.append(corr)
        
        # Handle single coin selection
        if not correlations:
            st.info("Select additional coins to view correlation metrics")
            return
            
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
        
    except ValueError as ve:
        logger.warning(f"Correlation gauge error: {str(ve)}")
        st.info(str(ve))
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
    """Render risk assessment visualization."""
    try:
        # Calculate risk metrics
        risk_data = df.copy()
        risk_data['risk_score'] = (
            risk_data['volatility'] * 0.4 +
            abs(risk_data['change_24h']) * 0.3 +
            (risk_data['volume_24h'] / risk_data['market_cap']) * 0.3
        ) * 100
        
        # Normalize risk score
        risk_data['risk_score'] = risk_data['risk_score'].clip(0, 100)
        
        # Create risk visualization
        fig = go.Figure()
        
        # Add scatter plot
        fig.add_trace(go.Scatter(
            x=risk_data['volatility'],
            y=risk_data['change_24h'],
            mode='markers+text',
            marker=dict(
                size=risk_data['risk_score'],
                color=risk_data['risk_score'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Risk Score')
            ),
            text=risk_data['symbol'],
            textposition='top center',
            hovertemplate=(
                '<b>%{text}</b><br>' +
                'Volatility: %{x:.2f}<br>' +
                'Change 24h: %{y:.2f}%<br>' +
                'Risk Score: %{marker.size:.0f}<br>' +
                '<extra></extra>'
            )
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=500,
            title="Risk Assessment Matrix",
            xaxis_title="Volatility",
            yaxis_title="24h Change (%)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering risk assessment: {str(e)}")
        st.warning("Unable to display risk assessment")