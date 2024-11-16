import os
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
import asyncio
from .websocket_manager import websocket_manager, ConnectionState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cryptocurrency symbol mapping
CRYPTO_SYMBOLS = {
    'bitcoin': {
        'primary': 'BTC/USDT',
        'alternatives': ['BTC/USD', 'XBT/USD'],
        'regional_pairs': {
            'NA': ['BTC/USD', 'BTC/USDT'],
            'EU': ['BTC/EUR', 'BTC/USDT'],
            'ASIA': ['BTC/USDT', 'BTC/JPY']
        },
        'coingecko_id': 'bitcoin'
    },
    'ethereum': {
        'primary': 'ETH/USDT',
        'alternatives': ['ETH/USD', 'ETH/BTC'],
        'regional_pairs': {
            'NA': ['ETH/USD', 'ETH/USDT'],
            'EU': ['ETH/EUR', 'ETH/USDT'],
            'ASIA': ['ETH/USDT', 'ETH/JPY']
        },
        'coingecko_id': 'ethereum'
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
                    elif region in ['GB', 'DE', 'FR', 'IT', 'ES']:
                        detected_region = 'EU'
                    elif region in ['JP', 'KR', 'CN', 'HK', 'SG']:
                        detected_region = 'ASIA'
                    
                    st.session_state.detected_region = detected_region
                    logger.info(f"Detected region: {detected_region}")
                    return detected_region
                    
            except Exception as e:
                logger.warning(f"Error with geolocation service {service}: {str(e)}")
                continue
                
        # Default to GLOBAL if all services fail
        logger.warning("Unable to detect region, defaulting to GLOBAL")
        return 'GLOBAL'
        
    except Exception as e:
        logger.error(f"Error in region detection: {str(e)}")
        return 'GLOBAL'

class ExchangeManager:
    def __init__(self):
        self.exchanges = {}
        self.fallback_sources = []
        self.connection_status = {}
        self.retry_delays = [1, 2, 4]  # Exponential backoff
        self.region = detect_region()
        self.websocket_enabled = False
        self.websocket_callbacks = {}
        self.active_exchange = None
        self._initialize_exchange()

    @property
    def current_exchange(self) -> Optional[str]:
        """Get the current active exchange ID."""
        return self.active_exchange.id if self.active_exchange else None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with proper cleanup."""
        await self.cleanup()

    def _initialize_exchange(self):
        """Initialize exchange with fallback options."""
        exchange_errors = []
        
        # Get API keys from environment variables
        api_key = os.getenv("KRAKEN_API_KEY")
        api_secret = os.getenv("KRAKEN_SECRET")
        
        for exchange_id in self._get_region_optimized_exchanges():
            try:
                exchange_class = getattr(ccxt, exchange_id)
                
                # Configure exchange with or without authentication
                exchange_config = {
                    'enableRateLimit': True,
                    'timeout': 30000
                }
                
                # Add API keys if available
                if api_key and api_secret and exchange_id == 'kraken':
                    exchange_config.update({
                        'apiKey': api_key,
                        'secret': api_secret
                    })
                    logger.info(f"Initializing {exchange_id} with API key authentication")
                else:
                    logger.info(f"Initializing {exchange_id} with public API endpoints only")
                
                exchange = exchange_class(exchange_config)
                
                # Test API access
                exchange.load_markets()
                self.active_exchange = exchange
                self.exchanges[exchange_id] = exchange
                
                # Update connection status with authentication level
                self.connection_status[exchange_id] = {
                    'status': 'available',
                    'auth_level': 'authenticated' if api_key and api_secret else 'public',
                    'last_checked': datetime.now()
                }
                
                logger.info(f"Successfully connected to {exchange_id}")
                break
                
            except ccxt.AuthenticationError as e:
                error_msg = (
                    f"Authentication failed for {exchange_id}. "
                    "Please check your API credentials. "
                    f"Error: {str(e)}"
                )
                exchange_errors.append(error_msg)
                logger.warning(error_msg)
                
                # Try to fallback to public API
                try:
                    exchange = exchange_class({
                        'enableRateLimit': True,
                        'timeout': 30000
                    })
                    exchange.load_markets()
                    self.active_exchange = exchange
                    self.exchanges[exchange_id] = exchange
                    logger.info(f"Fallback to public API successful for {exchange_id}")
                    break
                except Exception as e:
                    logger.warning(f"Public API fallback failed for {exchange_id}: {str(e)}")
                    
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

    async def enable_websocket(self, symbol: str, callback: callable) -> None:
        """Enable websocket connection for real-time data with enhanced error handling."""
        try:
            # Ensure exchange is initialized
            if not self.active_exchange:
                self._initialize_exchange()
            
            # Get current exchange ID
            exchange_id = self.current_exchange
            if not exchange_id:
                raise ValueError("No active exchange available")
            
            # Register callback
            self.websocket_callbacks[symbol] = callback
            
            # Connect to websocket
            await websocket_manager.connect(
                symbol=symbol,
                exchange=exchange_id,
                callback=self._handle_websocket_message
            )
            
            self.websocket_enabled = True
            logger.info(f"Enabled websocket for {symbol} on {exchange_id}")
            
        except Exception as e:
            logger.error(f"Error enabling websocket: {str(e)}")
            raise

    async def disable_websocket(self, symbol: str) -> None:
        """Disable websocket connection with proper cleanup."""
        try:
            if symbol in self.websocket_callbacks:
                exchange_id = self.active_exchange.id if self.active_exchange else None
                if exchange_id:
                    await websocket_manager.disconnect(symbol, exchange_id)
                del self.websocket_callbacks[symbol]
                
            self.websocket_enabled = False
            logger.info(f"Disabled websocket for {symbol}")
            
        except Exception as e:
            logger.error(f"Error disabling websocket: {str(e)}")
            raise

    async def _handle_websocket_message(self, message: dict) -> None:
        """Process incoming websocket messages with enhanced error handling."""
        try:
            # Extract symbol from message (format depends on exchange)
            symbol = self._extract_symbol_from_message(message)
            
            if symbol and symbol in self.websocket_callbacks:
                callback = self.websocket_callbacks[symbol]
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
                
        except Exception as e:
            logger.error(f"Error handling websocket message: {str(e)}")

    def _extract_symbol_from_message(self, message: dict) -> Optional[str]:
        """Extract symbol from websocket message based on exchange format."""
        try:
            if isinstance(message, dict):
                if 'pair' in message:  # Kraken format
                    return message['pair'][0] if isinstance(message['pair'], list) else message['pair']
                elif 'symbol' in message:  # KuCoin format
                    return message['symbol']
                elif 'data' in message and isinstance(message['data'], dict):
                    if 'symbol' in message['data']:
                        return message['data']['symbol']
            return None
        except Exception as e:
            logger.error(f"Error extracting symbol from message: {str(e)}")
            return None

    async def cleanup(self) -> None:
        """Cleanup resources including websocket connections with enhanced error handling."""
        try:
            if self.websocket_enabled:
                await websocket_manager.disconnect_all()
                self.websocket_enabled = False
                self.websocket_callbacks.clear()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def get_websocket_status(self, symbol: str) -> ConnectionState:
        """Get the current websocket connection state for a symbol."""
        if self.active_exchange:
            return websocket_manager.get_connection_state(
                symbol=symbol,
                exchange=self.active_exchange.id
            )
        return ConnectionState.DISCONNECTED

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
            timeframe='1d' if int(days) > 7 else '1h',
            limit=int(days) * (24 if int(days) <= 7 else 1)
        )

        if isinstance(data, pd.DataFrame) and not data.empty:
            st.session_state.data_source = source
            return data

        logger.warning(f"No data available from {source}, trying fallback sources...")
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error fetching crypto data: {str(e)}")
        return pd.DataFrame()

def get_exchange_status() -> Dict[str, Dict[str, Any]]:
    """Get detailed status of all exchanges."""
    return exchange_manager.connection_status