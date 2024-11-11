import pandas as pd
from pycoingecko import CoinGeckoAPI
import streamlit as st
from typing import Optional, Dict, Any

cg = CoinGeckoAPI()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_crypto_data(coin_id: str, days: str) -> pd.DataFrame:
    """Fetch cryptocurrency data from CoinGecko."""
    try:
        data = cg.get_coin_market_chart_by_id(
            id=coin_id,
            vs_currency='usd',
            days=days
        )
        
        # Create DataFrame with proper column names
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
    """Fetch Bitcoin dominance data using market cap data."""
    try:
        # Get Bitcoin market data
        btc_data = cg.get_coin_market_chart_by_id(
            id='bitcoin',
            vs_currency='usd',
            days=days
        )
        
        # Get global market data using the correct endpoint
        global_data = cg.get_global_history(days=days)
        
        # Process Bitcoin market cap data
        btc_market_caps = [(pd.to_datetime(ts, unit='ms'), mc) for ts, mc in btc_data['market_caps']]
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': [ts for ts, _ in btc_market_caps],
            'btc_market_cap': [mc for _, mc in btc_market_caps]
        })
        
        # Add total market cap and calculate dominance
        df['total_market_cap'] = df['timestamp'].map(
            lambda x: global_data.get(x.strftime('%d-%m-%Y'), {}).get('total_market_cap', {}).get('usd', 0)
        )
        
        # Calculate dominance percentage
        df['btc_dominance'] = (df['btc_market_cap'] / df['total_market_cap']) * 100
        
        # Handle missing or invalid values
        df['btc_dominance'] = df['btc_dominance'].fillna(0).clip(0, 100)
        
        # Set timestamp as index and select only the dominance column
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
