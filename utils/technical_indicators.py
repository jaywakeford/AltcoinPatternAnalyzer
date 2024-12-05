import pandas as pd
import numpy as np
from typing import Optional, Union, List, Dict
import talib

class TechnicalIndicators:
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators to the dataframe."""
        df = df.copy()
        
        # Trend Indicators
        df = TechnicalIndicators.add_moving_averages(df)
        df = TechnicalIndicators.add_macd(df)
        df = TechnicalIndicators.add_bollinger_bands(df)
        df = TechnicalIndicators.add_ichimoku_cloud(df)
        
        # Momentum Indicators
        df = TechnicalIndicators.add_rsi(df)
        df = TechnicalIndicators.add_stochastic(df)
        df = TechnicalIndicators.add_williams_r(df)
        df = TechnicalIndicators.add_mfi(df)
        
        # Volume Indicators
        df = TechnicalIndicators.add_obv(df)
        df = TechnicalIndicators.add_cmf(df)
        df = TechnicalIndicators.add_vwap(df)
        
        # Volatility Indicators
        df = TechnicalIndicators.add_atr(df)
        df = TechnicalIndicators.add_standard_deviation(df)
        
        # Pattern Recognition
        df = TechnicalIndicators.add_candlestick_patterns(df)
        
        # Trading Signals
        df = TechnicalIndicators.add_trading_signals(df)
        
        return df

    @staticmethod
    def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
        """Add various moving averages and crossover signals."""
        periods = [9, 20, 50, 100, 200]
        
        for period in periods:
            df[f'SMA_{period}'] = talib.SMA(df['close'], timeperiod=period)
            df[f'EMA_{period}'] = talib.EMA(df['close'], timeperiod=period)
        
        # Add Golden/Death Cross signals
        df['Golden_Cross'] = (df['SMA_50'] > df['SMA_200']) & (df['SMA_50'].shift(1) <= df['SMA_200'].shift(1))
        df['Death_Cross'] = (df['SMA_50'] < df['SMA_200']) & (df['SMA_50'].shift(1) >= df['SMA_200'].shift(1))
            
        return df

    @staticmethod
    def add_macd(df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD indicator and signals."""
        macd, signal, hist = talib.MACD(df['close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist
        
        # Add MACD crossover signals
        df['MACD_Bullish_Cross'] = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        df['MACD_Bearish_Cross'] = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        
        return df

    @staticmethod
    def add_bollinger_bands(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Add Bollinger Bands and signals."""
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = talib.BBANDS(
            df['close'], 
            timeperiod=period
        )
        
        # Add Bollinger Band signals
        df['BB_Oversold'] = df['close'] <= df['BB_Lower']
        df['BB_Overbought'] = df['close'] >= df['BB_Upper']
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        return df

    @staticmethod
    def add_ichimoku_cloud(df: pd.DataFrame) -> pd.DataFrame:
        """Add Ichimoku Cloud indicator and signals."""
        # Conversion Line (Tenkan-sen)
        high_9 = df['high'].rolling(window=9).max()
        low_9 = df['low'].rolling(window=9).min()
        df['Ichimoku_Conversion'] = (high_9 + low_9) / 2
        
        # Base Line (Kijun-sen)
        high_26 = df['high'].rolling(window=26).max()
        low_26 = df['low'].rolling(window=26).min()
        df['Ichimoku_Base'] = (high_26 + low_26) / 2
        
        # Leading Span A (Senkou Span A)
        df['Ichimoku_SpanA'] = ((df['Ichimoku_Conversion'] + df['Ichimoku_Base']) / 2).shift(26)
        
        # Leading Span B (Senkou Span B)
        high_52 = df['high'].rolling(window=52).max()
        low_52 = df['low'].rolling(window=52).min()
        df['Ichimoku_SpanB'] = ((high_52 + low_52) / 2).shift(26)
        
        # Add Ichimoku signals
        df['Ichimoku_Bull_Signal'] = (df['close'] > df['Ichimoku_SpanA']) & (df['close'] > df['Ichimoku_SpanB'])
        df['Ichimoku_Bear_Signal'] = (df['close'] < df['Ichimoku_SpanA']) & (df['close'] < df['Ichimoku_SpanB'])
        
        return df

    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add RSI indicator and signals."""
        df['RSI'] = talib.RSI(df['close'], timeperiod=period)
        
        # Add RSI signals
        df['RSI_Oversold'] = df['RSI'] < 30
        df['RSI_Overbought'] = df['RSI'] > 70
        df['RSI_Bull_Div'] = (df['close'] < df['close'].shift(1)) & (df['RSI'] > df['RSI'].shift(1))
        df['RSI_Bear_Div'] = (df['close'] > df['close'].shift(1)) & (df['RSI'] < df['RSI'].shift(1))
        
        return df

    @staticmethod
    def add_stochastic(df: pd.DataFrame) -> pd.DataFrame:
        """Add Stochastic Oscillator and signals."""
        df['Stoch_K'], df['Stoch_D'] = talib.STOCH(
            df['high'], 
            df['low'], 
            df['close']
        )
        
        # Add Stochastic signals
        df['Stoch_Oversold'] = (df['Stoch_K'] < 20) & (df['Stoch_D'] < 20)
        df['Stoch_Overbought'] = (df['Stoch_K'] > 80) & (df['Stoch_D'] > 80)
        df['Stoch_Bull_Cross'] = (df['Stoch_K'] > df['Stoch_D']) & (df['Stoch_K'].shift(1) <= df['Stoch_D'].shift(1))
        df['Stoch_Bear_Cross'] = (df['Stoch_K'] < df['Stoch_D']) & (df['Stoch_K'].shift(1) >= df['Stoch_D'].shift(1))
        
        return df

    @staticmethod
    def add_williams_r(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Williams %R indicator and signals."""
        df['Williams_R'] = talib.WILLR(
            df['high'],
            df['low'],
            df['close'],
            timeperiod=period
        )
        
        # Add Williams %R signals
        df['Williams_Oversold'] = df['Williams_R'] < -80
        df['Williams_Overbought'] = df['Williams_R'] > -20
        
        return df

    @staticmethod
    def add_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Money Flow Index and signals."""
        df['MFI'] = talib.MFI(
            df['high'],
            df['low'],
            df['close'],
            df['volume'],
            timeperiod=period
        )
        
        # Add MFI signals
        df['MFI_Oversold'] = df['MFI'] < 20
        df['MFI_Overbought'] = df['MFI'] > 80
        
        return df

    @staticmethod
    def add_obv(df: pd.DataFrame) -> pd.DataFrame:
        """Add On Balance Volume and signals."""
        df['OBV'] = talib.OBV(df['close'], df['volume'])
        
        # Add OBV signals
        df['OBV_SMA'] = df['OBV'].rolling(window=20).mean()
        df['OBV_Bull_Cross'] = (df['OBV'] > df['OBV_SMA']) & (df['OBV'].shift(1) <= df['OBV_SMA'].shift(1))
        df['OBV_Bear_Cross'] = (df['OBV'] < df['OBV_SMA']) & (df['OBV'].shift(1) >= df['OBV_SMA'].shift(1))
        
        return df

    @staticmethod
    def add_cmf(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Add Chaikin Money Flow and signals."""
        mf_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mf_volume = mf_multiplier * df['volume']
        df['CMF'] = mf_volume.rolling(window=period).sum() / df['volume'].rolling(window=period).sum()
        
        # Add CMF signals
        df['CMF_Bull_Signal'] = df['CMF'] > 0
        df['CMF_Bear_Signal'] = df['CMF'] < 0
        
        return df

    @staticmethod
    def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume Weighted Average Price and signals."""
        df['VWAP'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        
        # Add VWAP signals
        df['VWAP_Above'] = df['close'] > df['VWAP']
        df['VWAP_Below'] = df['close'] < df['VWAP']
        
        return df

    @staticmethod
    def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Average True Range and volatility signals."""
        df['ATR'] = talib.ATR(
            df['high'],
            df['low'],
            df['close'],
            timeperiod=period
        )
        
        # Add ATR-based signals
        df['ATR_High'] = df['ATR'] > df['ATR'].rolling(window=100).mean()
        df['ATR_Low'] = df['ATR'] < df['ATR'].rolling(window=100).mean()
        
        return df

    @staticmethod
    def add_standard_deviation(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Add Standard Deviation and volatility signals."""
        df['StdDev'] = df['close'].rolling(window=period).std()
        
        # Add StdDev signals
        df['StdDev_High'] = df['StdDev'] > df['StdDev'].rolling(window=100).mean()
        df['StdDev_Low'] = df['StdDev'] < df['StdDev'].rolling(window=100).mean()
        
        return df

    @staticmethod
    def add_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
        """Add candlestick pattern recognition."""
        # Bullish patterns
        df['Hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
        df['Inverted_Hammer'] = talib.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])
        df['Morning_Star'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
        df['Bullish_Engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
        df['Three_White_Soldiers'] = talib.CDL3WHITESOLDIERS(df['open'], df['high'], df['low'], df['close'])
        
        # Bearish patterns
        df['Hanging_Man'] = talib.CDLHANGINGMAN(df['open'], df['high'], df['low'], df['close'])
        df['Evening_Star'] = talib.CDLEVENINGSTAR(df['open'], df['high'], df['low'], df['close'])
        df['Bearish_Engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
        df['Three_Black_Crows'] = talib.CDL3BLACKCROWS(df['open'], df['high'], df['low'], df['close'])
        
        return df

    @staticmethod
    def add_trading_signals(df: pd.DataFrame) -> pd.DataFrame:
        """Add combined trading signals based on multiple indicators."""
        # Strong Buy Signal (multiple bullish indicators)
        df['Strong_Buy'] = (
            df['RSI_Oversold'] & 
            df['Stoch_Oversold'] & 
            (df['MACD'] > df['MACD_Signal']) &
            (df['close'] > df['SMA_50']) &
            (df['OBV'] > df['OBV_SMA'])
        )
        
        # Strong Sell Signal (multiple bearish indicators)
        df['Strong_Sell'] = (
            df['RSI_Overbought'] & 
            df['Stoch_Overbought'] & 
            (df['MACD'] < df['MACD_Signal']) &
            (df['close'] < df['SMA_50']) &
            (df['OBV'] < df['OBV_SMA'])
        )
        
        # Trend Strength
        df['Trend_Strength'] = np.where(
            df['close'] > df['SMA_200'],
            np.where(df['close'] > df['SMA_50'], 2, 1),
            np.where(df['close'] < df['SMA_50'], -2, -1)
        )
        
        return df
