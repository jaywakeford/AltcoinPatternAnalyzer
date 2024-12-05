import streamlit as st
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from utils.data_fetcher import ExchangeManager
from styles.theme import apply_custom_theme
from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.backtesting import render_backtesting_section
from components.portfolio_tracker import render_portfolio_section
from utils.symbol_converter import SymbolConverter
from utils.technical_indicators import TechnicalIndicators
from utils.social_sentiment import render_sentiment_section
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def initialize_session_state() -> bool:
    """Initialize session state variables with enhanced error handling."""
    try:
        if 'initialized' not in st.session_state:
            logger.info("Starting session state initialization")
            
            # Initialize symbol converter
            st.session_state.symbol_converter = SymbolConverter()
            
            # Initialize other session state variables
            st.session_state.update({
                'initialized': True,
                'exchange_manager': ExchangeManager(),
                'last_update': datetime.now(),
                'supported_exchanges': ['kraken', 'kucoin', 'binance'],
                'selected_timeframe': '1d',
                'selected_view': 'real-time'
            })
            
            logger.info("Session state initialized successfully")
            return True
            
        return True
        
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        st.error(f"Error initializing application: {str(e)}")
        return False

def main():
    """Main application entry point with enhanced error handling."""
    try:
        # Set page config first
        st.set_page_config(
            page_title="Crypto Analysis Platform",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply custom theme
        apply_custom_theme()
        
        # Initialize session state
        if not initialize_session_state():
            st.error("Failed to initialize application. Please refresh the page.")
            return
        
        # Page title and description
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Welcome to the Cryptocurrency Analysis Platform!
        This platform provides real-time analysis with custom symbol format support for multiple exchanges.
        """)

        # Render sidebar with error handling
        try:
            sidebar_config = render_sidebar()
            if not sidebar_config:
                st.warning("Please configure analysis settings in the sidebar")
                return
        except Exception as e:
            logger.error(f"Error rendering sidebar: {str(e)}")
            st.error("Error loading configuration interface")
            return
        
        # Create main navigation tabs
        main_tabs = st.tabs([
            "📊 Market Analysis",
            "📈 Historical Analysis",
            "💼 Portfolio Tracker",
            "📊 Technical Analysis",
            "🗣️ Social Sentiment",
            "⚙️ Strategy Builder"
        ])
        
        # Market Analysis Tab
        with main_tabs[0]:
            try:
                render_altcoin_analysis(view_mode="real-time")
            except Exception as e:
                logger.error(f"Error in market analysis tab: {str(e)}")
                st.error("Error loading market analysis")

        # Historical Analysis Tab
        with main_tabs[1]:
            try:
                render_altcoin_analysis(view_mode="historical")
            except Exception as e:
                logger.error(f"Error in historical analysis tab: {str(e)}")
                st.error("Error loading historical analysis")

        # Portfolio Tracker Tab
        with main_tabs[2]:
            try:
                render_portfolio_section()
            except Exception as e:
                logger.error(f"Error in portfolio tracker tab: {str(e)}")
                st.error("Error loading portfolio tracker")

        # Technical Analysis Tab
        with main_tabs[3]:
            try:
                selected_symbol = st.selectbox(
                    "Select Cryptocurrency",
                    ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
                )
                timeframe = st.selectbox(
                    "Select Timeframe",
                    ["1d", "4h", "1h", "15m"]
                )
                
                if selected_symbol and timeframe:
                    exchange_manager = ExchangeManager()
                    data = exchange_manager.get_historical_data(selected_symbol, timeframe)
                    
                    if not data.empty:
                        data = TechnicalIndicators.add_all_indicators(data)
                        
                        # Create technical analysis charts
                        fig = make_subplots(
                            rows=3, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.05,
                            row_heights=[0.5, 0.25, 0.25]
                        )
                        
                        # Price and MA Chart
                        fig.add_trace(go.Candlestick(
                            x=data.index,
                            open=data['open'],
                            high=data['high'],
                            low=data['low'],
                            close=data['close'],
                            name='Price'
                        ), row=1, col=1)
                        
                        # Add Moving Averages
                        for ma in [20, 50, 200]:
                            fig.add_trace(go.Scatter(
                                x=data.index,
                                y=data[f'SMA_{ma}'],
                                name=f'SMA {ma}',
                                line=dict(width=1)
                            ), row=1, col=1)
                        
                        # Volume Chart
                        fig.add_trace(go.Bar(
                            x=data.index,
                            y=data['volume'],
                            name='Volume'
                        ), row=2, col=1)
                        
                        # RSI Chart
                        fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data['RSI'],
                            name='RSI'
                        ), row=3, col=1)
                        
                        # Update layout
                        fig.update_layout(
                            title=f'{selected_symbol} Technical Analysis',
                            xaxis_title='Date',
                            height=800,
                            template='plotly_dark'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display additional indicators
                        with st.expander("View All Technical Indicators"):
                            indicators_df = pd.DataFrame({
                                'MACD': data['MACD'].iloc[-1],
                                'RSI': data['RSI'].iloc[-1],
                                'Stochastic K': data['Stoch_K'].iloc[-1],
                                'Stochastic D': data['Stoch_D'].iloc[-1],
                                'Williams %R': data['Williams_R'].iloc[-1],
                                'MFI': data['MFI'].iloc[-1],
                                'OBV': data['OBV'].iloc[-1],
                                'ATR': data['ATR'].iloc[-1]
                            }, index=[0])
                            
                            st.dataframe(indicators_df.style.format("{:.2f}"))
                    else:
                        st.warning("No data available for the selected symbol and timeframe")
                        
            except Exception as e:
                logger.error(f"Error in technical analysis tab: {str(e)}")
                st.error("Error loading technical analysis")

        # Social Sentiment Tab
        with main_tabs[4]:
            try:
                selected_symbol = st.selectbox(
                    "Select Cryptocurrency for Sentiment Analysis",
                    ["BTC", "ETH", "BNB", "SOL", "ADA"]
                )
                if selected_symbol:
                    render_sentiment_section(selected_symbol)
            except Exception as e:
                logger.error(f"Error in sentiment analysis tab: {str(e)}")
                st.error("Error loading sentiment analysis")

        # Strategy Builder Tab
        with main_tabs[5]:
            try:
                render_backtesting_section()
            except Exception as e:
                logger.error(f"Error in strategy builder tab: {str(e)}")
                st.error("Error loading strategy builder")
            
    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    main()
