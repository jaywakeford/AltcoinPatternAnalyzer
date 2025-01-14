import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
import random

# Cryptocurrency symbol mapping with lowercase symbols
CRYPTO_SYMBOLS = {
    'bitcoin': 'btc/usdt',
    'ethereum': 'eth/usdt',
    'cardano': 'ada/usdt',
    'binancecoin': 'bnb/usdt',
    'solana': 'sol/usdt'
}

# Initialize APIs
cg = CoinGeckoAPI()

def get_exchange_symbol(exchange_id: str, base_symbol: str) -> str:
    """Convert base symbol to exchange-specific format with error handling."""
    try:
        if not base_symbol:
            raise ValueError("Invalid base symbol")
        
        if exchange_id == 'kucoin':
            return base_symbol.replace('/', '-')
        return base_symbol.upper()  # Most exchanges prefer uppercase symbols
    except Exception as e:
        st.warning(f"Symbol conversion error: {str(e)}")
        return base_symbol

def init_exchanges() -> List[ccxt.Exchange]:
    """Initialize multiple cryptocurrency exchanges with error handling."""
    exchanges = []
    exchange_ids = ['kraken', 'coinbasepro', 'kucoin']
    
    for exchange_id in exchange_ids:
        try:
            exchange = getattr(ccxt, exchange_id)()
            exchange.load_markets()  # Load market symbols
            exchanges.append(exchange)
        except Exception as e:
            st.warning(f"Failed to initialize {exchange_id}: {str(e)}")
    
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
    """Fetch cryptocurrency data using multiple exchanges with fallback."""
    try:
        # Get symbol from mapping with validation
        symbol = CRYPTO_SYMBOLS.get(coin_id.lower())
        if not symbol:
            st.error(f"Unsupported cryptocurrency: {coin_id}")
            return pd.DataFrame()

        # Convert days to milliseconds for CCXT
        timeframe = '1d'
        if int(days) <= 7:
            timeframe = '1h'
        
        for exchange in exchanges:
            try:
                # Get exchange-specific symbol format
                exchange_symbol = get_exchange_symbol(exchange.id, symbol)
                
                def fetch_data():
                    return exchange.fetch_ohlcv(
                        exchange_symbol,
                        timeframe,
                        limit=int(days) * (24 if timeframe == '1h' else 1)
                    )
                
                # Fetch OHLCV data with retry logic
                ohlcv = retry_api_call(fetch_data)
                
                if ohlcv and len(ohlcv) > 0:
                    # Create DataFrame
                    df = pd.DataFrame(
                        ohlcv,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    
                    # Convert timestamp to datetime
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # Use close price as the main price
                    df['price'] = df['close']
                    
                    return df[['price', 'volume']]
                    
            except Exception as e:
                st.warning(f"Exchange {exchange.id} error: {str(e)}. Trying next exchange...")
                continue
        
        # Fallback to CoinGecko
        st.info("Using CoinGecko as fallback data source...")
        data = retry_api_call(
            lambda: cg.get_coin_market_chart_by_id(
                id=coin_id,
                vs_currency='usd',
                days=days
            )
        )
        
        if data:
            df = pd.DataFrame({
                'timestamp': [pd.to_datetime(ts, unit='ms') for ts, _ in data['prices']],
                'price': [p for _, p in data['prices']],
                'volume': [v for _, v in data['total_volumes']]
            })
            
            df.set_index('timestamp', inplace=True)
            return df
            
    except Exception as e:
        error_msg = _handle_api_error(e)
        st.error(error_msg)
    
    return pd.DataFrame()

@st.cache_data(ttl=300)
def get_bitcoin_dominance(days: str) -> pd.DataFrame:
    """Calculate Bitcoin dominance using CoinGecko market data."""
    try:
        # Get all coins market data
        global_data = retry_api_call(
            lambda: cg.get_coins_markets(
                vs_currency='usd',
                order='market_cap_desc',
                per_page=100,
                sparkline=False
            )
        )
        
        if not global_data:
            raise Exception("Failed to fetch market data")
        
        # Calculate total market cap and Bitcoin market cap
        total_market_cap = sum(coin['market_cap'] for coin in global_data if coin['market_cap'])
        btc_data = next((coin for coin in global_data if coin['id'] == 'bitcoin'), None)
        
        if not btc_data or not total_market_cap:
            raise Exception("Invalid market cap data")
        
        btc_market_cap = btc_data['market_cap']
        dominance = (btc_market_cap / total_market_cap * 100) if total_market_cap > 0 else 0
        
        # Create time series for the last N days
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=int(days),
            freq='D'
        )
        
        # Create DataFrame with the calculated dominance
        df = pd.DataFrame({
            'timestamp': timestamps,
            'btc_dominance': [dominance] * len(timestamps)
        })
        
        df.set_index('timestamp', inplace=True)
        return df[['btc_dominance']]
        
    except Exception as e:
        error_msg = _handle_api_error(e)
        st.error(error_msg)
        return pd.DataFrame({'btc_dominance': []})

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
