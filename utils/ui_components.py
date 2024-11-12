import streamlit as st

def show_error(title: str, message: str, suggestion: str = None):
    """Display styled error message."""
    st.markdown(f"""
    <style>
    .error-message {{
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        background: rgba(255,0,0,0.1);
        border: 1px solid rgba(255,0,0,0.2);
    }}
    
    .error-title {{
        font-weight: bold;
        margin-bottom: 5px;
        color: #ff4b4b;
    }}
    
    .error-content {{
        margin: 5px 0;
    }}
    
    .error-suggestion {{
        margin-top: 10px;
        font-style: italic;
        color: #ffd700;
    }}
    </style>
    <div class="error-message">
        <div class="error-title">❌ {title}</div>
        <div class="error-content">{message}</div>
        {f'<div class="error-suggestion">💡 {suggestion}</div>' if suggestion else ''}
    </div>
    """, unsafe_allow_html=True)

def show_warning(title: str, message: str):
    """Display styled warning message."""
    st.markdown(f"""
    <style>
    .warning-message {{
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        background: rgba(255,165,0,0.1);
        border: 1px solid rgba(255,165,0,0.2);
    }}
    
    .warning-title {{
        font-weight: bold;
        margin-bottom: 5px;
        color: #ffa500;
    }}
    
    .warning-content {{
        margin: 5px 0;
    }}
    </style>
    <div class="warning-message">
        <div class="warning-title">⚠️ {title}</div>
        <div class="warning-content">{message}</div>
    </div>
    """, unsafe_allow_html=True)

def group_elements(title: str):
    """Context manager for grouping related elements."""
    class GroupContext:
        def __init__(self, title):
            self.title = title
            
        def __enter__(self):
            st.markdown(f"""
            <style>
            .element-group {{
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 5px;
                padding: 10px;
                margin: 10px 0;
                background: rgba(0,0,0,0.2);
            }}
            
            .group-title {{
                font-size: 1.1em;
                font-weight: bold;
                margin-bottom: 10px;
                color: #FF4B4B;
                padding: 5px 10px;
                background: rgba(255,75,75,0.1);
                border-radius: 3px;
                display: inline-block;
            }}
            
            .group-content {{
                padding: 10px;
            }}
            </style>
            <div class="element-group">
                <div class="group-title">{self.title}</div>
                <div class="group-content">
            """, unsafe_allow_html=True)
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            st.markdown("</div></div>", unsafe_allow_html=True)
            
    return GroupContext(title)
