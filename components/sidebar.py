import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
import pytz
import logging
from utils.data_fetcher import get_exchange_status, detect_region
from utils.ui_components import show_error, show_exchange_status
from utils.symbol_converter import SymbolConverter

logger = logging.getLogger(__name__)

def display_exchange_formats():
    """Display exchange-specific symbol formats with enhanced information."""
    try:
        st.sidebar.markdown("### Exchange Format Guide")
        
        if not st.session_state.get('symbol_converter'):
            st.session_state.symbol_converter = SymbolConverter()
            
        exchange_formats = st.session_state.symbol_converter.get_exchange_formats()
        
        for exchange, format_info in exchange_formats.items():
            with st.sidebar.expander(f"{exchange.capitalize()} Format", expanded=False):
                st.markdown(f"**Description**: {format_info['description']}")
                st.markdown(f"**Example**: `{format_info['example']}`")
                
                if format_info.get('rules'):
                    st.markdown("**Rules:**")
                    for rule in format_info['rules']:
                        st.markdown(f"- {rule}")
                
                if format_info.get('special_cases'):
                    st.markdown("**Special Cases:**")
                    for original, special in format_info['special_cases'].items():
                        st.code(f"{original} → {special}")
                        
        logger.debug("Exchange formats displayed successfully")
                    
    except Exception as e:
        logger.error(f"Error displaying exchange formats: {str(e)}")
        st.sidebar.error("Error displaying format examples")

def get_exchange_config() -> Dict[str, Any]:
    """Get exchange configuration and status with improved error handling."""
    try:
        exchange_status = get_exchange_status()
        if exchange_status:
            return {
                'status': exchange_status,
                'region': st.session_state.get('selected_region', detect_region()),
                'timezone': st.session_state.get('selected_timezone', 'UTC')
            }
        return {}
    except Exception as e:
        logger.error(f"Error fetching exchange configuration: {str(e)}")
        show_error("Exchange Configuration Error", str(e))
        return {}

def render_sidebar() -> Optional[Dict[str, Any]]:
    """Render the sidebar with enhanced filtering options and exchange status."""
    try:
        st.sidebar.title("Analysis Settings")

        # Display exchange formats first
        display_exchange_formats()

        # Exchange Status
        st.sidebar.subheader("Exchange Status")
        exchange_config = get_exchange_config()
        if exchange_config.get('status'):
            show_exchange_status(exchange_config['status'])

        # Initialize session state for region and timezone if not exists
        if 'selected_region' not in st.session_state:
            st.session_state.selected_region = detect_region()
        if 'selected_timezone' not in st.session_state:
            st.session_state.selected_timezone = 'UTC'

        # Regional Settings Section
        with st.sidebar.expander("📍 Regional Settings", expanded=True):
            regions = {
                'NA': 'North America',
                'EU': 'Europe',
                'ASIA': 'Asia',
                'OCE': 'Oceania',
                'SA': 'South America',
                'AF': 'Africa',
                'GLOBAL': 'Global'
            }

            current_region = st.session_state.selected_region or 'GLOBAL'
            region_index = list(regions.keys()).index(current_region) if current_region in regions else list(regions.keys()).index('GLOBAL')

            selected_region = st.selectbox(
                "Select Region",
                options=list(regions.keys()),
                format_func=lambda x: regions[x],
                index=region_index,
                help="Choose your trading region"
            )
            st.session_state.selected_region = selected_region

            # Timezone selection with error handling
            common_timezones = [
                'UTC', 'America/New_York', 'America/Chicago',
                'America/Los_Angeles', 'Europe/London', 'Europe/Paris',
                'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Singapore',
                'Australia/Sydney'
            ]

            current_timezone = st.session_state.selected_timezone
            timezone_index = common_timezones.index(current_timezone) if current_timezone in common_timezones else 0

            selected_timezone = st.selectbox(
                "Select Timezone",
                options=common_timezones,
                index=timezone_index,
                help="Choose your preferred timezone"
            )
            st.session_state.selected_timezone = selected_timezone

            try:
                selected_timezone = st.session_state.selected_timezone or 'UTC'
                tz = pytz.timezone(selected_timezone)
                current_time = datetime.now(tz)
                st.info(f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            except Exception as e:
                logger.warning(f"Error setting timezone: {str(e)}. Using UTC.")
                current_time = datetime.now(pytz.UTC)
                st.info(f"Current Time (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        # Market Selection with error handling
        st.sidebar.subheader("Market Selection")
        selected_coins = st.sidebar.multiselect(
            "Select Cryptocurrencies",
            ["bitcoin", "ethereum", "binancecoin", "cardano", "solana"],
            default=["bitcoin"],
            help="Select cryptocurrencies to analyze"
        )

        timeframe = st.sidebar.selectbox(
            "Select Timeframe",
            ["7", "30", "90", "365"],
            index=1,
            format_func=lambda x: f"{x} days",
            help="Choose analysis timeframe"
        )

        # Technical indicators
        st.sidebar.subheader("Technical Indicators")
        selected_indicators = {
            "SMA": st.sidebar.checkbox("Simple Moving Average", value=True),
            "EMA": st.sidebar.checkbox("Exponential Moving Average"),
            "RSI": st.sidebar.checkbox("Relative Strength Index"),
            "MACD": st.sidebar.checkbox("MACD")
        }

        # Market filters
        st.sidebar.subheader("Market Filters")
        min_volume = st.sidebar.number_input(
            "Minimum 24h Volume (USD)",
            min_value=0,
            value=100000,
            step=10000,
            help="Filter by minimum trading volume"
        )

        regional_only = st.sidebar.checkbox(
            "Show Regional Exchanges Only",
            value=True,
            help="Filter to show only exchanges available in your region"
        )

        return {
            'selected_coins': selected_coins,
            'timeframe': timeframe,
            'indicators': selected_indicators,
            'filters': {
                'min_volume': min_volume,
                'regional_only': regional_only
            },
            'region': st.session_state.selected_region,
            'timezone': st.session_state.selected_timezone
        }

    except Exception as e:
        logger.error(f"Critical error in sidebar rendering: {str(e)}")
        show_error("Sidebar Error", str(e))
        return {
            'selected_coins': ["bitcoin"],
            'timeframe': "30",
            'indicators': {"SMA": True},
            'filters': {
                'min_volume': 100000,
                'regional_only': True
            },
            'region': 'GLOBAL',
            'timezone': 'UTC'
        }

if __name__ == "__main__":
    render_sidebar()
