import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
import random

# Initialize APIs
cg = CoinGeckoAPI()

# Initialize CCXT exchanges with proper error handling
def init_exchanges() -> List[ccxt.Exchange]:
    exchanges = []
    exchange_ids = ['kraken', 'coinbasepro', 'kucoin']  # Added KuCoin as another fallback
    
    for exchange_id in exchange_ids:
        try:
            exchange = getattr(ccxt, exchange_id)()
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
        # Convert days to milliseconds for CCXT
        timeframe = '1d'
        if int(days) <= 7:
            timeframe = '1h'
        
        for exchange in exchanges:
            try:
                # Get symbol in CCXT format
                symbol = f"{coin_id.upper()}/USDT"
                
                def fetch_data():
                    return exchange.fetch_ohlcv(
                        symbol,
                        timeframe,
                        limit=int(days) * (24 if timeframe == '1h' else 1)
                    )
                
                # Fetch OHLCV data with retry logic
                ohlcv = retry_api_call(fetch_data)
                
                if ohlcv:
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
    """Calculate Bitcoin dominance using CoinGecko global market data."""
    try:
        # Get Bitcoin market cap data
        btc_data = retry_api_call(
            lambda: cg.get_coin_market_chart_by_id(
                id='bitcoin',
                vs_currency='usd',
                days=days
            )
        )
        
        # Get global market data using correct endpoint
        global_data = retry_api_call(
            lambda: cg.get_global_market_chart(
                vs_currency='usd',
                days=days
            )
        )
        
        if not btc_data or not global_data:
            raise Exception("Failed to fetch market data")
        
        # Validate and process data
        btc_market_caps = []
        global_market_caps = []
        
        for btc_point, global_point in zip(btc_data['market_caps'], global_data['total_market_cap']):
            if all(isinstance(x, (int, float)) for x in [btc_point[1], global_point[1]]):
                timestamp = pd.to_datetime(btc_point[0], unit='ms')
                btc_market_caps.append((timestamp, btc_point[1]))
                global_market_caps.append((timestamp, global_point[1]))
        
        if not btc_market_caps or not global_market_caps:
            raise Exception("Invalid market cap data received")
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': [ts for ts, _ in btc_market_caps],
            'btc_market_cap': [mc for _, mc in btc_market_caps],
            'total_market_cap': [mc for _, mc in global_market_caps]
        })
        
        # Calculate dominance percentage with validation
        df['btc_dominance'] = df.apply(
            lambda row: (row['btc_market_cap'] / row['total_market_cap'] * 100)
            if row['total_market_cap'] > 0 else 0,
            axis=1
        )
        
        # Clean and validate the data
        df['btc_dominance'] = df['btc_dominance'].fillna(0).clip(0, 100)
        
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
