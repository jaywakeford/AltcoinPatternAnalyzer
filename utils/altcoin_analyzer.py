import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import streamlit as st

class AltcoinAnalyzer:
    def __init__(self):
        self.phases = {
            'phase1': 'Large Cap Leaders',
            'phase2': 'Mid Cap Layer-1s',
            'phase3': 'Sector-specific'
        }
        
    def analyze_market_phase(self, btc_target: float, btc_dominance_floor: float) -> Dict:
        """Analyze current market phase and provide recommendations."""
        try:
            phase_data = {}
            for phase, description in self.phases.items():
                phase_data[phase] = self._get_phase_specific_data(phase, btc_target, btc_dominance_floor)
            return phase_data
        except Exception as e:
            st.error(f"Error analyzing market phase: {str(e)}")
            return {}

    def _get_phase_specific_data(self, phase: str, btc_target: float, btc_dominance_floor: float) -> Dict:
        """Get phase-specific analysis and recommendations."""
        if phase == 'phase1':
            return {
                'name': 'Large Cap Leaders',
                'criteria': {
                    'market_cap_min': 10_000_000_000,  # $10B
                    'volume_24h_min': 100_000_000,     # $100M
                    'btc_correlation_min': 0.7
                },
                'entry_conditions': [
                    'BTC dominance below historical resistance',
                    'Large cap showing relative strength',
                    'Volume increasing vs 20-day average'
                ],
                'exit_conditions': [
                    'BTC dominance rising above threshold',
                    'Volume declining significantly',
                    'Price breaking below key support'
                ],
                'position_sizing': {
                    'initial_size': 0.3,  # 30% of trading capital
                    'max_size': 0.5,      # 50% maximum allocation
                    'risk_per_trade': 0.02  # 2% risk per trade
                },
                'risk_parameters': {
                    'stop_loss': 0.15,    # 15% stop loss
                    'take_profit': 0.45,  # 45% take profit
                    'trailing_stop': 0.1  # 10% trailing stop
                }
            }
        elif phase == 'phase2':
            return {
                'name': 'Mid Cap Layer-1s',
                'criteria': {
                    'market_cap_min': 1_000_000_000,  # $1B
                    'market_cap_max': 10_000_000_000, # $10B
                    'volume_24h_min': 50_000_000,     # $50M
                    'btc_correlation_min': 0.5
                },
                'entry_conditions': [
                    'Large caps showing momentum slowdown',
                    'Increasing developer activity',
                    'Growing ecosystem metrics'
                ],
                'exit_conditions': [
                    'Large cap momentum returning',
                    'Volume spikes with price decline',
                    'Breaking key technical levels'
                ],
                'position_sizing': {
                    'initial_size': 0.2,  # 20% of trading capital
                    'max_size': 0.4,      # 40% maximum allocation
                    'risk_per_trade': 0.015  # 1.5% risk per trade
                },
                'risk_parameters': {
                    'stop_loss': 0.2,     # 20% stop loss
                    'take_profit': 0.6,   # 60% take profit
                    'trailing_stop': 0.15 # 15% trailing stop
                }
            }
        else:  # phase3
            return {
                'name': 'Sector-specific',
                'criteria': {
                    'market_cap_min': 100_000_000,   # $100M
                    'market_cap_max': 1_000_000_000, # $1B
                    'volume_24h_min': 10_000_000,    # $10M
                    'btc_correlation_min': 0.3
                },
                'entry_conditions': [
                    'Sector-specific catalyst identified',
                    'Strong fundamental metrics',
                    'Early signs of accumulation'
                ],
                'exit_conditions': [
                    'Sector rotation signals',
                    'Declining fundamental metrics',
                    'Volume divergence'
                ],
                'position_sizing': {
                    'initial_size': 0.1,  # 10% of trading capital
                    'max_size': 0.3,      # 30% maximum allocation
                    'risk_per_trade': 0.01  # 1% risk per trade
                },
                'risk_parameters': {
                    'stop_loss': 0.25,    # 25% stop loss
                    'take_profit': 0.8,   # 80% take profit
                    'trailing_stop': 0.2  # 20% trailing stop
                }
            }

    def calculate_risk_metrics(self, price_data: pd.DataFrame, market_data: Dict) -> Dict:
        """Calculate risk management metrics."""
        try:
            return {
                'volatility': self._calculate_volatility(price_data),
                'correlation': self._calculate_correlation(price_data),
                'volume_profile': self._analyze_volume_profile(market_data),
                'market_depth': self._analyze_market_depth(market_data)
            }
        except Exception as e:
            st.error(f"Error calculating risk metrics: {str(e)}")
            return {}

    def _calculate_volatility(self, price_data: pd.DataFrame) -> float:
        """Calculate price volatility."""
        if price_data.empty:
            return 0.0
        returns = price_data['price'].pct_change().dropna()
        return returns.std() * np.sqrt(252)  # Annualized volatility

    def _calculate_correlation(self, price_data: pd.DataFrame) -> float:
        """Calculate correlation with BTC."""
        if price_data.empty:
            return 0.0
        # Implementation would need BTC price data as well
        return 0.5  # Placeholder

    def _analyze_volume_profile(self, market_data: Dict) -> Dict:
        """Analyze volume profile and liquidity."""
        return {
            'average_volume': market_data.get('volume_24h', 0),
            'volume_trend': 'increasing' if market_data.get('volume_change_24h', 0) > 0 else 'decreasing',
            'liquidity_score': min(1.0, market_data.get('volume_24h', 0) / 1_000_000_000)
        }

    def _analyze_market_depth(self, market_data: Dict) -> Dict:
        """Analyze market depth and order book."""
        return {
            'bid_depth': market_data.get('bid_depth', 0),
            'ask_depth': market_data.get('ask_depth', 0),
            'spread': market_data.get('spread', 0),
            'depth_score': min(1.0, (market_data.get('bid_depth', 0) + market_data.get('ask_depth', 0)) / 1_000_000)
        }

    def get_historical_cycles(self) -> Dict:
        """Get historical market cycle data."""
        return {
            '2017-2018': {
                'btc_peak': 19891.99,
                'btc_dominance_range': (33.41, 67.54),
                'alt_season_duration': 45,  # days
                'key_characteristics': [
                    'Retail-driven rally',
                    'ICO boom',
                    'Limited institutional presence'
                ]
            },
            '2021': {
                'btc_peak': 69044.77,
                'btc_dominance_range': (39.48, 71.86),
                'alt_season_duration': 75,  # days
                'key_characteristics': [
                    'Institutional adoption',
                    'DeFi summer',
                    'NFT boom'
                ]
            },
            '2024': {
                'btc_current': 35000,
                'btc_dominance_current': 53,
                'market_characteristics': [
                    'ETF approval impact',
                    'Institutional infrastructure',
                    'Regulatory clarity'
                ]
            }
        }
