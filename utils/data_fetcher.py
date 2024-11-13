import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any, List
import logging
import requests
import time
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
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

# Enhanced exchange configurations with improved regional optimization
EXCHANGE_CONFIGS = {
    'kraken': {
        'rateLimit': {
            'NA': 2000,
            'EU': 2000,
            'ASIA': 3000,
            'GLOBAL': 3000
        },
        'timeout': {
            'NA': 20000,
            'EU': 20000,
            'ASIA': 30000,
            'GLOBAL': 30000
        },
        'regions': ['NA', 'EU', 'UK', 'GLOBAL'],
        'reliability': 0.95,
        'features': ['spot', 'margin'],
        'endpoints': {
            'NA': 'api.kraken.com',
            'EU': 'eu.kraken.com',
            'UK': 'uk.kraken.com',
            'GLOBAL': 'api.kraken.com'
        },
        'fallback_priority': 1
    },
    'kucoin': {
        'rateLimit': {
            'ASIA': 1500,
            'NA': 2000,
            'GLOBAL': 2500
        },
        'timeout': {
            'ASIA': 20000,
            'NA': 25000,
            'GLOBAL': 30000
        },
        'regions': ['ASIA', 'NA', 'GLOBAL'],
        'reliability': 0.90,
        'features': ['spot', 'margin', 'futures'],
        'endpoints': {
            'ASIA': 'api-asia.kucoin.com',
            'NA': 'api.kucoin.com',
            'GLOBAL': 'api.kucoin.com'
        },
        'fallback_priority': 2
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

def get_optimal_exchange_config(exchange_id: str, region: str) -> Dict:
    """Get optimized exchange configuration based on region."""
    config = EXCHANGE_CONFIGS.get(exchange_id, {})
    
    rate_limit = (
        config.get('rateLimit', {}).get(region) or 
        config.get('rateLimit', {}).get('GLOBAL', 3000)
    )
    
    timeout = (
        config.get('timeout', {}).get(region) or 
        config.get('timeout', {}).get('GLOBAL', 30000)
    )
    
    endpoint = (
        config.get('endpoints', {}).get(region) or 
        config.get('endpoints', {}).get('GLOBAL')
    )
    
    return {
        'enableRateLimit': True,
        'timeout': timeout,
        'rateLimit': rate_limit,
        'hostname': endpoint,
        'options': {
            'adjustForTimeDifference': True,
            'recvWindow': 60000,
            'defaultType': 'spot',
            'createMarketBuyOrderRequiresPrice': False
        }
    }

class ExchangeManager:
    def __init__(self):
        self.exchanges = {}
        self.fallback_sources = []
        self.region = detect_region()
        self.connection_status = {}
        self._initialize_exchanges()

    def _initialize_exchanges(self):
        """Initialize exchanges with enhanced error handling and fallback mechanisms."""
        sorted_exchanges = sorted(
            EXCHANGE_CONFIGS.items(),
            key=lambda x: (x[1]['fallback_priority'], -x[1]['reliability'])
        )

        for exchange_id, config in sorted_exchanges:
            try:
                if self.region not in config['regions'] and 'GLOBAL' not in config['regions']:
                    logger.info(f"Skipping {exchange_id} - not available in {self.region}")
                    continue

                exchange_config = get_optimal_exchange_config(exchange_id, self.region)
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class(exchange_config)

                # Test connection with retry mechanism
                self._test_exchange_connection(exchange)
                
                # Add metadata
                exchange.region = self.region
                exchange.reliability = config['reliability']
                exchange.features = config['features']
                
                self.exchanges[exchange_id] = exchange
                self.connection_status[exchange_id] = {
                    'status': 'available',
                    'last_checked': datetime.now(),
                    'features': config['features'],
                    'reliability': config['reliability']
                }
                
                logger.info(f"Successfully initialized {exchange_id}")
                
            except Exception as e:
                logger.warning(f"Error initializing {exchange_id}: {str(e)}")
                self.connection_status[exchange_id] = {
                    'status': 'unavailable',
                    'last_checked': datetime.now(),
                    'error': str(e)
                }

        # Initialize fallback sources
        self._initialize_fallback_sources()

    def _test_exchange_connection(self, exchange, max_retries=3):
        """Test exchange connection with retry mechanism."""
        retry_delay = 1
        last_error = None

        for attempt in range(max_retries):
            try:
                exchange.load_markets()
                return True
            except ccxt.NetworkError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                continue
            except Exception as e:
                raise e

        if last_error:
            raise last_error

    def _initialize_fallback_sources(self):
        """Initialize fallback data sources."""
        try:
            cg = CoinGeckoAPI()
            cg.ping()  # Test connection
            self.fallback_sources.append(('coingecko', cg))
            logger.info("Successfully initialized CoinGecko as fallback source")
        except Exception as e:
            logger.warning(f"Error initializing CoinGecko: {str(e)}")

    async def get_market_data(self, symbol: str, timeframe: str = '1d', limit: int = 30):
        """Get market data with enhanced fallback mechanism."""
        errors = []
        
        # Try primary exchanges first
        for exchange_id, exchange in self.exchanges.items():
            try:
                if self.connection_status[exchange_id]['status'] == 'available':
                    data = await self._fetch_market_data(exchange, symbol, timeframe, limit)
                    if data is not None:
                        return data, exchange_id
            except Exception as e:
                errors.append(f"{exchange_id}: {str(e)}")
                continue

        # Try fallback sources if primary exchanges fail
        for source_name, source in self.fallback_sources:
            try:
                if source_name == 'coingecko':
                    data = self._fetch_coingecko_data(symbol, limit)
                    if data is not None:
                        return data, 'coingecko'
            except Exception as e:
                errors.append(f"{source_name}: {str(e)}")
                continue

        raise Exception(f"Failed to fetch market data. Errors: {'; '.join(errors)}")

    async def _fetch_market_data(self, exchange, symbol: str, timeframe: str, limit: int):
        """Fetch market data from exchange with timeout handling."""
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                data = await loop.run_in_executor(
                    pool,
                    partial(exchange.fetch_ohlcv, symbol, timeframe, limit=limit)
                )
                return pd.DataFrame(
                    data,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
        except Exception as e:
            logger.warning(f"Error fetching data from {exchange.id}: {str(e)}")
            return None

    def _fetch_coingecko_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch data from CoinGecko."""
        try:
            coin_id = next(
                (v['coingecko_id'] for k, v in CRYPTO_SYMBOLS.items() 
                 if v['primary'].startswith(symbol.split('/')[0])),
                None
            )
            if not coin_id:
                raise ValueError(f"No CoinGecko ID found for symbol {symbol}")

            source = self.fallback_sources[0][1]  # CoinGecko instance
            data = source.get_coin_market_chart_by_id(
                id=coin_id,
                vs_currency='usd',
                days=days
            )

            if data:
                df = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df

        except Exception as e:
            logger.error(f"Error fetching data from CoinGecko: {str(e)}")
            return None

    def get_exchange_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed status of all exchanges."""
        current_time = datetime.now()
        status_update = {}

        for exchange_id, exchange in self.exchanges.items():
            try:
                if (current_time - self.connection_status[exchange_id]['last_checked']).total_seconds() > 300:
                    # Test connection if last check was more than 5 minutes ago
                    self._test_exchange_connection(exchange)
                    self.connection_status[exchange_id]['last_checked'] = current_time
                    self.connection_status[exchange_id]['status'] = 'available'
            except Exception as e:
                self.connection_status[exchange_id].update({
                    'status': 'unavailable',
                    'last_checked': current_time,
                    'error': str(e)
                })

            status_update[exchange_id] = self.connection_status[exchange_id]

        return status_update

# Export singleton instance
exchange_manager = ExchangeManager()

async def get_crypto_data(coin_id: str, days: str = '30') -> pd.DataFrame:
    """Fetch cryptocurrency data with enhanced fallback mechanism."""
    try:
        symbols = CRYPTO_SYMBOLS.get(coin_id.lower())
        if not symbols:
            raise ValueError(f"Unsupported cryptocurrency: {coin_id}")

        data, source = await exchange_manager.get_market_data(
            symbols['primary'],
            limit=int(days)
        )
        
        if data is not None:
            data['source'] = source
            return data
            
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        st.error(f"Error fetching market data: {str(e)}")
    
    return pd.DataFrame()

def get_exchange_status() -> Dict[str, Dict[str, Any]]:
    """Get detailed status of all exchanges."""
    return exchange_manager.get_exchange_status()
