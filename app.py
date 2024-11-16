import streamlit as st
import pandas as pd
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from utils.data_fetcher import ExchangeManager
from styles.theme import apply_custom_theme
from components.sidebar import render_sidebar
from components.altcoin_analysis import render_altcoin_analysis
from components.backtesting import render_backtesting_section
from utils.symbol_converter import SymbolConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables."""
    try:
        if 'initialized' not in st.session_state:
            st.session_state.update({
                'initialized': True,
                'symbol_converter': None,
                'exchange_manager': None,
                'sidebar_config': None,
                'symbol_cache': {},
                'conversion_log': [],
                'last_update': datetime.now(),
                'cache_stats': None
            })
            logger.info("Session state initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        raise

def display_cache_metrics():
    """Display cache metrics in a formatted way."""
    try:
        if not st.session_state.get('cache_stats'):
            return

        cache_stats = st.session_state.cache_stats
        
        st.sidebar.markdown("### Symbol Cache Statistics")
        
        # Display cache usage
        usage_percentage = (cache_stats['cache_size'] / cache_stats['max_cache_size']) * 100
        st.sidebar.progress(usage_percentage / 100)
        st.sidebar.caption(f"Cache Usage: {cache_stats['cache_size']}/{cache_stats['max_cache_size']}")
        
        # Display hit rate
        if cache_stats['total_requests'] > 0:
            hit_rate = cache_stats['hit_rate']
            st.sidebar.metric("Cache Hit Rate", f"{hit_rate:.1f}%")
        
        # Display cache TTL
        st.sidebar.metric("Cache TTL", f"{cache_stats['cache_ttl_hours']:.1f} hours")
        
        # Display active pairs in an expander
        with st.sidebar.expander("Frequently Used Pairs"):
            if cache_stats.get('frequently_used_pairs'):
                for pair in cache_stats['frequently_used_pairs']:
                    st.code(pair, language='text')
            else:
                st.info("No frequently used pairs configured")
                
        # Display recent cache operations
        with st.sidebar.expander("Cache Operations"):
            st.metric("Cache Hits", cache_stats['cache_hits'])
            st.metric("Cache Misses", cache_stats['cache_misses'])
            st.text(f"Last Clear: {cache_stats['last_clear']}")

    except Exception as e:
        logger.error(f"Error displaying cache metrics: {str(e)}")
        st.sidebar.error("Error displaying cache statistics")

def main():
    """Main application entry point."""
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
        initialize_session_state()

        # Initialize components only if not already initialized
        if not st.session_state.get('symbol_converter'):
            st.session_state.symbol_converter = SymbolConverter()
            logger.info("SymbolConverter initialized")

        if not st.session_state.get('exchange_manager'):
            st.session_state.exchange_manager = ExchangeManager()
            logger.info("ExchangeManager initialized")

        # Update cache statistics
        st.session_state.cache_stats = st.session_state.symbol_converter.get_cache_stats()

        # Page title and description
        st.title("Cryptocurrency Analysis Platform")
        st.markdown("""
        Welcome to the Cryptocurrency Analysis Platform! 
        Select cryptocurrencies from the sidebar to begin analysis.
        """)

        # Render sidebar with cache metrics
        sidebar_config = render_sidebar()
        st.session_state.sidebar_config = sidebar_config
        display_cache_metrics()

        # Main content area
        if sidebar_config and sidebar_config.get('selected_coins'):
            selected_coins = sidebar_config['selected_coins']

            # Create main columns
            col1, col2 = st.columns([2, 1])

            # Dictionary to store converted symbols
            converted_symbols = {}

            with col1:
                # Symbol conversion and analysis section
                for coin in selected_coins:
                    with st.container():
                        st.markdown(f"### Analysis for {coin}")
                        
                        if st.session_state.symbol_converter:
                            trading_symbol = st.session_state.symbol_converter.convert_from_coin_name(coin)
                            converted_symbols[coin] = trading_symbol
                            
                            if trading_symbol:
                                st.success(f"Trading Symbol: {trading_symbol}")
                                
                                # Show conversion details
                                with st.expander("Symbol Conversion Details"):
                                    st.json({
                                        "original": coin,
                                        "trading_symbol": trading_symbol,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "cache_status": "hit" if trading_symbol in st.session_state.cache_stats['active_keys'] else "miss"
                                    })
                            else:
                                st.error(f"Could not convert {coin} to trading symbol")

            with col2:
                # Cache monitoring section
                st.markdown("### Cache Monitor")
                if st.session_state.cache_stats:
                    # Display active cache entries
                    with st.expander("Active Cache Entries", expanded=False):
                        active_keys = st.session_state.cache_stats['active_keys']
                        if active_keys:
                            for key in active_keys:
                                st.code(key, language='text')
                        else:
                            st.info("No active cache entries")
                    
                    # Cache maintenance controls
                    if st.button("Clear Cache"):
                        st.session_state.symbol_converter.clear_cache()
                        st.session_state.cache_stats = st.session_state.symbol_converter.get_cache_stats()
                        st.success("Cache cleared successfully")

            # Analysis tabs
            tab1, tab2, tab3 = st.tabs([
                "📈 Market Analysis",
                "🔄 Altcoin Analysis",
                "⚙️ Strategy Builder"
            ])

            with tab1:
                st.markdown("### Market Analysis")
                for coin, symbol in converted_symbols.items():
                    if symbol:
                        st.info(f"Analyzing {symbol}")

            with tab2:
                render_altcoin_analysis()

            with tab3:
                render_backtesting_section()

        else:
            st.info("👈 Please select cryptocurrencies from the sidebar to begin analysis.")

    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")
        st.exception(e)

if __name__ == "__main__":
    main()
