import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.altcoin_analyzer import AltcoinAnalyzer
import pandas as pd
import numpy as np
from typing import Dict, List
import seaborn as sns

def render_altcoin_analysis():
    """Render the altcoin analysis interface."""
    st.subheader("🔄 Altcoin Analysis & Strategy")
    
    # Initialize analyzer
    analyzer = AltcoinAnalyzer()
    
    # Fetch initial data
    df = analyzer.fetch_top_50_cryptocurrencies()
    
    # Market filters
    st.sidebar.subheader("Market Filters")
    min_market_cap = st.sidebar.number_input(
        "Minimum Market Cap (USD)",
        min_value=0,
        value=1000000,
        step=1000000
    )
    
    min_volume = st.sidebar.number_input(
        "Minimum 24h Volume (USD)",
        min_value=0,
        value=100000,
        step=100000
    )
    
    min_momentum = st.sidebar.slider(
        "Minimum Momentum Score",
        min_value=-100,
        max_value=100,
        value=-20
    )
    
    # Filter data
    filtered_df = df[
        (df['market_cap'] >= min_market_cap) &
        (df['volume_24h'] >= min_volume) &
        (df['momentum'] >= min_momentum)
    ]
    
    # Main content tabs
    tabs = st.tabs([
        "Market Overview",
        "Historical Analysis",
        "Correlation Analysis",
        "Strategy Builder"
    ])
    
    with tabs[0]:
        _render_market_overview(filtered_df)
    
    with tabs[1]:
        _render_historical_analysis(analyzer)
    
    with tabs[2]:
        _render_correlation_analysis(analyzer)
    
    with tabs[3]:
        _render_strategy_builder(analyzer)

def _render_market_overview(df: pd.DataFrame):
    """Render market overview section."""
    st.markdown("### Market Overview")
    
    # Category distribution
    category_counts = df['category'].value_counts()
    
    fig = px.pie(
        values=category_counts.values,
        names=category_counts.index,
        title="Market Cap Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Market metrics table
    st.markdown("### Market Metrics by Category")
    metrics_df = df.groupby('category').agg({
        'market_cap': 'sum',
        'volume_24h': 'sum',
        'change_24h': 'mean',
        'momentum': 'mean'
    }).round(2)
    
    st.dataframe(metrics_df)
    
    # Top movers
    st.markdown("### Top Movers")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top Gainers (24h)**")
        gainers = df.nlargest(5, 'change_24h')[
            ['symbol', 'category', 'change_24h', 'volume_24h']
        ]
        st.dataframe(gainers)
    
    with col2:
        st.markdown("**Top Volume**")
        volume_leaders = df.nlargest(5, 'volume_24h')[
            ['symbol', 'category', 'volume_24h', 'change_24h']
        ]
        st.dataframe(volume_leaders)

def _render_historical_analysis(analyzer: AltcoinAnalyzer):
    """Render historical analysis section."""
    st.markdown("### Historical Sequence Analysis")
    
    lookback_days = st.slider(
        "Lookback Period (days)",
        min_value=30,
        max_value=365,
        value=90
    )
    
    # Get historical sequence data
    sequence_data = analyzer.analyze_historical_sequence(
        timeframe='1d',
        lookback_days=lookback_days
    )
    
    if sequence_data:
        # Plot momentum distribution
        momentum_scores = pd.Series(sequence_data['momentum_scores'])
        fig = px.histogram(
            momentum_scores,
            title="Momentum Distribution",
            nbins=20,
            color_discrete_sequence=['lightblue']
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Phase indicators heatmap
        if sequence_data['phase_indicators']:
            phase_df = pd.DataFrame(sequence_data['phase_indicators']).T
            fig = px.imshow(
                phase_df,
                title="Phase Indicators Heatmap",
                color_continuous_scale="RdYlBu"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Display entry/exit points
        st.markdown("### Market Entry/Exit Points")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Suggested Entry Points**")
            entry_df = pd.DataFrame(sequence_data.get('entry_points', {})).T
            if not entry_df.empty:
                st.dataframe(entry_df)
        
        with col2:
            st.markdown("**Suggested Exit Points**")
            exit_df = pd.DataFrame(sequence_data.get('exit_points', {})).T
            if not exit_df.empty:
                st.dataframe(exit_df)

def _render_correlation_analysis(analyzer: AltcoinAnalyzer):
    """Render correlation analysis section."""
    st.markdown("### Correlation Analysis")
    
    # Get correlation data
    correlation_data = analyzer.analyze_btc_correlation()
    
    if correlation_data:
        # Plot cooling periods
        cooling_periods = pd.DataFrame(correlation_data['cooling_periods'])
        if not cooling_periods.empty:
            fig = px.bar(
                cooling_periods,
                x='start',
                y='duration',
                title="BTC Cooling Periods",
                color='price_change',
                color_continuous_scale="RdYlBu"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Plot alt performance during cooling periods
        alt_performance = pd.DataFrame(correlation_data['alt_performance'])
        if not alt_performance.empty:
            fig = px.box(
                alt_performance.melt(),
                y='value',
                x='variable',
                title="Alt Performance During BTC Cooling",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Correlation heatmap
        st.markdown("### Money Flow Correlation Heatmap")
        if 'correlation_matrix' in correlation_data:
            fig = px.imshow(
                correlation_data['correlation_matrix'],
                title="Inter-coin Correlation Heatmap",
                color_continuous_scale="RdBu"
            )
            st.plotly_chart(fig, use_container_width=True)

def _render_strategy_builder(analyzer: AltcoinAnalyzer):
    """Render strategy builder section."""
    st.markdown("### Stair-stepping Strategy Builder")
    
    initial_capital = st.number_input(
        "Initial Capital (USD)",
        min_value=1000,
        value=10000,
        step=1000
    )
    
    strategy = analyzer.calculate_stair_stepping_strategy(initial_capital)
    
    if strategy:
        # Display allocations
        st.markdown("#### Portfolio Allocations")
        allocations_df = pd.DataFrame(strategy['allocations']).T
        fig = px.pie(
            values=allocations_df['percentage'],
            names=allocations_df.index,
            title="Portfolio Allocation",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display entry/exit strategy
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Entry Strategy")
            for symbol, entry in strategy['entry_points'].items():
                st.markdown(f"**{symbol}**")
                st.write(f"Initial: ${entry['initial']:.2f}")
                st.write("DCA Levels:")
                for i, level in enumerate(entry['dca_levels'], 1):
                    st.write(f"Level {i}: ${level:.2f}")
        
        with col2:
            st.markdown("#### Exit Strategy")
            for symbol, exit_points in strategy['exit_points'].items():
                st.markdown(f"**{symbol}**")
                st.write("Take Profit Levels:")
                for i, level in enumerate(exit_points['take_profit_levels'], 1):
                    st.write(f"TP {i}: ${level:.2f}")
                st.write(f"Stop Loss: ${exit_points['stop_loss']:.2f}")
        
        # Risk metrics visualization with fixed size values
        st.markdown("#### Risk Metrics")
        risk_df = pd.DataFrame(strategy['risk_metrics']).T
        # Convert negative values to positive for scatter plot size
        risk_df['plot_size'] = risk_df['momentum_score'].abs() + 1  # Add 1 to ensure positive values
        fig = px.scatter(
            risk_df,
            x='volatility',
            y='volume_factor',
            size='plot_size',  # Use positive values for size
            hover_name=risk_df.index,
            title="Risk-Return Profile",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)