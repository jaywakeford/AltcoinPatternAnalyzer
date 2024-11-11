import streamlit as st

def apply_custom_theme():
    """Apply custom CSS styling."""
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .stMetric {
            background-color: rgba(28, 131, 225, 0.1);
            border-radius: 10px;
            padding: 1rem;
        }
        
        .stMetric:hover {
            background-color: rgba(28, 131, 225, 0.2);
            transition: background-color 0.3s ease;
        }
        
        .stPlotlyChart {
            border-radius: 10px;
            background-color: rgba(0, 0, 0, 0.1);
            padding: 1rem;
        }
        
        /* Dark mode adjustments */
        @media (prefers-color-scheme: dark) {
            .stApp {
                background-color: #0E1117;
            }
            
            .stMetric {
                background-color: rgba(255, 255, 255, 0.05);
            }
        }
        </style>
    """, unsafe_allow_html=True)
