import pandas as pd
import numpy as np

def calculate_sma(data: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return data['price'].rolling(window=period).mean()

def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return data['price'].ewm(span=period, adjust=False).mean()

def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = data['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data: pd.DataFrame) -> tuple:
    """Calculate MACD indicator."""
    exp1 = data['price'].ewm(span=12, adjust=False).mean()
    exp2 = data['price'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_advanced_metrics(data: pd.DataFrame) -> dict:
    """Calculate advanced market metrics."""
    try:
        metrics = {}
        
        # Calculate volatility (20-period)
        returns = data['close'].pct_change()
        metrics['volatility'] = min(returns.std() * np.sqrt(252) * 100, 100)  # Annualized volatility capped at 100
        
        # Calculate momentum (Rate of change)
        metrics['momentum'] = min(((data['close'].iloc[-1] / data['close'].iloc[-20]) - 1) * 100, 100)
        
        # Calculate market strength (combination of volume and price trend)
        volume_trend = data['volume'].rolling(window=20).mean().iloc[-1] / data['volume'].rolling(window=20).mean().iloc[-2]
        price_trend = data['close'].rolling(window=20).mean().iloc[-1] / data['close'].rolling(window=20).mean().iloc[-2]
        metrics['market_strength'] = min((volume_trend * price_trend - 1) * 100, 100)
        
        return metrics
    except Exception as e:
        return {
            'volatility': 0,
            'momentum': 0,
            'market_strength': 0
        }
