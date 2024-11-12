import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.backtesting import Backtester
from utils.data_fetcher import get_crypto_data
from components.strategy_builder import StrategyBuilder
from datetime import datetime

def render_backtesting_section():
    """Render the backtesting interface with separate tabs for builder and results."""
    st.subheader("🔄 Strategy Development & Testing")
    
    st.markdown("""
    Welcome to the strategy development and testing section. Here you can:
    1. Build and configure your trading strategy
    2. Test your strategy against historical data
    3. Analyze performance metrics and results
    """)
    
    # Create tabs for strategy building and backtesting
    strategy_tab, backtest_tab = st.tabs([
        "Build Strategy",
        "Test Strategy"
    ])
    
    with strategy_tab:
        strategy_builder = StrategyBuilder()
        result = strategy_builder.render()
        
        if result:
            strategy_config, backtest_config = result
            st.session_state['current_strategy'] = strategy_config
            st.session_state['current_backtest'] = backtest_config
            
            if st.button("▶️ Run Strategy Test", key=f"run_backtest_{datetime.now().timestamp()}"):
                _run_backtest(strategy_config, backtest_config)
    
    with backtest_tab:
        if 'backtest_results' in st.session_state:
            _display_backtest_results(st.session_state['backtest_results'])
        else:
            st.info("Create a strategy and run a test to see results here")

def _validate_backtest_params(strategy_config: dict, backtest_config: dict) -> bool:
    """Validate backtest parameters before execution."""
    errors = []
    
    # Validate strategy parameters
    if not strategy_config.get('entry_conditions'):
        errors.append("Strategy must have at least one entry condition")
    if not strategy_config.get('exit_conditions'):
        errors.append("Strategy must have at least one exit condition")
    if not strategy_config.get('position_size'):
        errors.append("Position size must be specified")
    
    # Validate backtest parameters
    if not backtest_config.get('asset'):
        errors.append("Trading asset must be selected")
    if not backtest_config.get('initial_capital'):
        errors.append("Initial capital must be specified")
    if backtest_config.get('initial_capital', 0) <= 0:
        errors.append("Initial capital must be positive")
    
    # Display errors if any
    if errors:
        for error in errors:
            st.error(error)
        return False
    
    return True

def _run_backtest(strategy_config: dict, backtest_config: dict):
    """Execute backtest with validation and error handling."""
    if not _validate_backtest_params(strategy_config, backtest_config):
        return
    
    with st.spinner("Running backtest..."):
        try:
            # Fetch historical data
            df = get_crypto_data(
                backtest_config['asset'].split('/')[0].lower(),
                strategy_config['timeframe']
            )
            
            if df.empty:
                st.error("Failed to fetch historical data")
                return
            
            # Initialize and run backtester
            backtester = Backtester(df, backtest_config['initial_capital'])
            results = backtester.run_strategy(strategy_config)
            
            if results:
                st.session_state['backtest_results'] = results
                _display_backtest_results(results)
            else:
                st.error("No results generated. Please check your parameters.")
                
        except Exception as e:
            st.error(f"Error during backtesting: {str(e)}")

def _display_backtest_results(results):
    """Display backtest results with improved visualizations."""
    # Performance Metrics
    st.subheader("Performance Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Return",
            f"{(results.metrics['avg_return'] * results.metrics['total_trades']):.2f}%",
            help="Total percentage return from all trades"
        )
        st.metric(
            "Win Rate",
            f"{results.metrics['win_rate']*100:.2f}%",
            help="Percentage of profitable trades"
        )
    
    with col2:
        st.metric(
            "Total Trades",
            results.metrics['total_trades'],
            help="Number of completed trades"
        )
        st.metric(
            "Max Drawdown",
            f"{results.metrics['max_drawdown']*100:.2f}%",
            help="Maximum percentage decline from peak"
        )
    
    with col3:
        st.metric(
            "Sharpe Ratio",
            f"{results.metrics['sharpe_ratio']:.2f}",
            help="Risk-adjusted return metric"
        )
        st.metric(
            "Profit Factor",
            f"{results.metrics['profit_factor']:.2f}",
            help="Ratio of gross profit to gross loss"
        )
    
    # Equity Curve
    st.subheader("Equity Curve")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=results.equity_curve.index,
        y=results.equity_curve.values,
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#17C37B', width=2)
    ))
    
    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (USD)",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trade Analysis
    st.subheader("Trade Analysis")
    
    # Monthly Returns Heatmap
    if results.equity_curve is not None:
        monthly_returns = results.equity_curve.pct_change().resample('M').sum()
        st.markdown("#### Monthly Returns")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_returns.index,
            y=monthly_returns.values * 100,
            name='Monthly Return (%)',
            marker_color=['red' if x < 0 else 'green' for x in monthly_returns.values]
        ))
        
        fig.update_layout(
            title="Monthly Returns Distribution",
            xaxis_title="Month",
            yaxis_title="Return (%)",
            template="plotly_dark",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Trade History
    st.subheader("Trade History")
    if results.trades:
        trades_df = pd.DataFrame(results.trades)
        trades_df['return_pct'] = trades_df['return_pct'] * 100
        trades_df = trades_df.round(2)
        st.dataframe(trades_df)