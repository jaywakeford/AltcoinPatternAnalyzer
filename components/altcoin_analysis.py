import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from utils.altcoin_analyzer import AltcoinAnalyzer
import pandas as pd
import numpy as np
from typing import Dict, List
import seaborn as sns
import logging

logger = logging.getLogger(__name__)

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
        _render_historical_analysis(analyzer, filtered_df)
    
    with tabs[2]:
        _render_correlation_analysis(analyzer)
    
    with tabs[3]:
        _render_strategy_builder(analyzer)

def _render_historical_analysis(analyzer: AltcoinAnalyzer, df: pd.DataFrame):
    """Render historical analysis section with enhanced visualization and guidance."""
    st.markdown("""
    ### Historical Sequence Analysis
    
    This section provides detailed insights into market momentum across different cryptocurrency categories:
    
    - **Overall Distribution**: Market-wide momentum patterns and trends
    - **Category Analysis**: Separate analysis for Large, Mid, and Small Cap coins
    - **Momentum Zones**: Clear identification of strong and weak momentum regions
    - **Market Insights**: Category-specific statistics and trends
    
    *💡 Use the filters and interactive legend to focus on specific market segments.*
    """)
    
    lookback_days = st.slider(
        "Lookback Period (days)",
        min_value=30,
        max_value=365,
        value=90,
        help="Adjust the historical data range for analysis"
    )
    
    # Get historical sequence data with error handling
    try:
        with st.spinner("Analyzing historical patterns..."):
            sequence_data = analyzer.analyze_historical_sequence(
                timeframe='1d',
                lookback_days=lookback_days
            )
        
        if not sequence_data:
            st.warning("No historical data available for analysis. Please try adjusting the lookback period.")
            return
            
        st.markdown("""
        #### 📊 Momentum Distribution Analysis
        
        The analysis below shows momentum distribution across different market cap categories:
        - **Large Caps**: Major cryptocurrencies with established market presence
        - **Mid Caps**: Emerging projects with significant growth potential
        - **Small Caps**: Early-stage projects with higher volatility
        
        *💡 Use the interactive legend to compare different market segments.*
        """)
        
        if 'momentum_scores' not in sequence_data or not sequence_data['momentum_scores']:
            st.warning("No momentum data available for the selected period.")
            return
        
        # Create momentum scores series with symbol index
        momentum_scores = pd.Series(sequence_data['momentum_scores'])
        
        # Group coins by cohorts
        cohorts = {
            'Large Caps': momentum_scores[momentum_scores.index.isin(df[df['category'] == 'Large Cap'].index)],
            'Mid Caps': momentum_scores[momentum_scores.index.isin(df[df['category'] == 'Mid Cap'].index)],
            'Small Caps': momentum_scores[momentum_scores.index.isin(df[df['category'] == 'Lower Cap'].index)]
        }
        
        # Create enhanced visualization with cohort analysis
        try:
            # Create subplots for overall and category-specific analysis
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Overall Momentum Distribution', 'Momentum by Market Cap Category'),
                vertical_spacing=0.2,
                specs=[[{"type": "histogram"}], [{"type": "box"}]],
                row_heights=[0.6, 0.4]
            )
            
            # Overall momentum distribution
            colors = ['rgba(23, 195, 123, 0.6)', '#FF9900', '#00FFFF']
            for i, (cohort_name, cohort_data) in enumerate(cohorts.items()):
                fig.add_trace(
                    go.Histogram(
                        x=cohort_data,
                        name=cohort_name,
                        nbinsx=30,
                        marker_color=colors[i],
                        marker_line=dict(color=colors[i].replace('0.6', '1'), width=1),
                        hovertemplate=(
                            "<b>%{text}</b><br>" +
                            "Momentum: %{x:.1f}<br>" +
                            "Count: %{y}<br>" +
                            f"Category: {cohort_name}<br>" +
                            "<extra></extra>"
                        ),
                        text=[cohort_name] * len(cohort_data)
                    ),
                    row=1, col=1
                )
            
            # Add momentum zones and trend lines
            zone_annotations = [
                dict(x=-75, y=1, text="Strong Bearish", showarrow=False, font=dict(color="red")),
                dict(x=-25, y=1, text="Weak Bearish", showarrow=False, font=dict(color="orange")),
                dict(x=25, y=1, text="Weak Bullish", showarrow=False, font=dict(color="lightgreen")),
                dict(x=75, y=1, text="Strong Bullish", showarrow=False, font=dict(color="green"))
            ]
            
            for zone in [-75, -25, 25, 75]:
                fig.add_vline(
                    x=zone,
                    line_dash="dash",
                    line_color="gray",
                    row=1, col=1
                )
            
            # Add category-specific box plots
            for i, (cohort_name, cohort_data) in enumerate(cohorts.items()):
                fig.add_trace(
                    go.Box(
                        x=cohort_data,
                        name=cohort_name,
                        marker_color=colors[i],
                        boxpoints='outliers',
                        hovertemplate=(
                            f"<b>{cohort_name}</b><br>" +
                            "Momentum: %{x:.1f}<br>" +
                            "Median: %{median:.1f}<br>" +
                            "Q1: %{q1:.1f}<br>" +
                            "Q3: %{q3:.1f}<br>" +
                            "<extra></extra>"
                        )
                    ),
                    row=2, col=1
                )
            
            # Update layout with enhanced styling
            fig.update_layout(
                title=dict(
                    text="Market Momentum Analysis",
                    font=dict(size=20)
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                template="plotly_dark",
                height=800,
                annotations=zone_annotations
            )
            
            # Update axes
            fig.update_xaxes(title_text="Momentum Score", row=1, col=1)
            fig.update_yaxes(title_text="Number of Coins", row=1, col=1)
            fig.update_xaxes(title_text="Momentum Score", row=2, col=1)
            fig.update_yaxes(title_text="Distribution", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add cohort-specific insights
            st.markdown("### 📈 Market Cohort Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"""
                **Large Caps ({len(cohorts['Large Caps'])} coins)**
                - Median Momentum: {cohorts['Large Caps'].median():.1f}
                - Volatility: {cohorts['Large Caps'].std():.1f}
                - Trend: {_get_trend_description(cohorts['Large Caps'].mean())}
                """)
            
            with col2:
                st.info(f"""
                **Mid Caps ({len(cohorts['Mid Caps'])} coins)**
                - Median Momentum: {cohorts['Mid Caps'].median():.1f}
                - Volatility: {cohorts['Mid Caps'].std():.1f}
                - Trend: {_get_trend_description(cohorts['Mid Caps'].mean())}
                """)
            
            with col3:
                st.info(f"""
                **Small Caps ({len(cohorts['Small Caps'])} coins)**
                - Median Momentum: {cohorts['Small Caps'].median():.1f}
                - Volatility: {cohorts['Small Caps'].std():.1f}
                - Trend: {_get_trend_description(cohorts['Small Caps'].mean())}
                """)
            
        except Exception as e:
            logger.error(f"Error creating momentum distribution plot: {str(e)}")
            st.error("Error creating momentum distribution visualization. Please try again later.")
            return
            
    except Exception as e:
        logger.error(f"Error in historical analysis: {str(e)}")
        st.error("An error occurred while analyzing historical data. Please try again later.")

def _get_trend_description(momentum: float) -> str:
    """Get trend description based on momentum value."""
    if momentum > 50:
        return "Strongly Bullish 🚀"
    elif momentum > 25:
        return "Moderately Bullish 📈"
    elif momentum > 0:
        return "Slightly Bullish ↗️"
    elif momentum > -25:
        return "Slightly Bearish ↘️"
    elif momentum > -50:
        return "Moderately Bearish 📉"
    else:
        return "Strongly Bearish 🔻"

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