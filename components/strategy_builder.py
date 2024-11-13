import streamlit as st
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
from utils.ui_components import show_error, show_warning, group_elements

class StrategyBuilder:
    def __init__(self):
        # Initialize default state
        if 'strategy_state' not in st.session_state:
            st.session_state.strategy_state = {
                'input_method': 'Natural Language',
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

    def render(self) -> Optional[Tuple[Dict, Dict]]:
        """Render strategy builder interface."""
        try:
            st.markdown("### 🛠️ Strategy Builder")
            
            # Method selector
            input_method = st.radio(
                "Strategy Input Method",
                ["Natural Language", "Template", "Manual Builder"],
                horizontal=True,
                help="Choose how you want to create your strategy"
            )
            
            # Add spacing
            st.markdown("<div style='margin: 1em 0;'></div>", unsafe_allow_html=True)
            
            # Update session state
            st.session_state.strategy_state['input_method'] = input_method

            strategy_config = None
            if input_method == "Natural Language":
                strategy_config = self._render_natural_language_input()
            elif input_method == "Template":
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

    def _render_natural_language_input(self) -> Optional[Dict]:
        """Render natural language input section."""
        with st.container():
            st.markdown("""
            ### Strategy Description Guidelines
            Describe your trading strategy in plain English. Include:

            **Required Information:**
            - Entry Conditions (e.g., "Buy when 50-day SMA crosses above 200-day SMA")
            - Exit Conditions (e.g., "Sell when RSI goes above 70")
            - Position Size (e.g., "Use 30% position size")
            - Risk Management (e.g., "Set stop loss at 5% and take profit at 15%")

            **Optional Information:**
            - Timeframe (e.g., "Use 4-hour timeframe")
            - Additional Indicators (e.g., "Monitor volume for confirmation")
            - Market Phase Filters (e.g., "Only trade during uptrend")
            """)

            description = st.text_area(
                "Strategy Description",
                value=st.session_state.strategy_state.get('description', ''),
                height=200,
                help="Describe your trading strategy in detail"
            )

            # Update session state
            st.session_state.strategy_state['description'] = description

            if description:
                if st.button("Parse Strategy", type="primary"):
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
                            "Please check your strategy description format."
                        )
            return None

    def _parse_strategy_text(self, text: str) -> Dict:
        """Parse strategy description from natural language text."""
        strategy = {
            "strategy_type": "custom",
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
        entry_section = re.search(r'entry conditions?:(.+?)(?=exit conditions?:|$)', 
                                text, re.DOTALL | re.IGNORECASE)
        if entry_section:
            conditions = entry_section.group(1).strip().split('\n')
            strategy["entry_conditions"] = [cond.strip() for cond in conditions if cond.strip()]
            
        # Extract exit conditions
        exit_section = re.search(r'exit conditions?:(.+?)(?=position size:|$)', 
                                text, re.DOTALL | re.IGNORECASE)
        if exit_section:
            conditions = exit_section.group(1).strip().split('\n')
            strategy["exit_conditions"] = [cond.strip() for cond in conditions if cond.strip()]
        
        # Validate required fields
        if not strategy["entry_conditions"]:
            raise ValueError("Entry conditions are required")
        if not strategy["exit_conditions"]:
            raise ValueError("Exit conditions are required")
        if not strategy["position_size"]:
            raise ValueError("Position size is required")
        
        return strategy

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

            # Update session state
            st.session_state.strategy_state['manual_config'].update({
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe
            })

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
