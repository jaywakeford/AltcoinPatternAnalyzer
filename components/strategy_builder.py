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
        
        # Initialize strategy templates (keeping existing ones)
        self.strategy_templates = {
            'Moving Average Crossover': '''
[Strategy Name]: Moving Average Crossover Strategy

**Entry Conditions:**
- Primary Signal: Buy when 50-day SMA crosses above 200-day SMA
- Confirmation Signals: RSI below 70, Volume above 20-day average

**Exit Conditions:**
- Primary Exit: Sell when 50-day SMA crosses below 200-day SMA
- Safety Exits: RSI above 70, Price below 200-day SMA

**Position Management:**
- Position Size: 30% of capital per trade
- Maximum Positions: 1 position at a time

**Risk Management:**
- Stop Loss: 5% below entry price
- Take Profit: 15% above entry price
- Trailing Stop: 2% trailing stop after 5% profit

**Trading Schedule:**
- Timeframe: Daily timeframe
- Trading Hours: All hours

**Market Conditions:**
- Market Phase: Only trade during uptrend
- Volume Requirements: Volume above 20-day average
- Volatility Filter: ATR below 5%
            ''',
            'RSI Reversal': '''
[Strategy Name]: RSI Reversal Strategy

**Entry Conditions:**
- Primary Signal: Buy when RSI falls below 30
- Confirmation Signals: 
  * Price above 20-day SMA
  * Volume spike above 200% average
  * Bullish candlestick pattern (hammer or engulfing)

**Exit Conditions:**
- Primary Exit: Sell when RSI rises above 70
- Safety Exits: Price breaks below 20-day SMA
- Additional Exits:
  * Bearish candlestick pattern
  * Volume decline below average

**Position Management:**
- Position Size: 20% of capital per trade
- Maximum Positions: 2 positions at a time

**Risk Management:**
- Stop Loss: 3.5% below entry price
- Take Profit: Multiple targets:
  * Target 1: 5% (40% of position)
  * Target 2: 10% (60% of position)
- Trailing Stop: 1.5% trailing stop after 4% profit

**Trading Schedule:**
- Timeframe: 4-hour timeframe
- Trading Hours: 09:30-16:00 EST
- Weekend Trading: No

**Market Conditions:**
- Market Phase: Trade in ranging markets
- Volume Requirements: Above 10-day average
- Volatility Conditions:
  * ATR between 1-4%
  * Bollinger Bands not extremely wide
            '''
        }

    def _validate_required_fields(self, description: str) -> List[str]:
        """Validate required fields with more flexible format recognition."""
        missing_fields = []
        
        # Strategy name check (more flexible)
        if not (re.search(r'\[Strategy Name\]:', description) or 
                re.search(r'Strategy Name:', description, re.IGNORECASE)):
            missing_fields.append("Strategy Name")
        
        # Entry conditions check (more flexible)
        if not (re.search(r'\*\*Entry Conditions:\*\*', description) or 
                re.search(r'Entry Conditions:', description, re.IGNORECASE) or
                re.search(r'Entry Rules:', description, re.IGNORECASE)):
            missing_fields.append("Entry Conditions")
        
        # Exit conditions check (more flexible)
        if not (re.search(r'\*\*Exit Conditions:\*\*', description) or 
                re.search(r'Exit Conditions:', description, re.IGNORECASE) or
                re.search(r'Exit Rules:', description, re.IGNORECASE)):
            missing_fields.append("Exit Conditions")
        
        # Position management check
        if not (re.search(r'Position Size:', description, re.IGNORECASE) or
                re.search(r'Position Management:', description, re.IGNORECASE)):
            missing_fields.append("Position Size")
        
        # Risk management check (more flexible)
        has_risk_management = (
            (re.search(r'Stop Loss:', description, re.IGNORECASE) and
             re.search(r'Take Profit:', description, re.IGNORECASE)) or
            re.search(r'Risk Management:', description, re.IGNORECASE)
        )
        if not has_risk_management:
            missing_fields.append("Risk Management (Stop Loss/Take Profit)")
        
        # Timeframe check (more flexible)
        if not (re.search(r'Timeframe:', description, re.IGNORECASE) or
                re.search(r'Time Frame:', description, re.IGNORECASE) or
                re.search(r'Trading Interval:', description, re.IGNORECASE)):
            missing_fields.append("Timeframe")
        
        return missing_fields

    def _parse_strategy_description(self, description: str) -> Dict:
        """Enhanced strategy parser with support for complex conditions."""
        try:
            # Extract strategy name (more flexible)
            strategy_name = (
                re.search(r'\[Strategy Name\]:\s*([^\n]+)', description) or
                re.search(r'Strategy Name:\s*([^\n]+)', description, re.IGNORECASE)
            )
            if not strategy_name:
                raise ValueError("Strategy name is required")

            # Extract position size (support for decimal percentages)
            position_size = re.search(
                r'Position Size:.*?(\d+\.?\d*)%',
                description,
                re.IGNORECASE | re.DOTALL
            )

            # Extract risk parameters (support for decimal percentages)
            stop_loss = re.search(
                r'Stop Loss:.*?(\d+\.?\d*)%',
                description,
                re.IGNORECASE | re.DOTALL
            )
            take_profit = re.search(
                r'Take Profit:.*?(\d+\.?\d*)%',
                description,
                re.IGNORECASE | re.DOTALL
            )

            # Extract trailing stop with conditions
            trailing_stop = self._parse_trailing_stop(description)

            # Extract timeframe
            timeframe = re.search(
                r'Timeframe:.*?(\d+)[-\s]?(minute|hour|day|week|m|h|d|w)',
                description,
                re.IGNORECASE | re.DOTALL
            )

            # Extract trading hours
            trading_hours = self._parse_trading_hours(description)

            # Extract market conditions
            market_conditions = self._parse_market_conditions(description)

            # Extract entry and exit conditions
            entry_conditions = self._extract_entry_conditions(description)
            exit_conditions = self._extract_exit_conditions(description)

            if not entry_conditions:
                raise ValueError("At least one entry condition is required")
            if not exit_conditions:
                raise ValueError("At least one exit condition is required")

            # Build strategy configuration
            strategy = {
                'name': strategy_name.group(1).strip(),
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'position_size': float(position_size.group(1)) if position_size else 10.0,
                'stop_loss': float(stop_loss.group(1)) if stop_loss else None,
                'take_profit': float(take_profit.group(1)) if take_profit else None,
                'timeframe': self._parse_timeframe(timeframe.group() if timeframe else '1-day'),
                'max_trades': self._parse_max_trades(description),
                'trailing_stop': trailing_stop,
                'market_conditions': market_conditions,
                'trading_hours': trading_hours
            }

            # Validate strategy parameters
            self._validate_strategy_parameters(strategy)

            return strategy

        except Exception as e:
            raise ValueError(f"Error parsing strategy: {str(e)}")

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
        """Enhanced entry condition extraction with support for multiple patterns."""
        conditions = []
        entry_section = (
            re.search(r'\*\*Entry Conditions:\*\*(.*?)(?:\*\*|$)', description, re.DOTALL) or
            re.search(r'Entry Conditions:(.*?)(?:\n\n|$)', description, re.DOTALL)
        )
        
        if entry_section:
            text = entry_section.group(1).lower()
            
            # Extract candlestick patterns
            for pattern in self.candlestick_patterns:
                if pattern in text:
                    conditions.append({
                        'type': 'candlestick',
                        'pattern': pattern
                    })
            
            # Moving Average patterns (enhanced)
            ma_matches = re.finditer(
                r'(?:buy|enter).*?(\d+)[-\s]?(?:day|hour|min)?(?:\s+)?'
                r'(sma|ema|vwap).*?(?:cross(?:es)?|above|below).*?'
                r'(\d+)[-\s]?(?:day|hour|min)?',
                text
            )
            
            for match in ma_matches:
                conditions.append({
                    'type': 'moving_average_cross',
                    'period1': int(match.group(1)),
                    'ma_type1': match.group(2).upper(),
                    'direction': 'above' if 'above' in match.group(0) else 'below',
                    'period2': int(match.group(3)),
                    'ma_type2': match.group(2).upper()
                })
            
            # RSI patterns (enhanced)
            rsi_matches = re.finditer(
                r'rsi.*?(?:cross(?:es)?|above|below|over|under)\s*(\d+)',
                text
            )
            
            for match in rsi_matches:
                conditions.append({
                    'type': 'rsi',
                    'direction': 'below' if any(x in match.group(0) for x in ['below', 'under']) else 'above',
                    'value': int(match.group(1))
                })
            
            # Volume conditions
            volume_matches = re.finditer(
                r'volume.*?(\d+)%?.*?(?:average|avg|mean)',
                text
            )
            
            for match in volume_matches:
                conditions.append({
                    'type': 'volume',
                    'threshold': int(match.group(1)),
                    'comparison': 'above' if 'above' in match.group(0) else 'below'
                })

        return conditions

    def _extract_exit_conditions(self, description: str) -> List[Dict]:
        """Enhanced exit condition extraction with support for multiple patterns."""
        conditions = []
        exit_section = (
            re.search(r'\*\*Exit Conditions:\*\*(.*?)(?:\*\*|$)', description, re.DOTALL) or
            re.search(r'Exit Conditions:(.*?)(?:\n\n|$)', description, re.DOTALL)
        )
        
        if exit_section:
            text = exit_section.group(1).lower()
            
            # Extract candlestick patterns
            for pattern in self.candlestick_patterns:
                if pattern in text:
                    conditions.append({
                        'type': 'candlestick',
                        'pattern': pattern
                    })
            
            # Moving Average patterns (enhanced)
            ma_matches = re.finditer(
                r'(?:sell|exit).*?(\d+)[-\s]?(?:day|hour|min)?(?:\s+)?'
                r'(sma|ema|vwap).*?(?:cross(?:es)?|above|below).*?'
                r'(\d+)[-\s]?(?:day|hour|min)?',
                text
            )
            
            for match in ma_matches:
                conditions.append({
                    'type': 'moving_average_cross',
                    'period1': int(match.group(1)),
                    'ma_type1': match.group(2).upper(),
                    'direction': 'above' if 'above' in match.group(0) else 'below',
                    'period2': int(match.group(3)),
                    'ma_type2': match.group(2).upper()
                })
            
            # RSI patterns (enhanced)
            rsi_matches = re.finditer(
                r'rsi.*?(?:cross(?:es)?|above|below|over|under)\s*(\d+)',
                text
            )
            
            for match in rsi_matches:
                conditions.append({
                    'type': 'rsi',
                    'direction': 'below' if any(x in match.group(0) for x in ['below', 'under']) else 'above',
                    'value': int(match.group(1))
                })
            
            # Time-based conditions
            time_matches = re.finditer(
                r'(?:after|before)\s+(\d{1,2}:\d{2})\s*([A-Za-z]{2,4})?',
                text
            )
            
            for match in time_matches:
                conditions.append({
                    'type': 'time',
                    'time': match.group(1),
                    'timezone': match.group(2) if match.group(2) else 'UTC'
                })

        return conditions

    def _parse_max_trades(self, description: str) -> int:
        """Parse maximum number of simultaneous trades."""
        max_trades_match = re.search(
            r'Maximum Positions:\s*(\d+)',
            description,
            re.IGNORECASE
        )
        return int(max_trades_match.group(1)) if max_trades_match else 1

    def _validate_strategy_parameters(self, strategy: Dict) -> None:
        """Validate strategy parameters with enhanced checks."""
        if strategy['position_size'] <= 0 or strategy['position_size'] > 100:
            raise ValueError("Position size must be between 0 and 100%")
        
        if strategy['stop_loss'] and (strategy['stop_loss'] <= 0 or strategy['stop_loss'] >= 100):
            raise ValueError("Stop loss must be between 0 and 100%")
        
        if strategy['take_profit'] and (strategy['take_profit'] <= 0 or strategy['take_profit'] >= 100):
            raise ValueError("Take profit must be between 0 and 100%")
        
        if strategy['stop_loss'] and strategy['take_profit']:
            if strategy['take_profit'] <= strategy['stop_loss']:
                raise ValueError("Take profit must be greater than stop loss")
        
        if strategy.get('trailing_stop'):
            if strategy['trailing_stop']['percentage'] <= 0 or strategy['trailing_stop']['percentage'] >= 100:
                raise ValueError("Trailing stop percentage must be between 0 and 100%")
            
            if 'activation_percentage' in strategy['trailing_stop']:
                if strategy['trailing_stop']['activation_percentage'] <= 0:
                    raise ValueError("Trailing stop activation percentage must be positive")

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

    def _display_parsed_strategy(self, strategy: Dict):
        """Display parsed strategy parameters with enhanced formatting."""
        st.markdown("### Parsed Strategy Parameters")
        
        # Strategy Overview
        st.markdown(f"""
        #### Strategy: {strategy.get('name', 'Unnamed Strategy')}
        """)
        
        # Display parameters in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Position Size",
                f"{strategy['position_size']}%",
                help="Percentage of capital to use per trade"
            )
            st.metric(
                "Stop Loss",
                f"{strategy['stop_loss']}%" if strategy['stop_loss'] else "Not Set",
                help="Price level where position will be closed to limit losses"
            )
            if strategy.get('trailing_stop'):
                st.metric(
                    "Trailing Stop",
                    f"{strategy['trailing_stop']['percentage']}%",
                    help="Dynamic stop loss that follows price movement"
                )
        
        with col2:
            st.metric(
                "Timeframe",
                strategy['timeframe'],
                help="Trading interval for analysis and execution"
            )
            st.metric(
                "Take Profit",
                f"{strategy['take_profit']}%" if strategy['take_profit'] else "Not Set",
                help="Price level where position will be closed to secure profits"
            )
            st.metric(
                "Max Trades",
                strategy['max_trades'],
                help="Maximum number of simultaneous positions"
            )
        
        # Display market conditions if present
        if strategy.get('market_conditions'):
            st.markdown("#### Market Conditions")
            market_conditions = strategy['market_conditions']
            if 'volatility' in market_conditions:
                st.metric("Volatility Threshold", f"{market_conditions['volatility']}%")
            if 'volume_threshold' in market_conditions:
                st.metric("Volume Requirement", f"{market_conditions['volume_threshold']}x average")
            if 'market_phase' in market_conditions:
                st.info(f"Market Phase: {market_conditions['market_phase'].title()}")
        
        # Display trading hours if present
        if strategy.get('trading_hours'):
            st.markdown("#### Trading Schedule")
            trading_hours = strategy['trading_hours']
            st.info(
                f"Trading Hours: {trading_hours['start']} - {trading_hours['end']} {trading_hours['timezone']}\n"
                f"Weekend Trading: {'Yes' if trading_hours['weekend_trading'] else 'No'}"
            )
        
        # Display conditions
        st.markdown("#### Entry Conditions")
        if strategy['entry_conditions']:
            for condition in strategy['entry_conditions']:
                st.code(str(condition))
        else:
            st.warning("No entry conditions defined")
        
        st.markdown("#### Exit Conditions")
        if strategy['exit_conditions']:
            for condition in strategy['exit_conditions']:
                st.code(str(condition))
        else:
            st.warning("No exit conditions defined")
