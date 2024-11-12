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
        
        # Initialize templates with improved descriptions
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
                    "entry_conditions": ["RSI below 30"],
                    "exit_conditions": ["RSI above 70"],
                    "position_size": 10.0,
                    "stop_loss": 3.0,
                    "take_profit": 9.0,
                    "timeframe": "4h"
                }
            }
        }
        
        # Technical indicators with descriptions
        self.indicators = {
            'Moving Average': {
                'indicators': ['SMA', 'EMA', 'WMA'],
                'description': 'Trend-following indicators that smooth price action'
            },
            'Momentum': {
                'indicators': ['RSI', 'MACD', 'Stochastic'],
                'description': 'Indicators that measure the strength of price movement'
            },
            'Volume': {
                'indicators': ['OBV', 'Volume Profile', 'VWAP'],
                'description': 'Indicators that analyze trading volume patterns'
            },
            'Volatility': {
                'indicators': ['Bollinger Bands', 'ATR', 'Keltner Channels'],
                'description': 'Indicators that measure market volatility'
            }
        }

    def render(self) -> Optional[Tuple[Dict, Dict]]:
        """Render strategy builder interface with improved visibility and feedback."""
        try:
            with st.spinner("Initializing Strategy Builder..."):
                # Main container with improved styling
                st.markdown("""
                <style>
                .strategy-container {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0;
                }
                .method-selector {
                    background-color: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                </style>
                """, unsafe_allow_html=True)

                # Method selector with improved visibility
                st.markdown('<div class="method-selector">', unsafe_allow_html=True)
                input_method = st.radio(
                    "Strategy Input Method",
                    ["Natural Language", "Template", "Manual Builder"],
                    help="Choose how you want to create your strategy",
                    index=["Natural Language", "Template", "Manual Builder"].index(
                        st.session_state.strategy_state['input_method']
                    )
                )
                st.markdown('</div>', unsafe_allow_html=True)

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
                    st.success("✅ Strategy configured successfully!")
                    backtest_config = self._render_backtest_config()
                    if backtest_config:
                        return strategy_config, backtest_config

                return None

        except Exception as e:
            show_error(
                "Strategy Builder Error",
                str(e),
                "Please try refreshing the page or contact support if the issue persists."
            )
            return None

    def _render_natural_language_input(self) -> Optional[Dict]:
        """Render natural language input section with improved guidance."""
        with st.container():
            st.markdown("""
            <div style='background-color: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
                <h4 style='margin-top: 0;'>Strategy Description Guidelines</h4>
                <p>Include the following in your description:</p>
                <ul>
                    <li>Entry Conditions (e.g., "Buy when RSI below 30")</li>
                    <li>Exit Conditions (e.g., "Sell when price hits take profit")</li>
                    <li>Position Size (e.g., "Use 10% of capital")</li>
                    <li>Risk Management (e.g., "5% stop loss, 15% take profit")</li>
                    <li>Optional: Timeframe and additional indicators</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            description = st.text_area(
                "Strategy Description",
                value=st.session_state.strategy_state.get('description', ''),
                height=300,
                help="Write your strategy in natural language"
            )

            # Update session state
            st.session_state.strategy_state['description'] = description

            if description:
                if st.button("Parse Strategy", use_container_width=True):
                    with st.spinner("Parsing strategy..."):
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

    def _render_template_selection(self) -> Optional[Dict]:
        """Render template selection with improved visualization."""
        with st.container():
            # Template showcase with cards
            st.markdown("""
            <style>
            .template-card {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;
            }
            .template-title {
                color: #FF4B4B;
                margin-bottom: 10px;
            }
            .template-description {
                font-size: 0.9em;
                margin-bottom: 15px;
            }
            </style>
            """, unsafe_allow_html=True)

            selected = st.selectbox(
                "Select Strategy Template",
                list(self.templates.keys()),
                help="Choose a pre-built strategy template"
            )

            if selected:
                template = self.templates[selected]
                st.markdown(f"""
                <div class="template-card">
                    <div class="template-title">{template['name']}</div>
                    <div class="template-description">{template['description']}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Use This Template", use_container_width=True):
                    with st.spinner("Loading template..."):
                        strategy = template['config']
                        self._display_strategy_summary(strategy)
                        return strategy
            return None

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

    def _render_manual_builder(self) -> Optional[Dict]:
        """Render manual strategy builder with improved organization and feedback."""
        with st.container():
            # Basic Settings
            with group_elements("Basic Settings"):
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
                        help="Stop loss percentage below entry price"
                    )
                
                with col2:
                    take_profit = st.number_input(
                        "Take Profit (%)",
                        min_value=1,
                        max_value=100,
                        value=st.session_state.strategy_state['manual_config']['take_profit'],
                        help="Take profit percentage above entry price"
                    )
                    timeframe = st.selectbox(
                        "Timeframe",
                        ["1m", "5m", "15m", "1h", "4h", "1d"],
                        index=["1m", "5m", "15m", "1h", "4h", "1d"].index(
                            st.session_state.strategy_state['manual_config']['timeframe']
                        ),
                        help="Chart timeframe for the strategy"
                    )

                # Update session state
                st.session_state.strategy_state['manual_config'].update({
                    'position_size': position_size,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'timeframe': timeframe
                })

            # Trading Rules
            with group_elements("Trading Rules"):
                # Entry Conditions
                st.subheader("Entry Conditions")
                entry_conditions = []
                
                indicator_type = st.selectbox(
                    "Indicator Type",
                    list(self.indicators.keys()),
                    key="entry_indicator_type"
                )
                
                if indicator_type:
                    st.markdown(f"*{self.indicators[indicator_type]['description']}*")
                    selected_indicator = st.selectbox(
                        "Select Indicator",
                        self.indicators[indicator_type]['indicators'],
                        key="entry_indicator"
                    )
                    if selected_indicator:
                        entry_conditions.append(f"Using {selected_indicator}")
                
                # Exit Conditions
                st.subheader("Exit Conditions")
                exit_conditions = []
                
                indicator_type = st.selectbox(
                    "Indicator Type",
                    list(self.indicators.keys()),
                    key="exit_indicator_type"
                )
                
                if indicator_type:
                    st.markdown(f"*{self.indicators[indicator_type]['description']}*")
                    selected_indicator = st.selectbox(
                        "Select Indicator",
                        self.indicators[indicator_type]['indicators'],
                        key="exit_indicator"
                    )
                    if selected_indicator:
                        exit_conditions.append(f"Using {selected_indicator}")

            if st.button("Create Strategy", use_container_width=True):
                with st.spinner("Creating strategy..."):
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

    def _render_backtest_config(self) -> Optional[Dict]:
        """Render backtesting configuration with improved layout."""
        with group_elements("Backtest Configuration"):
            col1, col2 = st.columns(2)
            
            with col1:
                asset = st.selectbox(
                    "Asset",
                    ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"],
                    help="Select the asset to backtest"
                )
                
                initial_capital = st.number_input(
                    "Initial Capital (USDT)",
                    min_value=100,
                    value=10000,
                    step=100,
                    help="Starting capital for backtesting"
                )
            
            with col2:
                start_date = st.date_input(
                    "Start Date",
                    help="Backtest start date"
                )
                
                end_date = st.date_input(
                    "End Date",
                    help="Backtest end date"
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
            st.markdown("""
            <style>
            .strategy-param {
                background-color: rgba(255, 255, 255, 0.05);
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="strategy-param">', unsafe_allow_html=True)
            st.markdown("#### Entry Conditions")
            for condition in strategy["entry_conditions"]:
                st.markdown(f"• {condition}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="strategy-param">', unsafe_allow_html=True)
            st.markdown("#### Exit Conditions")
            for condition in strategy["exit_conditions"]:
                st.markdown(f"• {condition}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Position Size", f"{strategy['position_size']}%")
            with col2:
                st.metric("Stop Loss", f"{strategy['stop_loss']}%")
            with col3:
                st.metric("Take Profit", f"{strategy['take_profit']}%")
            
            st.metric("Timeframe", strategy['timeframe'])