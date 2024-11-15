import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Union
from utils.altcoin_analyzer import AltcoinAnalyzer

logger = logging.getLogger(__name__)

def render_altcoin_analysis():
    """Main entry point for altcoin analysis."""
    try:
        analyzer = AltcoinAnalyzer()
        df = analyzer.fetch_top_50_cryptocurrencies()
        
        if df.empty:
            st.warning("Unable to fetch cryptocurrency data. Please try again later.")
            return
            
        tab1, tab2, tab3 = st.tabs([
            "🔄 Historical Analysis",
            "📊 Real-time Analysis",
            "🔗 Correlation Analysis"
        ])
        
        with tab1:
            _render_historical_analysis(analyzer, df)
            
        with tab2:
            _render_realtime_analysis(analyzer, df)
            
        with tab3:
            _render_correlation_analysis(analyzer)
            
    except Exception as e:
        logger.error(f"Error in altcoin analysis: {str(e)}")
        st.error("An error occurred while analyzing altcoin data. Please try again later.")

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

def _render_momentum_distribution(df: pd.DataFrame, sequence_data: Dict) -> None:
    """Render enhanced momentum distribution visualization."""
    try:
        if 'momentum_scores' not in sequence_data:
            st.warning("No momentum data available for the selected period.")
            return

        # User Guidance
        st.markdown("""
        ### 📊 Market Momentum Analysis Guide
        
        This visualization helps you understand market momentum across different cryptocurrency segments:
        
        #### How to Read the Charts:
        1. **Top Chart**: Shows overall momentum distribution
           - Higher bars indicate more coins in that momentum range
           - Color-coded by market cap category
           
        2. **Bottom Chart**: Shows momentum comparison across categories
           - Box plots show the spread of momentum values
           - Outliers indicate extreme performers
        
        #### Momentum Zones:
        - 🟢 Strong Bullish (>75): Strong upward trend
        - 🟡 Weak Bullish (25-75): Moderate upward movement
        - ⚪ Neutral (-25 to 25): Sideways movement
        - 🟠 Weak Bearish (-75 to -25): Moderate downward trend
        - 🔴 Strong Bearish (<-75): Strong downward trend
        
        💡 **Tip**: Hover over the charts for detailed information about each data point.
        """)

        # Convert momentum scores to pandas DataFrame
        momentum_df = pd.DataFrame.from_dict(
            sequence_data['momentum_scores'],
            orient='index',
            columns=['momentum']
        ).reset_index().rename(columns={'index': 'symbol'})
        
        # Convert momentum values to float
        momentum_df['momentum'] = pd.to_numeric(momentum_df['momentum'], errors='coerce')

        # Create cohorts
        cohorts = {
            'Large Caps': momentum_df[momentum_df['symbol'].isin(df[df['category'] == 'Large Cap'].symbol)],
            'Mid Caps': momentum_df[momentum_df['symbol'].isin(df[df['category'] == 'Mid Cap'].symbol)],
            'Small Caps': momentum_df[momentum_df['symbol'].isin(df[df['category'] == 'Lower Cap'].symbol)]
        }

        # Create visualization
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Overall Momentum Distribution', 'Momentum by Market Cap Category'),
            vertical_spacing=0.2,
            specs=[[{"type": "histogram"}], [{"type": "box"}]],
            row_heights=[0.6, 0.4]
        )

        # Add histograms
        colors = ['rgba(23, 195, 123, 0.6)', '#FF9900', '#00FFFF']
        for i, (cohort_name, cohort_data) in enumerate(cohorts.items()):
            if not cohort_data.empty:
                fig.add_trace(
                    go.Histogram(
                        x=cohort_data['momentum'].values,
                        name=cohort_name,
                        nbinsx=30,
                        marker_color=colors[i],
                        opacity=0.7,
                        hovertemplate=(
                            "<b>%{text}</b><br>" +
                            "Momentum: %{x:.1f}<br>" +
                            "Count: %{y}<br>" +
                            "<extra></extra>"
                        ),
                        text=[cohort_name] * len(cohort_data)
                    ),
                    row=1, col=1
                )

        # Add box plots
        for i, (cohort_name, cohort_data) in enumerate(cohorts.items()):
            if not cohort_data.empty:
                fig.add_trace(
                    go.Box(
                        x=cohort_data['momentum'].values,
                        name=cohort_name,
                        marker_color=colors[i],
                        boxpoints='outliers',
                        hovertemplate=(
                            f"<b>{cohort_name}</b><br>" +
                            "Momentum: %{x:.1f}<br>" +
                            "<extra></extra>"
                        )
                    ),
                    row=2, col=1
                )

        # Update layout
        fig.update_layout(
            title=dict(
                text="Market Momentum Distribution",
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
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Add momentum zones
        zones = [
            (-75, "Strong Bearish", "red"),
            (-25, "Weak Bearish", "orange"),
            (25, "Weak Bullish", "lightgreen"),
            (75, "Strong Bullish", "green")
        ]
        
        for zone_value, zone_text, zone_color in zones:
            # Add vertical lines for both plots
            fig.add_vline(
                x=float(zone_value),
                line_dash="dash",
                line_color="gray",
                row="1", col="1"
            )
            fig.add_vline(
                x=float(zone_value),
                line_dash="dash",
                line_color="gray",
                row="2", col="1"
            )
            
            # Add zone labels
            fig.add_annotation(
                x=float(zone_value),
                y=1,
                text=zone_text,
                showarrow=False,
                font=dict(color=zone_color),
                row="1", col="1"
            )

        st.plotly_chart(fig, use_container_width=True)

        # Add cohort insights
        st.markdown("### 📈 Market Cohort Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        for col, (cohort_name, cohort_data) in zip([col1, col2, col3], cohorts.items()):
            with col:
                if not cohort_data.empty:
                    momentum_values = cohort_data['momentum'].values
                    median_momentum = float(np.median(momentum_values))
                    volatility = float(np.std(momentum_values))
                    trend = _get_trend_description(float(np.mean(momentum_values)))

                    st.info(f"""
                    **{cohort_name}** ({len(cohort_data)} coins)
                    - **Median Momentum:** {median_momentum:.1f}
                    - **Volatility:** {volatility:.1f}
                    - **Current Trend:** {trend}
                    """)
                else:
                    st.info(f"**{cohort_name}**: No data available")

        # Add market action suggestions
        st.markdown("""
        ### 🎯 Suggested Market Actions
        
        Based on the momentum analysis above:
        
        1. **Strong Momentum (>75)**
        - Consider taking profits on highly bullish assets
        - Set trailing stops to protect gains
        
        2. **Moderate Momentum (25-75)**
        - Look for entry points on pullbacks
        - Consider scaling into positions
        
        3. **Neutral Zone (-25 to 25)**
        - Focus on accumulation strategies
        - Watch for breakout opportunities
        
        4. **Weak Momentum (-75 to -25)**
        - Exercise caution with new positions
        - Consider reducing exposure
        
        5. **Strong Bearish (<-75)**
        - Wait for momentum reversal signals
        - Consider hedging strategies
        
        💡 **Remember**: Always combine this analysis with other technical and fundamental factors before making trading decisions.
        """)

    except Exception as e:
        logger.error(f"Error rendering momentum distribution: {str(e)}")
        st.error("An error occurred while rendering the momentum distribution visualization. Please try again later.")

def _render_correlation_analysis(analyzer: AltcoinAnalyzer) -> None:
    """Render correlation analysis section with enhanced visualization."""
    try:
        st.markdown("### 📊 Correlation Analysis")
        
        timeframe = st.selectbox(
            "Select Correlation Timeframe",
            ["7d", "30d", "90d"],
            index=1,
            help="Choose the period for correlation analysis"
        )
        
        if timeframe:
            historical_days = int(timeframe.replace('d', ''))
            correlation_data = analyzer.analyze_btc_correlation(
                timeframe='1d',
                lookback_days=historical_days
            )
            
            if correlation_data and correlation_data.get('cooling_periods'):
                st.markdown("""
                ### Understanding Cooling Periods
                
                Cooling periods are times when Bitcoin's price action shows reduced volatility 
                or consolidation. These periods often present opportunities in the altcoin market:
                
                - 🔵 Blue zones indicate BTC cooling periods
                - Higher cooling period duration often correlates with stronger altcoin moves
                - Pay attention to volume patterns during these periods
                """)
                
                # Create visualization
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('BTC Price with Cooling Periods', 'Market Impact Analysis'),
                    vertical_spacing=0.2,
                    row_heights=[0.6, 0.4]
                )
                
                # Add BTC price line
                if 'btc_price' in correlation_data:
                    fig.add_trace(
                        go.Scatter(
                            x=pd.date_range(
                                end=pd.Timestamp.now(),
                                periods=len(correlation_data['btc_price']),
                                freq='D'
                            ),
                            y=correlation_data['btc_price'],
                            name="BTC Price",
                            line=dict(color='#F7931A', width=2)
                        ),
                        row="1", col="1"
                    )
                
                # Add cooling period overlays
                for period in correlation_data['cooling_periods']:
                    start_date = pd.Timestamp(period['start'])
                    end_date = pd.Timestamp(period['end'])
                    
                    fig.add_vrect(
                        x0=start_date,
                        x1=end_date,
                        fillcolor="rgba(0,0,255,0.2)",
                        layer="below",
                        line_width=0,
                        row="1", col="1"
                    )
                
                fig.update_layout(
                    height=800,
                    showlegend=True,
                    template="plotly_dark",
                    title=dict(
                        text="Bitcoin Cooling Periods Analysis",
                        font=dict(size=20)
                    ),
                    xaxis_title="Date",
                    yaxis_title="BTC Price (USD)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display cooling period statistics
                st.markdown("#### Cooling Period Statistics")
                for i, period in enumerate(correlation_data['cooling_periods'], 1):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"""
                        **Period {i}**
                        - Duration: {period['duration']:.1f} days
                        - Price Change: {period.get('price_change', 0):.2f}%
                        """)
            else:
                st.info("No cooling periods detected in the selected timeframe.")
                
    except Exception as e:
        logger.error(f"Error in correlation analysis: {str(e)}")
        st.error("An error occurred while analyzing correlations. Please try again later.")

def _render_historical_analysis(analyzer: AltcoinAnalyzer, df: pd.DataFrame) -> None:
    """Render historical analysis section with improved visualization."""
    try:
        st.markdown("""
        ### 📈 Historical Analysis
        
        This section provides insights into historical market patterns and momentum:
        - Analyze momentum distribution across different market segments
        - Track altcoin performance during Bitcoin's cooling periods
        - Identify potential market opportunities
        """)
        
        # Add timeframe selector
        timeframe = st.selectbox(
            "Select Analysis Timeframe",
            ["7d", "30d", "90d", "180d", "1y"],
            index=1,
            help="Choose the period for historical analysis"
        )

        # Convert timeframe to days
        days_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "180d": 180,
            "1y": 365
        }
        
        lookback_days = days_map.get(timeframe, 30)
        
        with st.spinner("Analyzing historical patterns..."):
            sequence_data = analyzer.analyze_historical_sequence(
                timeframe='1d',
                lookback_days=lookback_days
            )
            
            if sequence_data:
                _render_momentum_distribution(df, sequence_data)
            else:
                st.warning("No historical data available for analysis. Please try again later.")

    except Exception as e:
        logger.error(f"Error in historical analysis: {str(e)}")
        st.error("An error occurred while analyzing historical data. Please try again later.")

def _render_realtime_analysis(analyzer: AltcoinAnalyzer, df: pd.DataFrame) -> None:
    """Render real-time analysis section."""
    try:
        st.markdown("### 📊 Real-time Market Analysis")
        
        update_interval = st.selectbox(
            "Update Interval",
            ["1m", "5m", "15m", "30m", "1h"],
            index=2,
            help="Select data refresh interval"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            _render_market_overview(df)
        
        with col2:
            st.markdown("#### Top Movers")
            if not df.empty:
                top_movers = df.nlargest(5, 'change_24h')[
                    ['symbol', 'change_24h', 'volume_24h']
                ].copy()
                
                st.dataframe(
                    top_movers.style.format({
                        'change_24h': '{:,.2f}%',
                        'volume_24h': '${:,.0f}'
                    }),
                    use_container_width=True
                )
            else:
                st.warning("No market data available")
                
    except Exception as e:
        logger.error(f"Error in real-time analysis: {str(e)}")
        st.error("An error occurred while updating real-time analysis. Please try again later.")
