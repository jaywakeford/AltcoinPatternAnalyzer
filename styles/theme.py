import streamlit as st

def apply_custom_theme():
    """Apply custom CSS styling with optimized layout and content sizing."""
    st.markdown("""
        <style>
        /* Base styles */
        :root {
            --primary-color: #FF4B4B;
            --background-color: #0E1117;
            --secondary-background: rgba(255, 255, 255, 0.05);
            --text-color: #FAFAFA;
        }

        /* Main container */
        .main {
            background-color: var(--background-color);
            color: var(--text-color);
            max-width: 1400px !important;
            padding: 2rem !important;
            margin: 0 auto !important;
        }

        /* Headers */
        h1, h2, h3 {
            color: var(--text-color) !important;
        }

        /* Container elements */
        .stMarkdown, .stButton, .stSelectbox, .stMultiSelect {
            margin: 1rem 0 !important;
        }

        /* Content sections */
        .content-section {
            background: var(--secondary-background);
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Cache metrics styling */
        .cache-metrics {
            background: var(--secondary-background);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }

        /* Progress bar styling */
        .stProgress > div > div {
            background-color: var(--primary-color) !important;
        }

        /* Metric value styling */
        [data-testid="stMetricValue"] {
            background: rgba(255, 255, 255, 0.05);
            padding: 0.5rem;
            border-radius: 4px;
            font-size: 1.2rem !important;
        }

        /* Code block styling */
        .stCodeBlock {
            background: rgba(0, 0, 0, 0.2) !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 4px;
        }

        /* Success/Error message styling */
        .stSuccess, .stError {
            padding: 0.5rem !important;
            border-radius: 4px !important;
        }

        /* Button styling */
        .stButton > button {
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            border-radius: 4px !important;
        }

        /* Info box styling */
        .stInfo {
            background-color: rgba(255, 255, 255, 0.05) !important;
            color: var(--text-color) !important;
            padding: 1rem !important;
            border-radius: 4px !important;
        }
        </style>
    """, unsafe_allow_html=True)