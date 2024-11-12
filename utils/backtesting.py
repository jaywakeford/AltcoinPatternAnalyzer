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
    trailing_stop: Optional[float] = None

class BacktestResult:
    def __init__(self):
        self.trades: List[Dict] = []
        self.metrics: Dict = {}
        self.equity_curve: pd.Series = None
        self.risk_metrics: Dict = {}

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

        # Calculate risk management metrics
        self.risk_metrics = {
            'avg_risk_reward_ratio': self._calculate_avg_risk_reward_ratio(),
            'max_consecutive_losses': self._calculate_max_consecutive_losses(),
            'avg_time_in_trade': self._calculate_avg_time_in_trade(),
            'max_position_size': max([t['position_size'] for t in self.trades]),
            'risk_adjusted_return': self._calculate_risk_adjusted_return()
        }

        # Update metrics with risk metrics
        self.metrics.update(self.risk_metrics)

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

    def _calculate_avg_risk_reward_ratio(self) -> float:
        ratios = []
        for trade in self.trades:
            if 'stop_loss' in trade and 'take_profit' in trade:
                risk = abs(trade['entry_price'] - trade['stop_loss'])
                reward = abs(trade['take_profit'] - trade['entry_price'])
                if risk != 0:
                    ratios.append(reward / risk)
        return np.mean(ratios) if ratios else 0

    def _calculate_max_consecutive_losses(self) -> int:
        max_losses = 0
        current_losses = 0
        for trade in self.trades:
            if trade['return_pct'] < 0:
                current_losses += 1
                max_losses = max(max_losses, current_losses)
            else:
                current_losses = 0
        return max_losses

    def _calculate_avg_time_in_trade(self) -> float:
        durations = []
        for trade in self.trades:
            duration = (pd.Timestamp(trade['exit_time']) - pd.Timestamp(trade['entry_time'])).total_seconds() / 3600  # hours
            durations.append(duration)
        return np.mean(durations) if durations else 0

    def _calculate_risk_adjusted_return(self) -> float:
        if self.metrics.get('max_drawdown', 0) == 0:
            return 0
        return self.metrics.get('avg_return', 0) / self.metrics['max_drawdown']

class Backtester:
    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000):
        self.data = data
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: List[TradePosition] = []
        self.closed_trades: List[Dict] = []
        self.equity_curve = []

    def _validate_strategy_parameters(self, config: Dict) -> List[str]:
        """Validate strategy parameters before execution."""
        errors = []
        
        # Validate position size
        position_size = config.get('position_size', 0)
        if not 0 < position_size <= 100:
            errors.append(f"Position size must be between 0 and 100%, got {position_size}%")

        # Validate stop loss
        stop_loss = config.get('stop_loss')
        if stop_loss is not None and (stop_loss <= 0 or stop_loss >= 100):
            errors.append(f"Stop loss must be between 0 and 100%, got {stop_loss}%")

        # Validate take profit
        take_profit = config.get('take_profit')
        if take_profit is not None and (take_profit <= 0 or take_profit >= 100):
            errors.append(f"Take profit must be between 0 and 100%, got {take_profit}%")

        # Validate risk/reward ratio
        if stop_loss and take_profit and take_profit <= stop_loss:
            errors.append("Take profit must be greater than stop loss")

        # Validate max trades
        max_trades = config.get('max_trades', 1)
        if max_trades <= 0:
            errors.append(f"Maximum trades must be positive, got {max_trades}")

        return errors

    def run_strategy(self, strategy_config: Dict) -> BacktestResult:
        """Run backtesting with the given strategy configuration"""
        # Validate strategy parameters
        validation_errors = self._validate_strategy_parameters(strategy_config)
        if validation_errors:
            raise ValueError(f"Invalid strategy parameters: {'; '.join(validation_errors)}")

        self._reset()
        result = BacktestResult()

        try:
            for idx, row in self.data.iterrows():
                # Check for exit signals on existing positions
                self._check_exits(idx, row['price'], strategy_config)
                
                # Generate signals based on strategy
                signal = self._generate_signals(idx, strategy_config)
                
                if signal and len(self.positions) < strategy_config.get('max_trades', 1):
                    self._execute_trade(signal, row['price'], idx, strategy_config)

                # Update equity curve
                self.equity_curve.append(self._calculate_current_equity(row['price']))

            # Close any remaining positions
            self._close_all_positions(self.data.index[-1], self.data['price'].iloc[-1])

            # Prepare results
            result.trades = self.closed_trades
            result.equity_curve = pd.Series(self.equity_curve, index=self.data.index)
            result.calculate_metrics()

        except Exception as e:
            raise Exception(f"Error during backtesting: {str(e)}")

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

    def _execute_trade(self, signal: str, price: float, timestamp: pd.Timestamp, config: Dict):
        """Execute a trade with risk management parameters"""
        try:
            position_size_pct = config.get('position_size', 10)
            position_size = (self.current_capital * position_size_pct / 100) / price
            
            stop_loss_pct = config.get('stop_loss')
            take_profit_pct = config.get('take_profit')
            
            if signal == 'buy':
                stop_loss = price * (1 - stop_loss_pct/100) if stop_loss_pct else None
                take_profit = price * (1 + take_profit_pct/100) if take_profit_pct else None
                
                self.positions.append(TradePosition(
                    entry_price=price,
                    entry_time=timestamp,
                    position_size=position_size,
                    position_type='long',
                    stop_loss=stop_loss,
                    take_profit=take_profit
                ))
            elif signal == 'sell':
                stop_loss = price * (1 + stop_loss_pct/100) if stop_loss_pct else None
                take_profit = price * (1 - take_profit_pct/100) if take_profit_pct else None
                
                self.positions.append(TradePosition(
                    entry_price=price,
                    entry_time=timestamp,
                    position_size=position_size,
                    position_type='short',
                    stop_loss=stop_loss,
                    take_profit=take_profit
                ))

        except Exception as e:
            raise Exception(f"Error executing trade: {str(e)}")

    def _check_exits(self, current_time: pd.Timestamp, current_price: float, config: Dict):
        """Check and execute exit conditions with risk management"""
        for position in self.positions[:]:
            exit_signal = False
            exit_reason = ""
            
            # Check stop loss
            if position.position_type == 'long':
                if position.stop_loss and current_price <= position.stop_loss:
                    exit_signal = True
                    exit_reason = "stop_loss"
                elif position.take_profit and current_price >= position.take_profit:
                    exit_signal = True
                    exit_reason = "take_profit"
            else:  # short position
                if position.stop_loss and current_price >= position.stop_loss:
                    exit_signal = True
                    exit_reason = "stop_loss"
                elif position.take_profit and current_price <= position.take_profit:
                    exit_signal = True
                    exit_reason = "take_profit"

            # Check strategy exit conditions
            strategy_exit = self._check_strategy_exits(current_time, config)
            if strategy_exit:
                exit_signal = True
                exit_reason = "strategy"

            if exit_signal:
                self._close_position(position, current_time, current_price, exit_reason)
                self.positions.remove(position)

    def _close_position(self, position: TradePosition, exit_time: pd.Timestamp, exit_price: float, exit_reason: str = ""):
        """Close a position and record the trade with exit information"""
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
            'pnl': pnl,
            'stop_loss': position.stop_loss,
            'take_profit': position.take_profit,
            'exit_reason': exit_reason
        })

    def _check_strategy_exits(self, current_time: pd.Timestamp, config: Dict) -> bool:
        """Check for strategy-specific exit conditions"""
        # Implement strategy-specific exit logic if needed
        return False

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