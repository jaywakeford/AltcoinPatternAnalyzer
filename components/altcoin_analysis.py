from typing import Dict, List, Optional, Union
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from utils.altcoin_analyzer import AltcoinAnalyzer
from utils.symbol_converter import SymbolConverter

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
    'DeFi': ['UNI', 'AAVE', 'COMP', 'MKR', 'SNX'],
    'Layer-1': ['ETH', 'SOL', 'ADA', 'AVAX', 'DOT'],
    'Layer-2': ['MATIC', 'OP', 'ARB', 'IMX', 'LRC'],
    'Gaming': ['AXS', 'SAND', 'MANA', 'ENJ', 'GALA'],
    'AI & Data': ['OCEAN', 'FET', 'AGIX', 'GRT', 'RLC'],
    'Infrastructure': ['LINK', 'GRT', 'FIL', 'ATOM', 'QNT'],
    'Exchange': ['BNB', 'CRO', 'FTT', 'OKB', 'HT']
}

def render_altcoin_analysis(view_mode: Optional[str] = None) -> None:
    """Main function to render altcoin analysis with consolidated market overview."""
    try:
        # Initialize analyzer
        analyzer = AltcoinAnalyzer()
        
        # Market Overview Section
        st.title("Cryptocurrency Market Analysis")
        
        # Add asset selection at the top
        st.markdown("### Asset Selection")
        col1, col2 = st.columns([3, 1])
        with col1:
            available_pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
            selected_assets = st.multiselect(
                "Select Assets to Analyze",
                options=available_pairs,
                default=["BTC/USDT"],
                help="Choose assets to analyze",
                key=f"market_analysis_assets_{view_mode}"  # Updated key to be unique per view mode
            )

        with col2:
            if st.button("🔄 Refresh Data", help="Update market data"):
                st.experimental_rerun()
        
        if not selected_assets:
            st.warning("Please select at least one asset to analyze")
            return

        # Fetch market data
        with st.spinner("Fetching market data..."):
            df = analyzer.fetch_top_50_cryptocurrencies()
            
            if df.empty:
                st.error("Unable to fetch cryptocurrency data. Please try again later.")
                return
            
            # Add sector classification
            df['sector'] = df['symbol'].apply(lambda x: next(
                (sector for sector, coins in SECTORS.items() if x in coins), 'Other'
            ))
            
            # Convert numeric columns
            numeric_columns = ['market_cap', 'volume_24h', 'change_24h', 'momentum']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.fillna(0)
        
        # Market Overview Section
        st.markdown("### Market Overview")
        st.markdown("Comprehensive analysis of market health, momentum, and correlations")
        
        # Gauge Charts Row
        metric_cols = st.columns(3)
        
        with metric_cols[0]:
            health_value = min(100, max(0, 50 + df['change_24h'].mean()))
            _render_health_gauge(health_value)
            
        with metric_cols[1]:
            momentum_value = min(100, max(0, 50 + df['momentum'].mean()))
            _render_volatility_gauge(momentum_value)
            
        with metric_cols[2]:
            _render_correlation_gauge(df, selected_assets)
        
        # Market Analysis Section
        st.markdown("### Market Insights")
        st.markdown("Detailed analysis of volume distribution and market dominance")
        
        analysis_cols = st.columns(2)
        with analysis_cols[0]:
            _render_volume_distribution(df)
        with analysis_cols[1]:
            _render_market_dominance(df)
        
        # Sector Analysis
        st.markdown("### Sector Performance")
        st.markdown("Analysis of different market sectors and their performance")
        _render_sector_performance(df)
        
    except Exception as e:
        logger.error(f"Error in altcoin analysis: {str(e)}")
        st.error(f"An error occurred while analyzing market data: {str(e)}")

def _render_health_gauge(health: float) -> None:
    """Render market health gauge."""
    try:
        health_normalized = min(100, max(0, float(health)))
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_normalized,
            title={'text': "Market Health", 'font': {'size': 24, 'color': THEME['text']}},
            number={'suffix': "%", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': THEME['accent2']},
                'steps': [
                    {'range': [0, 30], 'color': "red"},
                    {'range': [30, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "green"}
                ]
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': THEME['text']}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering health gauge: {str(e)}")
        st.warning("Unable to display health gauge")

def _render_volatility_gauge(volatility: float) -> None:
    """Render volatility/momentum gauge."""
    try:
        volatility_normalized = min(100, max(0, float(volatility)))
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=volatility_normalized,
            title={'text': "Market Momentum", 'font': {'size': 24, 'color': THEME['text']}},
            number={'suffix': "%", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': THEME['accent1']},
                'steps': [
                    {'range': [0, 30], 'color': "red"},
                    {'range': [30, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "green"}
                ]
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': THEME['text']}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering volatility gauge: {str(e)}")
        st.warning("Unable to display momentum gauge")

def _render_correlation_gauge(df: pd.DataFrame, selected_assets: List[str]) -> None:
    try:
        # Get BTC data first
        btc_data = df[df['symbol'] == 'BTC']
        if btc_data.empty:
            st.warning("BTC data not available for correlation calculation")
            return
            
        correlations = []
        for symbol in selected_assets:
            if symbol != 'BTC/USDT':
                # Extract base symbol from trading pair
                base_symbol = symbol.split('/')[0]
                asset_data = df[df['symbol'] == base_symbol]
                
                if not asset_data.empty:
                    # Calculate correlation using both price change and momentum
                    price_corr = asset_data['change_24h'].corr(btc_data['change_24h'])
                    momentum_corr = asset_data['momentum'].corr(btc_data['momentum'])
                    
                    # Take average of both correlations
                    if not pd.isna(price_corr) and not pd.isna(momentum_corr):
                        avg_corr = (price_corr + momentum_corr) / 2
                        correlations.append(avg_corr)
        
        if not correlations:
            st.warning("Insufficient data for correlation calculation")
            return
            
        avg_correlation = np.mean(correlations)
        correlation_normalized = (avg_correlation + 1) * 50  # Scale from [-1,1] to [0,100]
        
        # Add debug logging
        logger.info(f"BTC correlation values: {correlations}")
        logger.info(f"Average correlation: {avg_correlation:.2f}")
        logger.info(f"Normalized correlation: {correlation_normalized:.2f}%")
        
        # Update gauge display
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=correlation_normalized,
            title={'text': "BTC Correlation", 'font': {'size': 24, 'color': THEME['text']}},
            number={'suffix': "%", 'font': {'size': 20}, 'valueformat': ".1f"},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': THEME['accent3']},
                'steps': [
                    {'range': [0, 30], 'color': "red"},
                    {'range': [30, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "green"}
                ]
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': THEME['text']}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering correlation gauge: {str(e)}")
        st.warning("Unable to display correlation gauge")

def _render_volume_distribution(df: pd.DataFrame) -> None:
    """Render volume distribution chart."""
    try:
        top_10 = df.nlargest(10, 'volume_24h')
        
        fig = go.Figure(data=[go.Bar(
            x=top_10['symbol'],
            y=top_10['volume_24h'],
            text=[f"${x:,.0f}" for x in top_10['volume_24h']],
            textposition='auto',
            marker_color=THEME['accent2']
        )])
        
        fig.update_layout(
            title="Volume Distribution (Top 10)",
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': THEME['text']},
            xaxis={'title': 'Symbol'},
            yaxis={'title': '24h Volume (USD)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering volume distribution: {str(e)}")
        st.warning("Unable to display volume distribution")

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
            textinfo='label+percent',
            marker={'colors': [THEME['accent1'], THEME['accent2'], THEME['accent3'], 
                             THEME['primary'], THEME['secondary'], THEME['muted']]}
        )])
        
        fig.update_layout(
            title="Market Dominance",
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': THEME['text']}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering market dominance: {str(e)}")
        st.warning("Unable to display market dominance")

def _render_sector_performance(df: pd.DataFrame) -> None:
    """Render sector performance analysis."""
    try:
        sector_metrics = df.groupby('sector').agg({
            'change_24h': 'mean',
            'market_cap': 'sum',
            'volume_24h': 'sum'
        }).round(2)
        
        fig = go.Figure(data=[
            go.Bar(
                x=sector_metrics.index,
                y=sector_metrics['change_24h'],
                text=[f"{x:,.2f}%" for x in sector_metrics['change_24h']],
                textposition='auto',
                marker_color=[THEME['accent2'] if x > 0 else THEME['secondary'] 
                            for x in sector_metrics['change_24h']]
            )
        ])
        
        fig.update_layout(
            title="Sector Performance (24h Change)",
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': THEME['text']},
            xaxis={'title': 'Sector'},
            yaxis={'title': 'Average 24h Change (%)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error rendering sector performance: {str(e)}")
        st.warning("Unable to display sector performance")
