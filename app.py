import streamlit as st
from components.strategy_builder import StrategyBuilder

st.set_page_config(
    page_title="Crypto Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """Main application entry point."""
    try:
        st.title("Cryptocurrency Analysis Platform")
        
        # Create and render strategy builder
        strategy_builder = StrategyBuilder()
        strategy_builder.render()
        
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()