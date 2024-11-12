import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.backtesting import Backtester
from utils.data_fetcher import get_crypto_data
from components.strategy_builder import StrategyBuilder
from datetime import datetime
from utils.ui_components import show_error, show_warning, group_elements

def render_backtesting_section():
    """Render the backtesting interface with improved layout and visibility."""
    # Create placeholder for the entire section
    main_container = st.container()
    
    with main_container:
        st.subheader("🔄 Strategy Development & Testing")
        
        # Add description with improved visibility
        st.markdown("""
        <div style='background-color: rgba(255, 255, 255, 0.1); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <h4 style='margin-top: 0;'>Welcome to the Strategy Development Center</h4>
            <p>Here you can:</p>
            <ul>
                <li>Build and configure your trading strategy</li>
                <li>Test your strategy against historical data</li>
                <li>Analyze performance metrics and results</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Create placeholders for strategy sections
        strategy_section = st.empty()
        backtest_section = st.empty()
        results_section = st.empty()
        
        # Strategy Builder Section with improved visibility
        with strategy_section.container():
            st.markdown("### Strategy Builder")
            strategy_builder = StrategyBuilder()
            
            # Add loading state feedback
            with st.spinner("Loading strategy builder..."):
                result = strategy_builder.render()
            
            if result:
                strategy_config, backtest_config = result
                st.session_state['current_strategy'] = strategy_config
                st.session_state['current_backtest'] = backtest_config
                
                # Add visual confirmation
                st.success("Strategy configuration complete! Ready for testing.")
                
                # Add run button with clear visibility
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("▶️ Run Strategy Test", 
                               key=f"run_backtest_{datetime.now().timestamp()}",
                               use_container_width=True):
                        with st.spinner("Running backtest..."):
                            _run_backtest(strategy_config, backtest_config)
        
        # Results Section
        if 'backtest_results' in st.session_state:
            with results_section.container():
                st.markdown("### Backtest Results")
                _display_backtest_results(st.session_state['backtest_results'])

def _validate_backtest_params(strategy_config: dict, backtest_config: dict) -> bool:
    """Validate backtest parameters before execution."""
    errors = []
    
    if not strategy_config.get('entry_conditions'):
        errors.append("Strategy must have at least one entry condition")
    if not strategy_config.get('exit_conditions'):
        errors.append("Strategy must have at least one exit condition")
    if not strategy_config.get('position_size'):
        errors.append("Position size must be specified")
    if not backtest_config.get('asset'):
        errors.append("Trading asset must be selected")
    if not backtest_config.get('initial_capital'):
        errors.append("Initial capital must be specified")
    if backtest_config.get('initial_capital', 0) <= 0:
        errors.append("Initial capital must be positive")
    
    if errors:
        for error in errors:
            show_error("Configuration Error", error)
        return False
    
    return True

def _run_backtest(strategy_config: dict, backtest_config: dict):
    """Execute backtest with improved error handling and visual feedback."""
    if not _validate_backtest_params(strategy_config, backtest_config):
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Update progress
        status_text.text("Fetching historical data...")
        progress_bar.progress(25)
        
        # Fetch historical data
        df = get_crypto_data(
            backtest_config['asset'].split('/')[0].lower(),
            strategy_config['timeframe']
        )
        
        if df.empty:
            show_error(
                "Data Error",
                "Failed to fetch historical data",
                "Please check your internet connection and try again"
            )
            return
        
        # Update progress
        status_text.text("Initializing backtester...")
        progress_bar.progress(50)
        
        # Initialize and run backtester
        backtester = Backtester(df, backtest_config['initial_capital'])
        
        status_text.text("Running strategy test...")
        progress_bar.progress(75)
        
        results = backtester.run_strategy(strategy_config)
        
        if results:
            progress_bar.progress(100)
            status_text.text("Backtest completed successfully!")
            st.session_state['backtest_results'] = results
            st.success("Strategy test completed successfully!")
            _display_backtest_results(results)
        else:
            show_error(
                "Backtest Error",
                "No results generated",
                "Please check your strategy parameters"
            )
            
    except Exception as e:
        show_error(
            "Backtest Error",
            str(e),
            "Please check your parameters and try again"
        )
    finally:
        # Clean up progress indicators
        progress_bar.empty()
        status_text.empty()

def _display_backtest_results(results):
    """Display backtest results with improved visualizations and layout."""
    # Performance Metrics with improved visibility
    with st.container():
        st.markdown("""
        <div style='background-color: rgba(255, 255, 255, 0.1); 
                    padding: 1rem; border-radius: 0.5rem; 
                    margin: 1rem 0;'>
            <h4 style='margin-top: 0;'>Performance Summary</h4>
        </div>
        """, unsafe_allow_html=True)
        
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
        
        # Equity Curve with improved styling
        st.markdown("### Portfolio Performance")
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
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Trade Analysis
        st.markdown("### Trade Analysis")
        if results.trades:
            trades_df = pd.DataFrame(results.trades)
            trades_df['return_pct'] = trades_df['return_pct'] * 100
            trades_df = trades_df.round(2)
            
            # Style the dataframe
            st.dataframe(
                trades_df,
                use_container_width=True,
                height=400
            )
