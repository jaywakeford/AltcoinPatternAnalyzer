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
            max-width: 1400px !important;
            padding: 2rem !important;
            margin: 0 auto !important;
        }

        /* Headers */
        h1 {
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            margin-bottom: 1.5rem !important;
            color: var(--text-color) !important;
        }

        h2, h3 {
            font-size: 1.8rem !important;
            font-weight: 600 !important;
            margin: 1.5rem 0 1rem !important;
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

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: rgba(0, 0, 0, 0.2) !important;
            padding: 2rem !important;
            min-width: 300px !important;
            max-width: 350px !important;
        }

        .sidebar .sidebar-content {
            padding: 1.5rem !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            background-color: rgba(0, 0, 0, 0.2);
            padding: 0.75rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            padding: 0 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
            border: none !important;
            font-weight: 500;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: var(--primary-color) !important;
            color: white !important;
        }

        /* Metric cards */
        [data-testid="stMetricValue"] {
            background: rgba(0, 0, 0, 0.2);
            padding: 1rem;
            border-radius: 10px;
            font-size: 1.5rem !important;
            font-weight: 600 !important;
        }

        /* Buttons */
        .stButton > button {
            width: 100%;
            background: var(--primary-color) !important;
            color: white !important;
            padding: 0.75rem 1.5rem !important;
            border: none !important;
            border-radius: 5px !important;
            font-weight: 500 !important;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        /* DataFrames */
        .stDataFrame {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }

        /* Plotly charts */
        .js-plotly-plot, .plot-container {
            background: rgba(0, 0, 0, 0.2) !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
            min-height: 400px !important;
        }

        /* Form inputs */
        .stTextInput > div > div, .stNumberInput > div > div {
            background: rgba(0, 0, 0, 0.2) !important;
            border-radius: 5px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            min-height: 40px !important;
        }

        /* Alerts */
        .stAlert {
            background: rgba(0, 0, 0, 0.2) !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 5px !important;
        }

        /* Loading spinner */
        .stSpinner > div {
            border-color: var(--primary-color) !important;
        }
        
        /* Scrollbars */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 5px;
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .main {
                padding: 1rem !important;
            }
            
            h1 {
                font-size: 2rem !important;
            }
            
            h2, h3 {
                font-size: 1.5rem !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                padding: 0 1rem;
                height: 2.5rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)
