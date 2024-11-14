import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import logging
from typing import Dict, List
from utils.altcoin_analyzer import AltcoinAnalyzer

logger = logging.getLogger(__name__)

def render_altcoin_analysis():
    """Render the altcoin analysis interface."""
    try:
        st.subheader("🔄 Altcoin Analysis & Strategy")
        
        # Initialize analyzer with error handling
        try:
            analyzer = AltcoinAnalyzer()
        except Exception as e:
            st.error(f"Failed to initialize analyzer: {str(e)}")
            st.info("Please try refreshing the page.")
            return
        
        # Fetch initial data with error handling
        try:
            df = analyzer.fetch_top_50_cryptocurrencies()
            if df.empty:
                st.warning("No cryptocurrency data available. Please try again later.")
                return
        except Exception as e:
            st.error(f"Error fetching cryptocurrency data: {str(e)}")
            return
        
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
        
        if filtered_df.empty:
            st.warning("No cryptocurrencies match the selected filters. Please adjust your criteria.")
            return
        
        # Main content tabs
        tabs = st.tabs([
            "Market Overview",
            "Historical Analysis",
            "Correlation Analysis"
        ])
        
        with tabs[0]:
            _render_market_overview(filtered_df)
        
        with tabs[1]:
            _render_historical_analysis(analyzer, filtered_df)
        
        with tabs[2]:
            _render_correlation_analysis(analyzer)
            
    except Exception as e:
        logger.error(f"Error in render_altcoin_analysis: {str(e)}")
        st.error("An unexpected error occurred. Please try refreshing the page.")

def _render_historical_analysis(analyzer: AltcoinAnalyzer, df: pd.DataFrame):
    """Render historical analysis section with enhanced visualization and guidance."""
    try:
        st.markdown("""
        ### Historical Sequence Analysis
        
        This section provides detailed insights into market momentum and capital flow patterns:
        
        - **Bitcoin Dominance Flow**: Track how market cap moves from BTC to altcoins
        - **Cohort Analysis**: Compare performance across different market segments
        - **Investment Sequencing**: Identify optimal entry and exit points
        - **Strategy Guidance**: Get clear investment and exit strategies
        
        *💡 Use the interactive controls to customize your analysis view.*
        """)
        
        # Add interactive timeframe selector
        timeframe = st.selectbox(
            "Analysis Timeframe",
            ["7d", "30d", "90d", "180d", "1y"],
            help="Select historical analysis period"
        )
        
        # Convert timeframe to days for analysis
        days_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "180d": 180,
            "1y": 365
        }
        lookback_days = days_map[timeframe]
        
        # Get historical sequence data with error handling
        with st.spinner("Analyzing historical patterns..."):
            try:
                sequence_data = analyzer.analyze_historical_sequence(
                    timeframe='1d',
                    lookback_days=lookback_days
                )
                
                if not sequence_data:
                    st.warning("No historical data available for analysis. Please try adjusting the lookback period.")
                    return
                    
            except Exception as e:
                st.error(f"Error analyzing historical data: {str(e)}")
                return
        
        # Create waterfall visualization
        st.markdown("### 🌊 Bitcoin Dominance Waterfall Analysis")
        
        # Create multi-panel visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "BTC Dominance Flow",
                "Cohort Market Cap Distribution",
                "Sequential Altcoin Gains",
                "Exit Strategy Heatmap"
            ),
            specs=[[{"type": "waterfall"}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "heatmap"}]]
        )
        
        # Add BTC Dominance Flow (Waterfall)
        if 'investment_sequence' in sequence_data:
            for phase, coins in sequence_data['investment_sequence'].items():
                momentum_values = [sequence_data.get('momentum_scores', {}).get(coin, 0) for coin in coins]
                if momentum_values:
                    fig.add_trace(
                        go.Waterfall(
                            name=phase,
                            orientation="v",
                            measure=["relative"] * len(coins),
                            x=coins,
                            y=momentum_values,
                            connector={"line": {"color": "rgb(63, 63, 63)"}},
                            decreasing={"marker": {"color": "red"}},
                            increasing={"marker": {"color": "green"}},
                            text=[f"{coin}: {val:.1f}%" for coin, val in zip(coins, momentum_values)],
                            textposition="outside"
                        ),
                        row=1, col=1
                    )
        
        # Add Cohort Market Cap Distribution (Pie)
        if not df.empty and 'category' in df.columns:
            cohort_data = df.groupby('category')['market_cap'].sum()
            fig.add_trace(
                go.Pie(
                    labels=cohort_data.index,
                    values=cohort_data.values,
                    hole=0.4,
                    textinfo='label+percent'
                ),
                row=1, col=2
            )
        
        # Add Sequential Altcoin Gains (Scatter)
        if 'investment_sequence' in sequence_data:
            for phase, coins in sequence_data['investment_sequence'].items():
                momentum_values = [sequence_data.get('momentum_scores', {}).get(coin, 0) for coin in coins]
                if momentum_values:
                    fig.add_trace(
                        go.Scatter(
                            x=list(range(len(coins))),
                            y=momentum_values,
                            mode='markers+text',
                            name=phase,
                            text=coins,
                            textposition="top center"
                        ),
                        row=2, col=1
                    )
        
        # Add Exit Strategy Heatmap
        if 'exit_strategy' in sequence_data:
            categories = ['Large Cap', 'Mid Cap', 'Small Cap']
            timeframes = ['Short-term', 'Mid-term', 'Long-term']
            exit_data = np.random.rand(len(categories), len(timeframes))  # Placeholder data
            
            fig.add_trace(
                go.Heatmap(
                    z=exit_data,
                    x=timeframes,
                    y=categories,
                    colorscale='RdYlGn'
                ),
                row=2, col=2
            )
        
        # Update layout with enhanced styling
        fig.update_layout(
            title="Market Cap Flow Analysis",
            height=800,
            template="plotly_dark",
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
        
        # Add narrative insights panel
        if 'investment_sequence' in sequence_data and 'exit_strategy' in sequence_data:
            st.markdown("### 📊 Market Flow Insights")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Sequential Investment Opportunities")
                for phase, coins in sequence_data['investment_sequence'].items():
                    st.info(f"**{phase}**\n" + "\n".join([f"• {coin}" for coin in coins]))
            
            with col2:
                st.markdown("#### Exit Strategy Guide")
                for category, strategy in sequence_data['exit_strategy'].items():
                    st.success(f"**{category}**\n{strategy}")
        
    except Exception as e:
        logger.error(f"Error in historical analysis: {str(e)}")
        st.error("An error occurred while rendering the historical analysis. Please try again later.")

def _render_market_overview(df: pd.DataFrame):
    """Render market overview section."""
    try:
        st.markdown("### Market Overview")
        
        if df.empty:
            st.warning("No market data available for overview.")
            return
        
        # Category distribution
        if 'category' in df.columns:
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
            
    except Exception as e:
        logger.error(f"Error in market overview: {str(e)}")
        st.error("An error occurred while rendering the market overview. Please try again later.")

def _render_correlation_analysis(analyzer: AltcoinAnalyzer):
    """Render correlation analysis section."""
    try:
        st.markdown("### Correlation Analysis")
        # Add correlation analysis implementation here
        st.info("Correlation analysis feature coming soon.")
        
    except Exception as e:
        logger.error(f"Error in correlation analysis: {str(e)}")
        st.error("An error occurred while rendering the correlation analysis. Please try again later.")