import streamlit as st
import plotly.graph_objects as go
from utils.sentiment_analyzer import SentimentAnalyzer

def render_sentiment_analysis(selected_coins):
    """Render sentiment analysis section."""
    st.subheader("Social Media Sentiment Analysis")
    
    analyzer = SentimentAnalyzer()
    
    # Create columns for each selected coin
    if not selected_coins:
        st.warning("Please select at least one cryptocurrency to analyze sentiment.")
        return

    cols = st.columns(min(len(selected_coins), 3))  # Limit to 3 columns per row
    
    for idx, coin in enumerate(selected_coins):
        col_idx = idx % 3
        with cols[col_idx]:
            sentiment_data = analyzer.get_twitter_sentiment(coin)
            
            if 'error' in sentiment_data:
                st.error(f"Error analyzing {coin}: {sentiment_data['error']}")
                continue
            
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=sentiment_data['score'],
                title={'text': f"{coin.title()} Sentiment"},
                gauge={
                    'axis': {'range': [-100, 100]},
                    'bar': {'color': _get_sentiment_color(sentiment_data['score'])},
                    'steps': [
                        {'range': [-100, -25], 'color': "rgba(255, 0, 0, 0.3)"},
                        {'range': [-25, 25], 'color': "rgba(128, 128, 128, 0.3)"},
                        {'range': [25, 100], 'color': "rgba(0, 255, 0, 0.3)"}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 2},
                        'thickness': 0.75,
                        'value': sentiment_data['score']
                    }
                }
            ))
            
            fig.update_layout(
                height=200,
                margin=dict(l=10, r=10, t=50, b=10),
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add metrics with color-coded sentiment
            st.metric(
                "Sample Size",
                f"{sentiment_data['samples']} tweets",
                delta=sentiment_data['sentiment_category'].title(),
                delta_color="normal"
            )

            # Add timestamp of analysis
            st.caption(f"Last updated: {sentiment_data['timestamp']}")

def _get_sentiment_color(score: float) -> str:
    """Return color based on sentiment score."""
    if score >= 25:
        return "rgb(0, 255, 0)"
    elif score <= -25:
        return "rgb(255, 0, 0)"
    return "rgb(128, 128, 128)"
