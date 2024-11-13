import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cryptocurrency symbol mapping
CRYPTO_SYMBOLS = {
    'bitcoin': 'BTC/USDT',
    'ethereum': 'ETH/USDT',
    'cardano': 'ADA/USDT',
    'binancecoin': 'BNB/USDT',
    'solana': 'SOL/USDT'
}

# Exchange configurations
EXCHANGE_CONFIGS = {
    'kraken': {
        'rateLimit': 3000,
        'timeout': 30000,
        'region': 'North America',
        'options': {'adjustForTimeDifference': True}
    },
    'coinbase': {
        'rateLimit': 4000,
        'timeout': 30000,
        'region': 'North America',
        'options': {'adjustForTimeDifference': True}
    },
    'kucoin': {
        'rateLimit': 2000,
        'timeout': 30000,
        'region': 'Global',
        'options': {'adjustForTimeDifference': True}
    },
    'binance': {
        'rateLimit': 1500,
        'timeout': 30000,
        'region': 'Global',
        'options': {'adjustForTimeDifference': True}
    }
}

# Initialize APIs
cg = CoinGeckoAPI()

def get_exchange_symbol(exchange_id: str, base_symbol: str) -> str:
    """Convert base symbol to exchange-specific format."""
    try:
        if not base_symbol:
            raise ValueError("Invalid base symbol")
        
        if exchange_id == 'kucoin':
            return base_symbol.replace('/', '-')
        return base_symbol
    except Exception as e:
        logger.warning(f"Symbol conversion error for {exchange_id}: {str(e)}")
        return base_symbol

def init_exchanges() -> List[ccxt.Exchange]:
    """Initialize multiple cryptocurrency exchanges with improved error handling."""
    exchanges = []
    # Prioritize North American exchanges
    exchange_ids = ['kraken', 'coinbase', 'kucoin', 'binance']
    
    for exchange_id in exchange_ids:
        try:
            config = EXCHANGE_CONFIGS.get(exchange_id, {})
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'enableRateLimit': True,
                'timeout': config.get('timeout', 30000),
                'rateLimit': config.get('rateLimit', 2000),
                'options': config.get('options', {})
            })
            
            # Test API access
            exchange.fetch_markets()
            exchanges.append(exchange)
            logger.info(f"Successfully connected to {exchange_id} ({config.get('region', 'Unknown')})")
            
        except ccxt.NetworkError as e:
            logger.error(f"Network error connecting to {exchange_id}: {str(e)}")
            st.warning(f"Network connectivity issues with {exchange_id}. Trying alternative exchanges...")
            
        except ccxt.ExchangeNotAvailable as e:
            logger.error(f"{exchange_id} is not available in your region ({config.get('region')}): {str(e)}")
            st.warning(f"{exchange_id} is not available in your region. Trying alternative exchanges...")
            
        except ccxt.AuthenticationError as e:
            logger.error(f"Authentication error with {exchange_id}: {str(e)}")
            st.warning(f"Authentication failed for {exchange_id}. Trying alternative exchanges...")
            
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error with {exchange_id}: {str(e)}")
            st.warning(f"Error accessing {exchange_id}. Trying alternative exchanges...")
            
        except Exception as e:
            logger.error(f"Unexpected error with {exchange_id}: {str(e)}")
            st.warning(f"Unexpected error with {exchange_id}. Trying alternative exchanges...")
    
    if not exchanges:
        error_message = (
            "Unable to connect to any cryptocurrency exchange. "
            "This might be due to regional restrictions or network issues. "
            "Please try again later or contact support."
        )
        logger.error(error_message)
        raise ccxt.ExchangeNotAvailable(error_message)
    
    return exchanges

# Initialize exchanges
exchanges = init_exchanges()

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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_crypto_data(coin_id: str, days: str) -> pd.DataFrame:
    """Fetch cryptocurrency data using CoinGecko API."""
    try:
        # Convert days to integer
        days_int = int(days) if days else 30
        
        data = cg.get_coin_market_chart_by_id(
            id=coin_id.lower(),
            vs_currency='usd',
            days=days_int
        )
        
        if data:
            df = pd.DataFrame({
                'timestamp': [pd.to_datetime(ts, unit='ms') for ts, _ in data['prices']],
                'price': [p for _, p in data['prices']],
                'volume': [v for _, v in data['total_volumes']]
            })
            
            df.set_index('timestamp', inplace=True)
            
            # Get Bitcoin dominance
            btc_dominance_df = get_bitcoin_dominance(days)
            if not btc_dominance_df.empty:
                df['btc_dominance'] = btc_dominance_df['btc_dominance']
            
            return df
            
    except Exception as e:
        logger.error(f"Error fetching crypto data: {str(e)}")
        st.error(f"Error fetching market data: {str(e)}")
    
    return pd.DataFrame()

def get_bitcoin_dominance(days: str) -> pd.DataFrame:
    """Get Bitcoin market dominance data."""
    try:
        global_data = cg.get_global()
        
        if not global_data or 'market_cap_percentage' not in global_data:
            raise Exception("Invalid market data format")
        
        btc_dominance = global_data['market_cap_percentage']['btc']
        
        # Create time series for the specified days
        days_int = int(days) if days else 30
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=days_int,
            freq='D'
        )
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'btc_dominance': [btc_dominance] * len(timestamps)
        })
        
        df.set_index('timestamp', inplace=True)
        return df
        
    except Exception as e:
        logger.error(f"Error fetching Bitcoin dominance: {str(e)}")
        return pd.DataFrame()

def _handle_api_error(error: Exception) -> str:
    """Handle API errors with detailed error messages."""
    error_msg = str(error)
    if "429" in error_msg:
        return "Rate limit exceeded. Please wait a few minutes and try again."
    elif "404" in error_msg:
        return "Data not found. The requested cryptocurrency might not be supported."
    elif "connection" in error_msg.lower():
        return "Network connection error. Please check your internet connection and try again."
    elif "forbidden" in error_msg.lower() or "restricted" in error_msg.lower():
        return "Access denied. The service might be restricted in your region."
    elif "timeout" in error_msg.lower():
        return "Request timed out. The server might be experiencing high load."
    else:
        return f"API error: {error_msg}. Please try again later."

@st.cache_data(ttl=300)
def get_bitcoin_dominance(days: str) -> pd.DataFrame:
    """Calculate Bitcoin dominance using CoinGecko global market data."""
    try:
        global_data = retry_api_call(
            lambda: cg.get_global()
        )

        if not global_data or 'market_cap_percentage' not in global_data:
            raise Exception("Invalid market data format")

        btc_dominance = global_data['market_cap_percentage']['btc']
        
        # Create time series for the last N days
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=int(days),
            freq='D'
        )
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'btc_dominance': [btc_dominance] * len(timestamps)
        })
        
        df.set_index('timestamp', inplace=True)
        return df[['btc_dominance']]
        
    except Exception as e:
        error_msg = _handle_api_error(e)
        st.error(error_msg)
        logger.error(f"Bitcoin dominance data error: {error_msg}")
        return pd.DataFrame({'btc_dominance': []})