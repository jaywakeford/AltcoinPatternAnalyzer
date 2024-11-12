import streamlit as st
import re
from typing import Dict, List, Optional, Tuple
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
    trailing_stop: Optional[float] = None
    market_conditions: Optional[Dict] = None
    trading_hours: Optional[Dict] = None

class StrategyBuilder:
    def __init__(self):
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
            ''',
            'RSI Reversal': '''
[Strategy Name]: RSI Reversal Strategy

**Entry Conditions:**
- Primary Signal: Buy when RSI falls below 30
- Confirmation Signals: Price above 20-day SMA, Volume spike

**Exit Conditions:**
- Primary Exit: Sell when RSI rises above 70
- Safety Exits: Price breaks below 20-day SMA

**Position Management:**
- Position Size: 20% of capital per trade
- Maximum Positions: 2 positions at a time

**Risk Management:**
- Stop Loss: 3% below entry price
- Take Profit: 9% above entry price
- Trailing Stop: 1.5% trailing stop after 4% profit

**Trading Schedule:**
- Timeframe: 4-hour timeframe
- Trading Hours: All hours

**Market Conditions:**
- Market Phase: Trade in ranging markets
- Volume Requirements: Volume above 10-day average
            '''
        }

        self.required_fields = {
            'strategy_name': False,
            'entry_conditions': False,
            'exit_conditions': False,
            'position_size': False,
            'stop_loss': False,
            'take_profit': False,
            'timeframe': False
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

    def _render_natural_language_input(self) -> Optional[Dict]:
        """Render natural language input interface with improved guidelines."""
        st.markdown("""
        ### Strategy Description Template

        Please describe your strategy using the following template:

        ```markdown
        [Strategy Name]: [Your strategy name]

        **Entry Conditions:**
        - Primary Signal: [e.g., "Buy when 50-day SMA crosses above 200-day SMA"]
        - Confirmation Signals: [e.g., "RSI below 70", "Volume above 20-day average"]

        **Exit Conditions:**
        - Primary Exit: [e.g., "Sell when 50-day SMA crosses below 200-day SMA"]
        - Safety Exits: [e.g., "RSI above 70", "Price below 200-day SMA"]

        **Position Management:**
        - Position Size: [e.g., "30% of capital per trade"]
        - Maximum Positions: [e.g., "1 position at a time"]

        **Risk Management:**
        - Stop Loss: [e.g., "5% below entry price"]
        - Take Profit: [e.g., "15% above entry price"]
        - Trailing Stop: [Optional, e.g., "2% trailing stop after 5% profit"]

        **Trading Schedule:**
        - Timeframe: [e.g., "Daily timeframe"]
        - Trading Hours: [Optional, e.g., "All hours"]

        **Market Conditions:**
        - Market Phase: [Optional, e.g., "Only trade during uptrend"]
        - Volume Requirements: [Optional, e.g., "Volume above 20-day average"]
        ```
        """)

        description = st.text_area(
            "Strategy Description",
            height=400,
            help="Describe your trading strategy following the template above",
            key="strategy_description"
        )

        if st.button("Validate Strategy", help="Check if all required fields are present"):
            if description:
                try:
                    # Validate required fields
                    missing_fields = self._validate_required_fields(description)
                    if missing_fields:
                        st.error(f"Missing required fields: {', '.join(missing_fields)}")
                        return None

                    # Parse strategy if validation passes
                    strategy = self._parse_strategy_description(description)
                    
                    # Display parsed strategy
                    self._display_parsed_strategy(strategy)
                    
                    # Add proceed button only if validation passes
                    if st.button("Proceed to Backtest", help="Continue with the validated strategy"):
                        return strategy
                except Exception as e:
                    st.error(f"Error parsing strategy: {str(e)}")
                    st.info("Please check your strategy description and try again.")
        return None

    def _validate_required_fields(self, description: str) -> List[str]:
        """Validate that all required fields are present in the strategy description."""
        missing_fields = []
        
        # Check strategy name
        if not re.search(r'\[Strategy Name\]:', description):
            missing_fields.append("Strategy Name")
        
        # Check entry conditions
        if not re.search(r'\*\*Entry Conditions:\*\*', description):
            missing_fields.append("Entry Conditions")
        
        # Check exit conditions
        if not re.search(r'\*\*Exit Conditions:\*\*', description):
            missing_fields.append("Exit Conditions")
        
        # Check position management
        if not re.search(r'Position Size:', description):
            missing_fields.append("Position Size")
        
        # Check risk management
        if not (re.search(r'Stop Loss:', description) and re.search(r'Take Profit:', description)):
            missing_fields.append("Risk Management (Stop Loss/Take Profit)")
        
        # Check timeframe
        if not re.search(r'Timeframe:', description):
            missing_fields.append("Timeframe")
        
        return missing_fields

    def _parse_strategy_description(self, description: str) -> Dict:
        """Parse strategy description with improved error handling."""
        try:
            # Extract strategy name
            strategy_name = re.search(r'\[Strategy Name\]:\s*([^\n]+)', description)
            if not strategy_name:
                raise ValueError("Strategy name is required")

            # Extract basic parameters
            position_size = re.search(r'Position Size:.*?(\d+)%', description)
            stop_loss = re.search(r'Stop Loss:.*?(\d+)%', description)
            take_profit = re.search(r'Take Profit:.*?(\d+)%', description)
            timeframe = re.search(r'Timeframe:.*?(\d+)[-\s]?(hour|day|week|h|d|w)', description)
            trailing_stop = re.search(r'Trailing Stop:.*?(\d+)%', description)

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
                'max_trades': 1,
                'trailing_stop': float(trailing_stop.group(1)) if trailing_stop else None
            }

            # Validate strategy parameters
            self._validate_strategy_parameters(strategy)

            return strategy

        except Exception as e:
            raise ValueError(f"Error parsing strategy: {str(e)}")

    def _validate_strategy_parameters(self, strategy: Dict) -> None:
        """Validate strategy parameters."""
        if strategy['position_size'] <= 0 or strategy['position_size'] > 100:
            raise ValueError("Position size must be between 0 and 100%")
        
        if strategy['stop_loss'] and (strategy['stop_loss'] <= 0 or strategy['stop_loss'] >= 100):
            raise ValueError("Stop loss must be between 0 and 100%")
        
        if strategy['take_profit'] and (strategy['take_profit'] <= 0 or strategy['take_profit'] >= 100):
            raise ValueError("Take profit must be between 0 and 100%")
        
        if strategy['stop_loss'] and strategy['take_profit']:
            if strategy['take_profit'] <= strategy['stop_loss']:
                raise ValueError("Take profit must be greater than stop loss")

    def _extract_entry_conditions(self, description: str) -> List[Dict]:
        """Extract entry conditions with improved pattern matching."""
        conditions = []
        entry_section = re.search(r'\*\*Entry Conditions:\*\*(.*?)\*\*', description, re.DOTALL)
        
        if entry_section:
            text = entry_section.group(1)
            
            # Moving Average patterns
            ma_matches = re.finditer(
                r'(?:buy|enter)\s+when\s+(\d+)[-\s]?(?:day|hour)?\s+(sma|ema)\s+crosses?\s+(above|below)\s+(\d+)[-\s]?(?:day|hour)?',
                text.lower()
            )
            
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
            rsi_matches = re.finditer(
                r'(?:buy|enter).*?rsi.*?(below|above|falls below|rises above)\s+(\d+)',
                text.lower()
            )
            
            for match in rsi_matches:
                conditions.append({
                    'type': 'rsi',
                    'direction': match.group(1),
                    'value': int(match.group(2))
                })

        return conditions

    def _extract_exit_conditions(self, description: str) -> List[Dict]:
        """Extract exit conditions with improved pattern matching."""
        conditions = []
        exit_section = re.search(r'\*\*Exit Conditions:\*\*(.*?)\*\*', description, re.DOTALL)
        
        if exit_section:
            text = exit_section.group(1)
            
            # Moving Average exit patterns
            ma_matches = re.finditer(
                r'(?:sell|exit)\s+when\s+(\d+)[-\s]?(?:day|hour)?\s+(sma|ema)\s+crosses?\s+(above|below)\s+(\d+)[-\s]?(?:day|hour)?',
                text.lower()
            )
            
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
            rsi_matches = re.finditer(
                r'(?:sell|exit).*?rsi.*?(below|above|falls below|rises above)\s+(\d+)',
                text.lower()
            )
            
            for match in rsi_matches:
                conditions.append({
                    'type': 'rsi',
                    'direction': match.group(1),
                    'value': int(match.group(2))
                })

        return conditions

    def _display_parsed_strategy(self, strategy: Dict):
        """Display parsed strategy parameters with improved formatting."""
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
                    f"{strategy['trailing_stop']}%",
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
