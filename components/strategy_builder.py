import streamlit as st
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
from utils.ui_components import show_error, show_warning, group_elements

class StrategyBuilder:
    def __init__(self):
        self.candlestick_patterns = [
            'doji', 'hammer', 'inverted hammer', 'bullish engulfing',
            'bearish engulfing', 'morning star', 'evening star',
            'shooting star', 'hanging man', 'dark cloud cover',
            'piercing pattern', 'three white soldiers', 'three black crows'
        ]
        
        self.indicators = {
            'Moving Average': ['SMA', 'EMA', 'WMA'],
            'Momentum': ['RSI', 'MACD', 'Stochastic'],
            'Volume': ['OBV', 'Volume Profile', 'VWAP'],
            'Volatility': ['Bollinger Bands', 'ATR', 'Keltner Channels']
        }

    def _parse_strategy_text(self, text: str) -> Dict:
        """Parse strategy description from natural language text."""
        strategy = {
            "entry_conditions": [],
            "exit_conditions": [],
            "position_size": None,
            "stop_loss": None,
            "take_profit": None,
            "timeframe": None
        }
        
        # Extract position size
        position_size_match = re.search(r'position size:?\s*(\d+)%', text.lower())
        if position_size_match:
            strategy["position_size"] = float(position_size_match.group(1))
            
        # Extract stop loss
        stop_loss_match = re.search(r'stop loss:?\s*(\d+)%', text.lower())
        if stop_loss_match:
            strategy["stop_loss"] = float(stop_loss_match.group(1))
            
        # Extract take profit
        take_profit_match = re.search(r'take profit:?\s*(\d+)%', text.lower())
        if take_profit_match:
            strategy["take_profit"] = float(take_profit_match.group(1))
            
        # Extract timeframe
        timeframe_match = re.search(r'timeframe:?\s*(\d+)([mhd])', text.lower())
        if timeframe_match:
            value, unit = timeframe_match.groups()
            strategy["timeframe"] = f"{value}{unit}"
            
        # Extract entry conditions
        entry_section = re.search(r'entry conditions?:(.+?)(?=exit conditions?:|$)', text, re.DOTALL | re.IGNORECASE)
        if entry_section:
            conditions = entry_section.group(1).strip().split('\n')
            strategy["entry_conditions"] = [cond.strip() for cond in conditions if cond.strip()]
            
        # Extract exit conditions
        exit_section = re.search(r'exit conditions?:(.+?)(?=position size:|$)', text, re.DOTALL | re.IGNORECASE)
        if exit_section:
            conditions = exit_section.group(1).strip().split('\n')
            strategy["exit_conditions"] = [cond.strip() for cond in conditions if cond.strip()]
        
        return strategy

    def render(self) -> Optional[Tuple[Dict, Dict]]:
        """Render strategy builder interface and return both strategy and backtesting configs."""
        timestamp = datetime.now().timestamp()

        with group_elements("Strategy Builder"):
            st.markdown("""
            Design your trading strategy using one of the following methods:
            - **Natural Language**: Describe your strategy in plain English
            - **Template**: Start with a pre-built strategy template
            - **Manual Builder**: Build your strategy step by step
            
            Your strategy will be automatically prepared for backtesting once configured.
            """)
            
            input_method = st.radio(
                "Strategy Input Method",
                ["Natural Language", "Template", "Manual Builder"],
                key=f"strategy_input_method_{timestamp}",
                help="Choose how you want to create your strategy"
            )
            
            strategy_config = None
            if input_method == "Natural Language":
                strategy_config = self._render_natural_language_input(timestamp)
            elif input_method == "Template":
                strategy_config = self._render_template_selection(timestamp)
            else:
                strategy_config = self._render_manual_builder(timestamp)
            
            if strategy_config:
                st.success("Strategy configured successfully! Now let's set up the testing parameters.")
                backtest_config = self._render_backtest_config(timestamp)
                if backtest_config:
                    return strategy_config, backtest_config
            
            return None

    def _render_natural_language_input(self, timestamp: float) -> Optional[Dict]:
        """Render natural language input section."""
        with group_elements("Strategy Description"):
            st.markdown("""
            Describe your strategy in plain English. Include:
            - Entry conditions
            - Exit conditions
            - Position size
            - Risk management (stop loss, take profit)
            """)
            
            description = st.text_area(
                "Strategy Description",
                height=300,
                key=f"strategy_description_{timestamp}",
                help="Write your strategy in natural language"
            )
            
            if description and st.button("Parse Strategy", key=f"parse_btn_{timestamp}"):
                try:
                    strategy = self._parse_strategy_text(description)
                    if strategy:
                        st.success("Strategy parsed successfully!")
                        self._display_strategy_summary(strategy)
                        return strategy
                except Exception as e:
                    show_error(
                        "Strategy Parsing Error",
                        str(e),
                        "Please check your strategy description format and try again."
                    )
            return None

    def _render_template_selection(self, timestamp: float) -> Optional[Dict]:
        """Render template selection section."""
        templates = {
            "Moving Average Crossover": {
                "entry_conditions": ["SMA50 crosses above SMA200"],
                "exit_conditions": ["SMA50 crosses below SMA200"],
                "position_size": 10.0,
                "stop_loss": 5.0,
                "take_profit": 15.0,
                "timeframe": "1d"
            },
            "RSI Reversal": {
                "entry_conditions": ["RSI below 30"],
                "exit_conditions": ["RSI above 70"],
                "position_size": 10.0,
                "stop_loss": 3.0,
                "take_profit": 9.0,
                "timeframe": "4h"
            }
        }
        
        with group_elements("Strategy Templates"):
            selected = st.selectbox(
                "Select Template",
                list(templates.keys()),
                key=f"template_select_{timestamp}",
                help="Choose a pre-built strategy template"
            )
            
            if selected and st.button("Use Template", key=f"template_btn_{timestamp}"):
                strategy = templates[selected]
                self._display_strategy_summary(strategy)
                return strategy
        return None

    def _render_manual_builder(self, timestamp: float) -> Optional[Dict]:
        """Render manual strategy builder section."""
        with group_elements("Manual Strategy Builder"):
            col1, col2 = st.columns(2)
            
            with col1:
                position_size = st.number_input(
                    "Position Size (%)",
                    min_value=1,
                    max_value=100,
                    value=10,
                    help="Percentage of capital to use per trade",
                    key=f"position_size_{timestamp}"
                )
                stop_loss = st.number_input(
                    "Stop Loss (%)",
                    min_value=1,
                    max_value=50,
                    value=5,
                    help="Stop loss percentage below entry price",
                    key=f"stop_loss_{timestamp}"
                )
            
            with col2:
                take_profit = st.number_input(
                    "Take Profit (%)",
                    min_value=1,
                    max_value=100,
                    value=15,
                    help="Take profit percentage above entry price",
                    key=f"take_profit_{timestamp}"
                )
                timeframe = st.selectbox(
                    "Timeframe",
                    ["1m", "5m", "15m", "1h", "4h", "1d"],
                    help="Chart timeframe for the strategy",
                    key=f"timeframe_{timestamp}"
                )

            with group_elements("Trading Rules"):
                st.subheader("Entry Conditions")
                entry_conditions = []
                
                indicator_type = st.selectbox(
                    "Indicator Type",
                    list(self.indicators.keys()),
                    key=f"entry_indicator_type_{timestamp}"
                )
                
                if indicator_type:
                    selected_indicator = st.selectbox(
                        "Select Indicator",
                        self.indicators[indicator_type],
                        key=f"entry_indicator_{timestamp}"
                    )
                    if selected_indicator:
                        entry_conditions.append(f"Using {selected_indicator}")
                
                st.subheader("Exit Conditions")
                exit_conditions = []
                
                indicator_type = st.selectbox(
                    "Indicator Type",
                    list(self.indicators.keys()),
                    key=f"exit_indicator_type_{timestamp}"
                )
                
                if indicator_type:
                    selected_indicator = st.selectbox(
                        "Select Indicator",
                        self.indicators[indicator_type],
                        key=f"exit_indicator_{timestamp}"
                    )
                    if selected_indicator:
                        exit_conditions.append(f"Using {selected_indicator}")

            if st.button("Create Strategy", key=f"create_strategy_btn_{timestamp}"):
                if not entry_conditions:
                    show_error(
                        "Invalid Strategy",
                        "Entry conditions are required",
                        "Please select at least one entry condition"
                    )
                    return None
                    
                if not exit_conditions:
                    show_error(
                        "Invalid Strategy",
                        "Exit conditions are required",
                        "Please select at least one exit condition"
                    )
                    return None
                
                strategy = {
                    "entry_conditions": entry_conditions,
                    "exit_conditions": exit_conditions,
                    "position_size": position_size,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "timeframe": timeframe
                }
                
                self._display_strategy_summary(strategy)
                return strategy
        return None

    def _render_backtest_config(self, timestamp: float) -> Optional[Dict]:
        """Render backtesting configuration section."""
        with group_elements("Backtesting Configuration"):
            col1, col2 = st.columns(2)
            
            with col1:
                asset = st.selectbox(
                    "Asset",
                    ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"],
                    help="Select the asset to backtest",
                    key=f"backtest_asset_{timestamp}"
                )
                
                initial_capital = st.number_input(
                    "Initial Capital (USDT)",
                    min_value=100,
                    value=10000,
                    step=100,
                    help="Starting capital for backtesting",
                    key=f"initial_capital_{timestamp}"
                )
            
            with col2:
                start_date = st.date_input(
                    "Start Date",
                    help="Backtest start date",
                    key=f"start_date_{timestamp}"
                )
                
                end_date = st.date_input(
                    "End Date",
                    help="Backtest end date",
                    key=f"end_date_{timestamp}"
                )
            
            if asset and initial_capital and start_date and end_date:
                if isinstance(start_date, datetime):
                    start_date = start_date.date()
                if isinstance(end_date, datetime):
                    end_date = end_date.date()
                
                if start_date >= end_date:
                    show_error(
                        "Invalid Date Range",
                        "Start date must be before end date",
                        "Please adjust your date selection"
                    )
                    return None
                    
                return {
                    "asset": asset,
                    "initial_capital": initial_capital,
                    "start_date": start_date,
                    "end_date": end_date
                }
        return None

    def _display_strategy_summary(self, strategy: Dict):
        """Display strategy summary with improved formatting."""
        with group_elements("Strategy Summary"):
            st.write("**Entry Conditions:**", strategy["entry_conditions"])
            st.write("**Exit Conditions:**", strategy["exit_conditions"])
            st.write(f"**Position Size:** {strategy['position_size']}%")
            st.write(f"**Stop Loss:** {strategy['stop_loss']}%")
            st.write(f"**Take Profit:** {strategy['take_profit']}%")
            st.write(f"**Timeframe:** {strategy['timeframe']}")
