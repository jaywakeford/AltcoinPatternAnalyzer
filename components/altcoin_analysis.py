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
    'NFT': ['APE', 'SAND', 'MANA', 'AXS', 'ENJ'],
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
            
            # Add proper initialization and validation for volatility
            df['volatility'] = df.get('volatility', pd.Series([0] * len(df)))
            df['volatility'] = pd.to_numeric(df['volatility'], errors='coerce').fillna(0)
            
            # Add sector classification
            df['sector'] = df['symbol'].apply(lambda x: next(
                (sector for sector, coins in SECTORS.items() if x in coins), 'Other'
            ))
            
            # Drop any rows with invalid numeric data
            df = df.dropna(subset=numeric_columns)
            
            if df.empty:
                st.warning("No valid market data available")
                return

        # Create single Market Analysis tab for consolidated view
        _render_market_overview(df)
        _render_market_metrics(df)
        _render_sector_analysis(df)
        _render_market_structure(df)
        _render_risk_assessment(df)
            
    except Exception as e:
        logger.error(f"Error in altcoin analysis: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

def _render_market_overview(df: pd.DataFrame) -> None:
    """Render comprehensive market overview with enhanced visualizations."""
    try:
        # Calculate market metrics
        total_market_cap = df['market_cap'].sum()
        total_volume = df['volume_24h'].sum()
        avg_change = df['change_24h'].mean()
        volatility = df['volatility'].mean()
        avg_momentum = df['momentum'].mean()
        market_health = min(100, max(0, 50 + (avg_change * 2)))

        # Create a row of 4 columns for the gauges
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            _render_momentum_gauge(avg_momentum)
        with col2:
            _render_volatility_gauge(volatility)
        with col3:
            _render_health_gauge(market_health)
        with col4:
            _render_correlation_gauge(df)
        
        # Market Overview Section
        st.subheader("Market Overview")
        
        # Volume Analysis
        _render_volume_distribution(df)
        
        # Market Dominance
        _render_market_dominance(df)
            
    except Exception as e:
        logger.error(f"Error rendering market overview: {str(e)}")
        st.error("Unable to display market overview")

def _render_market_metrics(df: pd.DataFrame) -> None:
    """Render market metrics with real-time updates."""
    try:
        st.subheader("Price Analysis")
        
        # Real-time price change scatter plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['change_24h'],
            y=df['volume_24h'],
            mode='markers',
            marker=dict(
                size=df['market_cap'] / df['market_cap'].max() * 50,
                color=df['momentum'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Momentum")
            ),
            text=df['symbol'],
            hovertemplate="<b>%{text}</b><br>" +
                         "24h Change: %{x:.2f}%<br>" +
                         "Volume: $%{y:,.0f}<br>" +
                         "<extra></extra>"
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=500,
            title="Price Changes vs Volume",
            xaxis_title="24h Price Change (%)",
            yaxis_title="24h Volume (USD)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering market metrics: {str(e)}")
        st.error("Unable to display market metrics")

def _render_sector_analysis(df: pd.DataFrame) -> None:
    """Render sector analysis with performance comparison."""
    try:
        st.subheader("Sector Analysis")
        
        # Calculate sector performance
        sector_performance = df.groupby('sector').agg({
            'change_24h': 'mean',
            'market_cap': 'sum',
            'volume_24h': 'sum'
        }).reset_index()
        
        # Sector Performance Comparison
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=sector_performance['sector'],
            y=sector_performance['change_24h'],
            marker_color=sector_performance['change_24h'].apply(
                lambda x: 'green' if x > 0 else 'red'
            ),
            text=sector_performance['change_24h'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto'
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Sector Performance Comparison",
            xaxis_title="Sector",
            yaxis_title="Average 24h Change (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Sector Correlation Matrix
        sector_corr = df.pivot_table(
            index='sector',
            values='change_24h',
            aggfunc=lambda x: x.tolist()
        )
        correlation_matrix = pd.DataFrame(
            index=sector_corr.index,
            columns=sector_corr.index,
            data=[[np.corrcoef(a, b)[0, 1] if len(a) == len(b) else np.nan
                   for b in sector_corr.values]
                  for a in sector_corr.values]
        )
        
        fig = px.imshow(
            correlation_matrix,
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Sector Correlation Matrix"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering sector analysis: {str(e)}")
        st.error("Unable to display sector analysis")

def _render_market_structure(df: pd.DataFrame) -> None:
    """Render market structure visualizations."""
    try:
        st.subheader("Market Structure Analysis")
        
        # Market Cap Flow
        market_phases = {
            'Bitcoin': df[df['symbol'] == 'BTC']['market_cap'].sum(),
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
            connector={"line": {"color": THEME['muted']}},
            decreasing={"marker": {"color": THEME['secondary']}},
            increasing={"marker": {"color": THEME['accent2']}}
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=500,
            title="Market Cap Distribution Flow",
            xaxis_title="Market Segments",
            yaxis_title="Market Cap (USD)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering market structure: {str(e)}")
        st.error("Unable to display market structure")

def _render_risk_assessment(df: pd.DataFrame) -> None:
    """Render risk assessment cards for top altcoins."""
    try:
        st.subheader("Risk Assessment")
        
        # Calculate risk scores
        df['risk_score'] = (
            df['volatility'] * 0.4 +
            abs(df['change_24h']) * 0.3 +
            (1 / df['market_cap'] * df['market_cap'].max()) * 0.3
        ) * 100
        
        # Create risk assessment cards
        cols = st.columns(3)
        for idx, coin in df.nlargest(6, 'market_cap').iterrows():
            with cols[idx % 3]:
                st.markdown(f"""
                <div style='
                    background-color: {THEME['card_bg']};
                    padding: 1rem;
                    border-radius: 0.5rem;
                    margin-bottom: 1rem;
                '>
                    <h3 style='color: {THEME['text']}'>{coin['symbol']}</h3>
                    <p style='color: {THEME['muted']}'>Risk Score: {coin['risk_score']:.0f}/100</p>
                    <div style='
                        background-color: {THEME['primary']};
                        height: 4px;
                        width: {coin['risk_score']}%;
                        border-radius: 2px;
                    '></div>
                </div>
                """, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Error rendering risk assessment: {str(e)}")
        st.error("Unable to display risk assessment")

def _render_volume_distribution(df: pd.DataFrame) -> None:
    """Render enhanced volume distribution chart."""
    try:
        top_10 = df.nlargest(10, 'volume_24h')
        fig = go.Figure(data=[
            go.Bar(
                x=top_10['symbol'],
                y=top_10['volume_24h'],
                marker=dict(
                    color=top_10['change_24h'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="24h Change (%)")
                ),
                text=top_10['change_24h'].apply(lambda x: f"{x:.2f}%"),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Top 10 Volume Distribution",
            xaxis_title="Symbol",
            yaxis_title="24h Volume (USD)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering volume distribution: {str(e)}")
        st.error("Unable to display volume distribution")

def _render_market_dominance(df: pd.DataFrame) -> None:
    """Render market dominance pie chart with improved styling."""
    try:
        top_5 = df.nlargest(5, 'market_cap')
        others = pd.Series({
            'symbol': 'Others',
            'market_cap': df.nsmallest(len(df)-5, 'market_cap')['market_cap'].sum()
        })
        
        data = pd.concat([top_5, pd.DataFrame([others])], ignore_index=True)
        
        fig = go.Figure(data=[
            go.Pie(
                labels=data['symbol'],
                values=data['market_cap'],
                hole=0.4,
                textinfo='label+percent',
                marker=dict(
                    colors=[
                        THEME['primary'],
                        THEME['secondary'],
                        THEME['accent1'],
                        THEME['accent2'],
                        THEME['accent3'],
                        THEME['muted']
                    ]
                )
            )
        ])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=THEME['background'],
            plot_bgcolor=THEME['card_bg'],
            height=400,
            title="Market Dominance Distribution",
            showlegend=True,
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
        logger.error(f"Error rendering market dominance: {str(e)}")
        st.error("Unable to display market dominance")

def _render_momentum_gauge(momentum: float) -> None:
    """Render momentum gauge with enhanced styling."""
    try:
        # Ensure momentum is a valid number
        if pd.isna(momentum) or not isinstance(momentum, (int, float)):
            momentum = 0
            
        momentum_normalized = min(40, max(-40, float(momentum)))
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=momentum_normalized,
            title={'text': "Market Momentum", 'font': {'color': THEME['text']}},
            gauge={
                'axis': {'range': [-40, 40], 'tickcolor': THEME['muted']},
                'bar': {'color': THEME['primary']},
                'bgcolor': THEME['card_bg'],
                'bordercolor': THEME['muted'],
                'steps': [
                    {'range': [-40, -20], 'color': THEME['secondary']},
                    {'range': [-20, 0], 'color': THEME['accent1']},
                    {'range': [0, 20], 'color': THEME['accent2']},
                    {'range': [20, 40], 'color': THEME['accent3']}
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
        st.error("Unable to display momentum gauge")

def _render_volatility_gauge(volatility: float) -> None:
    """Render volatility gauge with enhanced styling."""
    try:
        # Ensure volatility is a valid number
        if pd.isna(volatility) or not isinstance(volatility, (int, float)):
            volatility = 0
            
        volatility_normalized = min(100, max(0, float(volatility) * 10))
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=volatility_normalized,
            title={'text': "Volatility Index", 'font': {'color': THEME['text']}},
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
    """Render market health gauge with enhanced styling."""
    try:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health,
            title={'text': "Market Health", 'font': {'color': THEME['text']}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': THEME['muted']},
                'bar': {'color': THEME['primary']},
                'bgcolor': THEME['card_bg'],
                'bordercolor': THEME['muted'],
                'steps': [
                    {'range': [0, 25], 'color': THEME['secondary']},
                    {'range': [25, 50], 'color': THEME['accent1']},
                    {'range': [50, 75], 'color': THEME['accent2']},
                    {'range': [75, 100], 'color': THEME['accent3']}
                ],
                'threshold': {
                    'line': {'color': THEME['text'], 'width': 4},
                    'thickness': 0.75,
                    'value': health
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
        st.error("Unable to display health gauge")

def _render_correlation_gauge(df: pd.DataFrame) -> None:
    """Render BTC correlation gauge with enhanced styling."""
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
                title={'text': "BTC Correlation", 'font': {'color': THEME['text']}},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': THEME['muted']},
                    'bar': {'color': THEME['primary']},
                    'bgcolor': THEME['card_bg'],
                    'bordercolor': THEME['muted'],
                    'steps': [
                        {'range': [0, 25], 'color': THEME['secondary']},
                        {'range': [25, 50], 'color': THEME['accent1']},
                        {'range': [50, 75], 'color': THEME['accent2']},
                        {'range': [75, 100], 'color': THEME['accent3']}
                    ],
                    'threshold': {
                        'line': {'color': THEME['text'], 'width': 4},
                        'thickness': 0.75,
                        'value': correlation_score
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
        st.error("Unable to display correlation gauge")