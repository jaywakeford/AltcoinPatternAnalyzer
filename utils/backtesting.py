import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from utils.technical_analysis import calculate_sma, calculate_ema, calculate_rsi, calculate_macd

@dataclass
class TradePosition:
    entry_price: float
    entry_time: pd.Timestamp
    position_size: float
    position_type: str  # 'long' or 'short'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class BacktestResult:
    def __init__(self):
        self.trades: List[Dict] = []
        self.metrics: Dict = {}
        self.equity_curve: pd.Series = None

    def calculate_metrics(self):
        if not self.trades:
            return

        returns = [trade['return_pct'] for trade in self.trades]
        self.metrics = {
            'total_trades': len(self.trades),
            'winning_trades': len([r for r in returns if r > 0]),
            'losing_trades': len([r for r in returns if r < 0]),
            'win_rate': len([r for r in returns if r > 0]) / len(returns),
            'avg_return': np.mean(returns),
            'max_drawdown': self._calculate_max_drawdown(),
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'profit_factor': self._calculate_profit_factor()
        }

    def _calculate_max_drawdown(self) -> float:
        if self.equity_curve is None:
            return 0.0
        rolling_max = self.equity_curve.expanding().max()
        drawdowns = self.equity_curve / rolling_max - 1
        return abs(min(drawdowns))

    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        if not returns:
            return 0.0
        returns_series = pd.Series(returns)
        excess_returns = returns_series - risk_free_rate/252  # Daily risk-free rate
        return np.sqrt(252) * (excess_returns.mean() / excess_returns.std()) if excess_returns.std() != 0 else 0

    def _calculate_profit_factor(self) -> float:
        winning_trades = [t['return_pct'] for t in self.trades if t['return_pct'] > 0]
        losing_trades = [abs(t['return_pct']) for t in self.trades if t['return_pct'] < 0]
        
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = sum(losing_trades) if losing_trades else 0
        
        return gross_profit / gross_loss if gross_loss != 0 else 0

class Backtester:
    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000):
        self.data = data
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: List[TradePosition] = []
        self.closed_trades: List[Dict] = []
        self.equity_curve = []

    def run_strategy(self, strategy_config: Dict) -> BacktestResult:
        """
        Run backtesting with the given strategy configuration
        """
        self._reset()
        result = BacktestResult()

        for idx, row in self.data.iterrows():
            # Check for exit signals on existing positions
            self._check_exits(idx, row['price'])
            
            # Generate signals based on strategy
            signal = self._generate_signals(idx, strategy_config)
            
            if signal:
                self._execute_trade(signal, row['price'], idx)

            # Update equity curve
            self.equity_curve.append(self._calculate_current_equity(row['price']))

        # Close any remaining positions
        self._close_all_positions(self.data.index[-1], self.data['price'].iloc[-1])

        # Prepare results
        result.trades = self.closed_trades
        result.equity_curve = pd.Series(self.equity_curve, index=self.data.index)
        result.calculate_metrics()

        return result

    def _reset(self):
        """Reset the backtester state"""
        self.current_capital = self.initial_capital
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []

    def _generate_signals(self, current_time: pd.Timestamp, config: Dict) -> Optional[str]:
        """Generate trading signals based on strategy configuration"""
        if len(self.data[:current_time]) < config.get('lookback', 20):
            return None

        lookback_data = self.data[:current_time]
        
        # Strategy implementation based on config
        if config['strategy_type'] == 'trend_following':
            return self._trend_following_strategy(lookback_data, config)
        elif config['strategy_type'] == 'mean_reversion':
            return self._mean_reversion_strategy(lookback_data, config)
        elif config['strategy_type'] == 'breakout':
            return self._breakout_strategy(lookback_data, config)
        
        return None

    def _trend_following_strategy(self, data: pd.DataFrame, config: Dict) -> Optional[str]:
        """Implement trend following strategy"""
        sma_short = calculate_sma(data, config.get('sma_short', 20))
        sma_long = calculate_sma(data, config.get('sma_long', 50))
        
        if sma_short.iloc[-1] > sma_long.iloc[-1] and sma_short.iloc[-2] <= sma_long.iloc[-2]:
            return 'buy'
        elif sma_short.iloc[-1] < sma_long.iloc[-1] and sma_short.iloc[-2] >= sma_long.iloc[-2]:
            return 'sell'
        
        return None

    def _mean_reversion_strategy(self, data: pd.DataFrame, config: Dict) -> Optional[str]:
        """Implement mean reversion strategy"""
        rsi = calculate_rsi(data, config.get('rsi_period', 14))
        
        if rsi.iloc[-1] < config.get('oversold', 30):
            return 'buy'
        elif rsi.iloc[-1] > config.get('overbought', 70):
            return 'sell'
        
        return None

    def _breakout_strategy(self, data: pd.DataFrame, config: Dict) -> Optional[str]:
        """Implement breakout strategy"""
        lookback = config.get('lookback', 20)
        high = data['price'].rolling(window=lookback).max()
        low = data['price'].rolling(window=lookback).min()
        
        if data['price'].iloc[-1] > high.iloc[-2]:
            return 'buy'
        elif data['price'].iloc[-1] < low.iloc[-2]:
            return 'sell'
        
        return None

    def _execute_trade(self, signal: str, price: float, timestamp: pd.Timestamp):
        """Execute a trade based on the signal"""
        position_size = self.current_capital * 0.1  # Use 10% of capital per trade
        
        if signal == 'buy':
            self.positions.append(TradePosition(
                entry_price=price,
                entry_time=timestamp,
                position_size=position_size/price,
                position_type='long'
            ))
        elif signal == 'sell':
            self.positions.append(TradePosition(
                entry_price=price,
                entry_time=timestamp,
                position_size=position_size/price,
                position_type='short'
            ))

    def _check_exits(self, current_time: pd.Timestamp, current_price: float):
        """Check and execute exit conditions"""
        for position in self.positions[:]:
            exit_signal = False
            
            # Implement exit logic (e.g., stop-loss, take-profit)
            if position.position_type == 'long':
                if position.stop_loss and current_price <= position.stop_loss:
                    exit_signal = True
                elif position.take_profit and current_price >= position.take_profit:
                    exit_signal = True
            else:  # short position
                if position.stop_loss and current_price >= position.stop_loss:
                    exit_signal = True
                elif position.take_profit and current_price <= position.take_profit:
                    exit_signal = True

            if exit_signal:
                self._close_position(position, current_time, current_price)
                self.positions.remove(position)

    def _close_position(self, position: TradePosition, exit_time: pd.Timestamp, exit_price: float):
        """Close a position and record the trade"""
        if position.position_type == 'long':
            return_pct = (exit_price - position.entry_price) / position.entry_price
        else:  # short position
            return_pct = (position.entry_price - exit_price) / position.entry_price

        pnl = position.position_size * position.entry_price * return_pct
        self.current_capital += pnl

        self.closed_trades.append({
            'entry_time': position.entry_time,
            'exit_time': exit_time,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'position_type': position.position_type,
            'position_size': position.position_size,
            'return_pct': return_pct,
            'pnl': pnl
        })

    def _close_all_positions(self, exit_time: pd.Timestamp, exit_price: float):
        """Close all open positions"""
        for position in self.positions[:]:
            self._close_position(position, exit_time, exit_price)
        self.positions = []

    def _calculate_current_equity(self, current_price: float) -> float:
        """Calculate current equity including open positions"""
        equity = self.current_capital
        
        for position in self.positions:
            if position.position_type == 'long':
                equity += position.position_size * (current_price - position.entry_price)
            else:  # short position
                equity += position.position_size * (position.entry_price - current_price)
                
        return equity
