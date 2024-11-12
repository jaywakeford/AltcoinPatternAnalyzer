import streamlit as st
import json
from typing import Dict, List, Optional
import pandas as pd

class StrategyBuilder:
    def __init__(self):
        self.condition_types = {
            'Price Action': ['Above', 'Below', 'Crosses Above', 'Crosses Below'],
            'Technical Indicators': ['RSI', 'MACD', 'Moving Average'],
            'Volume': ['Volume Spike', 'Volume Decline'],
            'Market Phase': ['Accumulation', 'Distribution', 'Mark Up', 'Mark Down']
        }
        
        self.timeframes = ['1h', '4h', '1d', '1w']
        
        # Example strategies for templates
        self.example_strategies = {
            "RSI Reversal": {
                "description": "Buy oversold conditions (RSI < 30) and sell overbought conditions (RSI > 70)",
                "entry_conditions": [{"category": "Technical Indicators", "indicator": "RSI", "value": 30}],
                "exit_conditions": [{"category": "Technical Indicators", "indicator": "RSI", "value": 70}],
                "risk_management": {"stop_loss": 5, "take_profit": 15}
            },
            "Moving Average Crossover": {
                "description": "Buy when fast MA crosses above slow MA, sell on crossover below",
                "entry_conditions": [{"category": "Price Action", "indicator": "Crosses Above", "value": "MA20"}],
                "exit_conditions": [{"category": "Price Action", "indicator": "Crosses Below", "value": "MA50"}],
                "risk_management": {"stop_loss": 3, "take_profit": 9}
            }
        }

    def render(self) -> Optional[Dict]:
        """Render the strategy builder interface with enhanced documentation and validation."""
        st.subheader("📊 Custom Strategy Builder")
        
        # Initialize variables to avoid unbounded issues
        trailing_stop_distance = None
        max_pyramid_positions = None
        
        # Strategy templates
        with st.expander("📚 Strategy Templates", expanded=True):
            st.markdown("""
            ### Quick Start with Templates
            Select a pre-built strategy template to get started quickly. You can modify any parameters after loading.
            """)
            template = st.selectbox(
                "Select Template",
                ["Custom Strategy"] + list(self.example_strategies.keys()),
                help="Choose a template or start from scratch with 'Custom Strategy'"
            )
            
            if template != "Custom Strategy":
                st.info(f"💡 {self.example_strategies[template]['description']}")
                if st.button("Load Template"):
                    st.session_state.strategy_template = template

        # Strategy Basic Info
        with st.expander("📝 Strategy Information", expanded=True):
            st.markdown("""
            ### Basic Strategy Configuration
            Define the fundamental parameters of your trading strategy:
            - **Strategy Name**: A unique identifier for your strategy
            - **Description**: Detailed explanation of strategy logic
            - **Timeframe**: The time interval for analysis
            - **Position Size**: Percentage of capital per trade
            """)
            
            strategy_name = st.text_input(
                "Strategy Name",
                value="My Custom Strategy",
                help="Give your strategy a unique, descriptive name"
            )
            
            strategy_description = st.text_area(
                "Strategy Description",
                value="Enter a detailed description of your strategy...",
                help="Explain your strategy's logic, goals, and key components"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                timeframe = st.selectbox(
                    "Timeframe",
                    self.timeframes,
                    help="Choose the time interval for your strategy execution"
                )
                position_size = st.slider(
                    "Position Size (%)",
                    min_value=1,
                    max_value=100,
                    value=10,
                    help="Percentage of total capital to risk per trade"
                )
            
            with col2:
                max_trades = st.number_input(
                    "Maximum Open Trades",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Maximum number of concurrent open positions"
                )
                risk_per_trade = st.slider(
                    "Risk Per Trade (%)",
                    min_value=1,
                    max_value=10,
                    value=2,
                    help="Maximum percentage of capital to risk on each trade"
                )

        # Entry Conditions
        with st.expander("📈 Entry Conditions", expanded=True):
            st.markdown("""
            ### Entry Rules Configuration
            Define conditions that must be met to enter a trade:
            - **Multiple conditions**: Add multiple conditions that must all be met
            - **Technical indicators**: Use RSI, MACD, or Moving Averages
            - **Price action**: Set price-based entry signals
            - **Volume conditions**: Add volume-based confirmations
            """)
            entry_conditions = self._render_condition_builder("entry")

        # Exit Conditions
        with st.expander("📉 Exit Conditions", expanded=True):
            st.markdown("""
            ### Exit Rules Configuration
            Define conditions for exiting trades:
            - **Take profit**: Set profit targets
            - **Stop loss**: Define maximum acceptable loss
            - **Technical exits**: Use indicators for exit signals
            - **Trailing stops**: Dynamic profit protection
            """)
            exit_conditions = self._render_condition_builder("exit")

        # Risk Management
        with st.expander("🛡️ Risk Management", expanded=True):
            st.markdown("""
            ### Risk Management Settings
            Configure protective measures to preserve capital:
            - **Stop Loss**: Maximum acceptable loss per trade
            - **Take Profit**: Profit target levels
            - **Position Sizing**: Trade size calculation rules
            - **Pyramiding**: Rules for scaling into positions
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                stop_loss = st.number_input(
                    "Stop Loss (%)",
                    min_value=1,
                    max_value=50,
                    value=5,
                    help="Percentage below entry price to place stop loss"
                )
                trailing_stop = st.checkbox(
                    "Use Trailing Stop",
                    help="Enable dynamic stop loss that follows price movement"
                )
                if trailing_stop:
                    trailing_stop_distance = st.number_input(
                        "Trailing Stop Distance (%)",
                        min_value=1,
                        max_value=20,
                        value=3,
                        help="Distance to maintain for trailing stop"
                    )
            
            with col2:
                take_profit = st.number_input(
                    "Take Profit (%)",
                    min_value=1,
                    max_value=200,
                    value=15,
                    help="Percentage above entry price to take profits"
                )
                pyramiding = st.checkbox(
                    "Allow Pyramiding",
                    help="Enable adding to winning positions"
                )
                if pyramiding:
                    max_pyramid_positions = st.number_input(
                        "Max Pyramid Positions",
                        min_value=1,
                        max_value=5,
                        value=2,
                        help="Maximum number of entries per trend"
                    )

        # Strategy Preview and Validation
        if st.button("Generate Strategy"):
            # Validate strategy parameters
            validation_errors = self._validate_strategy(
                entry_conditions,
                exit_conditions,
                stop_loss,
                take_profit
            )
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"⚠️ {error}")
                return None
            
            strategy_config = {
                "name": strategy_name,
                "description": strategy_description,
                "timeframe": timeframe,
                "position_size": position_size,
                "max_trades": max_trades,
                "risk_per_trade": risk_per_trade,
                "entry_conditions": entry_conditions,
                "exit_conditions": exit_conditions,
                "risk_management": {
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "trailing_stop": trailing_stop,
                    "trailing_stop_distance": float(trailing_stop_distance) if trailing_stop else None,
                    "pyramiding": pyramiding,
                    "max_pyramid_positions": int(max_pyramid_positions) if pyramiding else None
                }
            }
            
            # Display strategy summary
            st.success("✅ Strategy successfully configured!")
            st.markdown("### Strategy Summary")
            st.markdown(f"""
            **{strategy_name}**
            - Timeframe: {timeframe}
            - Position Size: {position_size}%
            - Risk per Trade: {risk_per_trade}%
            - Stop Loss: {stop_loss}%
            - Take Profit: {take_profit}%
            """)
            
            st.json(json.dumps(strategy_config, indent=2))
            return strategy_config
            
        return None

    def _render_condition_builder(self, condition_type: str) -> List[Dict]:
        """Render condition builder with enhanced UI and validation."""
        conditions = []
        
        # Add condition button with clear visibility
        if st.button(f"➕ Add {condition_type.title()} Condition"):
            if f"{condition_type}_conditions" not in st.session_state:
                st.session_state[f"{condition_type}_conditions"] = 1
            else:
                st.session_state[f"{condition_type}_conditions"] += 1
        
        # Initialize session state for conditions if not exists
        if f"{condition_type}_conditions" not in st.session_state:
            st.session_state[f"{condition_type}_conditions"] = 1
        
        # Render condition inputs
        for i in range(st.session_state[f"{condition_type}_conditions"]):
            with st.container():
                st.markdown(f"#### Condition {i+1}")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    category = st.selectbox(
                        "Category",
                        list(self.condition_types.keys()),
                        key=f"{condition_type}_cat_{i}",
                        help="Select the type of condition to apply"
                    )
                
                with col2:
                    indicator = st.selectbox(
                        "Indicator",
                        self.condition_types[category],
                        key=f"{condition_type}_ind_{i}",
                        help="Choose the specific indicator or signal"
                    )
                
                with col3:
                    if indicator in ['RSI', 'MACD', 'Moving Average']:
                        value = st.number_input(
                            "Value",
                            key=f"{condition_type}_val_{i}",
                            help="Enter the numeric value for the indicator"
                        )
                    else:
                        value = st.text_input(
                            "Value",
                            key=f"{condition_type}_val_{i}",
                            help="Enter the condition value"
                        )
                
                conditions.append({
                    "category": category,
                    "indicator": indicator,
                    "value": str(value)  # Convert all values to string
                })
        
        return conditions

    def _validate_strategy(self, entry_conditions: List[Dict],
                         exit_conditions: List[Dict],
                         stop_loss: float,
                         take_profit: float) -> List[str]:
        """Validate strategy parameters and return any errors."""
        errors = []
        
        if not entry_conditions:
            errors.append("At least one entry condition is required")
        
        if not exit_conditions:
            errors.append("At least one exit condition is required")
        
        if stop_loss >= take_profit:
            errors.append("Take profit must be greater than stop loss")
        
        return errors
