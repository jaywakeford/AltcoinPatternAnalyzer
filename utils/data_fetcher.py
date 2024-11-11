import pandas as pd
import ccxt
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import time

# Initialize APIs
cg = CoinGeckoAPI()

# Initialize CCXT exchange (using Binance as primary source)
try:
    exchange = ccxt.binance()
except Exception as e:
    st.warning(f"Failed to initialize CCXT exchange: {str(e)}")
    exchange = None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_crypto_data(coin_id: str, days: str) -> pd.DataFrame:
    """Fetch cryptocurrency data using CCXT with CoinGecko fallback."""
    try:
        # Convert days to milliseconds for CCXT
        timeframe = '1d'
        if int(days) <= 7:
            timeframe = '1h'
        
        if exchange:
            try:
                # Get symbol in CCXT format
                symbol = f"{coin_id.upper()}/USDT"
                
                # Fetch OHLCV data
                ohlcv = exchange.fetch_ohlcv(
                    symbol,
                    timeframe,
                    limit=int(days) * (24 if timeframe == '1h' else 1)
                )
                
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
                st.warning(f"CCXT error: {str(e)}. Falling back to CoinGecko.")
        
        # Fallback to CoinGecko
        data = cg.get_coin_market_chart_by_id(
            id=coin_id,
            vs_currency='usd',
            days=days
        )
        
        df = pd.DataFrame({
            'timestamp': [pd.to_datetime(ts, unit='ms') for ts, _ in data['prices']],
            'price': [p for _, p in data['prices']],
            'volume': [v for _, v in data['total_volumes']]
        })
        
        df.set_index('timestamp', inplace=True)
        return df
        
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_bitcoin_dominance(days: str) -> pd.DataFrame:
    """Calculate Bitcoin dominance using CCXT market data with CoinGecko fallback."""
    try:
        if exchange:
            try:
                # Get BTC price and volume
                btc_data = get_crypto_data('bitcoin', days)
                
                # Get total market data from exchange tickers
                tickers = exchange.fetch_tickers()
                total_volume = 0
                total_market_cap = 0
                
                for symbol, ticker in tickers.items():
                    if symbol.endswith('/USDT'):
                        price = ticker.get('last', 0)
                        volume = ticker.get('quoteVolume', 0)
                        total_volume += volume
                        # Estimate market cap (this is approximate)
                        if 'info' in ticker and 'weightedAvgPrice' in ticker['info']:
                            total_market_cap += float(ticker['info']['weightedAvgPrice']) * volume
                
                # Calculate dominance
                btc_market_cap = btc_data['price'].iloc[-1] * btc_data['volume'].iloc[-1]
                dominance = (btc_market_cap / total_market_cap * 100) if total_market_cap > 0 else 0
                
                # Create DataFrame with calculated dominance
                dates = pd.date_range(
                    end=datetime.now(),
                    periods=int(days),
                    freq='D'
                )
                
                df = pd.DataFrame({
                    'timestamp': dates,
                    'btc_dominance': [dominance] * len(dates)
                })
                
                df.set_index('timestamp', inplace=True)
                return df
                
            except Exception as e:
                st.warning(f"CCXT market data error: {str(e)}. Falling back to CoinGecko.")
        
        # Fallback to CoinGecko
        btc_data = cg.get_coin_market_chart_by_id(
            id='bitcoin',
            vs_currency='usd',
            days=days
        )
        
        global_data = cg.get_global_market_chart_by_id(
            vs_currency='usd',
            days=days
        )
        
        # Process Bitcoin market cap data
        btc_market_caps = [(pd.to_datetime(ts, unit='ms'), mc) for ts, mc in btc_data['market_caps']]
        global_market_caps = [(pd.to_datetime(ts, unit='ms'), mc) for ts, mc in global_data['market_caps']]
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': [ts for ts, _ in btc_market_caps],
            'btc_market_cap': [mc for _, mc in btc_market_caps],
            'total_market_cap': [mc for _, mc in global_market_caps]
        })
        
        # Calculate dominance percentage
        df['btc_dominance'] = (df['btc_market_cap'] / df['total_market_cap']) * 100
        df['btc_dominance'] = df['btc_dominance'].fillna(0).clip(0, 100)
        
        df.set_index('timestamp', inplace=True)
        return df[['btc_dominance']]
        
    except Exception as e:
        error_msg = _handle_api_error(e)
        st.error(error_msg)
        return pd.DataFrame({'btc_dominance': []})

def _handle_api_error(error: Exception) -> str:
    """Handle API errors and return appropriate error messages."""
    error_msg = str(error)
    if "429" in error_msg:
        return "Rate limit exceeded. Please try again in a few minutes."
    elif "404" in error_msg:
        return "Data not found. Please check if the API endpoint is correct."
    elif "connection" in error_msg.lower():
        return "Connection error. Please check your internet connection."
    else:
        return f"API error: {error_msg}"
