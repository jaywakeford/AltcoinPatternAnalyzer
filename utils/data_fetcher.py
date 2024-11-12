import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
import random

# Cryptocurrency symbol mapping
CRYPTO_SYMBOLS = {
    'bitcoin': 'BTC/USDT',
    'ethereum': 'ETH/USDT',
    'cardano': 'ADA/USDT',
    'binancecoin': 'BNB/USDT',
    'solana': 'SOL/USDT'
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
        st.warning(f"Symbol conversion error: {str(e)}")
        return base_symbol

def init_exchanges() -> List[ccxt.Exchange]:
    """Initialize multiple cryptocurrency exchanges with error handling."""
    exchanges = []
    exchange_ids = ['kraken', 'kucoin', 'binance']
    
    for exchange_id in exchange_ids:
        try:
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'enableRateLimit': True,
                'timeout': 30000
            })
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
        # Use CoinGecko as primary data source
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
            
        # Fallback to exchange data if CoinGecko fails
        symbol = CRYPTO_SYMBOLS.get(coin_id.lower())
        if not symbol:
            raise ValueError(f"Unsupported cryptocurrency: {coin_id}")

        timeframe = '1d'
        if int(days) <= 7:
            timeframe = '1h'
        
        for exchange in exchanges:
            try:
                exchange_symbol = get_exchange_symbol(exchange.id, symbol)
                
                ohlcv = retry_api_call(
                    lambda: exchange.fetch_ohlcv(
                        exchange_symbol,
                        timeframe,
                        limit=int(days) * (24 if timeframe == '1h' else 1)
                    )
                )
                
                if ohlcv:
                    df = pd.DataFrame(
                        ohlcv,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    df['price'] = df['close']
                    
                    return df[['price', 'volume']]
                    
            except Exception as e:
                st.warning(f"Exchange {exchange.id} error: {str(e)}. Trying next exchange...")
                continue
            
    except Exception as e:
        error_msg = _handle_api_error(e)
        st.error(error_msg)
    
    return pd.DataFrame()

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