import pandas as pd
from pycoingecko import CoinGeckoAPI
import streamlit as st

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
        
        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Add volume
        df['volume'] = [x[1] for x in data['total_volumes']]
        
        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_bitcoin_dominance(days: str) -> pd.DataFrame:
    """Fetch Bitcoin dominance data."""
    try:
        data = cg.get_global_history(days=days)
        df = pd.DataFrame(data)
        df.index = pd.to_datetime(df.index)
        df['btc_dominance'] = df['market_cap_percentage'].apply(lambda x: x['btc'])
        return df[['btc_dominance']]
    except Exception as e:
        st.error(f"Error fetching dominance data: {str(e)}")
        return pd.DataFrame()
