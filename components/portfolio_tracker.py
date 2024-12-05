import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional
from utils.data_fetcher import ExchangeManager

class PortfolioTracker:
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        
    def initialize_portfolio(self):
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = {
                'holdings': {},  # {symbol: {'amount': float, 'avg_price': float}}
                'transactions': [],  # [{date, symbol, type, amount, price}]
                'total_value_history': [],  # [{date, value}]
                'performance_metrics': {},  # Store calculated performance metrics
                'risk_metrics': {}  # Store risk metrics
            }

    def add_transaction(self, symbol: str, amount: float, price: float, transaction_type: str):
        """Add a buy/sell transaction to the portfolio."""
        transaction = {
            'date': datetime.now().isoformat(),
            'symbol': symbol,
            'type': transaction_type,
            'amount': amount,
            'price': price,
            'value': amount * price
        }
        
        if symbol not in st.session_state.portfolio['holdings']:
            st.session_state.portfolio['holdings'][symbol] = {'amount': 0, 'avg_price': 0, 'realized_pnl': 0}
            
        holdings = st.session_state.portfolio['holdings'][symbol]
        
        if transaction_type == 'buy':
            # Update average price
            total_cost = holdings['amount'] * holdings['avg_price'] + amount * price
            new_total_amount = holdings['amount'] + amount
            holdings['avg_price'] = total_cost / new_total_amount if new_total_amount > 0 else 0
            holdings['amount'] += amount
        else:  # sell
            # Calculate realized PnL
            sell_value = amount * price
            cost_basis = amount * holdings['avg_price']
            holdings['realized_pnl'] += sell_value - cost_basis
            
            holdings['amount'] -= amount
            if holdings['amount'] <= 0:
                holdings['amount'] = 0
                holdings['avg_price'] = 0
                
        st.session_state.portfolio['transactions'].append(transaction)
        self._update_portfolio_value()
        self._calculate_metrics()

    def _update_portfolio_value(self):
        """Update total portfolio value history."""
        total_value = 0
        holdings_value = {}
        
        for symbol, holding in st.session_state.portfolio['holdings'].items():
            current_price = self.exchange_manager.get_current_price(symbol)
            if current_price:
                value = holding['amount'] * current_price
                total_value += value
                holdings_value[symbol] = value
                
        st.session_state.portfolio['total_value_history'].append({
            'date': datetime.now().isoformat(),
            'value': total_value,
            'holdings_value': holdings_value
        })

    def _calculate_metrics(self):
        """Calculate portfolio performance and risk metrics."""
        if not st.session_state.portfolio['total_value_history']:
            return
            
        values = pd.DataFrame(st.session_state.portfolio['total_value_history'])
        values['date'] = pd.to_datetime(values['date'])
        values = values.set_index('date')
        
        # Calculate returns
        returns = values['value'].pct_change()
        
        # Performance Metrics
        metrics = {
            'total_value': values['value'].iloc[-1],
            'daily_return': returns.iloc[-1] if len(returns) > 0 else 0,
            'total_return': (values['value'].iloc[-1] / values['value'].iloc[0] - 1) if len(values) > 1 else 0,
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'volatility': returns.std() * np.sqrt(365) if len(returns) > 1 else 0,
            'max_drawdown': self._calculate_max_drawdown(values['value']),
            'win_rate': self._calculate_win_rate(returns)
        }
        
        st.session_state.portfolio['performance_metrics'] = metrics

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate the Sharpe Ratio."""
        if len(returns) < 2:
            return 0
        excess_returns = returns - risk_free_rate/365
        return np.sqrt(365) * excess_returns.mean() / returns.std() if returns.std() != 0 else 0

    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """Calculate the maximum drawdown."""
        if len(values) < 2:
            return 0
        peak = values.expanding(min_periods=1).max()
        drawdown = (values - peak) / peak
        return drawdown.min()

    def _calculate_win_rate(self, returns: pd.Series) -> float:
        """Calculate the win rate (percentage of positive returns)."""
        if len(returns) < 2:
            return 0
        return (returns > 0).sum() / len(returns)

    def render_portfolio_dashboard(self):
        """Render the enhanced portfolio tracking dashboard."""
        st.subheader("Portfolio Dashboard")
        
        # Portfolio Summary Metrics
        if st.session_state.portfolio['performance_metrics']:
            metrics = st.session_state.portfolio['performance_metrics']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Value", f"${metrics['total_value']:,.2f}")
            with col2:
                st.metric("Daily Return", f"{metrics['daily_return']*100:.2f}%")
            with col3:
                st.metric("Total Return", f"{metrics['total_return']*100:.2f}%")
            with col4:
                st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Volatility", f"{metrics['volatility']*100:.2f}%")
            with col2:
                st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.2f}%")
            with col3:
                st.metric("Win Rate", f"{metrics['win_rate']*100:.2f}%")
        
        # Add new transaction form
        with st.expander("Add Transaction"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                symbol = st.text_input("Symbol (e.g., BTC/USDT)")
            with col2:
                amount = st.number_input("Amount", min_value=0.0)
            with col3:
                price = st.number_input("Price", min_value=0.0)
            with col4:
                transaction_type = st.selectbox("Type", ["buy", "sell"])
                
            if st.button("Add Transaction"):
                if symbol and amount and price:
                    self.add_transaction(symbol, amount, price, transaction_type)
                    st.success(f"Added {transaction_type} transaction for {symbol}")

        # Portfolio Composition
        if st.session_state.portfolio['holdings']:
            st.subheader("Portfolio Composition")
            
            # Create pie chart of portfolio composition
            holdings_data = []
            for symbol, holding in st.session_state.portfolio['holdings'].items():
                current_price = self.exchange_manager.get_current_price(symbol)
                if current_price and holding['amount'] > 0:
                    holdings_data.append({
                        'Symbol': symbol,
                        'Value': holding['amount'] * current_price
                    })
            
            if holdings_data:
                df_composition = pd.DataFrame(holdings_data)
                fig = px.pie(df_composition, values='Value', names='Symbol',
                           title='Portfolio Composition')
                st.plotly_chart(fig, use_container_width=True)

        # Holdings Table
        if st.session_state.portfolio['holdings']:
            st.subheader("Current Holdings")
            holdings_data = []
            
            for symbol, holding in st.session_state.portfolio['holdings'].items():
                current_price = self.exchange_manager.get_current_price(symbol)
                if current_price and holding['amount'] > 0:
                    value = holding['amount'] * current_price
                    unrealized_pnl = value - (holding['amount'] * holding['avg_price'])
                    unrealized_pnl_pct = (unrealized_pnl / (holding['amount'] * holding['avg_price'])) * 100
                    
                    holdings_data.append({
                        'Symbol': symbol,
                        'Amount': holding['amount'],
                        'Avg Price': holding['avg_price'],
                        'Current Price': current_price,
                        'Value': value,
                        'Unrealized P/L': unrealized_pnl,
                        'Unrealized P/L %': unrealized_pnl_pct,
                        'Realized P/L': holding['realized_pnl']
                    })
            
            if holdings_data:
                df = pd.DataFrame(holdings_data)
                st.dataframe(df.style.format({
                    'Amount': '{:.4f}',
                    'Avg Price': '${:.2f}',
                    'Current Price': '${:.2f}',
                    'Value': '${:.2f}',
                    'Unrealized P/L': '${:.2f}',
                    'Unrealized P/L %': '{:.2f}%',
                    'Realized P/L': '${:.2f}'
                }))

        # Portfolio Performance Chart
        if st.session_state.portfolio['total_value_history']:
            st.subheader("Portfolio Performance")
            
            # Create performance chart
            df_history = pd.DataFrame(st.session_state.portfolio['total_value_history'])
            df_history['date'] = pd.to_datetime(df_history['date'])
            
            fig = go.Figure()
            
            # Add total value line
            fig.add_trace(go.Scatter(
                x=df_history['date'],
                y=df_history['value'],
                mode='lines',
                name='Total Value',
                line=dict(color='#00ff00', width=2)
            ))
            
            # Add individual asset value lines
            for symbol in st.session_state.portfolio['holdings'].keys():
                asset_values = []
                for record in st.session_state.portfolio['total_value_history']:
                    holdings_value = record.get('holdings_value', {})
                    asset_values.append(holdings_value.get(symbol, 0))
                
                if any(v > 0 for v in asset_values):
                    fig.add_trace(go.Scatter(
                        x=df_history['date'],
                        y=asset_values,
                        mode='lines',
                        name=symbol,
                        line=dict(width=1),
                        opacity=0.7
                    ))
            
            fig.update_layout(
                title='Portfolio Value Over Time',
                xaxis_title='Date',
                yaxis_title='Value (USD)',
                template='plotly_dark',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

        # Transaction History
        if st.session_state.portfolio['transactions']:
            st.subheader("Transaction History")
            df_transactions = pd.DataFrame(st.session_state.portfolio['transactions'])
            df_transactions['date'] = pd.to_datetime(df_transactions['date'])
            df_transactions = df_transactions.sort_values('date', ascending=False)
            
            st.dataframe(df_transactions.style.format({
                'amount': '{:.4f}',
                'price': '${:.2f}',
                'value': '${:.2f}'
            }))

def render_portfolio_section():
    tracker = PortfolioTracker()
    tracker.initialize_portfolio()
    tracker.render_portfolio_dashboard()
