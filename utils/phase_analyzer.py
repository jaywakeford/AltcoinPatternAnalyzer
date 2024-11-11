import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from utils.technical_analysis import calculate_rsi, calculate_macd

class PhaseAnalyzer:
    def __init__(self):
        self.phase_thresholds = {
            'btc_dominance': {
                'high': 60,
                'low': 53
            },
            'rsi': {
                'overbought': 70,
                'oversold': 30
            },
            'volume_surge': 2.0  # 2x average volume
        }

    def analyze_market_phase(self, 
                           btc_data: pd.DataFrame, 
                           dominance_data: pd.DataFrame) -> Dict:
        """
        Analyze the current market phase based on multiple indicators.
        Returns the current phase and relevant metrics.
        """
        current_phase = self._determine_phase(btc_data, dominance_data)
        metrics = self._calculate_phase_metrics(btc_data, dominance_data)
        recommendations = self._generate_recommendations(current_phase)
        
        return {
            'current_phase': current_phase,
            'metrics': metrics,
            'recommendations': recommendations
        }

    def _determine_phase(self, 
                        btc_data: pd.DataFrame, 
                        dominance_data: pd.DataFrame) -> str:
        """
        Determine the current market phase based on indicators.
        """
        # Get latest metrics
        btc_dominance = dominance_data['btc_dominance'].iloc[-1]
        rsi = calculate_rsi(btc_data).iloc[-1]
        price_change = self._calculate_price_change(btc_data, window=30)
        volume_ratio = self._calculate_volume_ratio(btc_data)
        
        # Phase determination logic
        if btc_dominance > self.phase_thresholds['btc_dominance']['high']:
            return "Phase 1: Bitcoin Dominance"
        elif (btc_dominance < self.phase_thresholds['btc_dominance']['low'] and 
              price_change > 0 and volume_ratio > 1.5):
            return "Phase 2: Large Cap Altcoins"
        elif (btc_dominance < self.phase_thresholds['btc_dominance']['low'] and 
              volume_ratio > 2.0):
            return "Phase 3: Mid Cap & Sector Rotation"
        else:
            return "Accumulation Phase"

    def _calculate_phase_metrics(self, 
                               btc_data: pd.DataFrame, 
                               dominance_data: pd.DataFrame) -> Dict:
        """
        Calculate relevant metrics for phase analysis.
        """
        # Calculate key metrics
        rsi = calculate_rsi(btc_data).iloc[-1]
        macd, signal = calculate_macd(btc_data)
        macd_value = macd.iloc[-1]
        volume_ratio = self._calculate_volume_ratio(btc_data)
        price_volatility = btc_data['price'].pct_change().std() * 100
        
        return {
            'rsi': round(rsi, 2),
            'macd': round(macd_value, 2),
            'volume_ratio': round(volume_ratio, 2),
            'volatility': round(price_volatility, 2),
            'btc_dominance': round(dominance_data['btc_dominance'].iloc[-1], 2)
        }

    def _generate_recommendations(self, current_phase: str) -> List[str]:
        """
        Generate strategic recommendations based on the current phase.
        """
        phase_recommendations = {
            "Phase 1: Bitcoin Dominance": [
                "Focus on Bitcoin accumulation",
                "Monitor large-cap altcoins for potential breakouts",
                "Keep high cash reserves for upcoming opportunities",
                "Set alerts for Bitcoin dominance decline"
            ],
            "Phase 2: Large Cap Altcoins": [
                "Begin rotating into top 10 altcoins",
                "Monitor volume profiles for breakouts",
                "Set stop-losses at key support levels",
                "Watch for sector-specific momentum"
            ],
            "Phase 3: Mid Cap & Sector Rotation": [
                "Focus on high-momentum sectors",
                "Consider taking profits on large-cap positions",
                "Monitor for signs of market exhaustion",
                "Increase position in promising mid-cap projects"
            ],
            "Accumulation Phase": [
                "Build positions in blue-chip cryptocurrencies",
                "Dollar-cost average into strong projects",
                "Maintain higher cash reserves",
                "Research upcoming project developments"
            ]
        }
        
        return phase_recommendations.get(current_phase, [])

    def _calculate_price_change(self, 
                              data: pd.DataFrame, 
                              window: int) -> float:
        """
        Calculate price change over specified window.
        """
        return ((data['price'].iloc[-1] / data['price'].iloc[-window]) - 1) * 100

    def _calculate_volume_ratio(self, data: pd.DataFrame) -> float:
        """
        Calculate current volume relative to moving average.
        """
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(window=20).mean().iloc[-1]
        return current_volume / avg_volume if avg_volume != 0 else 0

    def get_phase_signals(self, 
                         btc_data: pd.DataFrame, 
                         dominance_data: pd.DataFrame) -> Dict:
        """
        Get detailed signals for phase transition analysis.
        """
        rsi = calculate_rsi(btc_data).iloc[-1]
        volume_ratio = self._calculate_volume_ratio(btc_data)
        btc_dominance = dominance_data['btc_dominance'].iloc[-1]
        
        signals = {
            'momentum': {
                'status': 'high' if rsi > 70 else 'low' if rsi < 30 else 'neutral',
                'value': round(rsi, 2)
            },
            'volume': {
                'status': 'high' if volume_ratio > 2 else 'normal',
                'value': round(volume_ratio, 2)
            },
            'dominance': {
                'status': 'high' if btc_dominance > 60 else 'low' if btc_dominance < 53 else 'neutral',
                'value': round(btc_dominance, 2)
            }
        }
        
        return signals

    def get_risk_level(self, metrics: Dict) -> Tuple[str, float]:
        """
        Calculate current market risk level based on metrics.
        """
        risk_score = 0
        
        # RSI risk factor
        if metrics['rsi'] > 80:
            risk_score += 3
        elif metrics['rsi'] > 70:
            risk_score += 2
        elif metrics['rsi'] < 30:
            risk_score += 1
        
        # Volatility risk factor
        if metrics['volatility'] > 5:
            risk_score += 2
        elif metrics['volatility'] > 3:
            risk_score += 1
        
        # Volume risk factor
        if metrics['volume_ratio'] > 3:
            risk_score += 2
        elif metrics['volume_ratio'] > 2:
            risk_score += 1
        
        # Normalize risk score (0-10 scale)
        normalized_score = min(risk_score / 7 * 10, 10)
        
        # Risk levels
        if normalized_score >= 7:
            return "High", normalized_score
        elif normalized_score >= 4:
            return "Medium", normalized_score
        else:
            return "Low", normalized_score
