import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from utils.altcoin_analyzer import AltcoinAnalyzer

logger = logging.getLogger(__name__)

def _initialize_session_state():
    """Initialize session state variables for altcoin analysis."""
    if 'analysis_state' not in st.session_state:
        st.session_state.analysis_state = {
            'start_date': (datetime.now() - timedelta(days=30)).date(),
            'end_date': datetime.now().date(),
            'selected_cohort': "Market Cap",
            'selected_subcohorts': [],
            'show_tooltips': True,
            'show_guidance': True
        }

def _safe_convert_to_float(value) -> float:
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

def render_altcoin_analysis():
    """Render the altcoin analysis interface with enhanced visualizations."""
    try:
        st.title("Altcoin Analysis & Market Flow")
        
        # Initialize session state
        _initialize_session_state()
        
        # Enhanced user guidance
        with st.expander("📚 Analysis Guide", expanded=st.session_state.analysis_state['show_guidance']):
            st.markdown("""
            ### Understanding the Market Flow Analysis
            
            This dashboard helps you analyze capital movement patterns:
            
            1. **Bitcoin Dominance Flow** 📊
               - Shows how capital moves from BTC to altcoins
               - Green bars indicate positive momentum
               - Red bars show negative momentum
            
            2. **Market Cap Distribution** 🔄
               - Visualizes market share by category
               - Helps identify market rotation patterns
            
            3. **Enhanced Momentum Distribution** 📈
               - Shows relative strength of each coin
               - Trend line indicates overall market direction
               - Outliers may present opportunities
            
            4. **Exit Strategy Heatmap** 🎯
               - Darker colors indicate stronger signals
               - Use for timing your exits
               - Consider multiple timeframes
            
            ### How to Use This Tool
            1. Select your analysis timeframe
            2. Monitor the waterfall chart for capital flow
            3. Use the momentum distribution to confirm trends
            4. Check the heatmap for exit timing
            """)
        
        # Timeframe selection with improved guidance
        st.subheader("📅 Analysis Period")
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=st.session_state.analysis_state['start_date'],
                help="Select the beginning of your analysis period"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=st.session_state.analysis_state['end_date'],
                min_value=start_date,
                help="Select the end of your analysis period"
            )
        
        # Update session state
        st.session_state.analysis_state.update({
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Calculate lookback period
        lookback_days = (end_date - start_date).days
        if lookback_days <= 0:
            st.warning("Please select a valid date range. Using default 30-day period.")
            lookback_days = 30
        
        # Initialize analyzer and fetch data
        try:
            analyzer = AltcoinAnalyzer()
            with st.spinner("📊 Analyzing market patterns..."):
                sequence_data = analyzer.analyze_historical_sequence(
                    timeframe='1d',
                    lookback_days=lookback_days
                )
                
                if not sequence_data:
                    st.warning("No historical data available for the selected period.")
                    return
                    
                df = analyzer.fetch_top_50_cryptocurrencies()
                if df.empty:
                    st.warning("Unable to fetch current market data.")
                    return
                    
        except Exception as e:
            st.error(f"⚠️ Error initializing analysis: {str(e)}")
            return
        
        # Create enhanced visualization layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Bitcoin Dominance Flow",
                "Market Cap Distribution",
                "Enhanced Momentum Distribution",
                "Exit Strategy Heatmap"
            ),
            specs=[[{"type": "waterfall"}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "heatmap"}]],
            horizontal_spacing=0.15,
            vertical_spacing=0.15
        )
        
        # Enhanced waterfall chart
        if sequence_data.get('investment_sequence'):
            for phase, coins in sequence_data['investment_sequence'].items():
                if not coins:
                    continue
                
                values = [
                    _safe_convert_to_float(
                        sequence_data.get('momentum_scores', {}).get(coin, 0)
                    ) for coin in coins
                ]
                
                fig.add_trace(
                    go.Waterfall(
                        name=phase,
                        orientation="v",
                        measure=["relative"] * len(coins),
                        x=coins,
                        y=values,
                        connector={"line": {"color": "rgb(63, 63, 63)"}},
                        decreasing={"marker": {"color": "#FF4B4B"}},
                        increasing={"marker": {"color": "#17C37B"}},
                        text=[f"{coin}: {val:.1f}%" for coin, val in zip(coins, values)],
                        textposition="outside",
                        hovertemplate="<b>%{x}</b><br>" +
                                    "Momentum: %{y:.1f}%<br>" +
                                    "<extra></extra>"
                    ),
                    row=1, col=1
                )
        
        # Enhanced market cap distribution
        if not df.empty and 'category' in df.columns:
            cap_data = df.groupby('category')['market_cap'].sum()
            fig.add_trace(
                go.Pie(
                    labels=cap_data.index,
                    values=cap_data.values,
                    hole=0.4,
                    textinfo='label+percent',
                    hovertemplate="<b>%{label}</b><br>" +
                                "Market Cap: $%{value:,.0f}<br>" +
                                "<extra></extra>"
                ),
                row=1, col=2
            )
        
        # Enhanced momentum distribution
        if sequence_data.get('momentum_scores'):
            scores = sequence_data['momentum_scores']
            symbols = list(scores.keys())
            values = [_safe_convert_to_float(v) for v in scores.values()]
            
            # Calculate trend and outliers
            x_range = np.arange(len(values))
            mean_val = np.mean(values)
            std_val = np.std(values) if len(values) > 1 else 1
            z_scores = np.abs((np.array(values) - mean_val) / std_val)
            
            # Add scatter plot with improved visuals
            fig.add_trace(
                go.Scatter(
                    x=symbols,
                    y=values,
                    mode='markers+text',
                    name='Momentum',
                    marker=dict(
                        size=12,
                        color=values,
                        colorscale='RdYlGn',
                        showscale=True,
                        colorbar=dict(
                            title="Momentum Score",
                            titleside="right"
                        )
                    ),
                    text=[f"{s}" for s in symbols],
                    textposition="top center",
                    hovertemplate="<b>%{text}</b><br>" +
                                "Momentum: %{y:.1f}%<br>" +
                                "<extra></extra>"
                ),
                row=2, col=1
            )
            
            # Add trend line with confidence band
            if len(values) > 1:
                z = np.polyfit(x_range, values, 1)
                p = np.poly1d(z)
                trend_line = p(x_range)
                
                fig.add_trace(
                    go.Scatter(
                        x=symbols,
                        y=trend_line,
                        mode='lines',
                        name='Trend',
                        line=dict(color='white', dash='dash'),
                        hovertemplate="Trend: %{y:.1f}%<br>" +
                                    "<extra></extra>"
                    ),
                    row=2, col=1
                )
        
        # Enhanced exit strategy heatmap
        if sequence_data.get('investment_sequence'):
            categories = ['Short-term', 'Mid-term', 'Long-term']
            phases = list(sequence_data['investment_sequence'].keys())
            
            exit_data = np.zeros((len(phases), len(categories)))
            for i, phase in enumerate(phases):
                coins = sequence_data['investment_sequence'][phase]
                if coins:
                    scores = []
                    for coin in coins:
                        momentum = _safe_convert_to_float(
                            sequence_data.get('momentum_scores', {}).get(coin, 0)
                        )
                        scores.append(momentum)
                    
                    if scores:
                        avg_score = np.mean(scores)
                        exit_data[i] = [
                            max(0, min(100, avg_score + 20)),  # Short-term
                            max(0, min(100, avg_score)),       # Mid-term
                            max(0, min(100, avg_score - 20))   # Long-term
                        ]
            
            fig.add_trace(
                go.Heatmap(
                    z=exit_data,
                    x=categories,
                    y=phases,
                    colorscale='RdYlGn',
                    showscale=True,
                    text=[[f"{val:.1f}%" for val in row] for row in exit_data],
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hovertemplate="<b>%{y}</b><br>" +
                                "%{x}: %{z:.1f}%<br>" +
                                "<extra></extra>"
                ),
                row=2, col=2
            )
        
        # Update layout with improved styling
        fig.update_layout(
            height=800,
            showlegend=True,
            template="plotly_dark",
            title={
                'text': "Market Analysis Dashboard",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="rgba(255,255,255,0.2)"
            )
        )
        
        # Display the enhanced visualization
        st.plotly_chart(fig, use_container_width=True)
        
        # Display actionable insights
        if sequence_data.get('investment_sequence'):
            st.markdown("### 📊 Market Insights")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Current Market Leaders")
                for phase, coins in sequence_data['investment_sequence'].items():
                    with st.expander(phase, expanded=True):
                        for coin in coins:
                            momentum = _safe_convert_to_float(
                                sequence_data.get('momentum_scores', {}).get(coin, 0)
                            )
                            color = (
                                "green" if momentum > 20 else
                                "orange" if momentum > 0 else
                                "red"
                            )
                            st.markdown(f"• **{coin}** - Momentum: :{color}[{momentum:.1f}%]")
            
            with col2:
                st.markdown("#### Strategic Exit Guide")
                if sequence_data.get('exit_strategy'):
                    for strategy, description in sequence_data['exit_strategy'].items():
                        st.markdown(f"**{strategy}**")
                        st.markdown(f"_{description}_")
        
    except Exception as e:
        logger.error(f"Error in historical analysis: {str(e)}")
        st.error("⚠️ Error rendering analysis section")
        st.info("💡 Please try refreshing the page or contact support.")
