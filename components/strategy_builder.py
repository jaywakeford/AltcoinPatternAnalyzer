import streamlit as st
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, time

@dataclass
class Strategy:
    entry_conditions: List[Dict]
    exit_conditions: List[Dict]
    position_size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    timeframe: str
    max_trades: int
    trailing_stop: Optional[float] = None
    market_conditions: Optional[Dict] = None
    trading_hours: Optional[Dict] = None
    volatility_filters: Optional[Dict] = None

class StrategyBuilder:
    def __init__(self):
        # Initialize candlestick patterns
        self.candlestick_patterns = [
            'doji', 'hammer', 'inverted hammer', 'bullish engulfing',
            'bearish engulfing', 'morning star', 'evening star',
            'shooting star', 'hanging man', 'dark cloud cover',
            'piercing pattern', 'three white soldiers', 'three black crows'
        ]
        
        # Initialize template with new clearer format
        self.strategy_template = '''
[Strategy Name]: <Your Strategy Name>

Entry Conditions:
- Primary Signal: <describe main entry signal>
- Additional Confirmations: <describe confirmation signals>

Exit Conditions:
- Primary Exit: <describe main exit signal>
- Safety Exits: <describe additional exit conditions>

Position Management:
- Position Size: <specify percentage>
- Maximum Positions: <specify number>

Risk Management:
- Stop Loss: <specify percentage>
- Take Profit: <specify percentage>
- Trailing Stop: <optional, specify conditions>

Trading Schedule:
- Timeframe: <specify timeframe>
- Trading Hours: <optional, specify hours>
'''
        
        # Example strategies using new format
        self.strategy_templates = {
            'Moving Average Crossover': '''
[Strategy Name]: Moving Average Crossover Strategy

Entry Conditions:
- Primary Signal: Buy when 50-day SMA crosses above 200-day SMA
- Additional Confirmations:
  * RSI below 70
  * Volume above 20-day average
  * Price above 20-day EMA

Exit Conditions:
- Primary Exit: Sell when 50-day SMA crosses below 200-day SMA
- Safety Exits:
  * RSI above 70
  * Price breaks below 200-day SMA
  * Volume drops below average

Position Management:
- Position Size: 30% of capital per trade
- Maximum Positions: 1 position at a time

Risk Management:
- Stop Loss: 5% below entry price
- Take Profit: 15% above entry price
- Trailing Stop: 2% trailing stop after 5% profit

Trading Schedule:
- Timeframe: Daily timeframe
- Trading Hours: All hours
''',
            'RSI Reversal': '''
[Strategy Name]: RSI Reversal Strategy

Entry Conditions:
- Primary Signal: Buy when RSI falls below 30
- Additional Confirmations:
  * Price above 20-day SMA
  * Volume spike above 200% average
  * Bullish candlestick pattern (hammer or engulfing)

Exit Conditions:
- Primary Exit: Sell when RSI rises above 70
- Safety Exits:
  * Price breaks below 20-day SMA
  * Bearish candlestick pattern appears
  * Volume decline below average

Position Management:
- Position Size: 20% of capital per trade
- Maximum Positions: 2 positions at a time

Risk Management:
- Stop Loss: 3.5% below entry price
- Take Profit: Multiple targets:
  * Target 1: 5% (40% of position)
  * Target 2: 10% (60% of position)
- Trailing Stop: 1.5% trailing stop after 4% profit

Trading Schedule:
- Timeframe: 4-hour timeframe
- Trading Hours: 09:30-16:00 EST
'''
        }

    def render(self) -> Optional[Dict]:
        """Main render method for strategy builder interface."""
        st.markdown("### Strategy Builder")
        
        st.info("""
        Create your trading strategy using one of these methods:
        1. Natural Language: Describe your strategy in plain English
        2. Template: Use pre-built strategy templates
        3. Manual Builder: Build your strategy step by step
        """)
        
        # Strategy input method selection
        input_method = st.radio(
            "Strategy Input Method",
            ["Natural Language", "Template", "Manual Builder"]
        )
        
        if input_method == "Natural Language":
            return self._render_natural_language_input()
        elif input_method == "Template":
            return self._render_template_selection()
        else:
            return self._render_manual_builder()

    def _render_natural_language_input(self) -> Optional[Dict]:
        """Render natural language input interface with improved guidelines."""
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
        
        # Show template example
        with st.expander("View Format Template"):
            st.code(self.strategy_template, language="markdown")
        
        description = st.text_area(
            "Strategy Description",
            height=400,
            help="Describe your trading strategy following the guidelines above"
        )
        
        if description:
            try:
                # Validate required fields
                missing_fields = self._validate_required_fields(description)
                if missing_fields:
                    st.error(f"""
                    Missing required fields:
                    {', '.join(missing_fields)}
                    
                    Please include all required fields in your strategy description.
                    Check the template above for the correct format.
                    """)
                    return None
                    
                # Parse strategy if validation passes
                strategy = self._parse_strategy_description(description)
                
                # Display parsed strategy for verification
                self._display_parsed_strategy(strategy)
                
                return strategy
                
            except Exception as e:
                st.error(f"""
                Error parsing strategy: {str(e)}
                
                Please check your strategy description format and try again.
                Make sure to follow the template structure and include all required fields.
                """)
                return None
        return None

    def _render_template_selection(self) -> Optional[Dict]:
        """Render template selection interface."""
        st.markdown("### Strategy Templates")
        template_name = st.selectbox(
            "Select a template",
            list(self.strategy_templates.keys())
        )
        
        if template_name:
            template = self.strategy_templates[template_name]
            st.text_area("Template Strategy", value=template, height=400, disabled=True)
            if st.button("Use this template"):
                try:
                    return self._parse_strategy_description(template)
                except Exception as e:
                    st.error(f"Error using template: {str(e)}")
                    return None
        return None

    def _render_manual_builder(self) -> Optional[Dict]:
        """Render manual strategy builder interface."""
        st.markdown("### Manual Strategy Builder")
        
        entry_conditions = []
        exit_conditions = []
        
        # Entry Conditions
        st.subheader("Entry Conditions")
        entry_type = st.selectbox(
            "Entry Signal Type",
            ["Moving Average", "RSI", "Price Action", "Volume"],
            key="entry_type"
        )
        
        # Exit Conditions
        st.subheader("Exit Conditions")
        exit_type = st.selectbox(
            "Exit Signal Type",
            ["Moving Average", "RSI", "Price Action", "Stop Loss/Take Profit"],
            key="exit_type"
        )
        
        # Position and Risk Management
        st.subheader("Position & Risk Management")
        col1, col2 = st.columns(2)
        
        with col1:
            position_size = st.number_input(
                "Position Size (%)",
                min_value=1,
                max_value=100,
                value=10,
                help="Percentage of capital to risk per trade"
            )
            stop_loss = st.number_input(
                "Stop Loss (%)",
                min_value=0.1,
                max_value=50.0,
                value=5.0,
                help="Stop loss percentage below entry"
            )
        
        with col2:
            take_profit = st.number_input(
                "Take Profit (%)",
                min_value=0.1,
                max_value=100.0,
                value=15.0,
                help="Take profit percentage above entry"
            )
            max_trades = st.number_input(
                "Maximum Concurrent Trades",
                min_value=1,
                max_value=10,
                value=1,
                help="Maximum number of open positions"
            )
        
        # Timeframe
        timeframe = st.selectbox(
            "Timeframe",
            ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
            index=5,
            help="Trading timeframe"
        )
        
        if st.button("Create Strategy", help="Generate strategy with current settings"):
            strategy = {
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'max_trades': max_trades
            }
            
            # Display strategy summary
            self._display_parsed_strategy(strategy)
            return strategy
            
        return None

    def _validate_required_fields(self, description: str) -> List[str]:
        """Validate required fields with more flexible format recognition."""
        missing_fields = []
        
        # Strategy name check (flexible format)
        if not any(re.search(pattern, description, re.IGNORECASE) for pattern in [
            r'\[Strategy Name\]:\s*\S+',
            r'Strategy Name:\s*\S+',
            r'Name:\s*\S+'
        ]):
            missing_fields.append("Strategy Name")
        
        # Entry conditions check (flexible format)
        if not any(re.search(pattern, description, re.IGNORECASE) for pattern in [
            r'Entry Conditions:',
            r'When to Buy:',
            r'Entry Rules:',
            r'Buy Signals:'
        ]):
            missing_fields.append("Entry Conditions")
        
        # Exit conditions check (flexible format)
        if not any(re.search(pattern, description, re.IGNORECASE) for pattern in [
            r'Exit Conditions:',
            r'When to Sell:',
            r'Exit Rules:',
            r'Sell Signals:'
        ]):
            missing_fields.append("Exit Conditions")
        
        # Position management check
        if not any(re.search(pattern, description, re.IGNORECASE) for pattern in [
            r'Position Size:',
            r'Position Management:',
            r'Trade Size:'
        ]):
            missing_fields.append("Position Management")
        
        # Risk management check
        has_risk_management = (
            any(re.search(pattern, description, re.IGNORECASE) for pattern in [
                r'Risk Management:',
                r'Stop Loss:.*?(\d+\.?\d*)%',
                r'Take Profit:.*?(\d+\.?\d*)%'
            ])
        )
        if not has_risk_management:
            missing_fields.append("Risk Management")
        
        # Timeframe check
        if not any(re.search(pattern, description, re.IGNORECASE) for pattern in [
            r'Timeframe:',
            r'Time Frame:',
            r'Trading Interval:',
            r'Trading Period:'
        ]):
            missing_fields.append("Timeframe")
        
        return missing_fields

    def _parse_strategy_description(self, description: str) -> Dict:
        """Enhanced strategy parser with support for various formats."""
        try:
            # Extract strategy name (flexible format)
            strategy_name = None
            for pattern in [
                r'\[Strategy Name\]:\s*([^\n]+)',
                r'Strategy Name:\s*([^\n]+)',
                r'Name:\s*([^\n]+)'
            ]:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    strategy_name = match.group(1).strip()
                    break
            
            if not strategy_name:
                raise ValueError("""Strategy name is required. 
                Use one of these formats:
                - [Strategy Name]: Your Strategy
                - Strategy Name: Your Strategy
                - Name: Your Strategy""")

            # Extract position management (flexible format)
            position_size = None
            for pattern in [
                r'Position Size:.*?(\d+\.?\d*)%',
                r'Position Management:.*?(\d+\.?\d*)%.*?(?:of|per)',
                r'Trade Size:.*?(\d+\.?\d*)%'
            ]:
                match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
                if match:
                    position_size = float(match.group(1))
                    break

            if not position_size:
                position_size = 10.0  # Default position size

            # Extract risk parameters
            stop_loss = None
            take_profit = None
            
            sl_match = re.search(r'Stop Loss:.*?(\d+\.?\d*)%', description, re.IGNORECASE | re.DOTALL)
            if sl_match:
                stop_loss = float(sl_match.group(1))
            
            tp_match = re.search(r'Take Profit:.*?(\d+\.?\d*)%', description, re.IGNORECASE | re.DOTALL)
            if tp_match:
                take_profit = float(tp_match.group(1))

            # Extract trailing stop
            trailing_stop = self._parse_trailing_stop(description)

            # Extract timeframe (flexible format)
            timeframe = None
            for pattern in [
                r'Timeframe:.*?(\d+)[-\s]?(minute|hour|day|week|m|h|d|w)',
                r'Time Frame:.*?(\d+)[-\s]?(minute|hour|day|week|m|h|d|w)',
                r'Trading Period:.*?(\d+)[-\s]?(minute|hour|day|week|m|h|d|w)'
            ]:
                match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
                if match:
                    timeframe = self._parse_timeframe(match.group(0))
                    break

            if not timeframe:
                timeframe = "1d"  # Default timeframe

            # Extract trading hours
            trading_hours = self._parse_trading_hours(description)

            # Extract market conditions
            market_conditions = self._parse_market_conditions(description)

            # Extract entry and exit conditions
            entry_conditions = self._extract_entry_conditions(description)
            exit_conditions = self._extract_exit_conditions(description)

            if not entry_conditions:
                raise ValueError("""Entry conditions are required.
                Please specify at least one entry condition in your strategy.""")
                
            if not exit_conditions:
                raise ValueError("""Exit conditions are required.
                Please specify at least one exit condition in your strategy.""")

            # Build strategy configuration
            strategy = {
                'name': strategy_name,
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'max_trades': self._parse_max_trades(description),
                'trailing_stop': trailing_stop,
                'market_conditions': market_conditions,
                'trading_hours': trading_hours
            }

            # Validate strategy parameters
            self._validate_strategy_parameters(strategy)

            return strategy

        except Exception as e:
            raise ValueError(f"Error parsing strategy: {str(e)}\nPlease check the strategy template for the correct format.")

    def _parse_trailing_stop(self, description: str) -> Optional[Dict]:
        """Parse trailing stop with conditions."""
        trailing_stop_match = re.search(
            r'Trailing Stop:.*?(\d+\.?\d*)%(?:.*?after\s+(\d+\.?\d*)%)?',
            description,
            re.IGNORECASE | re.DOTALL
        )
        
        if trailing_stop_match:
            result = {
                'percentage': float(trailing_stop_match.group(1))
            }
            if trailing_stop_match.group(2):
                result['activation_percentage'] = float(trailing_stop_match.group(2))
            return result
        return None

    def _parse_trading_hours(self, description: str) -> Optional[Dict]:
        """Parse trading hours and schedule."""
        trading_hours_match = re.search(
            r'Trading Hours:\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*([A-Za-z]{2,4})',
            description,
            re.IGNORECASE
        )
        
        if trading_hours_match:
            return {
                'start': trading_hours_match.group(1),
                'end': trading_hours_match.group(2),
                'timezone': trading_hours_match.group(3),
                'weekend_trading': 'weekend' in description.lower()
            }
        return None

    def _parse_market_conditions(self, description: str) -> Dict:
        """Parse complex market conditions."""
        conditions = {}
        
        # Volatility requirements
        volatility_match = re.search(
            r'ATR.*?(\d+\.?\d*)%',
            description,
            re.IGNORECASE
        )
        if volatility_match:
            conditions['volatility'] = float(volatility_match.group(1))
        
        # Volume requirements
        volume_match = re.search(
            r'Volume.*?(\d+).*?average',
            description,
            re.IGNORECASE
        )
        if volume_match:
            conditions['volume_threshold'] = int(volume_match.group(1))
        
        # Market phase
        if 'uptrend' in description.lower():
            conditions['market_phase'] = 'uptrend'
        elif 'downtrend' in description.lower():
            conditions['market_phase'] = 'downtrend'
        elif 'ranging' in description.lower():
            conditions['market_phase'] = 'ranging'
        
        return conditions

    def _extract_entry_conditions(self, description: str) -> List[Dict]:
        """Extract entry conditions from strategy description."""
        conditions = []
        entry_section = re.search(r'Entry Conditions:(.*?)(?:Exit Conditions:|$)', 
                                description, re.IGNORECASE | re.DOTALL)
        
        if entry_section:
            text = entry_section.group(1).lower()
            
            # Parse moving average conditions
            ma_pattern = r'(\d+)[-\s]?(?:day|hour|min)?[-\s]?(sma|ema|vwap)'
            ma_matches = re.finditer(ma_pattern, text)
            for match in ma_matches:
                conditions.append({
                    'type': 'moving_average',
                    'period': int(match.group(1)),
                    'ma_type': match.group(2).upper()
                })
            
            # Parse RSI conditions
            rsi_pattern = r'rsi.*?(?:below|under|above|over)\s*(\d+)'
            rsi_matches = re.finditer(rsi_pattern, text)
            for match in rsi_matches:
                conditions.append({
                    'type': 'rsi',
                    'threshold': int(match.group(1))
                })
            
            # Parse volume conditions
            vol_pattern = r'volume.*?(\d+)%?.*?(?:average|avg)'
            vol_matches = re.finditer(vol_pattern, text)
            for match in vol_matches:
                conditions.append({
                    'type': 'volume',
                    'threshold': int(match.group(1))
                })
            
            # Parse candlestick patterns
            for pattern in self.candlestick_patterns:
                if pattern in text:
                    conditions.append({
                        'type': 'candlestick',
                        'pattern': pattern
                    })
        
        return conditions

    def _extract_exit_conditions(self, description: str) -> List[Dict]:
        """Extract exit conditions from strategy description."""
        conditions = []
        exit_section = re.search(r'Exit Conditions:(.*?)(?:Position Management:|$)', 
                               description, re.IGNORECASE | re.DOTALL)
        
        if exit_section:
            text = exit_section.group(1).lower()
            
            # Parse stop loss
            sl_pattern = r'stop[-\s]?loss.*?(\d+\.?\d*)%'
            sl_match = re.search(sl_pattern, text)
            if sl_match:
                conditions.append({
                    'type': 'stop_loss',
                    'percentage': float(sl_match.group(1))
                })
            
            # Parse take profit
            tp_pattern = r'take[-\s]?profit.*?(\d+\.?\d*)%'
            tp_match = re.search(tp_pattern, text)
            if tp_match:
                conditions.append({
                    'type': 'take_profit',
                    'percentage': float(tp_match.group(1))
                })
            
            # Parse trailing stop
            ts_pattern = r'trailing[-\s]?stop.*?(\d+\.?\d*)%'
            ts_match = re.search(ts_pattern, text)
            if ts_match:
                conditions.append({
                    'type': 'trailing_stop',
                    'percentage': float(ts_match.group(1))
                })
            
            # Parse indicator-based exits
            for condition in self._extract_entry_conditions(text):
                condition['context'] = 'exit'
                conditions.append(condition)
        
        return conditions

    def _parse_timeframe(self, timeframe_str: str) -> str:
        """Convert timeframe string to standard format."""
        if not timeframe_str:
            return '1d'
        
        timeframe_str = timeframe_str.lower()
        value = re.search(r'(\d+)', timeframe_str)
        value = value.group(1) if value else '1'
        
        if 'minute' in timeframe_str or 'min' in timeframe_str or 'm' in timeframe_str:
            return f"{value}m"
        elif 'hour' in timeframe_str or 'hr' in timeframe_str or 'h' in timeframe_str:
            return f"{value}h"
        elif 'day' in timeframe_str or 'd' in timeframe_str:
            return f"{value}d"
        elif 'week' in timeframe_str or 'w' in timeframe_str:
            return f"{value}w"
        
        return '1d'

    def _parse_max_trades(self, description: str) -> int:
        """Parse maximum concurrent trades."""
        match = re.search(r'Maximum Positions:.*?(\d+)', description, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 1

    def _validate_strategy_parameters(self, strategy: Dict):
        """Validate strategy parameters to ensure consistency."""
        # Validate position size
        if strategy['position_size'] <= 0 or strategy['position_size'] > 100:
            raise ValueError("Invalid position size. Position size must be between 1% and 100%.")

        # Validate stop loss
        if strategy.get('stop_loss'):
            if strategy['stop_loss'] <= 0:
                raise ValueError("Invalid stop loss value. Stop loss must be greater than 0%.")

        # Validate take profit
        if strategy.get('take_profit'):
            if strategy['take_profit'] <= 0:
                raise ValueError("Invalid take profit value. Take profit must be greater than 0%.")

        # Validate trailing stop
        if strategy.get('trailing_stop'):
            if strategy['trailing_stop']['percentage'] <= 0:
                raise ValueError("Invalid trailing stop value. Trailing stop percentage must be greater than 0%.")

        # Validate maximum trades
        if strategy['max_trades'] <= 0:
            raise ValueError("Invalid maximum trades value. Maximum trades must be greater than 0.")

        # Validate trading hours
        if strategy.get('trading_hours'):
            start_time = datetime.strptime(strategy['trading_hours']['start'], "%H:%M").time()
            end_time = datetime.strptime(strategy['trading_hours']['end'], "%H:%M").time()
            if start_time >= end_time:
                raise ValueError("Invalid trading hours. Start time must be before end time.")

        # Validate market conditions
        if strategy.get('market_conditions'):
            if 'volatility' in strategy['market_conditions']:
                if strategy['market_conditions']['volatility'] <= 0:
                    raise ValueError("Invalid volatility value. Volatility must be greater than 0%.")
            if 'volume_threshold' in strategy['market_conditions']:
                if strategy['market_conditions']['volume_threshold'] <= 0:
                    raise ValueError("Invalid volume threshold value. Volume threshold must be greater than 0.")

    def _display_parsed_strategy(self, strategy: Dict):
        """Display parsed strategy parameters."""
        st.markdown("### Parsed Strategy Parameters")
        
        # Strategy name
        st.markdown(f"#### {strategy.get('name', 'Unnamed Strategy')}")
        
        # Display metrics in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Position Size",
                f"{strategy['position_size']}%",
                help="Percentage of capital per trade"
            )
            st.metric(
                "Stop Loss",
                f"{strategy.get('stop_loss', 'Not Set')}%",
                help="Stop loss percentage"
            )
        
        with col2:
            st.metric(
                "Take Profit",
                f"{strategy.get('take_profit', 'Not Set')}%",
                help="Take profit percentage"
            )
            st.metric(
                "Timeframe",
                strategy.get('timeframe', '1d'),
                help="Trading timeframe"
            )
        
        # Display conditions
        st.markdown("#### Entry Conditions")
        if strategy.get('entry_conditions'):
            for condition in strategy['entry_conditions']:
                st.code(str(condition))
        else:
            st.warning("No entry conditions defined")
        
        st.markdown("#### Exit Conditions")
        if strategy.get('exit_conditions'):
            for condition in strategy['exit_conditions']:
                st.code(str(condition))
        else:
            st.warning("No exit conditions defined")