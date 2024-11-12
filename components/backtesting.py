import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.backtesting import Backtester
from utils.data_fetcher import get_crypto_data
from components.strategy_builder import StrategyBuilder

def render_backtesting_section():
    """Render the backtesting interface and results."""
    st.subheader("🔄 Strategy Backtesting")
    
    # Add description
    st.markdown("""
    Test your trading strategies using historical cryptocurrency data. You can either:
    1. Use pre-built strategies with configurable parameters
    2. Create a custom strategy using the strategy builder
    """)
    
    # Strategy Selection
    strategy_mode = st.radio(
        "Strategy Mode",
        ["Pre-built Strategies", "Custom Strategy Builder"]
    )
    
    if strategy_mode == "Pre-built Strategies":
        _render_prebuilt_strategy_section()
    else:
        _render_custom_strategy_section()

def _render_prebuilt_strategy_section():
    """Render the pre-built strategy configuration section."""
    with st.expander("Strategy Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            strategy_type = st.selectbox(
                "Strategy Type",
                ["Trend Following", "Mean Reversion", "Breakout"],
                help="Choose your trading strategy"
            )
            
            timeframe = st.selectbox(
                "Timeframe",
                ["30", "90", "180", "365"],
                help="Historical data period (days)"
            )
        
        with col2:
            selected_coin = st.selectbox(
                "Asset",
                ["bitcoin", "ethereum", "cardano", "solana"],
                help="Select cryptocurrency to test"
            )
            
            initial_capital = st.number_input(
                "Initial Capital (USD)",
                min_value=1000,
                value=10000,
                step=1000,
                help="Starting capital for backtesting"
            )
        
        # Strategy-specific parameters
        st.markdown("### Strategy Parameters")
        strategy_config = _get_strategy_parameters(strategy_type)
        
        if st.button("Run Backtest"):
            _run_prebuilt_strategy_backtest(selected_coin, timeframe, strategy_config, initial_capital)

def _render_custom_strategy_section():
    """Render the custom strategy builder section."""
    strategy_builder = StrategyBuilder()
    strategy_config = strategy_builder.render()
    
    if strategy_config:
        col1, col2 = st.columns(2)
        with col1:
            selected_coin = st.selectbox(
                "Asset",
                ["bitcoin", "ethereum", "cardano", "solana"],
                help="Select cryptocurrency to test"
            )
        
        with col2:
            initial_capital = st.number_input(
                "Initial Capital (USD)",
                min_value=1000,
                value=10000,
                step=1000,
                help="Starting capital for backtesting"
            )
        
        if st.button("Run Backtest"):
            _run_custom_strategy_backtest(selected_coin, strategy_config, initial_capital)

def _get_strategy_parameters(strategy_type: str) -> dict:
    """Get strategy-specific parameters based on the selected strategy type."""
    config = {'strategy_type': strategy_type.lower().replace(' ', '_')}
    
    if strategy_type == "Trend Following":
        col1, col2 = st.columns(2)
        with col1:
            config['sma_short'] = st.number_input(
                "Short SMA Period",
                min_value=5,
                max_value=50,
                value=20,
                help="Short-term moving average period"
            )
        with col2:
            config['sma_long'] = st.number_input(
                "Long SMA Period",
                min_value=10,
                max_value=200,
                value=50,
                help="Long-term moving average period"
            )
    
    elif strategy_type == "Mean Reversion":
        col1, col2 = st.columns(2)
        with col1:
            config['rsi_period'] = st.number_input(
                "RSI Period",
                min_value=2,
                max_value=30,
                value=14,
                help="Period for RSI calculation"
            )
        with col2:
            config['rsi_threshold'] = st.number_input(
                "RSI Threshold",
                min_value=10,
                max_value=40,
                value=30,
                help="RSI level for trade signals"
            )
    
    elif strategy_type == "Breakout":
        config['lookback'] = st.number_input(
            "Lookback Period",
            min_value=5,
            max_value=100,
            value=20,
            help="Period for calculating breakout levels"
        )
    
    return config

def _run_prebuilt_strategy_backtest(coin: str, timeframe: str, config: dict, initial_capital: float):
    """Execute backtest with pre-built strategy parameters."""
    _execute_backtest(coin, timeframe, config, initial_capital)

def _run_custom_strategy_backtest(coin: str, strategy_config: dict, initial_capital: float):
    """Execute backtest with custom strategy parameters."""
    timeframe = strategy_config['timeframe']
    _execute_backtest(coin, timeframe, strategy_config, initial_capital)

def _execute_backtest(coin: str, timeframe: str, config: dict, initial_capital: float):
    """Execute backtest and display results."""
    with st.spinner("Running backtest..."):
        try:
            # Fetch historical data
            df = get_crypto_data(coin, timeframe)
            if df.empty:
                st.error("Failed to fetch historical data")
                return
            
            # Initialize and run backtester
            backtester = Backtester(df, initial_capital)
            results = backtester.run_strategy(config)
            
            if results:
                _display_results(results)
            else:
                st.error("No results generated. Please check your parameters.")
        except Exception as e:
            st.error(f"Error during backtesting: {str(e)}")

def _display_results(results):
    """Display backtest results with visualizations."""
    # Performance Metrics
    st.subheader("Performance Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Return",
            f"{(results.metrics['avg_return'] * results.metrics['total_trades']):.2f}%"
        )
        st.metric(
            "Win Rate",
            f"{results.metrics['win_rate']*100:.2f}%"
        )
    
    with col2:
        st.metric(
            "Total Trades",
            results.metrics['total_trades']
        )
        st.metric(
            "Max Drawdown",
            f"{results.metrics['max_drawdown']*100:.2f}%"
        )
    
    with col3:
        st.metric(
            "Sharpe Ratio",
            f"{results.metrics['sharpe_ratio']:.2f}"
        )
        st.metric(
            "Profit Factor",
            f"{results.metrics['profit_factor']:.2f}"
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
    
    # Trade History
    st.subheader("Trade History")
    if results.trades:
        trades_df = pd.DataFrame(results.trades)
        trades_df['return_pct'] = trades_df['return_pct'] * 100
        trades_df = trades_df.round(2)
        st.dataframe(trades_df)
