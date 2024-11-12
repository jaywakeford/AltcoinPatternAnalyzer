import streamlit as st
import json
import re
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
        
        # Example strategies templates
        self.example_strategies = {
            "RSI Reversal": {
                "description": "Buy when RSI falls below 30 (oversold) and sell when RSI rises above 70 (overbought)",
                "entry_conditions": [{"category": "Technical Indicators", "indicator": "RSI", "value": "30"}],
                "exit_conditions": [{"category": "Technical Indicators", "indicator": "RSI", "value": "70"}],
                "risk_management": {"stop_loss": 5, "take_profit": 15}
            },
            "Moving Average Crossover": {
                "description": "Buy when 50-day SMA crosses above 200-day SMA (golden cross) and sell on death cross",
                "entry_conditions": [{"category": "Price Action", "indicator": "Crosses Above", "value": "MA50"}],
                "exit_conditions": [{"category": "Price Action", "indicator": "Crosses Below", "value": "MA200"}],
                "risk_management": {"stop_loss": 3, "take_profit": 9}
            }
        }

    def _parse_strategy_description(self, description: str) -> Dict:
        """Parse strategy description using regex patterns."""
        # Initialize extracted parameters
        params = {
            "strategy_type": "custom",
            "entry_conditions": [],
            "exit_conditions": [],
            "risk_management": {
                "stop_loss": 5,  # Default values
                "take_profit": 15,
                "trailing_stop": False,
                "pyramiding": False
            },
            "position_size": 10,  # Default value
            "timeframe": "1d"  # Default value
        }
        
        description = description.lower()
        
        # Extract moving averages
        ma_pattern = r'(\d+)[-\s]?day(?:\s+)?(sma|ema)'
        ma_matches = list(re.finditer(ma_pattern, description))
        
        if ma_matches:
            params["strategy_type"] = "trend_following"
            ma_periods = [(int(m.group(1)), m.group(2).upper()) for m in ma_matches]
            
            if len(ma_periods) >= 2:
                # Sort periods to use shorter period for entry and longer for exit
                ma_periods.sort(key=lambda x: x[0])
                params["entry_conditions"].append({
                    "category": "Price Action",
                    "indicator": "Crosses Above",
                    "value": f"{ma_periods[0][1]}{ma_periods[0][0]}"
                })
                params["exit_conditions"].append({
                    "category": "Price Action",
                    "indicator": "Crosses Below",
                    "value": f"{ma_periods[1][1]}{ma_periods[1][0]}"
                })

        # Extract RSI conditions
        rsi_pattern = r'rsi\s*(?:is\s*)?(<|>|below|above)?\s*(\d+)'
        rsi_matches = list(re.finditer(rsi_pattern, description))
        
        for match in rsi_matches:
            operator = match.group(1) if match.group(1) else "below"
            value = match.group(2)
            
            if operator in ["<", "below"] and int(value) < 50:
                params["entry_conditions"].append({
                    "category": "Technical Indicators",
                    "indicator": "RSI",
                    "value": value
                })
            elif operator in [">", "above"] and int(value) > 50:
                params["exit_conditions"].append({
                    "category": "Technical Indicators",
                    "indicator": "RSI",
                    "value": value
                })
                params["strategy_type"] = "mean_reversion"

        # Extract risk management parameters
        stop_loss_pattern = r'stop\s*loss\s*(?:at|of)?\s*(\d+)%?'
        take_profit_pattern = r'take\s*profit\s*(?:at|of)?\s*(\d+)%?'
        
        sl_match = re.search(stop_loss_pattern, description)
        tp_match = re.search(take_profit_pattern, description)
        
        if sl_match:
            params["risk_management"]["stop_loss"] = int(sl_match.group(1))
        if tp_match:
            params["risk_management"]["take_profit"] = int(tp_match.group(1))

        # Extract position sizing
        if "fully allocated" in description:
            params["position_size"] = 100
        else:
            size_match = re.search(r'(\d+)%\s*(?:of|position|size)', description)
            if size_match:
                params["position_size"] = int(size_match.group(1))

        # Extract timeframe
        timeframe_pattern = r'(\d+)\s*(hour|day|week|h|d|w)'
        tf_match = re.search(timeframe_pattern, description)
        if tf_match:
            value = tf_match.group(1)
            unit = tf_match.group(2)
            if unit.startswith('h'):
                params["timeframe"] = f"{value}h"
            elif unit.startswith('d'):
                params["timeframe"] = f"{value}d"
            elif unit.startswith('w'):
                params["timeframe"] = f"{value}w"

        return params

    def render(self) -> Optional[Dict]:
        """Render the strategy builder interface."""
        st.subheader("📊 Custom Strategy Builder")
        
        # Natural Language Input
        with st.expander("🗣️ Strategy Description Input", expanded=True):
            st.markdown("""
            ### Describe Your Strategy
            Enter your trading strategy in plain text. Include details about:
            - Entry and exit conditions
            - Technical indicators (MA, RSI, etc.)
            - Risk management rules
            - Position sizing
            
            Example: "Buy when 50-day SMA crosses above 200-day SMA with 30% position size. 
            Set stop loss at 5% and take profit at 15%. Exit when price crosses below 200-day SMA."
            """)
            
            strategy_description = st.text_area(
                "Strategy Description",
                height=100,
                help="Describe your trading strategy in plain text"
            )
            
            if strategy_description and st.button("Parse Strategy"):
                parsed_params = self._parse_strategy_description(strategy_description)
                st.session_state.parsed_strategy = parsed_params
                st.success("✅ Strategy parsed successfully! Parameters extracted below.")

        # Strategy templates
        with st.expander("📚 Strategy Templates", expanded=True):
            st.markdown("""
            ### Quick Start with Templates
            Select a pre-built strategy template or use your parsed strategy.
            """)
            template_options = ["Custom Strategy"] + list(self.example_strategies.keys())
            if hasattr(st.session_state, 'parsed_strategy'):
                template_options.insert(1, "Parsed Strategy")
            
            template = st.selectbox(
                "Select Template",
                template_options,
                help="Choose a template or use your parsed strategy"
            )
            
            if template != "Custom Strategy":
                if template == "Parsed Strategy" and hasattr(st.session_state, 'parsed_strategy'):
                    st.info("Using parameters from your natural language description")
                else:
                    st.info(f"💡 {self.example_strategies[template]['description']}")
                    if st.button("Load Template"):
                        st.session_state.strategy_template = template

        # Initialize variables to avoid unbounded issues
        trailing_stop_distance = None
        max_pyramid_positions = None

        # Strategy Basic Info
        with st.expander("📝 Strategy Information", expanded=True):
            st.markdown("""
            ### Basic Strategy Configuration
            Review and adjust the extracted parameters or enter them manually.
            """)
            
            # Use parsed parameters if available
            default_name = "My Custom Strategy"
            default_description = "Enter a detailed description of your strategy..."
            default_position_size = 10
            
            if hasattr(st.session_state, 'parsed_strategy'):
                default_position_size = st.session_state.parsed_strategy["position_size"]
            
            strategy_name = st.text_input(
                "Strategy Name",
                value=default_name,
                help="Give your strategy a unique, descriptive name"
            )
            
            strategy_description = st.text_area(
                "Strategy Description",
                value=default_description,
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
                    value=default_position_size,
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
            Define or adjust the conditions for entering trades.
            """)
            entry_conditions = self._render_condition_builder("entry")

        # Exit Conditions
        with st.expander("📉 Exit Conditions", expanded=True):
            st.markdown("""
            ### Exit Rules Configuration
            Define or adjust the conditions for exiting trades.
            """)
            exit_conditions = self._render_condition_builder("exit")

        # Risk Management
        with st.expander("🛡️ Risk Management", expanded=True):
            st.markdown("""
            ### Risk Management Settings
            Configure protective measures to preserve capital.
            """)
            
            default_stop_loss = 5
            default_take_profit = 15
            
            if hasattr(st.session_state, 'parsed_strategy'):
                default_stop_loss = st.session_state.parsed_strategy["risk_management"]["stop_loss"]
                default_take_profit = st.session_state.parsed_strategy["risk_management"]["take_profit"]
            
            col1, col2 = st.columns(2)
            with col1:
                stop_loss = st.number_input(
                    "Stop Loss (%)",
                    min_value=1,
                    max_value=50,
                    value=default_stop_loss,
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
                    value=default_take_profit,
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

    def _validate_strategy(self, entry_conditions: List[Dict], exit_conditions: List[Dict],
                         stop_loss: float, take_profit: float) -> List[str]:
        """Validate strategy parameters."""
        errors = []
        
        # Basic validation
        if not entry_conditions:
            errors.append("At least one entry condition is required")
        if not exit_conditions:
            errors.append("At least one exit condition is required")
        if stop_loss >= take_profit:
            errors.append("Take profit must be greater than stop loss")
        
        # Validate condition values
        for condition in entry_conditions + exit_conditions:
            if condition["indicator"] in ['RSI', 'MACD', 'Moving Average']:
                try:
                    value = float(condition["value"])
                    if condition["indicator"] == 'RSI' and (value < 0 or value > 100):
                        errors.append(f"RSI value must be between 0 and 100, got {value}")
                except ValueError:
                    errors.append(f"Invalid numeric value for {condition['indicator']}: {condition['value']}")
        
        return errors

    def _render_condition_builder(self, condition_type: str) -> List[Dict]:
        """Render condition builder interface."""
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
        
        # Use parsed conditions if available
        default_conditions = []
        if hasattr(st.session_state, 'parsed_strategy'):
            if condition_type == "entry":
                default_conditions = st.session_state.parsed_strategy["entry_conditions"]
            else:
                default_conditions = st.session_state.parsed_strategy["exit_conditions"]
        
        # Render condition inputs
        for i in range(st.session_state[f"{condition_type}_conditions"]):
            with st.container():
                st.markdown(f"#### Condition {i+1}")
                col1, col2, col3 = st.columns(3)
                
                # Get default values from parsed strategy if available
                default_category = default_conditions[i]["category"] if i < len(default_conditions) else list(self.condition_types.keys())[0]
                default_indicator = default_conditions[i]["indicator"] if i < len(default_conditions) else self.condition_types[default_category][0]
                default_value = default_conditions[i]["value"] if i < len(default_conditions) else ""
                
                with col1:
                    category = st.selectbox(
                        "Category",
                        list(self.condition_types.keys()),
                        key=f"{condition_type}_cat_{i}",
                        index=list(self.condition_types.keys()).index(default_category),
                        help="Select the type of condition to apply"
                    )
                
                with col2:
                    indicator = st.selectbox(
                        "Indicator",
                        self.condition_types[category],
                        key=f"{condition_type}_ind_{i}",
                        index=self.condition_types[category].index(default_indicator) if default_indicator in self.condition_types[category] else 0,
                        help="Choose the specific indicator or signal"
                    )
                
                with col3:
                    if indicator in ['RSI', 'MACD', 'Moving Average']:
                        value = st.number_input(
                            "Value",
                            key=f"{condition_type}_val_{i}",
                            value=float(default_value) if default_value.replace('.', '').isdigit() else 0,
                            help="Enter the numeric value for the indicator"
                        )
                    else:
                        value = st.text_input(
                            "Value",
                            key=f"{condition_type}_val_{i}",
                            value=default_value,
                            help="Enter the condition value"
                        )
                
                conditions.append({
                    "category": category,
                    "indicator": indicator,
                    "value": str(value)  # Convert all values to string
                })
        
        return conditions