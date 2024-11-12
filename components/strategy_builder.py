import streamlit as st
import json
from typing import Dict, List
import pandas as pd

class StrategyBuilder:
    def __init__(self):
        self.condition_types = {
            'Price Action': ['Above', 'Below', 'Crosses Above', 'Crosses Below'],
            'Technical Indicators': ['RSI', 'MACD', 'Moving Average'],
            'Volume': ['Volume Spike', 'Volume Decline'],
            'Market Phase': ['Accumulation', 'Distribution', 'Mark Up', 'Mark Down']
        }
        
        self.timeframes = ['1h', '4h', '1d', '1w']
        
    def render(self):
        st.subheader("📊 Custom Strategy Builder")
        
        # Strategy Basic Info
        with st.expander("Strategy Information", expanded=True):
            strategy_name = st.text_input("Strategy Name", "My Custom Strategy")
            strategy_description = st.text_area("Strategy Description", 
                "Enter a detailed description of your strategy...")
            
            col1, col2 = st.columns(2)
            with col1:
                timeframe = st.selectbox("Timeframe", self.timeframes)
                position_size = st.slider("Position Size (%)", 1, 100, 10)
            
            with col2:
                max_trades = st.number_input("Maximum Open Trades", 1, 10, 3)
                risk_per_trade = st.slider("Risk Per Trade (%)", 1, 10, 2)
        
        # Entry Conditions
        with st.expander("Entry Conditions", expanded=True):
            st.markdown("### Entry Rules")
            entry_conditions = self._render_condition_builder("entry")
            
        # Exit Conditions
        with st.expander("Exit Conditions", expanded=True):
            st.markdown("### Exit Rules")
            exit_conditions = self._render_condition_builder("exit")
            
        # Risk Management
        with st.expander("Risk Management", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                stop_loss = st.number_input("Stop Loss (%)", 1, 50, 5)
                trailing_stop = st.checkbox("Use Trailing Stop")
                if trailing_stop:
                    trailing_stop_distance = st.number_input("Trailing Stop Distance (%)", 1, 20, 3)
            
            with col2:
                take_profit = st.number_input("Take Profit (%)", 1, 200, 15)
                pyramiding = st.checkbox("Allow Pyramiding")
                if pyramiding:
                    max_pyramid_positions = st.number_input("Max Pyramid Positions", 1, 5, 2)
        
        # Strategy Preview
        if st.button("Generate Strategy"):
            strategy_config = {
                "name": strategy_name,
                "description": strategy_description,
                "timeframe": timeframe,
                "position_size": position_size,
                "max_trades": max_trades,
                "risk_per_trade": risk_per_trade,
                "entry_conditions": entry_conditions,
                "exit_conditions": exit_conditions,
                "risk_management": {
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "trailing_stop": trailing_stop,
                    "trailing_stop_distance": trailing_stop_distance if trailing_stop else None,
                    "pyramiding": pyramiding,
                    "max_pyramid_positions": max_pyramid_positions if pyramiding else None
                }
            }
            
            st.json(json.dumps(strategy_config, indent=2))
            return strategy_config
            
        return None
    
    def _render_condition_builder(self, condition_type: str) -> List[Dict]:
        conditions = []
        
        # Add condition button
        if st.button(f"Add {condition_type.title()} Condition"):
            if f"{condition_type}_conditions" not in st.session_state:
                st.session_state[f"{condition_type}_conditions"] = 1
            else:
                st.session_state[f"{condition_type}_conditions"] += 1
        
        # Initialize session state for conditions if not exists
        if f"{condition_type}_conditions" not in st.session_state:
            st.session_state[f"{condition_type}_conditions"] = 1
        
        # Render condition inputs
        for i in range(st.session_state[f"{condition_type}_conditions"]):
            with st.container():
                st.markdown(f"#### Condition {i+1}")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    category = st.selectbox(
                        "Category",
                        list(self.condition_types.keys()),
                        key=f"{condition_type}_cat_{i}"
                    )
                
                with col2:
                    indicator = st.selectbox(
                        "Indicator",
                        self.condition_types[category],
                        key=f"{condition_type}_ind_{i}"
                    )
                
                with col3:
                    if indicator in ['RSI', 'MACD', 'Moving Average']:
                        value = st.number_input(
                            "Value",
                            key=f"{condition_type}_val_{i}"
                        )
                    else:
                        value = st.text_input(
                            "Value",
                            key=f"{condition_type}_val_{i}"
                        )
                
                conditions.append({
                    "category": category,
                    "indicator": indicator,
                    "value": value
                })
        
        return conditions
