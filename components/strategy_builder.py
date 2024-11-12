import streamlit as st
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time

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

    def render(self) -> Optional[Tuple[Dict, Dict]]:
        """Render strategy builder interface and return both strategy and backtesting configs."""
        timestamp = datetime.now().timestamp()
        
        st.markdown("### Strategy Builder")
        
        input_method = st.radio(
            "Strategy Input Method",
            ["Natural Language", "Template", "Manual Builder"],
            key=f"strategy_input_method_{timestamp}"
        )
        
        strategy_config = None
        if input_method == "Natural Language":
            strategy_config = self._render_natural_language_input(timestamp)
        elif input_method == "Template":
            strategy_config = self._render_template_selection(timestamp)
        else:
            strategy_config = self._render_manual_builder(timestamp)
        
        if strategy_config:
            backtest_config = self._render_backtest_config(timestamp)
            if backtest_config:
                return strategy_config, backtest_config
        
        return None

    def _render_natural_language_input(self, timestamp: float) -> Optional[Dict]:
        st.markdown("""
        ### Strategy Description
        Describe your trading strategy in plain English. Include:
        - Entry conditions
        - Exit conditions
        - Position size
        - Risk management (stop loss, take profit)
        """)
        
        description = st.text_area(
            "Strategy Description",
            height=300,
            key=f"strategy_description_{timestamp}"
        )
        
        if description and st.button("Parse Strategy", key=f"parse_btn_{timestamp}"):
            try:
                strategy = self._parse_strategy_text(description)
                if strategy:
                    st.success("Strategy parsed successfully!")
                    self._display_strategy_summary(strategy)
                    return strategy
            except Exception as e:
                st.error(f"Error parsing strategy: {str(e)}")
        return None

    def _render_template_selection(self, timestamp: float) -> Optional[Dict]:
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
        
        selected = st.selectbox(
            "Select Template",
            list(templates.keys()),
            key=f"template_select_{timestamp}"
        )
        
        if selected and st.button("Use Template", key=f"template_btn_{timestamp}"):
            strategy = templates[selected]
            self._display_strategy_summary(strategy)
            return strategy
        return None

    def _render_manual_builder(self, timestamp: float) -> Optional[Dict]:
        st.subheader("Manual Strategy Builder")
        
        col1, col2 = st.columns(2)
        
        with col1:
            position_size = st.number_input(
                "Position Size (%)",
                1, 100, 10,
                key=f"position_size_{timestamp}"
            )
            stop_loss = st.number_input(
                "Stop Loss (%)",
                1, 50, 5,
                key=f"stop_loss_{timestamp}"
            )
        
        with col2:
            take_profit = st.number_input(
                "Take Profit (%)",
                1, 100, 15,
                key=f"take_profit_{timestamp}"
            )
            timeframe = st.selectbox(
                "Timeframe",
                ["1m", "5m", "15m", "1h", "4h", "1d"],
                key=f"timeframe_{timestamp}"
            )
        
        entry_conditions = []
        exit_conditions = []
        
        st.subheader("Entry Conditions")
        indicator = st.selectbox(
            "Indicator",
            list(self.indicators.keys()),
            key=f"entry_indicator_{timestamp}"
        )
        if indicator:
            entry_conditions.append(f"Using {indicator}")
        
        st.subheader("Exit Conditions")
        indicator = st.selectbox(
            "Indicator",
            list(self.indicators.keys()),
            key=f"exit_indicator_{timestamp}"
        )
        if indicator:
            exit_conditions.append(f"Using {indicator}")
        
        if st.button("Create Strategy", key=f"create_strategy_btn_{timestamp}"):
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
        st.markdown("### Backtesting Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            asset = st.selectbox(
                "Asset",
                ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"],
                key=f"backtest_asset_{timestamp}"
            )
            
            initial_capital = st.number_input(
                "Initial Capital (USDT)",
                min_value=100,
                value=10000,
                step=100,
                key=f"initial_capital_{timestamp}"
            )
        
        with col2:
            start_date = st.date_input(
                "Start Date",
                key=f"start_date_{timestamp}"
            )
            
            end_date = st.date_input(
                "End Date",
                key=f"end_date_{timestamp}"
            )
        
        if asset and initial_capital and start_date and end_date:
            if start_date >= end_date:
                st.error("Start date must be before end date")
                return None
                
            return {
                "asset": asset,
                "initial_capital": initial_capital,
                "start_date": start_date,
                "end_date": end_date
            }
        return None

    def _parse_strategy_text(self, text: str) -> Dict:
        strategy = {
            "entry_conditions": [],
            "exit_conditions": [],
            "position_size": 10.0,
            "stop_loss": None,
            "take_profit": None,
            "timeframe": "1d"
        }
        
        # Extract position size
        position_match = re.search(r'position size[:\s]+(\d+)', text, re.IGNORECASE)
        if position_match:
            strategy["position_size"] = float(position_match.group(1))
        
        # Extract stop loss
        stop_loss_match = re.search(r'stop loss[:\s]+(\d+)', text, re.IGNORECASE)
        if stop_loss_match:
            strategy["stop_loss"] = float(stop_loss_match.group(1))
        
        # Extract take profit
        take_profit_match = re.search(r'take profit[:\s]+(\d+)', text, re.IGNORECASE)
        if take_profit_match:
            strategy["take_profit"] = float(take_profit_match.group(1))
        
        # Extract timeframe
        timeframe_match = re.search(r'timeframe[:\s]+(\w+)', text, re.IGNORECASE)
        if timeframe_match:
            strategy["timeframe"] = timeframe_match.group(1)
        
        # Extract entry conditions
        entry_section = re.search(r'entry conditions?:(.+?)(?=exit conditions?:|$)', text, re.IGNORECASE | re.DOTALL)
        if entry_section:
            conditions = entry_section.group(1).strip().split('\n')
            strategy["entry_conditions"] = [c.strip() for c in conditions if c.strip()]
        
        # Extract exit conditions
        exit_section = re.search(r'exit conditions?:(.+?)(?=position size:|$)', text, re.IGNORECASE | re.DOTALL)
        if exit_section:
            conditions = exit_section.group(1).strip().split('\n')
            strategy["exit_conditions"] = [c.strip() for c in conditions if c.strip()]
        
        return strategy

    def _display_strategy_summary(self, strategy: Dict):
        st.markdown("### Strategy Summary")
        st.write("Entry Conditions:", strategy["entry_conditions"])
        st.write("Exit Conditions:", strategy["exit_conditions"])
        st.write(f"Position Size: {strategy['position_size']}%")
        st.write(f"Stop Loss: {strategy['stop_loss']}%")
        st.write(f"Take Profit: {strategy['take_profit']}%")
        st.write(f"Timeframe: {strategy['timeframe']}")
