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
    """Render historical analysis section with enhanced visualization and guidance."""
    st.markdown("""
    ### Historical Sequence Analysis
    
    This section helps you understand the historical patterns and momentum distribution 
    across different cryptocurrency categories. The analysis provides insights into:
    
    - **Momentum Distribution**: Shows how coins are distributed across different momentum ranges
    - **Phase Indicators**: Visualizes key market cycle phases and trend strength
    - **Entry/Exit Points**: Identifies potential trading opportunities
    
    *💡 Use the lookback period slider to adjust the analysis timeframe.*
    """)
    
    lookback_days = st.slider(
        "Lookback Period (days)",
        min_value=30,
        max_value=365,
        value=90,
        help="Adjust the historical data range for analysis"
    )
    
    # Get historical sequence data
    with st.spinner("Analyzing historical patterns..."):
        sequence_data = analyzer.analyze_historical_sequence(
            timeframe='1d',
            lookback_days=lookback_days
        )
    
    if sequence_data:
        # Enhanced momentum distribution plot
        st.markdown("""
        #### 📊 Momentum Distribution Analysis
        
        The momentum distribution shows how cryptocurrencies are spread across different momentum ranges:
        - **Positive Values**: Indicate upward price momentum
        - **Negative Values**: Indicate downward price momentum
        - **Distribution Shape**: Shows market sentiment and trend strength
        
        *💡 Hover over the bars to see detailed statistics.*
        """)
        
        momentum_scores = pd.Series(sequence_data['momentum_scores'])
        
        # Create enhanced histogram with better visual appeal
        fig = go.Figure()
        
        # Add histogram trace with custom styling
        fig.add_trace(go.Histogram(
            x=momentum_scores,
            nbinsx=30,
            name="Coins",
            marker_color='rgba(23, 195, 123, 0.6)',
            marker_line=dict(color='rgba(23, 195, 123, 1)', width=1),
            hovertemplate=(
                "<b>Momentum Range</b>: %{x:.1f} to %{x:.1f} + %{y}<br>" +
                "<b>Number of Coins</b>: %{y}<br>" +
                "<extra></extra>"
            )
        ))
        
        # Add mean and median lines
        mean_momentum = momentum_scores.mean()
        median_momentum = momentum_scores.median()
        
        fig.add_vline(
            x=mean_momentum,
            line_dash="dash",
            line_color="yellow",
            annotation=dict(
                text=f"Mean: {mean_momentum:.1f}",
                font=dict(color="yellow")
            )
        )
        
        fig.add_vline(
            x=median_momentum,
            line_dash="dash",
            line_color="cyan",
            annotation=dict(
                text=f"Median: {median_momentum:.1f}",
                font=dict(color="cyan")
            )
        )
        
        # Update layout with enhanced styling
        fig.update_layout(
            title=dict(
                text="Momentum Distribution",
                font=dict(size=20)
            ),
            xaxis_title="Momentum Score",
            yaxis_title="Number of Coins",
            template="plotly_dark",
            height=500,
            showlegend=False,
            hovermode='x',
            margin=dict(l=50, r=50, t=80, b=50),
            annotations=[
                dict(
                    text="Strong Bearish",
                    x=-75,
                    y=fig.data[0].y.max() if len(fig.data) > 0 else 0,
                    yref="y",
                    xref="x",
                    showarrow=False,
                    font=dict(color="red", size=12)
                ),
                dict(
                    text="Strong Bullish",
                    x=75,
                    y=fig.data[0].y.max() if len(fig.data) > 0 else 0,
                    yref="y",
                    xref="x",
                    showarrow=False,
                    font=dict(color="green", size=12)
                )
            ]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add interpretation guidance
        col1, col2 = st.columns(2)
        with col1:
            st.info("""
            **📈 How to Interpret:**
            - **Skew**: Distribution leaning right indicates bullish momentum
            - **Spread**: Wide spread shows high market volatility
            - **Peaks**: Multiple peaks suggest market segmentation
            """)
        
        with col2:
            st.info("""
            **🎯 Trading Implications:**
            - High positive momentum: Consider taking profits
            - Low negative momentum: Look for potential entries
            - Neutral zone: Focus on range-bound strategies
            """)
        
        # Phase indicators heatmap with enhanced visualization
        if sequence_data['phase_indicators']:
            st.markdown("""
            #### 🌊 Market Phase Analysis
            
            The heatmap below shows different market phases and indicators:
            - **Volume Trend**: Indicates trading activity strength
            - **Price Trend**: Shows directional movement
            - **Volatility**: Measures price fluctuation intensity
            
            *💡 Darker colors indicate stronger signals.*
            """)
            
            phase_df = pd.DataFrame(sequence_data['phase_indicators']).T
            
            # Create enhanced heatmap
            fig = px.imshow(
                phase_df,
                title="Phase Indicators Heatmap",
                color_continuous_scale=[
                    [0, "rgb(165,0,38)"],
                    [0.5, "rgb(49,54,149)"],
                    [1, "rgb(0,104,55)"]
                ],
                aspect="auto",
                labels=dict(
                    color="Strength",
                    x="Indicator",
                    y="Asset"
                )
            )
            
            fig.update_layout(
                height=max(400, len(phase_df) * 20),
                margin=dict(l=50, r=50, t=80, b=50)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Display entry/exit points with enhanced formatting
        st.markdown("### 🎯 Market Entry/Exit Points")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### Entry Opportunities
            *Identified based on momentum and phase analysis*
            """)
            entry_df = pd.DataFrame(sequence_data.get('entry_points', {})).T
            if not entry_df.empty:
                st.dataframe(
                    entry_df,
                    use_container_width=True,
                    height=400
                )
        
        with col2:
            st.markdown("""
            #### Exit Signals
            *Based on momentum shifts and market conditions*
            """)
            exit_df = pd.DataFrame(sequence_data.get('exit_points', {})).T
            if not exit_df.empty:
                st.dataframe(
                    exit_df,
                    use_container_width=True,
                    height=400
                )

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
            values=allocations_df['capital'],
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
        
        # Risk metrics visualization
        st.markdown("#### Risk Metrics")
        risk_df = pd.DataFrame(strategy['risk_metrics']).T
        # Convert negative values to positive for scatter plot size
        risk_df['plot_size'] = risk_df['momentum_score'].abs() + 1
        fig = px.scatter(
            risk_df,
            x='volatility',
            y='volume_factor',
            size='plot_size',
            hover_name=risk_df.index,
            title="Risk-Return Profile",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
