import streamlit as st
from typing import Dict, Optional, Tuple
import re
from datetime import datetime
from utils.ui_components import show_error, show_warning, group_elements

class StrategyBuilder:
    def __init__(self):
        # Initialize default state
        if 'strategy_state' not in st.session_state:
            st.session_state.strategy_state = {
                'input_method': 'Template',
                'description': '',
                'template': None,
                'manual_config': {
                    'position_size': 10,
                    'stop_loss': 5,
                    'take_profit': 15,
                    'timeframe': '1h'
                }
            }
        
        # Initialize templates
        self.templates = {
            "Moving Average Crossover": {
                "name": "Moving Average Crossover Strategy",
                "description": """
                A trend-following strategy that uses two moving averages to identify trend changes.
                - Entry: When fast MA crosses above slow MA
                - Exit: When fast MA crosses below slow MA
                - Recommended for: Trending markets
                """,
                "config": {
                    "strategy_type": "trend_following",
                    "entry_conditions": ["SMA50 crosses above SMA200"],
                    "exit_conditions": ["SMA50 crosses below SMA200"],
                    "position_size": 10.0,
                    "stop_loss": 5.0,
                    "take_profit": 15.0,
                    "timeframe": "1d"
                }
            },
            "RSI Reversal": {
                "name": "RSI Reversal Strategy",
                "description": """
                A mean reversion strategy using RSI to identify overbought/oversold conditions.
                - Entry: When RSI falls below 30
                - Exit: When RSI rises above 70
                - Recommended for: Range-bound markets
                """,
                "config": {
                    "strategy_type": "mean_reversion",
                    "entry_conditions": ["RSI below 30"],
                    "exit_conditions": ["RSI above 70"],
                    "position_size": 10.0,
                    "stop_loss": 3.0,
                    "take_profit": 9.0,
                    "timeframe": "4h"
                }
            }
        }

    def _parse_strategy_text(self, text: str) -> Dict:
        """Simple rule-based strategy text parser."""
        strategy = {
            "entry_conditions": [],
            "exit_conditions": [],
            "position_size": 10.0,
            "stop_loss": None,
            "take_profit": None,
            "timeframe": "1h"
        }
        
        lines = text.lower().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if 'entry' in line and ':' in line:
                current_section = 'entry'
                continue
            elif 'exit' in line and ':' in line:
                current_section = 'exit'
                continue
            elif 'position' in line and 'size' in line:
                matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)
                if matches:
                    strategy['position_size'] = float(matches[0])
                continue
            elif 'stop' in line and 'loss' in line:
                matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)
                if matches:
                    strategy['stop_loss'] = float(matches[0])
                continue
            elif 'take' in line and 'profit' in line:
                matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)
                if matches:
                    strategy['take_profit'] = float(matches[0])
                continue
            elif 'timeframe' in line:
                timeframes = {
                    'minute': '1m',
                    'hour': '1h',
                    'day': '1d',
                    'week': '1w'
                }
                for key, value in timeframes.items():
                    if key in line:
                        strategy['timeframe'] = value
                        break
                continue
                
            if current_section == 'entry' and line:
                strategy['entry_conditions'].append(line)
            elif current_section == 'exit' and line:
                strategy['exit_conditions'].append(line)
                
        return strategy

    def render(self) -> Optional[Tuple[Dict, Dict]]:
        """Render strategy builder interface."""
        try:
            st.markdown("### 🛠️ Strategy Builder")
            
            # Method selector
            input_method = st.radio(
                "Strategy Input Method",
                ["Template", "Manual Builder"],
                horizontal=True,
                help="Choose how you want to create your strategy"
            )
            
            # Update session state
            st.session_state.strategy_state['input_method'] = input_method

            strategy_config = None
            if input_method == "Template":
                strategy_config = self._render_template_selection()
            else:
                strategy_config = self._render_manual_builder()

            if strategy_config:
                backtest_config = self._render_backtest_config()
                if backtest_config:
                    return strategy_config, backtest_config

            return None

        except Exception as e:
            show_error(
                "Strategy Builder Error",
                str(e),
                "Please try refreshing the page or contact support."
            )
            return None

    def _render_template_selection(self) -> Optional[Dict]:
        """Render template selection."""
        with st.container():
            selected = st.selectbox(
                "Select Strategy Template",
                list(self.templates.keys()),
                help="Choose a pre-built strategy template"
            )

            if selected:
                template = self.templates[selected]
                st.markdown(f"""
                ### {template['name']}
                {template['description']}
                """)

                if st.button("Use This Template", type="primary"):
                    strategy = template['config']
                    self._display_strategy_summary(strategy)
                    return strategy
            return None

    def _render_manual_builder(self) -> Optional[Dict]:
        """Render manual strategy builder."""
        with st.container():
            # Basic Settings
            st.subheader("Basic Settings")
            col1, col2 = st.columns(2)
            
            with col1:
                position_size = st.number_input(
                    "Position Size (%)",
                    min_value=1,
                    max_value=100,
                    value=st.session_state.strategy_state['manual_config']['position_size'],
                    help="Percentage of capital to use per trade"
                )
                stop_loss = st.number_input(
                    "Stop Loss (%)",
                    min_value=1,
                    max_value=50,
                    value=st.session_state.strategy_state['manual_config']['stop_loss'],
                    help="Price distance for stop loss"
                )
            
            with col2:
                take_profit = st.number_input(
                    "Take Profit (%)",
                    min_value=1,
                    max_value=100,
                    value=st.session_state.strategy_state['manual_config']['take_profit'],
                    help="Price distance for take profit"
                )
                timeframe = st.selectbox(
                    "Timeframe",
                    ["1m", "5m", "15m", "1h", "4h", "1d"],
                    index=["1m", "5m", "15m", "1h", "4h", "1d"].index(
                        st.session_state.strategy_state['manual_config']['timeframe']
                    ),
                    help="Chart timeframe for analysis"
                )

            # Strategy Type
            strategy_type = st.selectbox(
                "Strategy Type",
                ["trend_following", "mean_reversion", "breakout"],
                help="Choose your strategy type"
            )

            # Entry Conditions
            entry_conditions = []
            st.markdown("#### Entry Conditions")
            entry_condition = st.text_area(
                "Enter your entry conditions",
                height=100,
                help="Describe when to enter a trade"
            )
            if entry_condition:
                entry_conditions.append(entry_condition)

            # Exit Conditions
            exit_conditions = []
            st.markdown("#### Exit Conditions")
            exit_condition = st.text_area(
                "Enter your exit conditions",
                height=100,
                help="Describe when to exit a trade"
            )
            if exit_condition:
                exit_conditions.append(exit_condition)

            if st.button("Create Strategy", type="primary"):
                if not entry_conditions:
                    show_error(
                        "Invalid Strategy",
                        "Entry conditions are required"
                    )
                    return None
                    
                if not exit_conditions:
                    show_error(
                        "Invalid Strategy",
                        "Exit conditions are required"
                    )
                    return None
                
                strategy = {
                    "strategy_type": strategy_type,
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

    def _render_backtest_config(self) -> Dict:
        """Render backtesting configuration section."""
        st.markdown("### 📊 Backtest Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            asset = st.selectbox(
                "Asset",
                ["BTC/USDT", "ETH/USDT", "BNB/USDT"],
                help="Select the trading pair"
            )
        
        with col2:
            initial_capital = st.number_input(
                "Initial Capital (USD)",
                min_value=100,
                value=10000,
                step=100,
                help="Starting capital for backtesting"
            )
        
        return {
            "asset": asset,
            "initial_capital": initial_capital
        }

    def _display_strategy_summary(self, strategy: Dict):
        """Display strategy configuration summary."""
        st.markdown("### Strategy Summary")
        
        if strategy.get("entry_conditions"):
            st.markdown("#### Entry Conditions")
            for condition in strategy["entry_conditions"]:
                st.markdown(f"- {condition}")
                
        if strategy.get("exit_conditions"):
            st.markdown("#### Exit Conditions")
            for condition in strategy["exit_conditions"]:
                st.markdown(f"- {condition}")
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Position Size", f"{strategy.get('position_size', 0)}%")
        with col2:
            st.metric("Stop Loss", f"{strategy.get('stop_loss', 0)}%")
        with col3:
            st.metric("Take Profit", f"{strategy.get('take_profit', 0)}%")
