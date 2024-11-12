import streamlit as st
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Strategy:
    entry_conditions: List[Dict]
    exit_conditions: List[Dict]
    position_size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    timeframe: str
    max_trades: int

class StrategyBuilder:
    def __init__(self):
        self.strategy_templates = {
            'Moving Average Crossover': '''
                Buy when 50-day SMA crosses above 200-day SMA with 30% position size.
                Set stop loss at 5% and take profit at 15%.
                Exit when price crosses below 200-day SMA.
                Trade on 4-hour timeframe and only during uptrend.
            ''',
            'RSI Reversal': '''
                Buy when RSI falls below 30 with 20% position size.
                Set stop loss at 3% and take profit at 9%.
                Exit when RSI rises above 70.
                Trade on 1-hour timeframe during ranging markets.
            ''',
            'Breakout Strategy': '''
                Buy when price breaks above 20-day high with 25% position size.
                Set stop loss at 4% and take profit at 12%.
                Exit when price falls below 10-day low.
                Trade on 1-day timeframe during trending markets.
            '''
        }

    def render(self) -> Optional[Dict]:
        st.markdown("### Strategy Builder")
        
        # Strategy input method selection
        input_method = st.radio(
            "Strategy Input Method",
            ["Natural Language", "Template", "Manual Builder"],
            help="Choose how you want to create your strategy"
        )
        
        if input_method == "Natural Language":
            return self._render_natural_language_input()
        elif input_method == "Template":
            return self._render_template_selection()
        else:
            return self._render_manual_builder()
    
    def _parse_strategy_description(self, description: str) -> Dict:
        """Extract strategy parameters using regex patterns."""
        # Extract basic parameters
        position_size = re.search(r'(\d+)%\s*position\s*size', description)
        stop_loss = re.search(r'stop\s*loss\s*(?:at|of)?\s*(\d+)%', description)
        take_profit = re.search(r'take\s*profit\s*(?:at|of)?\s*(\d+)%', description)
        timeframe = re.search(r'(\d+)[-\s]?(hour|day|week|h|d|w)\s*timeframe', description)
        
        # Extract entry and exit conditions
        entry_conditions = self._extract_entry_conditions(description)
        exit_conditions = self._extract_exit_conditions(description)
        
        # Build strategy configuration
        return {
            'entry_conditions': entry_conditions,
            'exit_conditions': exit_conditions,
            'position_size': float(position_size.group(1)) if position_size else 10.0,
            'stop_loss': float(stop_loss.group(1)) if stop_loss else None,
            'take_profit': float(take_profit.group(1)) if take_profit else None,
            'timeframe': self._parse_timeframe(timeframe.group() if timeframe else '1-day'),
            'max_trades': 1
        }
    
    def _extract_entry_conditions(self, description: str) -> List[Dict]:
        """Extract entry conditions from strategy description."""
        conditions = []
        
        # Moving Average patterns
        ma_pattern = r'(?:buy|enter)\s+when\s+(\d+)[-\s]?day\s+(sma|ema)\s+crosses?\s+(above|below)\s+(\d+)[-\s]?day'
        ma_matches = re.finditer(ma_pattern, description.lower())
        
        for match in ma_matches:
            conditions.append({
                'type': 'moving_average_cross',
                'period1': int(match.group(1)),
                'ma_type1': match.group(2).upper(),
                'direction': match.group(3),
                'period2': int(match.group(4)),
                'ma_type2': match.group(2).upper()
            })
        
        # RSI patterns
        rsi_pattern = r'(?:buy|enter)\s+when\s+rsi\s+(?:is\s+)?(below|above|falls below|rises above)\s+(\d+)'
        rsi_matches = re.finditer(rsi_pattern, description.lower())
        
        for match in rsi_matches:
            conditions.append({
                'type': 'rsi',
                'direction': match.group(1),
                'value': int(match.group(2))
            })
        
        # Price breakout patterns
        breakout_pattern = r'(?:buy|enter)\s+when\s+price\s+breaks?\s+(above|below)\s+(\d+)[-\s]?day\s+(high|low)'
        breakout_matches = re.finditer(breakout_pattern, description.lower())
        
        for match in breakout_matches:
            conditions.append({
                'type': 'breakout',
                'direction': match.group(1),
                'period': int(match.group(2)),
                'level': match.group(3)
            })
        
        return conditions
    
    def _extract_exit_conditions(self, description: str) -> List[Dict]:
        """Extract exit conditions from strategy description."""
        conditions = []
        
        # Moving Average exit patterns
        ma_pattern = r'exit\s+when\s+(\d+)[-\s]?day\s+(sma|ema)\s+crosses?\s+(above|below)\s+(\d+)[-\s]?day'
        ma_matches = re.finditer(ma_pattern, description.lower())
        
        for match in ma_matches:
            conditions.append({
                'type': 'moving_average_cross',
                'period1': int(match.group(1)),
                'ma_type1': match.group(2).upper(),
                'direction': match.group(3),
                'period2': int(match.group(4)),
                'ma_type2': match.group(2).upper()
            })
        
        # RSI exit patterns
        rsi_pattern = r'exit\s+when\s+rsi\s+(?:is\s+)?(below|above|falls below|rises above)\s+(\d+)'
        rsi_matches = re.finditer(rsi_pattern, description.lower())
        
        for match in rsi_matches:
            conditions.append({
                'type': 'rsi',
                'direction': match.group(1),
                'value': int(match.group(2))
            })
        
        return conditions
    
    def _parse_timeframe(self, timeframe_str: str) -> str:
        """Convert timeframe string to standard format."""
        if not timeframe_str:
            return '1d'
            
        parts = timeframe_str.lower().split('-')
        value = parts[0].strip()
        unit = parts[1].strip() if len(parts) > 1 else 'day'
        
        if unit.startswith('hour') or unit.startswith('h'):
            return f"{value}h"
        elif unit.startswith('day') or unit.startswith('d'):
            return f"{value}d"
        elif unit.startswith('week') or unit.startswith('w'):
            return f"{value}w"
        
        return '1d'
    
    def _render_natural_language_input(self) -> Optional[Dict]:
        """Render natural language input interface."""
        st.markdown('''
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
        ''')
        
        description = st.text_area(
            "Strategy Description",
            height=150,
            help="Describe your trading strategy using natural language",
            placeholder="Example: Buy when 50-day SMA crosses above 200-day SMA with 30% position size..."
        )
        
        if st.button("Parse Strategy"):
            if description:
                try:
                    strategy = self._parse_strategy_description(description)
                    self._display_parsed_strategy(strategy)
                    return strategy
                except Exception as e:
                    st.error(f"Error parsing strategy: {str(e)}")
                    st.info("Please check your strategy description and try again.")
        return None
    
    def _render_template_selection(self) -> Optional[Dict]:
        """Render template selection interface."""
        st.markdown("""
        ### Strategy Templates
        Choose a pre-built strategy template as a starting point.
        You can modify the parameters after selection.
        """)
        
        template = st.selectbox(
            "Select Template",
            list(self.strategy_templates.keys()),
            help="Choose a pre-built strategy template"
        )
        
        if template:
            st.markdown("### Template Description")
            st.text(self.strategy_templates[template])
            
            if st.button("Use Template"):
                try:
                    strategy = self._parse_strategy_description(self.strategy_templates[template])
                    self._display_parsed_strategy(strategy)
                    return strategy
                except Exception as e:
                    st.error(f"Error parsing template: {str(e)}")
        return None
    
    def _render_manual_builder(self) -> Optional[Dict]:
        """Render manual strategy builder interface."""
        st.markdown("### Manual Strategy Builder")
        
        # Basic Settings
        col1, col2 = st.columns(2)
        with col1:
            position_size = st.slider(
                "Position Size (%)",
                min_value=1,
                max_value=100,
                value=10,
                help="Percentage of capital to use per trade"
            )
            
            timeframe = st.selectbox(
                "Timeframe",
                ["1h", "4h", "1d", "1w"],
                help="Trading timeframe"
            )
        
        with col2:
            stop_loss = st.number_input(
                "Stop Loss (%)",
                min_value=0.1,
                max_value=50.0,
                value=5.0,
                help="Stop loss percentage"
            )
            
            take_profit = st.number_input(
                "Take Profit (%)",
                min_value=0.1,
                max_value=100.0,
                value=15.0,
                help="Take profit percentage"
            )
        
        # Entry Conditions
        st.markdown("### Entry Conditions")
        entry_conditions = self._build_conditions("entry")
        
        # Exit Conditions
        st.markdown("### Exit Conditions")
        exit_conditions = self._build_conditions("exit")
        
        if st.button("Generate Strategy"):
            if not entry_conditions:
                st.error("At least one entry condition is required.")
                return None
                
            if not exit_conditions:
                st.error("At least one exit condition is required.")
                return None
                
            strategy = {
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'position_size': float(position_size),
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'timeframe': timeframe,
                'max_trades': 1
            }
            
            self._display_parsed_strategy(strategy)
            return strategy
            
        return None
    
    def _build_conditions(self, condition_type: str) -> List[Dict]:
        """Build trading conditions interface."""
        conditions = []
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            indicator = st.selectbox(
                f"Select {condition_type.title()} Indicator",
                ["Moving Average", "RSI", "Price"],
                key=f"{condition_type}_indicator"
            )
        
        with col2:
            if indicator == "Moving Average":
                ma_type = st.selectbox(
                    "MA Type",
                    ["SMA", "EMA"],
                    key=f"{condition_type}_ma_type"
                )
                period = st.number_input(
                    "Period",
                    min_value=1,
                    max_value=200,
                    value=20,
                    key=f"{condition_type}_period"
                )
                conditions.append({
                    'type': 'moving_average',
                    'ma_type': ma_type,
                    'period': period
                })
            
            elif indicator == "RSI":
                rsi_value = st.number_input(
                    "RSI Value",
                    min_value=0,
                    max_value=100,
                    value=30 if condition_type == "entry" else 70,
                    key=f"{condition_type}_rsi"
                )
                conditions.append({
                    'type': 'rsi',
                    'value': rsi_value
                })
            
            elif indicator == "Price":
                price_condition = st.selectbox(
                    "Price Condition",
                    ["Above", "Below", "Crosses Above", "Crosses Below"],
                    key=f"{condition_type}_price"
                )
                conditions.append({
                    'type': 'price',
                    'condition': price_condition
                })
        
        return conditions
    
    def _display_parsed_strategy(self, strategy: Dict):
        """Display parsed strategy parameters."""
        st.markdown("### Parsed Strategy Parameters")
        
        # Display basic parameters
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Position Size", f"{strategy['position_size']}%")
            st.metric("Stop Loss", f"{strategy['stop_loss']}%" if strategy['stop_loss'] else "Not Set")
        
        with col2:
            st.metric("Timeframe", strategy['timeframe'])
            st.metric("Take Profit", f"{strategy['take_profit']}%" if strategy['take_profit'] else "Not Set")
        
        # Display conditions
        st.markdown("#### Entry Conditions")
        for condition in strategy['entry_conditions']:
            st.code(str(condition))
        
        st.markdown("#### Exit Conditions")
        for condition in strategy['exit_conditions']:
            st.code(str(condition))
