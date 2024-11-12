import streamlit as st
import plotly.graph_objects as go
from utils.altcoin_analyzer import AltcoinAnalyzer
import pandas as pd
from typing import Dict, List

def render_altcoin_analysis():
    """Render the altcoin analysis interface."""
    st.subheader("🔄 Altcoin Analysis & Strategy")
    
    # Initialize analyzer
    analyzer = AltcoinAnalyzer()
    
    # Sidebar configuration
    with st.sidebar:
        st.subheader("Market Parameters")
        btc_target = st.slider(
            "BTC Price Target ($)",
            min_value=30000,
            max_value=150000,
            value=100000,
            step=1000,
            help="Set your Bitcoin price target"
        )
        
        btc_dominance_floor = st.slider(
            "BTC Dominance Floor (%)",
            min_value=40,
            max_value=80,
            value=50,
            help="Set minimum Bitcoin dominance threshold"
        )
    
    # Main content
    tabs = st.tabs(["Phase Analysis", "Market Cycles", "Risk Management"])
    
    with tabs[0]:
        _render_phase_analysis(analyzer, btc_target, btc_dominance_floor)
    
    with tabs[1]:
        _render_market_cycles(analyzer)
    
    with tabs[2]:
        _render_risk_management(analyzer)

def _render_phase_analysis(analyzer: AltcoinAnalyzer, btc_target: float, btc_dominance_floor: float):
    """Render the phase analysis section."""
    st.markdown("### Market Phase Analysis")
    
    # Get phase analysis data
    phase_data = analyzer.analyze_market_phase(btc_target, btc_dominance_floor)
    
    # Display phases in columns
    cols = st.columns(3)
    
    for idx, (phase, data) in enumerate(phase_data.items()):
        with cols[idx]:
            st.markdown(f"#### {data['name']}")
            
            # Criteria
            st.markdown("**Entry Criteria:**")
            for criterion in data['entry_conditions']:
                st.markdown(f"- {criterion}")
            
            # Position Sizing
            st.markdown("**Position Sizing:**")
            pos_size = data['position_sizing']
            st.markdown(f"""
            - Initial: {pos_size['initial_size']*100}%
            - Maximum: {pos_size['max_size']*100}%
            - Risk/Trade: {pos_size['risk_per_trade']*100}%
            """)
            
            # Risk Parameters
            st.markdown("**Risk Management:**")
            risk = data['risk_parameters']
            st.markdown(f"""
            - Stop Loss: {risk['stop_loss']*100}%
            - Take Profit: {risk['take_profit']*100}%
            - Trailing Stop: {risk['trailing_stop']*100}%
            """)

def _render_market_cycles(analyzer: AltcoinAnalyzer):
    """Render market cycles comparison."""
    st.markdown("### Historical Market Cycles")
    
    cycles = analyzer.get_historical_cycles()
    
    # Create cycle comparison visualization
    fig = go.Figure()
    
    # Add cycle data
    cycles_data = {
        '2017-2018': {
            'x': ['Peak', 'Dom Min', 'Dom Max'],
            'y': [19891.99, 33.41, 67.54]
        },
        '2021': {
            'x': ['Peak', 'Dom Min', 'Dom Max'],
            'y': [69044.77, 39.48, 71.86]
        },
        '2024': {
            'x': ['Current', 'Dom Current'],
            'y': [35000, 53]
        }
    }
    
    colors = {'2017-2018': '#1f77b4', '2021': '#ff7f0e', '2024': '#2ca02c'}
    
    for cycle, data in cycles_data.items():
        fig.add_trace(go.Bar(
            name=cycle,
            x=data['x'],
            y=data['y'],
            marker_color=colors[cycle]
        ))
    
    fig.update_layout(
        title="Market Cycle Comparison",
        barmode='group',
        xaxis_title="Metrics",
        yaxis_title="Value",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display cycle characteristics
    for cycle, data in cycles.items():
        st.markdown(f"**{cycle} Cycle**")
        if 'key_characteristics' in data:
            for char in data['key_characteristics']:
                st.markdown(f"- {char}")
        elif 'market_characteristics' in data:
            for char in data['market_characteristics']:
                st.markdown(f"- {char}")
        st.markdown("---")

def _render_risk_management(analyzer: AltcoinAnalyzer):
    """Render risk management dashboard."""
    st.markdown("### Risk Management Dashboard")
    
    # Example market data for demonstration
    market_data = {
        'volume_24h': 500_000_000,
        'volume_change_24h': 0.15,
        'bid_depth': 1_000_000,
        'ask_depth': 1_200_000,
        'spread': 0.001
    }
    
    # Example price data
    price_data = pd.DataFrame({
        'price': [100, 102, 98, 103, 101],
        'timestamp': pd.date_range(start='2024-01-01', periods=5)
    }).set_index('timestamp')
    
    # Calculate risk metrics
    risk_metrics = analyzer.calculate_risk_metrics(price_data, market_data)
    
    # Display metrics in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Market Metrics")
        st.metric("Volatility", f"{risk_metrics.get('volatility', 0):.2%}")
        st.metric("BTC Correlation", f"{risk_metrics.get('correlation', 0):.2f}")
    
    with col2:
        st.markdown("#### Volume Analysis")
        volume_profile = risk_metrics.get('volume_profile', {})
        st.metric("24h Volume", f"${volume_profile.get('average_volume', 0):,.0f}")
        st.metric("Volume Trend", volume_profile.get('volume_trend', 'N/A'))
    
    # Market depth visualization
    market_depth = risk_metrics.get('market_depth', {})
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Bid Depth',
        x=['Bid'],
        y=[market_depth.get('bid_depth', 0)],
        marker_color='green'
    ))
    
    fig.add_trace(go.Bar(
        name='Ask Depth',
        x=['Ask'],
        y=[market_depth.get('ask_depth', 0)],
        marker_color='red'
    ))
    
    fig.update_layout(
        title="Market Depth Analysis",
        barmode='group',
        template="plotly_dark",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
