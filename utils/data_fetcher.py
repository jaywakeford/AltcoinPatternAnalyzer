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
        # Get global market data from CoinGecko
        data = cg.get_global_history(days=days)
        
        # Create DataFrame with proper structure
        df = pd.DataFrame(columns=['btc_dominance'])
        
        # Process the data
        dates = []
        dominance_values = []
        
        for date, daily_data in data.items():
            try:
                dates.append(pd.to_datetime(date))
                dominance_values.append(daily_data['market_cap_percentage']['btc'])
            except (KeyError, TypeError) as e:
                st.warning(f"Missing data for date {date}: {str(e)}")
                continue
        
        # Create DataFrame with processed data
        df = pd.DataFrame({
            'btc_dominance': dominance_values
        }, index=dates)
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching dominance data: {str(e)}")
        # Return empty DataFrame with correct column
        return pd.DataFrame(columns=['btc_dominance'])
