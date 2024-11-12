import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import streamlit as st
import ccxt
import plotly.graph_objects as go
import plotly.express as px
from sklearn.preprocessing import StandardScaler
import seaborn as sns

class AltcoinAnalyzer:
    def __init__(self):
        self.phases = {
            'phase1': 'Large Cap Leaders (2-10)',
            'phase2': 'Mid Cap Layer-1s (11-25)',
            'phase3': 'Lower Caps (26-50)'
        }
        self.exchange = ccxt.binance()
        
    def fetch_top_50_cryptocurrencies(self) -> pd.DataFrame:
        """Fetch and track top 50 cryptocurrencies by market cap."""
        try:
            markets = self.exchange.fetch_markets()
            tickers = self.exchange.fetch_tickers()
            
            crypto_data = []
            for market in markets:
                if market['quote'] == 'USDT':
                    symbol = market['symbol']
                    if symbol in tickers:
                        ticker = tickers[symbol]
                        crypto_data.append({
                            'symbol': market['base'],
                            'market_cap': ticker.get('quoteVolume', 0) * ticker.get('last', 0),
                            'volume_24h': ticker.get('quoteVolume', 0),
                            'price': ticker.get('last', 0),
                            'change_24h': ticker.get('percentage', 0),
                            'momentum': ticker.get('change', 0)
                        })
            
            df = pd.DataFrame(crypto_data)
            df = df.sort_values('market_cap', ascending=False).head(50)
            df['rank'] = range(1, len(df) + 1)
            df['category'] = df['rank'].apply(self._assign_category)
            
            return df
        except Exception as e:
            st.error(f"Error fetching cryptocurrency data: {str(e)}")
            return pd.DataFrame()
    
    def _assign_category(self, rank: int) -> str:
        """Assign category based on market cap rank."""
        if 2 <= rank <= 10:
            return 'Large Cap'
        elif 11 <= rank <= 25:
            return 'Mid Cap'
        else:
            return 'Lower Cap'
    
    def analyze_historical_sequence(self, timeframe: str = '1d', lookback_days: int = 365) -> Dict:
        """Analyze historical alt season patterns."""
        try:
            df = self.fetch_top_50_cryptocurrencies()
            historical_data = {}
            
            for symbol in df['symbol']:
                try:
                    ohlcv = self.exchange.fetch_ohlcv(
                        f"{symbol}/USDT",
                        timeframe,
                        limit=lookback_days
                    )
                    if ohlcv:
                        historical_data[symbol] = pd.DataFrame(
                            ohlcv,
                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                        )
                        historical_data[symbol]['timestamp'] = pd.to_datetime(
                            historical_data[symbol]['timestamp'], unit='ms'
                        )
                except Exception:
                    continue
            
            return self._calculate_sequence_metrics(historical_data)
        except Exception as e:
            st.error(f"Error analyzing historical sequence: {str(e)}")
            return {}
    
    def _calculate_sequence_metrics(self, historical_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate sequence metrics for alt season patterns."""
        metrics = {
            'momentum_scores': {},
            'correlation_matrix': None,
            'phase_indicators': {},
            'entry_points': {},
            'exit_points': {}
        }
        
        try:
            # Calculate momentum scores
            for symbol, data in historical_data.items():
                momentum = (
                    (data['close'] - data['close'].shift(20)) / 
                    data['close'].shift(20) * 100
                )
                metrics['momentum_scores'][symbol] = momentum.iloc[-1]
            
            # Calculate correlation matrix
            close_prices = pd.DataFrame({
                symbol: data['close'] 
                for symbol, data in historical_data.items()
            })
            metrics['correlation_matrix'] = close_prices.corr()
            
            # Calculate phase indicators
            for symbol, data in historical_data.items():
                vol_change = (
                    (data['volume'].rolling(7).mean() / 
                     data['volume'].rolling(30).mean() - 1) * 100
                )
                price_change = (
                    (data['close'] - data['close'].shift(30)) / 
                    data['close'].shift(30) * 100
                )
                
                metrics['phase_indicators'][symbol] = {
                    'volume_trend': vol_change.iloc[-1],
                    'price_trend': price_change.iloc[-1],
                    'volatility': data['close'].pct_change().std() * 100
                }
            
            return metrics
        except Exception as e:
            st.error(f"Error calculating sequence metrics: {str(e)}")
            return metrics
    
    def analyze_btc_correlation(self, timeframe: str = '1d', lookback_days: int = 90) -> Dict:
        """Analyze correlation between BTC cooling periods and alt movements."""
        try:
            btc_data = self.exchange.fetch_ohlcv(
                'BTC/USDT',
                timeframe,
                limit=lookback_days
            )
            btc_df = pd.DataFrame(
                btc_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'], unit='ms')
            
            # Identify cooling periods
            btc_df['sma20'] = btc_df['close'].rolling(20).mean()
            btc_df['cooling'] = btc_df['close'] < btc_df['sma20']
            
            cooling_periods = self._identify_cooling_periods(btc_df)
            alt_performance = self._calculate_alt_performance(cooling_periods)
            
            return {
                'cooling_periods': cooling_periods,
                'alt_performance': alt_performance
            }
        except Exception as e:
            st.error(f"Error analyzing BTC correlation: {str(e)}")
            return {}
    
    def _identify_cooling_periods(self, btc_df: pd.DataFrame) -> List[Dict]:
        """Identify BTC cooling periods."""
        cooling_periods = []
        cooling = False
        start_idx = None
        
        for idx, row in btc_df.iterrows():
            if row['cooling'] and not cooling:
                cooling = True
                start_idx = idx
            elif not row['cooling'] and cooling:
                cooling = False
                if start_idx is not None:
                    cooling_periods.append({
                        'start': start_idx,
                        'end': idx,
                        'duration': (idx - start_idx).days,
                        'price_change': (
                            btc_df.loc[idx, 'close'] / 
                            btc_df.loc[start_idx, 'close'] - 1
                        ) * 100
                    })
        
        return cooling_periods
    
    def _calculate_alt_performance(self, cooling_periods: List[Dict]) -> Dict:
        """Calculate alt performance during BTC cooling periods."""
        try:
            df = self.fetch_top_50_cryptocurrencies()
            performance = {}
            
            for period in cooling_periods:
                start_date = period['start']
                end_date = period['end']
                
                for symbol in df['symbol']:
                    try:
                        ohlcv = self.exchange.fetch_ohlcv(
                            f"{symbol}/USDT",
                            '1d',
                            since=int(start_date.timestamp() * 1000),
                            limit=(end_date - start_date).days + 1
                        )
                        if ohlcv:
                            price_change = (ohlcv[-1][4] / ohlcv[0][4] - 1) * 100
                            if symbol not in performance:
                                performance[symbol] = []
                            performance[symbol].append(price_change)
                    except Exception:
                        continue
            
            return performance
        except Exception as e:
            st.error(f"Error calculating alt performance: {str(e)}")
            return {}
    
    def calculate_stair_stepping_strategy(self, capital: float = 10000) -> Dict:
        """Calculate stair-stepping strategy allocations and entry/exit points."""
        try:
            df = self.fetch_top_50_cryptocurrencies()
            strategy = {
                'allocations': {},
                'entry_points': {},
                'exit_points': {},
                'risk_metrics': {}
            }
            
            # Calculate base allocations
            total_allocation = 0
            for category in ['Large Cap', 'Mid Cap', 'Lower Cap']:
                category_df = df[df['category'] == category]
                if category == 'Large Cap':
                    allocation = 0.5  # 50% to large caps
                elif category == 'Mid Cap':
                    allocation = 0.3  # 30% to mid caps
                else:
                    allocation = 0.2  # 20% to lower caps
                
                category_capital = capital * allocation
                per_coin_capital = category_capital / len(category_df)
                
                for _, coin in category_df.iterrows():
                    strategy['allocations'][coin['symbol']] = {
                        'capital': per_coin_capital,
                        'percentage': (per_coin_capital / capital) * 100
                    }
                    
                    # Calculate entry and exit points
                    strategy['entry_points'][coin['symbol']] = {
                        'initial': coin['price'],
                        'dca_levels': [
                            coin['price'] * (1 - level/100)
                            for level in [5, 10, 15, 20]
                        ]
                    }
                    
                    strategy['exit_points'][coin['symbol']] = {
                        'take_profit_levels': [
                            coin['price'] * (1 + level/100)
                            for level in [20, 35, 50, 75]
                        ],
                        'stop_loss': coin['price'] * 0.85  # 15% stop loss
                    }
                    
                    # Calculate risk metrics
                    strategy['risk_metrics'][coin['symbol']] = {
                        'volatility': coin.get('change_24h', 0),
                        'volume_factor': coin['volume_24h'] / coin['market_cap'],
                        'momentum_score': coin.get('momentum', 0)
                    }
            
            return strategy
        except Exception as e:
            st.error(f"Error calculating stair-stepping strategy: {str(e)}")
            return {}
