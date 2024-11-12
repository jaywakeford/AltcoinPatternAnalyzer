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
    ### Choose Your Trading Approach
    
    **1. Custom Strategy Builder** 📊
    - Design your own unique trading strategy
    - Full control over entry/exit conditions
    - Flexible risk management settings
    - Save and load strategy templates
    
    **2. Pre-built Strategies** 🚀
    - Ready-to-use proven strategies
    - Configurable parameters
    - Quick setup and testing
    - Ideal for learning and comparison
    """)
    
    # Strategy Selection with unique key
    strategy_mode = st.radio(
        "Strategy Mode",
        ["Custom Strategy Builder", "Pre-built Strategies"],
        help="Choose between creating your own strategy or using pre-built ones",
        key="strategy_mode_selector"  # Add unique key
    )
    
    st.markdown("---")
    
    if strategy_mode == "Custom Strategy Builder":
        _render_custom_strategy_section()
    else:
        _render_prebuilt_strategy_section()

def _render_prebuilt_strategy_section():
    """Render the pre-built strategy configuration section."""
    with st.expander("Strategy Configuration", expanded=True):
        st.markdown("""
        ### Pre-built Strategy Setup
        Configure parameters for established trading strategies:
        - Trend Following: Based on moving average crossovers
        - Mean Reversion: Uses RSI for oversold/overbought conditions
        - Breakout: Identifies price breakouts from ranges
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            strategy_type = st.selectbox(
                "Strategy Type",
                ["Trend Following", "Mean Reversion", "Breakout"],
                help="Choose your trading strategy type"
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
    st.markdown("""
    ### 🛠️ Custom Strategy Builder
    
    Create your own trading strategy with full control over:
    - Entry and exit conditions
    - Risk management rules
    - Position sizing
    - Market phase analysis
    
    Use the strategy builder below to define your trading rules.
    """)
    
    strategy_builder = StrategyBuilder()
    strategy_config = strategy_builder.render()
    
    if strategy_config:
        st.markdown("### 📊 Backtest Configuration")
        col1, col2 = st.columns(2)
        with col1:
            selected_coin = st.selectbox(
                "Asset",
                ["bitcoin", "ethereum", "cardano", "solana"],
                help="Select cryptocurrency to backtest your strategy"
            )
        
        with col2:
            initial_capital = st.number_input(
                "Initial Capital (USD)",
                min_value=1000,
                value=10000,
                step=1000,
                help="Starting capital for your backtest"
            )
        
        # Strategy Summary
        st.markdown("### Strategy Overview")
        st.markdown(f"""
        **Risk Management**
        - Stop Loss: {strategy_config['risk_management']['stop_loss']}%
        - Take Profit: {strategy_config['risk_management']['take_profit']}%
        - Position Size: {strategy_config['position_size']}%
        
        **Trading Rules**
        - Entry Conditions: {len(strategy_config['entry_conditions'])}
        - Exit Conditions: {len(strategy_config['exit_conditions'])}
        - Maximum Open Trades: {strategy_config['max_trades']}
        """)
        
        if st.button("▶️ Run Backtest", help="Start the backtesting process with your custom strategy"):
            _run_custom_strategy_backtest(selected_coin, strategy_config, initial_capital)

def _get_strategy_parameters(strategy_type: str) -> dict:
    """Get strategy-specific parameters based on the selected strategy type."""
    config = {'strategy_type': strategy_type.lower().replace(' ', '_')}
    
    if strategy_type == "Trend Following":
        col1, col2 = st.columns(2)
        with col1:
            sma_short = st.number_input(
                "Short SMA Period",
                min_value=5,
                max_value=50,
                value=20,
                help="Short-term moving average period"
            )
            config['sma_short'] = str(sma_short)
        with col2:
            sma_long = st.number_input(
                "Long SMA Period",
                min_value=10,
                max_value=200,
                value=50,
                help="Long-term moving average period"
            )
            config['sma_long'] = str(sma_long)
    
    elif strategy_type == "Mean Reversion":
        col1, col2 = st.columns(2)
        with col1:
            rsi_period = st.number_input(
                "RSI Period",
                min_value=2,
                max_value=30,
                value=14,
                help="Period for RSI calculation"
            )
            config['rsi_period'] = str(rsi_period)
        with col2:
            rsi_threshold = st.number_input(
                "RSI Threshold",
                min_value=10,
                max_value=40,
                value=30,
                help="RSI level for trade signals"
            )
            config['rsi_threshold'] = str(rsi_threshold)
    
    elif strategy_type == "Breakout":
        lookback = st.number_input(
            "Lookback Period",
            min_value=5,
            max_value=100,
            value=20,
            help="Period for calculating breakout levels"
        )
        config['lookback'] = str(lookback)
    
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