import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.backtesting import Backtester
from utils.data_fetcher import get_crypto_data

def render_backtesting_section():
    """Render the backtesting interface and results."""
    st.header("Strategy Backtesting")
    
    # Strategy selection
    strategy_type = st.selectbox(
        "Select Strategy Type",
        ["Trend Following", "Mean Reversion", "Breakout"],
        key="strategy_type"
    )
    
    # Strategy parameters based on selection
    strategy_config = _get_strategy_config(strategy_type)
    
    # Asset and timeframe selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_coin = st.selectbox(
            "Select Asset",
            ["bitcoin", "ethereum", "cardano", "solana"],
            key="backtest_asset"
        )
    
    with col2:
        timeframe = st.selectbox(
            "Select Timeframe",
            ["30", "90", "180", "365"],
            key="backtest_timeframe"
        )
    
    # Capital and risk parameters
    initial_capital = st.number_input(
        "Initial Capital (USD)",
        min_value=1000,
        value=100000,
        step=1000,
        key="initial_capital"
    )
    
    # Run backtest button
    if st.button("Run Backtest"):
        with st.spinner("Running backtest..."):
            results = _run_backtest(
                selected_coin,
                timeframe,
                strategy_config,
                initial_capital
            )
            _display_results(results)

def _get_strategy_config(strategy_type: str) -> dict:
    """Get strategy configuration based on user inputs."""
    config = {'strategy_type': strategy_type.lower().replace(' ', '_')}
    
    if strategy_type == "Trend Following":
        col1, col2 = st.columns(2)
        with col1:
            config['sma_short'] = st.number_input(
                "Short SMA Period",
                min_value=1,
                value=20,
                key="sma_short"
            )
        with col2:
            config['sma_long'] = st.number_input(
                "Long SMA Period",
                min_value=1,
                value=50,
                key="sma_long"
            )
    
    elif strategy_type == "Mean Reversion":
        col1, col2, col3 = st.columns(3)
        with col1:
            config['rsi_period'] = st.number_input(
                "RSI Period",
                min_value=1,
                value=14,
                key="rsi_period"
            )
        with col2:
            config['oversold'] = st.number_input(
                "Oversold Level",
                min_value=1,
                max_value=100,
                value=30,
                key="oversold"
            )
        with col3:
            config['overbought'] = st.number_input(
                "Overbought Level",
                min_value=1,
                max_value=100,
                value=70,
                key="overbought"
            )
    
    elif strategy_type == "Breakout":
        config['lookback'] = st.number_input(
            "Lookback Period",
            min_value=1,
            value=20,
            key="lookback"
        )
    
    return config

def _run_backtest(coin: str, timeframe: str, config: dict, initial_capital: float):
    """Run backtest with selected parameters."""
    # Fetch historical data
    df = get_crypto_data(coin, timeframe)
    
    if df.empty:
        st.error("Failed to fetch historical data. Please try again.")
        return None
    
    # Initialize and run backtester
    backtester = Backtester(df, initial_capital)
    results = backtester.run_strategy(config)
    
    return results

def _display_results(results):
    """Display backtest results."""
    if not results:
        return
    
    # Display metrics
    st.subheader("Performance Metrics")
    metrics = results.metrics
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Return", f"{(metrics['avg_return'] * metrics['total_trades']):.2f}%")
        st.metric("Win Rate", f"{metrics['win_rate']*100:.2f}%")
    
    with col2:
        st.metric("Total Trades", metrics['total_trades'])
        st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
    
    with col3:
        st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.2f}%")
        st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
    
    # Plot equity curve
    st.subheader("Equity Curve")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=results.equity_curve.index,
        y=results.equity_curve.values,
        name="Equity",
        line=dict(color='#17C37B')
    ))
    
    fig.update_layout(
        title="Portfolio Equity Over Time",
        xaxis_title="Date",
        yaxis_title="Equity (USD)",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display trade list
    st.subheader("Trade History")
    if results.trades:
        trades_df = pd.DataFrame(results.trades)
        trades_df['duration'] = trades_df['exit_time'] - trades_df['entry_time']
        trades_df = trades_df[[
            'entry_time', 'exit_time', 'position_type',
            'entry_price', 'exit_price', 'return_pct', 'pnl'
        ]]
        trades_df['return_pct'] = trades_df['return_pct'] * 100
        trades_df = trades_df.round(2)
        st.dataframe(trades_df)
