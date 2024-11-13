import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any, List
import logging
import requests
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cryptocurrency symbol mapping with alternative symbols
CRYPTO_SYMBOLS = {
    'bitcoin': {
        'primary': 'BTC/USDT',
        'alternatives': ['BTC/USD', 'BTC/USDC']
    },
    'ethereum': {
        'primary': 'ETH/USDT',
        'alternatives': ['ETH/USD', 'ETH/USDC']
    },
    'binancecoin': {
        'primary': 'BNB/USDT',
        'alternatives': ['BNB/USD', 'BNB/USDC']
    },
    'cardano': {
        'primary': 'ADA/USDT',
        'alternatives': ['ADA/USD', 'ADA/USDC']
    },
    'solana': {
        'primary': 'SOL/USDT',
        'alternatives': ['SOL/USD', 'SOL/USDC']
    }
}

# Enhanced exchange configurations with regional optimization
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
        }
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
        }
    }
}

def detect_region() -> str:
    """Enhanced region detection with better Canadian support."""
    try:
        # Check if region is already cached in session state
        if 'detected_region' in st.session_state:
            return st.session_state.detected_region

        # List of geolocation services for redundancy
        services = [
            'https://ipapi.co/json/',
            'https://ip-api.com/json/',
            'https://ipwhois.app/json/',
            'https://geolocation-db.com/json/'
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract region information with multiple field fallbacks
                    region = (
                        data.get('country_code') or 
                        data.get('countryCode') or 
                        data.get('country_code2') or 
                        'GLOBAL'
                    )
                    
                    continent = (
                        data.get('continent_code') or 
                        data.get('continentCode') or 
                        ''
                    )
                    
                    # Enhanced regional mapping with improved Canadian support
                    detected_region = 'GLOBAL'
                    if region in ['US', 'CA']:  # Explicitly handle Canadian users
                        detected_region = 'NA'
                        logger.info(f"North American user detected: {region}")
                    elif region in ['GB', 'IE']:
                        detected_region = 'UK'
                    elif continent == 'EU' or region in ['CH', 'NO', 'SE', 'DK', 'FI']:
                        detected_region = 'EU'
                    elif region in ['CN', 'JP', 'KR', 'SG', 'HK', 'IN', 'VN', 'ID']:
                        detected_region = 'ASIA'
                    elif region in ['AU', 'NZ']:
                        detected_region = 'OCE'
                    
                    # Cache the detected region
                    st.session_state.detected_region = detected_region
                    logger.info(f"Region detected: {detected_region} (Country: {region})")
                    return detected_region
                    
            except Exception as e:
                logger.warning(f"Error with geolocation service {service}: {str(e)}")
                continue
                
    except Exception as e:
        logger.warning(f"Error detecting region: {str(e)}")
    
    return 'GLOBAL'

def get_optimal_exchange_config(exchange_id: str, region: str) -> Dict:
    """Get optimized exchange configuration based on region."""
    config = EXCHANGE_CONFIGS.get(exchange_id, {})
    
    # Get region-specific settings with fallback to global
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

def init_exchanges() -> List[ccxt.Exchange]:
    """Initialize cryptocurrency exchanges with enhanced regional optimization."""
    region = detect_region()
    exchanges = []
    errors = []
    
    # Sort exchanges by reliability for the region
    sorted_exchanges = sorted(
        EXCHANGE_CONFIGS.items(),
        key=lambda x: (
            x[1]['regions'].count(region) > 0,  # Prioritize region-specific exchanges
            x[1].get('reliability', 0)  # Then by reliability
        ),
        reverse=True
    )
    
    logger.info("Skipping Coinbase initialization - exchange removed from configuration")
    
    for exchange_id, config in sorted_exchanges:
        # Skip exchanges not available in the user's region
        if region not in config['regions'] and 'GLOBAL' not in config['regions']:
            logger.info(f"Skipping {exchange_id} - not available in {region}")
            continue
            
        try:
            # Get optimized configuration for the region
            exchange_config = get_optimal_exchange_config(exchange_id, region)
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class(exchange_config)
            
            # Test connection with retry mechanism
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    exchange.load_markets()
                    # Add metadata
                    exchange.region = region
                    exchange.reliability = config['reliability']
                    exchange.features = config['features']
                    
                    exchanges.append(exchange)
                    logger.info(f"Successfully connected to {exchange_id}")
                    break
                    
                except ccxt.ExchangeNotAvailable as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(retry_delay * (2 ** attempt))
                except ccxt.AuthenticationError:
                    # Skip retries for authentication errors
                    raise
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(retry_delay * (2 ** attempt))
            
        except Exception as e:
            error_msg = f"Error initializing {exchange_id}: {str(e)}"
            errors.append(error_msg)
            logger.warning(error_msg)
    
    if not exchanges:
        fallback_msg = (
            f"Limited exchange access in {region}. Using alternative data sources. "
            "This won't affect the platform's analysis capabilities."
        )
        logger.warning(fallback_msg)
        st.warning(fallback_msg)
    
    return exchanges

def get_exchange_status() -> Dict[str, Dict[str, Any]]:
    """Get detailed status of all configured exchanges with regional considerations."""
    status = {}
    region = detect_region()
    start_time = time.time()
    
    for exchange_id, config in EXCHANGE_CONFIGS.items():
        try:
            # Skip exchanges not available in the region
            if region not in config['regions'] and 'GLOBAL' not in config['regions']:
                status[exchange_id] = {
                    'status': 'restricted',
                    'reliability': config['reliability'],
                    'features': config['features'],
                    'regions': config['regions'],
                    'error': f'Exchange not available in {region}'
                }
                continue
            
            # Initialize exchange with region-specific settings
            exchange_config = {
                'timeout': config['timeout'],
                'enableRateLimit': True
            }
            
            if region in config['endpoints']:
                exchange_config['hostname'] = config['endpoints'][region]
            
            exchange = getattr(ccxt, exchange_id)(exchange_config)
            
            # Test basic API functionality
            exchange.fetch_markets()
            
            # Calculate response time
            response_time = time.time() - start_time
            
            status[exchange_id] = {
                'status': 'available',
                'reliability': config['reliability'],
                'features': config['features'],
                'response_time': response_time,
                'regions': config['regions'],
                'endpoint': config['endpoints'].get(region, config['endpoints']['GLOBAL'])
            }
            
        except ccxt.ExchangeNotAvailable:
            status[exchange_id] = {
                'status': 'unavailable',
                'error': 'Exchange is temporarily unavailable',
                'reliability': config['reliability'],
                'features': config['features'],
                'regions': config['regions']
            }
        except ccxt.AuthenticationError:
            status[exchange_id] = {
                'status': 'unavailable',
                'error': 'Authentication required',
                'reliability': config['reliability'],
                'features': config['features'],
                'regions': config['regions']
            }
        except Exception as e:
            status[exchange_id] = {
                'status': 'error',
                'error': str(e),
                'reliability': config['reliability'],
                'features': config['features'],
                'regions': config['regions']
            }
    
    return status

@st.cache_data(ttl=300)
def get_crypto_data(coin_id: str, days: str = '30') -> pd.DataFrame:
    """Fetch cryptocurrency data with enhanced error handling and fallback mechanisms."""
    try:
        symbols = CRYPTO_SYMBOLS.get(coin_id.lower())
        if not symbols:
            raise ValueError(f"Unsupported cryptocurrency: {coin_id}")
        
        if not hasattr(st.session_state, 'exchanges'):
            st.session_state.exchanges = init_exchanges()
        
        # Try each exchange in order of reliability
        for exchange in sorted(st.session_state.exchanges, key=lambda x: x.reliability, reverse=True):
            for symbol in [symbols['primary']] + symbols['alternatives']:
                try:
                    ohlcv = exchange.fetch_ohlcv(
                        symbol,
                        '1d',
                        limit=int(days)
                    )
                    if ohlcv:
                        df = pd.DataFrame(
                            ohlcv,
                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                        )
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('timestamp', inplace=True)
                        df['price'] = df['close']
                        df['exchange'] = exchange.id
                        return df
                except Exception as e:
                    logger.warning(f"Error fetching {symbol} from {exchange.id}: {str(e)}")
                    continue
        
        # Fallback to CoinGecko
        logger.info("Falling back to CoinGecko API")
        cg = CoinGeckoAPI()
        data = cg.get_coin_market_chart_by_id(
            id=coin_id.lower(),
            vs_currency='usd',
            days=int(days)
        )
        
        if data:
            df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df['exchange'] = 'coingecko'
            return df
            
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        st.error(f"Error fetching market data: {str(e)}")
    
    return pd.DataFrame()

def get_bitcoin_dominance(timeframe: str) -> pd.DataFrame:
    """Get Bitcoin dominance data with improved error handling."""
    try:
        cg = CoinGeckoAPI()
        days = int(timeframe) if timeframe.isdigit() else 30
        
        data = retry_api_call(
            lambda: cg.get_global_market_chart(vs_currency='usd', days=days)
        )
        
        if data and 'market_cap_percentage' in data:
            df = pd.DataFrame({
                'timestamp': [pd.to_datetime(ts, unit='ms') for ts, _ in data['market_cap_percentage']],
                'btc_dominance': [v for _, v in data['market_cap_percentage']]
            })
            df.set_index('timestamp', inplace=True)
            return df
            
    except Exception as e:
        logger.error(f"Error fetching Bitcoin dominance: {str(e)}")
        st.error(f"Error fetching dominance data: {str(e)}")
    
    return pd.DataFrame()

def retry_api_call(func, max_retries=3, delay=1):
    """Retry API calls with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay * (2 ** attempt))
            continue
    return None
