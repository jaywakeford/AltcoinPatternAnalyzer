import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from utils.altcoin_analyzer import AltcoinAnalyzer

logger = logging.getLogger(__name__)

def _render_momentum_analysis(df: pd.DataFrame) -> None:
    """Render momentum analysis visualization with proper type handling."""
    try:
        # Convert numeric columns with proper error handling
        df['change_24h'] = pd.to_numeric(df['change_24h'], errors='coerce')
        df['volume_24h'] = pd.to_numeric(df['volume_24h'], errors='coerce')
        
        # Drop any rows with invalid numeric data
        valid_data = df.dropna(subset=['change_24h', 'volume_24h'])
        if valid_data.empty:
            st.warning("No valid data available for momentum analysis")
            return
            
        # Get top momentum movers (using absolute change)
        try:
            momentum_data = valid_data.nlargest(10, 'change_24h', key=abs)[
                ['symbol', 'change_24h', 'volume_24h']
            ]
            
            if momentum_data.empty:
                st.warning("No valid momentum data available")
                return
                
            fig = go.Figure(data=[
                go.Scatter(
                    x=momentum_data['change_24h'].astype(float),
                    y=momentum_data['volume_24h'].astype(float),
                    mode='markers+text',
                    text=momentum_data['symbol'],
                    textposition="top center",
                    marker=dict(
                        size=abs(momentum_data['change_24h'].astype(float)) * 2,
                        color=momentum_data['change_24h'].astype(float),
                        colorscale='RdYlGn',
                        showscale=True
                    ),
                    hovertemplate="<b>%{text}</b><br>" +
                                "Change: %{x:.2f}%<br>" +
                                "Volume: $%{y:,.0f}<br>" +
                                "<extra></extra>"
                )
            ])
            
            fig.update_layout(
                title="Momentum Analysis",
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                template="plotly_dark",
                xaxis_title="24h Change (%)",
                yaxis_title="24h Volume ($)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            logger.error(f"Error creating momentum plot: {str(e)}")
            st.error("Unable to create momentum analysis visualization")
            
    except Exception as e:
        logger.error(f"Error rendering momentum analysis: {str(e)}")
        st.error("Unable to generate momentum analysis. Please try again later.")

def render_altcoin_analysis():
    """Main function to render altcoin analysis."""
    try:
        st.title("Altcoin Market Analysis")
        
        # Initialize analyzer
        analyzer = AltcoinAnalyzer()
        
        # Fetch initial data
        with st.spinner("Fetching market data..."):
            df = analyzer.fetch_top_50_cryptocurrencies()
            
            if df.empty:
                st.error("Unable to fetch cryptocurrency data. Please try again later.")
                return
        
        # Create tabs for different analysis sections
        tab1, tab2, tab3 = st.tabs([
            "📊 Real-time Analysis",
            "📈 Historical Patterns",
            "🔄 Correlation Analysis"
        ])
        
        with tab1:
            _render_realtime_analysis(analyzer, df)
            
        with tab2:
            _render_historical_analysis(analyzer, df)
            
        with tab3:
            _render_correlation_analysis(analyzer)
            
    except Exception as e:
        logger.error(f"Error in altcoin analysis: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

def _calculate_advanced_metrics(df: pd.DataFrame) -> Dict:
    """Calculate advanced market metrics with proper error handling."""
    metrics = {
        'dominance': {},
        'volatility': 0.0,
        'momentum': 0.0,
        'health_score': 0.0,
        'volume_concentration': 0.0
    }
    
    try:
        if not df.empty:
            # Market Dominance
            total_market_cap = df['market_cap'].sum()
            if total_market_cap > 0:
                metrics['dominance'] = {
                    symbol: (cap / total_market_cap) * 100 
                    for symbol, cap in df.nlargest(5, 'market_cap')[['symbol', 'market_cap']].values
                }
            
            # Convert numeric columns ensuring proper types
            df['change_24h'] = pd.to_numeric(df['change_24h'], errors='coerce')
            df['volume_24h'] = pd.to_numeric(df['volume_24h'], errors='coerce')
            
            # Volatility Index
            metrics['volatility'] = df['change_24h'].std() or 0.0
            
            # Market Momentum
            metrics['momentum'] = df['change_24h'].mean() or 0.0
            
            # Market Health Score
            positive_changes = (df['change_24h'] > 0).sum()
            metrics['health_score'] = (positive_changes / len(df)) * 100 if len(df) > 0 else 0.0
            
            # Volume Analysis
            total_volume = df['volume_24h'].sum()
            if total_volume > 0:
                metrics['volume_concentration'] = (
                    df.nlargest(10, 'volume_24h')['volume_24h'].sum() / 
                    total_volume * 100
                )
                
    except Exception as e:
        logger.error(f"Error calculating advanced metrics: {str(e)}")
        
    return metrics

def _render_realtime_analysis(analyzer: AltcoinAnalyzer, df: pd.DataFrame) -> None:
    """Render real-time analysis section."""
    try:
        st.markdown("### 📊 Real-time Market Analysis")
        
        # Interval selection
        intervals = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600
        }
        
        col1, col2 = st.columns([2, 1])
        with col1:
            update_interval = st.selectbox(
                "Update Interval",
                list(intervals.keys()),
                index=2,
                help="Select data refresh interval"
            )
        
        with col2:
            # Replace toggle with checkbox
            auto_refresh = st.checkbox("Enable Auto-refresh", value=True)
        
        # Initialize or update session state
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        
        # Auto-refresh logic
        current_time = datetime.now()
        if auto_refresh and (current_time - st.session_state.last_update).total_seconds() >= intervals[update_interval]:
            df = analyzer.fetch_top_50_cryptocurrencies()
            st.session_state.last_update = current_time
        
        st.caption(f"Last Updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate and display metrics
        metrics = _calculate_advanced_metrics(df)
        
        # Create dashboard layout
        col1, col2 = st.columns(2)
        
        with col1:
            _render_market_overview(df, metrics)
            _render_volume_analysis(df)
            
        with col2:
            _render_market_momentum(df, metrics)
            _render_dominance_chart(metrics)
        
        # Market Movement Analysis
        st.markdown("### 📈 Market Movements")
        movement_tabs = st.tabs(["24h Changes", "Volume Leaders", "Momentum"])
        
        with movement_tabs[0]:
            _render_price_changes(df)
        with movement_tabs[1]:
            _render_volume_leaders(df)
        with movement_tabs[2]:
            _render_momentum_analysis(df)
            
    except Exception as e:
        logger.error(f"Error in real-time analysis: {str(e)}")
        st.error("Unable to update real-time data. Please try again later.")

def _render_market_overview(df: pd.DataFrame, metrics: Dict) -> None:
    """Render enhanced market overview section."""
    st.markdown("#### Market Overview")
    
    # Calculate market metrics
    total_market_cap = df['market_cap'].sum()
    total_volume = df['volume_24h'].sum()
    
    # Create metrics display
    cols = st.columns(4)
    
    with cols[0]:
        st.metric(
            "Total Market Cap",
            f"${total_market_cap:,.0f}",
            delta=f"{df['market_cap'].pct_change().mean():.2f}%"
        )
    
    with cols[1]:
        st.metric(
            "24h Volume",
            f"${total_volume:,.0f}",
            delta=f"{df['volume_24h'].pct_change().mean():.2f}%"
        )
    
    with cols[2]:
        st.metric(
            "Market Health",
            f"{metrics.get('health_score', 0):.1f}%",
            delta=f"{metrics.get('momentum', 0):.2f}%"
        )
    
    with cols[3]:
        st.metric(
            "Volatility Index",
            f"{metrics.get('volatility', 0):.2f}",
            delta=None
        )

def _render_volume_analysis(df: pd.DataFrame) -> None:
    """Render enhanced volume analysis visualization."""
    st.markdown("#### Volume Analysis")
    
    # Create volume distribution chart
    volume_data = df.nlargest(10, 'volume_24h')[['symbol', 'volume_24h', 'price']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=volume_data['symbol'],
            y=volume_data['volume_24h'],
            marker_color='rgba(23, 195, 178, 0.6)',
            hovertemplate="<b>%{x}</b><br>" +
                         "Volume: $%{y:,.0f}<br>" +
                         "<extra></extra>"
        )
    ])
    
    fig.update_layout(
        title="Top 10 Volume Distribution",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_dark",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _render_market_momentum(df: pd.DataFrame, metrics: Dict) -> None:
    """Render market momentum visualization."""
    st.markdown("#### Market Momentum")
    
    # Create momentum gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=metrics.get('momentum', 0),
        title={'text': "Market Momentum"},
        gauge={
            'axis': {'range': [-50, 50]},
            'bar': {'color': "rgba(23, 195, 178, 0.8)"},
            'steps': [
                {'range': [-50, -25], 'color': "rgba(255, 0, 0, 0.3)"},
                {'range': [-25, 25], 'color': "rgba(128, 128, 128, 0.3)"},
                {'range': [25, 50], 'color': "rgba(0, 255, 0, 0.3)"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 2},
                'thickness': 0.75,
                'value': metrics.get('momentum', 0)
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _render_dominance_chart(metrics: Dict) -> None:
    """Render market dominance visualization."""
    st.markdown("#### Market Dominance")
    
    dominance = metrics.get('dominance', {})
    if dominance:
        fig = go.Figure(data=[
            go.Pie(
                labels=list(dominance.keys()),
                values=list(dominance.values()),
                hole=.4,
                marker=dict(colors=px.colors.qualitative.Set3)
            )
        ])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
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

def _render_price_changes(df: pd.DataFrame) -> None:
    """Render price changes visualization."""
    changes = df.nlargest(5, 'change_24h')[['symbol', 'change_24h', 'price']]
    changes = pd.concat([
        changes,
        df.nsmallest(5, 'change_24h')[['symbol', 'change_24h', 'price']]
    ])
    
    fig = go.Figure(data=[
        go.Bar(
            x=changes['symbol'],
            y=changes['change_24h'],
            marker_color=['green' if x >= 0 else 'red' for x in changes['change_24h']],
            hovertemplate="<b>%{x}</b><br>" +
                         "Change: %{y:.2f}%<br>" +
                         "<extra></extra>"
        )
    ])
    
    fig.update_layout(
        title="Top Gainers & Losers (24h)",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_dark",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _render_volume_leaders(df: pd.DataFrame) -> None:
    """Render volume leaders visualization."""
    volume_leaders = df.nlargest(10, 'volume_24h')[
        ['symbol', 'volume_24h', 'price', 'change_24h']
    ]
    
    fig = go.Figure(data=[
        go.Bar(
            x=volume_leaders['symbol'],
            y=volume_leaders['volume_24h'],
            marker_color='rgba(23, 195, 178, 0.6)',
            hovertemplate="<b>%{x}</b><br>" +
                         "Volume: $%{y:,.0f}<br>" +
                         "<extra></extra>"
        )
    ])
    
    fig.update_layout(
        title="Volume Leaders",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_dark",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

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