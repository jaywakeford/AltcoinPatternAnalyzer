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

# Enhanced cryptocurrency symbol mapping with alternatives and fallbacks
CRYPTO_SYMBOLS = {
    'bitcoin': {
        'primary': 'BTC/USDT',
        'alternatives': ['BTC/USD', 'BTC/USDC'],
        'coingecko_id': 'bitcoin'
    },
    'ethereum': {
        'primary': 'ETH/USDT',
        'alternatives': ['ETH/USD', 'ETH/USDC'],
        'coingecko_id': 'ethereum'
    },
    'binancecoin': {
        'primary': 'BNB/USDT',
        'alternatives': ['BNB/USD', 'BNB/USDC'],
        'coingecko_id': 'binancecoin'
    },
    'cardano': {
        'primary': 'ADA/USDT',
        'alternatives': ['ADA/USD', 'ADA/USDC'],
        'coingecko_id': 'cardano'
    },
    'solana': {
        'primary': 'SOL/USDT',
        'alternatives': ['SOL/USD', 'SOL/USDC'],
        'coingecko_id': 'solana'
    }
}

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

class ExchangeManager:
    def __init__(self):
        self.exchanges = {}
        self.fallback_sources = []
        self.connection_status = {}
        self.region = detect_region()
        self._initialize_exchanges()

    def _initialize_exchanges(self):
        """Initialize exchanges with enhanced error handling and fallback mechanisms."""
        exchange_ids = ['kraken', 'kucoin']
        
        for exchange_id in exchange_ids:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 30000,
                    'enableLastJsonResponse': True,
                })
                
                # Test connection with retry
                retry_count = 3
                while retry_count > 0:
                    try:
                        exchange.load_markets()
                        self.exchanges[exchange_id] = exchange
                        self.connection_status[exchange_id] = {
                            'status': 'available',
                            'last_checked': datetime.now(),
                            'features': ['spot', 'margin'],
                            'reliability': 0.95,
                            'response_time': 0.5,
                            'regions': ['GLOBAL', self.region]
                        }
                        logger.info(f"Successfully initialized {exchange_id}")
                        break
                    except ccxt.RequestTimeout:
                        retry_count -= 1
                        if retry_count == 0:
                            raise
                        time.sleep(1)
                    except Exception:
                        raise
                
            except ccxt.ExchangeNotAvailable as e:
                logger.warning(f"Exchange {exchange_id} not available: {str(e)}")
                self.connection_status[exchange_id] = {
                    'status': 'unavailable',
                    'last_checked': datetime.now(),
                    'error': f"Service unavailable: {str(e)}",
                    'regions': []
                }
            except ccxt.ExchangeError as e:
                logger.warning(f"Error with {exchange_id}: {str(e)}")
                self.connection_status[exchange_id] = {
                    'status': 'restricted',
                    'last_checked': datetime.now(),
                    'error': f"Access restricted: {str(e)}",
                    'regions': []
                }
            except Exception as e:
                logger.error(f"Unexpected error with {exchange_id}: {str(e)}")
                self.connection_status[exchange_id] = {
                    'status': 'error',
                    'last_checked': datetime.now(),
                    'error': str(e),
                    'regions': []
                }

        # Initialize fallback sources
        self._initialize_fallback_sources()

    def _initialize_fallback_sources(self):
        """Initialize fallback data sources with retry mechanism."""
        MAX_RETRIES = 3
        RETRY_DELAY = 1

        for attempt in range(MAX_RETRIES):
            try:
                cg = CoinGeckoAPI()
                # Test connection
                cg.ping()
                self.fallback_sources.append(('coingecko', cg))
                logger.info("Successfully initialized CoinGecko as fallback source")
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} to initialize CoinGecko failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
                else:
                    logger.error("All attempts to initialize CoinGecko failed")

    def get_market_data(self, symbol: str, timeframe: str = '1d', limit: int = 30) -> Tuple[Optional[pd.DataFrame], str]:
        """Get market data with enhanced fallback mechanism."""
        errors = []
        
        # Try primary exchanges first
        for exchange_id, exchange in self.exchanges.items():
            try:
                if self.connection_status[exchange_id]['status'] == 'available':
                    data = self._fetch_market_data(exchange, symbol, timeframe, limit)
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        st.session_state.data_source = exchange_id
                        return data, exchange_id
            except Exception as e:
                errors.append(f"{exchange_id}: {str(e)}")
                continue

        # Try alternative symbols if primary fails
        coin_id = next((k for k, v in CRYPTO_SYMBOLS.items() if v['primary'] == symbol), None)
        if coin_id:
            for alt_symbol in CRYPTO_SYMBOLS[coin_id]['alternatives']:
                for exchange_id, exchange in self.exchanges.items():
                    try:
                        if self.connection_status[exchange_id]['status'] == 'available':
                            data = self._fetch_market_data(exchange, alt_symbol, timeframe, limit)
                            if isinstance(data, pd.DataFrame) and not data.empty:
                                st.session_state.data_source = exchange_id
                                return data, exchange_id
                    except Exception as e:
                        errors.append(f"{exchange_id} ({alt_symbol}): {str(e)}")
                        continue

        # Try fallback sources if all exchanges fail
        for source_name, source in self.fallback_sources:
            try:
                if source_name == 'coingecko':
                    data = self._fetch_coingecko_data(symbol, limit)
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        st.session_state.data_source = 'coingecko'
                        return data, 'coingecko'
            except Exception as e:
                errors.append(f"{source_name}: {str(e)}")
                continue

        error_msg = "Failed to fetch market data. Errors: " + "; ".join(errors)
        logger.error(error_msg)
        return None, "none"

    def _fetch_market_data(self, exchange, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        """Fetch market data from exchange with timeout and error handling."""
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not data:
                return None
                
            df = pd.DataFrame(
                data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logger.warning(f"Error fetching data from {exchange.id}: {str(e)}")
            return None

    def _fetch_coingecko_data(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """Fetch data from CoinGecko with enhanced error handling."""
        try:
            # Extract coin ID from symbol
            coin_id = next(
                (k for k, v in CRYPTO_SYMBOLS.items() if v['primary'] == symbol),
                None
            )
            
            if not coin_id:
                logger.warning(f"No CoinGecko ID found for symbol {symbol}")
                return None

            source = next((s[1] for s in self.fallback_sources if s[0] == 'coingecko'), None)
            if not source:
                logger.warning("CoinGecko source not initialized")
                return None

            data = source.get_coin_market_chart_by_id(
                id=coin_id,
                vs_currency='usd',
                days=days
            )

            if not data or 'prices' not in data:
                logger.warning("Invalid data received from CoinGecko")
                return None

            df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            if 'volume' in data:
                df['volume'] = [v[1] for v in data['volume']]
            
            return df

        except Exception as e:
            logger.error(f"Error fetching data from CoinGecko: {str(e)}")
            return None

    def get_exchange_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed status of all exchanges with health checks."""
        current_time = datetime.now()
        status_update = {}

        for exchange_id, exchange in self.exchanges.items():
            try:
                # Check if we need to refresh status (every 5 minutes)
                if (current_time - self.connection_status[exchange_id]['last_checked']).total_seconds() > 300:
                    start_time = time.time()
                    exchange.fetch_status()
                    response_time = time.time() - start_time
                    
                    self.connection_status[exchange_id].update({
                        'status': 'available',
                        'last_checked': current_time,
                        'response_time': response_time,
                        'reliability': min(1.0, self.connection_status[exchange_id].get('reliability', 0.95) + 0.01)
                    })
                    
            except Exception as e:
                self.connection_status[exchange_id].update({
                    'status': 'unavailable',
                    'last_checked': current_time,
                    'error': str(e),
                    'reliability': max(0.0, self.connection_status[exchange_id].get('reliability', 0.95) - 0.05)
                })

            status_update[exchange_id] = self.connection_status[exchange_id]

        return status_update

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
    return exchange_manager.get_exchange_status()
