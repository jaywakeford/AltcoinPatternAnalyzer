import numpy as np
import pandas as pd
from typing import Tuple, List, Dict
from datetime import datetime, timedelta

class PricePredictor:
    def __init__(self):
        self.models = {
            'sma': self._predict_sma,
            'ema': self._predict_ema,
            'momentum': self._predict_momentum
        }
    
    def predict(self, data: pd.DataFrame, forecast_days: int = 7) -> Dict[str, pd.DataFrame]:
        """Generate predictions using multiple models."""
        predictions = {}
        
        for model_name, predict_func in self.models.items():
            try:
                pred_df = predict_func(data, forecast_days)
                predictions[model_name] = pred_df
            except Exception as e:
                print(f"Error in {model_name} prediction: {str(e)}")
                continue
        
        return predictions
    
    def _predict_sma(self, data: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
        """Predict using Simple Moving Average."""
        # Calculate short and long term SMAs
        short_sma = data['price'].rolling(window=7).mean()
        long_sma = data['price'].rolling(window=21).mean()
        
        # Calculate trend
        trend = (short_sma - long_sma) / long_sma
        
        # Generate future dates
        last_date = data.index[-1]
        future_dates = [last_date + timedelta(days=x) for x in range(1, forecast_days + 1)]
        
        # Predict future values based on trend
        last_price = data['price'].iloc[-1]
        predictions = []
        current_price = last_price
        
        for _ in range(forecast_days):
            change = current_price * trend.iloc[-1]
            current_price += change
            predictions.append(current_price)
        
        return pd.DataFrame({
            'price': predictions,
            'model': 'SMA'
        }, index=future_dates)
    
    def _predict_ema(self, data: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
        """Predict using Exponential Moving Average."""
        # Calculate EMAs
        ema_short = data['price'].ewm(span=7, adjust=False).mean()
        ema_long = data['price'].ewm(span=21, adjust=False).mean()
        
        # Calculate momentum
        momentum = (ema_short - ema_long) / ema_long
        
        # Generate future dates
        last_date = data.index[-1]
        future_dates = [last_date + timedelta(days=x) for x in range(1, forecast_days + 1)]
        
        # Predict future values
        last_price = data['price'].iloc[-1]
        predictions = []
        current_price = last_price
        
        for _ in range(forecast_days):
            change = current_price * momentum.iloc[-1]
            current_price += change
            predictions.append(current_price)
        
        return pd.DataFrame({
            'price': predictions,
            'model': 'EMA'
        }, index=future_dates)
    
    def _predict_momentum(self, data: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
        """Predict using Price Momentum."""
        # Calculate price changes
        price_changes = data['price'].pct_change()
        
        # Calculate momentum indicators
        momentum = price_changes.rolling(window=7).mean()
        volatility = price_changes.rolling(window=14).std()
        
        # Generate future dates
        last_date = data.index[-1]
        future_dates = [last_date + timedelta(days=x) for x in range(1, forecast_days + 1)]
        
        # Predict future values
        last_price = data['price'].iloc[-1]
        predictions = []
        current_price = last_price
        
        for _ in range(forecast_days):
            # Add momentum and adjust for volatility
            change = current_price * (momentum.iloc[-1] + np.random.normal(0, volatility.iloc[-1]))
            current_price += change
            predictions.append(max(0, current_price))  # Ensure non-negative prices
        
        return pd.DataFrame({
            'price': predictions,
            'model': 'Momentum'
        }, index=future_dates)
    
    def get_prediction_metrics(self, predictions: Dict[str, pd.DataFrame], actual_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate prediction accuracy metrics."""
        metrics = {}
        
        for model_name, pred_df in predictions.items():
            if pred_df.empty:
                continue
                
            # Calculate error metrics where we have actual data
            overlap_idx = pred_df.index.intersection(actual_data.index)
            if len(overlap_idx) > 0:
                actual = actual_data.loc[overlap_idx, 'price']
                predicted = pred_df.loc[overlap_idx, 'price']
                
                mape = np.mean(np.abs((actual - predicted) / actual)) * 100
                rmse = np.sqrt(np.mean((actual - predicted) ** 2))
                
                metrics[model_name] = {
                    'mape': mape,
                    'rmse': rmse
                }
        
        return metrics
