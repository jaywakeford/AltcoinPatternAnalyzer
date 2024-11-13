import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime

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

def show_warning(title: str, message: str, suggestion: str = None):
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
    
    .warning-suggestion {{
        margin-top: 10px;
        font-style: italic;
        color: #ffd700;
    }}
    </style>
    <div class="warning-message">
        <div class="warning-title">⚠️ {title}</div>
        <div class="warning-content">{message}</div>
        {f'<div class="warning-suggestion">💡 {suggestion}</div>' if suggestion else ''}
    </div>
    """, unsafe_allow_html=True)

def show_success(title: str, message: str):
    """Display styled success message."""
    st.markdown(f"""
    <style>
    .success-message {{
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        background: rgba(0,255,0,0.1);
        border: 1px solid rgba(0,255,0,0.2);
    }}
    
    .success-title {{
        font-weight: bold;
        margin-bottom: 5px;
        color: #00ff00;
    }}
    
    .success-content {{
        margin: 5px 0;
    }}
    </style>
    <div class="success-message">
        <div class="success-title">✅ {title}</div>
        <div class="success-content">{message}</div>
    </div>
    """, unsafe_allow_html=True)

def show_exchange_status(exchange_status: Dict[str, Dict[str, Any]]):
    """Display detailed exchange status information."""
    st.markdown("""
    <style>
    .exchange-status {
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        background: rgba(0,0,0,0.2);
    }
    
    .exchange-header {
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .exchange-item {
        padding: 10px;
        margin: 5px 0;
        border-radius: 3px;
    }
    
    .status-available {
        background: rgba(0,255,0,0.1);
        border: 1px solid rgba(0,255,0,0.2);
    }
    
    .status-unavailable {
        background: rgba(255,0,0,0.1);
        border: 1px solid rgba(255,0,0,0.2);
    }
    
    .status-restricted {
        background: rgba(255,165,0,0.1);
        border: 1px solid rgba(255,165,0,0.2);
    }
    
    .exchange-details {
        margin-top: 5px;
        font-size: 0.9em;
        color: #888;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### Exchange Status")
    
    for exchange_id, status in exchange_status.items():
        status_class = f"status-{status['status']}"
        status_icon = "🟢" if status['status'] == 'available' else "🔴" if status['status'] == 'unavailable' else "⚠️"
        
        st.markdown(f"""
        <div class="exchange-item {status_class}">
            <div class="exchange-header">
                {status_icon} {exchange_id.upper()}
            </div>
            <div class="exchange-details">
                Status: {status['status'].capitalize()}<br>
                {'Features: ' + ', '.join(status.get('features', [])) + '<br>' if 'features' in status else ''}
                {'Reliability: ' + f"{status.get('reliability', 0)*100:.1f}%" + '<br>' if 'reliability' in status else ''}
                {'Error: ' + status.get('error') + '<br>' if 'error' in status else ''}
                Last checked: {status.get('last_checked', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
            </div>
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

def show_data_source_info(source: str, details: Optional[Dict[str, Any]] = None):
    """Display information about the current data source."""
    st.markdown(f"""
    <style>
    .data-source-info {{
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        background: rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.1);
    }}
    </style>
    <div class="data-source-info">
        <strong>Data Source:</strong> {source.upper()}
        {f"<br><small>{', '.join(f'{k}: {v}' for k, v in details.items())}</small>" if details else ""}
    </div>
    """, unsafe_allow_html=True)
