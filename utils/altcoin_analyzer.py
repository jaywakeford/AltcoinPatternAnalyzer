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
import logging

logger = logging.getLogger(__name__)

class AltcoinAnalyzer:
    def __init__(self):
        self.phases = {
            'phase1': 'Large Cap Leaders (2-10)',
            'phase2': 'Mid Cap Layer-1s (11-25)',
            'phase3': 'Lower Caps (26-50)'
        }
        self.exchanges = [
            'kraken',
            'kucoin'
        ]
        self.active_exchange = None
        self._initialize_exchange()
        
    def _initialize_exchange(self):
        """Initialize exchange with fallback options."""
        exchange_errors = []
        
        for exchange_id in self.exchanges:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 30000,
                })
                # Test API access
                exchange.fetch_markets()
                self.active_exchange = exchange
                logger.info(f"Successfully connected to {exchange_id}")
                break
            except ccxt.ExchangeNotAvailable as e:
                error_msg = f"{exchange_id} is not available: {str(e)}"
                exchange_errors.append(error_msg)
                logger.warning(error_msg)
            except ccxt.ExchangeError as e:
                error_msg = f"Error connecting to {exchange_id}: {str(e)}"
                exchange_errors.append(error_msg)
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error with {exchange_id}: {str(e)}"
                exchange_errors.append(error_msg)
                logger.error(error_msg)
        
        if not self.active_exchange:
            error_message = (
                "Unable to connect to any cryptocurrency exchange. "
                "This might be due to regional restrictions or temporary service issues.\n"
                "Errors encountered:\n" + "\n".join(exchange_errors)
            )
            logger.error(error_message)
            raise ccxt.ExchangeNotAvailable(error_message)

    def _ensure_exchange_connection(self):
        """Ensure exchange connection is active, attempt reconnection if needed."""
        if not self.active_exchange:
            try:
                self._initialize_exchange()
            except Exception as e:
                logger.error(f"Failed to re-establish exchange connection: {str(e)}")
                raise

    def fetch_top_50_cryptocurrencies(self) -> pd.DataFrame:
        """Fetch and track top 50 cryptocurrencies by market cap with fallback handling."""
        try:
            self._ensure_exchange_connection()
            markets = self.active_exchange.fetch_markets()
            tickers = self.active_exchange.fetch_tickers()
            
            crypto_data = []
            for market in markets:
                try:
                    if market['quote'] == 'USDT' and market['active']:
                        symbol = market['symbol']
                        if symbol in tickers:
                            ticker = tickers[symbol]
                            market_cap = float(ticker.get('quoteVolume', 0)) * float(ticker.get('last', 0))
                            if market_cap > 0:  # Filter out zero market cap entries
                                crypto_data.append({
                                    'symbol': market['base'],
                                    'market_cap': market_cap,
                                    'volume_24h': float(ticker.get('quoteVolume', 0)),
                                    'price': float(ticker.get('last', 0)),
                                    'change_24h': float(ticker.get('percentage', 0)),
                                    'momentum': float(ticker.get('change', 0))
                                })
                except (TypeError, ValueError) as e:
                    logger.warning(f"Error processing market data for {market.get('symbol', 'unknown')}: {str(e)}")
                    continue
            
            if not crypto_data:
                raise ValueError("No valid cryptocurrency data retrieved")
            
            df = pd.DataFrame(crypto_data)
            df = df.sort_values('market_cap', ascending=False).head(50)
            df['rank'] = range(1, len(df) + 1)
            df['category'] = df['rank'].apply(self._assign_category)
            
            return df
        except ccxt.ExchangeNotAvailable as e:
            logger.error(f"Exchange not available: {str(e)}")
            st.error("Unable to access cryptocurrency exchange. This might be due to regional restrictions.")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching cryptocurrency data: {str(e)}")
            st.error(f"Error fetching market data: {str(e)}")
            return pd.DataFrame()

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
                    # Convert timestamps to datetime if they aren't already
                    if isinstance(idx, (int, float)):
                        end_time = pd.Timestamp(idx)
                        start_time = pd.Timestamp(start_idx)
                    else:
                        end_time = idx
                        start_time = start_idx
                    
                    duration = (end_time - start_time).total_seconds() / (24 * 3600)  # Convert to days
                    cooling_periods.append({
                        'start': start_idx,
                        'end': idx,
                        'duration': duration,
                        'price_change': (
                            btc_df.loc[idx, 'close'] / 
                            btc_df.loc[start_idx, 'close'] - 1
                        ) * 100
                    })
        
        return cooling_periods

    def analyze_historical_sequence(self, timeframe: str = '1d', lookback_days: int = 365) -> Dict:
        """Analyze historical alt season patterns with improved error handling."""
        try:
            self._ensure_exchange_connection()
            df = self.fetch_top_50_cryptocurrencies()
            if df.empty:
                return {}
                
            historical_data = {}
            failed_symbols = []
            
            for symbol in df['symbol']:
                try:
                    ohlcv = self.active_exchange.fetch_ohlcv(
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
                except ccxt.ExchangeError as e:
                    failed_symbols.append(f"{symbol}: {str(e)}")
                    logger.warning(f"Error fetching data for {symbol}: {str(e)}")
                    continue
            
            if failed_symbols:
                st.warning(f"Unable to fetch data for some symbols:\n{', '.join(failed_symbols)}")
            
            if not historical_data:
                raise ValueError("No historical data available for analysis")
            
            return self._calculate_sequence_metrics(historical_data)
            
        except Exception as e:
            logger.error(f"Error in historical sequence analysis: {str(e)}")
            st.error("Unable to complete historical analysis. Please try again later.")
            return {}

    def analyze_btc_correlation(self, timeframe: str = '1d', lookback_days: int = 90) -> Dict:
        """Analyze correlation between BTC cooling periods and alt movements."""
        try:
            self._ensure_exchange_connection()
            btc_data = self.active_exchange.fetch_ohlcv(
                'BTC/USDT',
                timeframe,
                limit=lookback_days
            )
            
            if not btc_data:
                raise ValueError("No BTC data available for analysis")
                
            btc_df = pd.DataFrame(
                btc_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'], unit='ms')
            
            # Calculate metrics with error checking
            btc_df['sma20'] = btc_df['close'].rolling(20, min_periods=1).mean()
            btc_df['cooling'] = btc_df['close'] < btc_df['sma20']
            
            cooling_periods = self._identify_cooling_periods(btc_df)
            if not cooling_periods:
                st.warning("No cooling periods identified in the analyzed timeframe")
                
            alt_performance = self._calculate_alt_performance(cooling_periods)
            
            return {
                'cooling_periods': cooling_periods,
                'alt_performance': alt_performance,
                'exchange_used': self.active_exchange.id
            }
            
        except ccxt.ExchangeNotAvailable as e:
            logger.error(f"Exchange not available: {str(e)}")
            st.error("Unable to access cryptocurrency exchange. Please try again later.")
            return {}
        except Exception as e:
            logger.error(f"Error in BTC correlation analysis: {str(e)}")
            st.error(f"Error analyzing BTC correlation: {str(e)}")
            return {}

    def _calculate_sequence_metrics(self, historical_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate sequence metrics with improved error handling."""
        metrics = {
            'momentum_scores': {},
            'correlation_matrix': None,
            'phase_indicators': {},
            'entry_points': {},
            'exit_points': {}
        }
        
        try:
            if not historical_data:
                return metrics
                
            # Calculate momentum scores
            for symbol, data in historical_data.items():
                try:
                    close_prices = pd.to_numeric(data['close'], errors='coerce')
                    if close_prices.isnull().all():
                        continue
                        
                    momentum = (
                        (close_prices - close_prices.shift(20)) / 
                        close_prices.shift(20) * 100
                    ).fillna(0)
                    
                    metrics['momentum_scores'][symbol] = momentum.iloc[-1]
                except Exception as e:
                    logger.warning(f"Error calculating momentum for {symbol}: {str(e)}")
                    continue
            
            # Calculate correlation matrix
            try:
                close_prices = pd.DataFrame({
                    symbol: pd.to_numeric(data['close'], errors='coerce')
                    for symbol, data in historical_data.items()
                })
                metrics['correlation_matrix'] = close_prices.corr().fillna(0)
            except Exception as e:
                logger.warning(f"Error calculating correlation matrix: {str(e)}")
            
            # Calculate phase indicators
            for symbol, data in historical_data.items():
                try:
                    volume = pd.to_numeric(data['volume'], errors='coerce')
                    close = pd.to_numeric(data['close'], errors='coerce')
                    
                    if volume.isnull().all() or close.isnull().all():
                        continue
                        
                    metrics['phase_indicators'][symbol] = {
                        'volume_trend': (
                            (volume.rolling(7, min_periods=1).mean() / 
                             volume.rolling(30, min_periods=1).mean() - 1) * 100
                        ).iloc[-1],
                        'price_trend': (
                            (close - close.shift(30)) / 
                            close.shift(30) * 100
                        ).iloc[-1],
                        'volatility': close.pct_change().std() * 100
                    }
                except Exception as e:
                    logger.warning(f"Error calculating phase indicators for {symbol}: {str(e)}")
                    continue
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating sequence metrics: {str(e)}")
            return metrics
    
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
                        ohlcv = self.active_exchange.fetch_ohlcv(
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
    
    def _assign_category(self, rank: int) -> str:
        """Assign category based on market cap rank."""
        if 2 <= rank <= 10:
            return 'Large Cap'
        elif 11 <= rank <= 25:
            return 'Mid Cap'
        else:
            return 'Lower Cap'
    
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
                            for level in [5, 10, 15]  # DCA at 5%, 10%, and 15% drops
                        ]
                    }
                    
                    # Set exit strategy
                    strategy['exit_points'][coin['symbol']] = {
                        'take_profit_levels': [
                            coin['price'] * (1 + level/100)
                            for level in [10, 20, 30]  # Take profits at 10%, 20%, and 30% gains
                        ],
                        'stop_loss': coin['price'] * 0.85  # 15% stop loss
                    }
                    
                    # Calculate risk metrics
                    volatility = df[df['symbol'] == coin['symbol']]['change_24h'].std()
                    momentum = df[df['symbol'] == coin['symbol']]['momentum'].iloc[0]
                    volume_factor = df[df['symbol'] == coin['symbol']]['volume_24h'].iloc[0] / df['volume_24h'].mean()
                    
                    strategy['risk_metrics'][coin['symbol']] = {
                        'volatility': volatility,
                        'momentum_score': momentum,
                        'volume_factor': volume_factor
                    }
            
            return strategy
            
        except Exception as e:
            st.error(f"Error calculating strategy: {str(e)}")
            return {}