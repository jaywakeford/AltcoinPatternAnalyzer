import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
import logging
import requests
import time
from datetime import datetime, timedelta
from functools import partial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_region() -> str:
    """Enhanced region detection with better error handling."""
    try:
        if 'detected_region' in st.session_state:
            return st.session_state.detected_region

        services = [
            'https://ipapi.co/json/',
            'https://ip-api.com/json/',
            'https://ipwhois.app/json/'
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    
                    region = (
                        data.get('country_code') or 
                        data.get('countryCode') or 
                        'GLOBAL'
                    )
                    
                    detected_region = 'GLOBAL'
                    if region in ['US', 'CA']:
                        detected_region = 'NA'
                        logger.info(f"North American user detected: {region}")
                    elif region in ['GB', 'IE']:
                        detected_region = 'UK'
                    elif region in ['CH', 'NO', 'SE', 'DK', 'FI'] or data.get('continent_code') == 'EU':
                        detected_region = 'EU'
                    elif region in ['CN', 'JP', 'KR', 'SG', 'HK', 'IN']:
                        detected_region = 'ASIA'
                    
                    st.session_state.detected_region = detected_region
                    logger.info(f"Region detected: {detected_region} (Country: {region})")
                    return detected_region
                    
            except Exception as e:
                logger.warning(f"Error with geolocation service {service}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error detecting region: {str(e)}")
    
    return 'GLOBAL'

# Enhanced cryptocurrency symbol mapping with alternatives and regional fallbacks
CRYPTO_SYMBOLS = {
    'bitcoin': {
        'primary': 'BTC/USDT',
        'alternatives': ['BTC/USD', 'BTC/USDC'],
        'regional_pairs': {
            'NA': ['BTC/USD', 'BTC/USDC'],
            'EU': ['BTC/EUR', 'BTC/USDT'],
            'ASIA': ['BTC/USDT', 'BTC/JPY']
        },
        'coingecko_id': 'bitcoin'
    },
    'ethereum': {
        'primary': 'ETH/USDT',
        'alternatives': ['ETH/USD', 'ETH/USDC'],
        'regional_pairs': {
            'NA': ['ETH/USD', 'ETH/USDC'],
            'EU': ['ETH/EUR', 'ETH/USDT'],
            'ASIA': ['ETH/USDT', 'ETH/JPY']
        },
        'coingecko_id': 'ethereum'
    }
}

class ExchangeManager:
    def __init__(self):
        self.exchanges = {}
        self.fallback_sources = []
        self.connection_status = {}
        self.retry_delays = [1, 2, 4]  # Exponential backoff
        self.region = detect_region()
        self._initialize_exchanges()

    def _initialize_exchanges(self):
        """Initialize exchanges with enhanced error handling and fallback mechanisms."""
        exchange_ids = self._get_region_optimized_exchanges()
        
        for exchange_id in exchange_ids:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 30000,
                    'enableLastJsonResponse': True,
                })
                
                # Test connection with retry mechanism
                self._test_exchange_connection(exchange, exchange_id)
                
            except Exception as e:
                self._handle_exchange_error(exchange_id, e)

        # Initialize fallback sources
        self._initialize_fallback_sources()

    def _get_region_optimized_exchanges(self) -> List[str]:
        """Get region-optimized list of exchanges."""
        regional_exchanges = {
            'NA': ['kraken', 'kucoin'],  # North America optimized
            'EU': ['kraken', 'kucoin'],  # Europe optimized
            'ASIA': ['kucoin', 'kraken'],  # Asia optimized
            'GLOBAL': ['kraken', 'kucoin']  # Global fallback
        }
        return regional_exchanges.get(self.region, regional_exchanges['GLOBAL'])

    def _test_exchange_connection(self, exchange: ccxt.Exchange, exchange_id: str):
        """Test exchange connection with retry mechanism."""
        last_error = None
        
        for delay in self.retry_delays:
            try:
                exchange.load_markets()
                self.exchanges[exchange_id] = exchange
                self.connection_status[exchange_id] = {
                    'status': 'available',
                    'last_checked': datetime.now(),
                    'features': self._get_exchange_features(exchange),
                    'reliability': 0.95,
                    'response_time': 0.5,
                    'regions': ['GLOBAL', self.region]
                }
                logger.info(f"Successfully initialized {exchange_id}")
                return
            except ccxt.RequestTimeout:
                last_error = f"Timeout connecting to {exchange_id}"
                time.sleep(delay)
            except Exception as e:
                last_error = str(e)
                break
                
        if last_error:
            raise Exception(last_error)

    def _get_exchange_features(self, exchange: ccxt.Exchange) -> List[str]:
        """Get supported features for an exchange."""
        features = ['spot']
        if getattr(exchange, 'has', {}).get('margin'):
            features.append('margin')
        if getattr(exchange, 'has', {}).get('future'):
            features.append('futures')
        return features

    def _handle_exchange_error(self, exchange_id: str, error: Exception):
        """Handle exchange initialization errors."""
        error_msg = str(error)
        status = 'unavailable'
        
        if isinstance(error, ccxt.ExchangeNotAvailable):
            status = 'unavailable'
        elif isinstance(error, ccxt.AuthenticationError):
            status = 'restricted'
        elif isinstance(error, ccxt.ExchangeError):
            status = 'error'
        
        self.connection_status[exchange_id] = {
            'status': status,
            'last_checked': datetime.now(),
            'error': error_msg,
            'regions': []
        }
        logger.warning(f"Error initializing {exchange_id}: {error_msg}")

    def _initialize_fallback_sources(self):
        """Initialize fallback data sources with enhanced retry mechanism."""
        MAX_RETRIES = 3
        
        for attempt in range(MAX_RETRIES):
            try:
                cg = CoinGeckoAPI()
                # Test connection
                cg.ping()
                self.fallback_sources.append(('coingecko', cg))
                logger.info("Successfully initialized CoinGecko as fallback source")
                break
            except Exception as e:
                delay = self.retry_delays[min(attempt, len(self.retry_delays)-1)]
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} to initialize CoinGecko failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(delay)
                else:
                    logger.error("All attempts to initialize CoinGecko failed")

    def get_market_data(self, symbol: str, timeframe: str = '1d', limit: int = 30) -> Tuple[Optional[pd.DataFrame], str]:
        """Get market data with enhanced fallback mechanism and regional optimization."""
        errors = []
        
        # Try primary exchange for the region
        regional_exchanges = self._get_region_optimized_exchanges()
        for exchange_id in regional_exchanges:
            if exchange_id in self.exchanges:
                try:
                    data = self._fetch_market_data(self.exchanges[exchange_id], symbol, timeframe, limit)
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        return data, exchange_id
                except Exception as e:
                    errors.append(f"{exchange_id}: {str(e)}")
        
        # Try alternative symbols based on region
        coin_id = next((k for k, v in CRYPTO_SYMBOLS.items() if v['primary'] == symbol), None)
        if coin_id and coin_id in CRYPTO_SYMBOLS:
            regional_pairs = CRYPTO_SYMBOLS[coin_id]['regional_pairs'].get(self.region, CRYPTO_SYMBOLS[coin_id]['alternatives'])
            
            for alt_symbol in regional_pairs:
                for exchange_id, exchange in self.exchanges.items():
                    try:
                        data = self._fetch_market_data(exchange, alt_symbol, timeframe, limit)
                        if isinstance(data, pd.DataFrame) and not data.empty:
                            return data, exchange_id
                    except Exception as e:
                        errors.append(f"{exchange_id} ({alt_symbol}): {str(e)}")

        # Try fallback sources
        for source_name, source in self.fallback_sources:
            try:
                data = self._fetch_coingecko_data(symbol, limit)
                if isinstance(data, pd.DataFrame) and not data.empty:
                    return data, 'coingecko'
            except Exception as e:
                errors.append(f"{source_name}: {str(e)}")

        error_msg = "Failed to fetch market data. Errors: " + "; ".join(errors)
        logger.error(error_msg)
        return None, "none"

    def _fetch_market_data(self, exchange: ccxt.Exchange, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        """Fetch market data with timeout and retry mechanism."""
        for delay in self.retry_delays:
            try:
                data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                if not data:
                    continue
                    
                df = pd.DataFrame(
                    data,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df
                
            except ccxt.RequestTimeout:
                time.sleep(delay)
                continue
            except Exception as e:
                logger.warning(f"Error fetching data from {exchange.id}: {str(e)}")
                break
                
        return None

    def _fetch_coingecko_data(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """Fetch data from CoinGecko with enhanced error handling."""
        try:
            coin_id = next((k for k, v in CRYPTO_SYMBOLS.items() if v['primary'] == symbol), None)
            if not coin_id:
                logger.warning(f"No CoinGecko ID found for symbol {symbol}")
                return None

            source = next((s[1] for s in self.fallback_sources if s[0] == 'coingecko'), None)
            if not source:
                logger.warning("CoinGecko source not initialized")
                return None

            for delay in self.retry_delays:
                try:
                    data = source.get_coin_market_chart_by_id(
                        id=CRYPTO_SYMBOLS[coin_id]['coingecko_id'],
                        vs_currency='usd',
                        days=days
                    )
                    
                    if not data or 'prices' not in data:
                        time.sleep(delay)
                        continue

                    df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    if 'total_volumes' in data:
                        df['volume'] = [v[1] for v in data['total_volumes']]
                    
                    return df
                    
                except Exception:
                    if delay == self.retry_delays[-1]:  # Last retry
                        raise
                    time.sleep(delay)
                    continue

        except Exception as e:
            logger.error(f"Error fetching data from CoinGecko: {str(e)}")
            return None

# Export singleton instance
exchange_manager = ExchangeManager()

def get_crypto_data(coin_id: str, days: str = '30') -> pd.DataFrame:
    """Fetch cryptocurrency data with enhanced fallback mechanism."""
    try:
        symbols = CRYPTO_SYMBOLS.get(coin_id.lower())
        if not symbols:
            raise ValueError(f"Unsupported cryptocurrency: {coin_id}")

        data, source = exchange_manager.get_market_data(
            symbols['primary'],
            limit=int(days)
        )
        
        if isinstance(data, pd.DataFrame) and not data.empty:
            st.session_state.data_source = source
            return data
            
        return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

def get_exchange_status() -> Dict[str, Dict[str, Any]]:
    """Get detailed status of all exchanges."""
    return exchange_manager.connection_status
