import streamlit as st
from typing import Dict, Any, Optional
from utils.data_fetcher import get_exchange_status, detect_region
from datetime import datetime
import pytz

def render_sidebar() -> Optional[Dict[str, Any]]:
    """
    Render the sidebar with enhanced filtering options and exchange status.
    """
    try:
        st.sidebar.title("Analysis Settings")
        
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
            
            st.session_state.selected_region = st.selectbox(
                "Select Region",
                options=list(regions.keys()),
                format_func=lambda x: regions[x],
                index=list(regions.keys()).index(st.session_state.selected_region),
                help="Choose your trading region"
            )
            
            # Timezone selection
            common_timezones = [
                'UTC',
                'America/New_York',
                'America/Chicago',
                'America/Los_Angeles',
                'Europe/London',
                'Europe/Paris',
                'Asia/Tokyo',
                'Asia/Shanghai',
                'Asia/Singapore',
                'Australia/Sydney'
            ]
            
            timezone_index = 0
            if st.session_state.selected_timezone in common_timezones:
                timezone_index = common_timezones.index(st.session_state.selected_timezone)
            
            st.session_state.selected_timezone = st.selectbox(
                "Select Timezone",
                options=common_timezones,
                index=timezone_index,
                help="Choose your preferred timezone"
            )
            
            # Display current time in selected timezone
            try:
                current_time = datetime.now(pytz.timezone(st.session_state.selected_timezone))
                st.info(f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            except Exception as e:
                st.warning(f"Error setting timezone: {str(e)}. Using UTC.")
                current_time = datetime.now(pytz.UTC)
                st.info(f"Current Time (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Exchange Status with improved visualization and error handling
        st.sidebar.subheader("Exchange Status")
        try:
            exchange_status = get_exchange_status()
            
            # Group exchanges by availability
            available_exchanges = []
            restricted_exchanges = []
            unavailable_exchanges = []
            
            for exchange_id, status in exchange_status.items():
                if status['status'] == 'available':
                    available_exchanges.append((exchange_id, status))
                elif status['status'] == 'restricted':
                    restricted_exchanges.append((exchange_id, status))
                else:
                    unavailable_exchanges.append((exchange_id, status))
            
            # Display available exchanges
            if available_exchanges:
                st.sidebar.markdown("#### 🟢 Available Exchanges")
                for exchange_id, status in available_exchanges:
                    with st.sidebar.expander(f"{exchange_id.upper()}"):
                        st.write("Features:", ", ".join(status.get('features', ['Basic trading'])))
                        st.write("Reliability:", f"{status.get('reliability', 0.0)*100:.1f}%")
                        if 'response_time' in status:
                            st.write("Response Time:", f"{status['response_time']*1000:.0f}ms")
                        st.write("Regions:", ", ".join(status.get('regions', ['GLOBAL'])))
            else:
                st.sidebar.warning("No exchanges currently available. Using fallback data sources.")
            
            # Display restricted exchanges
            if restricted_exchanges:
                st.sidebar.markdown("#### 🔸 Restricted Exchanges")
                for exchange_id, status in restricted_exchanges:
                    with st.sidebar.expander(f"{exchange_id.upper()}"):
                        st.write("Reason:", status.get('error', 'Region restricted'))
                        st.write("Available Regions:", ", ".join(status.get('regions', ['Unknown'])))
            
            # Display unavailable exchanges
            if unavailable_exchanges:
                st.sidebar.markdown("#### 🔴 Unavailable Exchanges")
                for exchange_id, status in unavailable_exchanges:
                    with st.sidebar.expander(f"{exchange_id.upper()}"):
                        st.write("Error:", status.get('error', 'Unknown error'))
        except Exception as e:
            st.sidebar.error(f"Error loading exchange status: {str(e)}")
            st.sidebar.info("Continuing with fallback data sources...")
        
        # Coin selection with regional filtering
        st.sidebar.subheader("Market Selection")
        selected_coins = st.sidebar.multiselect(
            "Select Cryptocurrencies",
            ["bitcoin", "ethereum", "binancecoin", "cardano", "solana"],
            default=["bitcoin"],
            help="Select cryptocurrencies to analyze"
        )
        
        # Timeframe selection
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
        
        # Market filters with regional optimization
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
        
        # Help section with regional considerations
        with st.sidebar.expander("Help & Information"):
            st.markdown("""
            ### How to use this platform:
            1. Set your region and timezone preferences
            2. Check exchange availability for your region
            3. Select cryptocurrencies to analyze
            4. Choose your preferred timeframe
            5. Enable technical indicators
            6. Use market filters to refine analysis
            
            #### Regional Access Guide:
            - 🟢 Available: Exchange is operational and accessible
            - 🔸 Restricted: Exchange has limited access in your region
            - 🔴 Unavailable: Exchange is currently not accessible
            - Region-specific features may vary by exchange
            """)
        
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
        st.sidebar.error(f"Error rendering sidebar: {str(e)}")
        st.sidebar.warning("Some features may be limited. Please refresh the page.")
        return None
