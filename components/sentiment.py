import streamlit as st
import plotly.graph_objects as go
from utils.sentiment_analyzer import SentimentAnalyzer
from datetime import datetime

def render_sentiment_analysis(selected_coins):
    """Render sentiment analysis section with detailed source attribution and loading states."""
    if not selected_coins:
        st.warning("Please select at least one cryptocurrency to analyze sentiment.")
        return
    
    # Initialize analyzer with error handling
    try:
        analyzer = SentimentAnalyzer()
    except Exception as e:
        st.error("⚠️ Failed to initialize sentiment analysis")
        st.info("💡 Please try refreshing the page or check your internet connection.")
        return
    
    st.caption("""
    Sentiment analysis combines data from multiple sources including RSS feeds, price movements, and social media. 
    Hover over the metrics to see more details about confidence scores and data sources.
    """)
    
    # Create columns for each selected coin
    cols = st.columns(min(len(selected_coins), 3))  # Limit to 3 columns per row
    
    for idx, coin in enumerate(selected_coins):
        col_idx = idx % 3
        with cols[col_idx]:
            with st.container():
                st.markdown(f"### {coin.upper()}")
                
                with st.spinner(f"Analyzing sentiment for {coin}..."):
                    sentiment_data = analyzer.get_crypto_news_sentiment(coin.lower())
                    
                    if sentiment_data.get('error'):
                        if sentiment_data.get('failed_sources'):
                            st.warning(f"⚠️ Error analyzing {coin}: Some sources failed: {', '.join(sentiment_data['failed_sources'])}")
                        else:
                            st.warning(f"⚠️ Error analyzing {coin}: {sentiment_data['error']}")
                        st.info("""
                        💡 The analysis will continue with available sources.
                        Try refreshing in a few minutes if the issue persists.
                        """)
                    
                    if sentiment_data['samples'] == 0:
                        st.info(f"No recent sentiment data found for {coin}")
                        continue
                    
                    # Display sentiment gauge
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=sentiment_data['score'],
                        title={'text': "Market Sentiment"},
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
                    
                    # Display confidence score
                    confidence = sentiment_data['confidence'] * 100
                    confidence_color = (
                        "green" if confidence >= 70 else 
                        "yellow" if confidence >= 40 else 
                        "red"
                    )
                    
                    st.markdown(f"""
                    **Overall Confidence:** :{confidence_color}[{confidence:.1f}%]  
                    **Total Samples:** {sentiment_data['samples']}  
                    **Sentiment Category:** {sentiment_data['sentiment_category'].title()}
                    """)
                    
                    # Display source breakdown
                    if sentiment_data['sources']:
                        st.markdown("#### Data Sources")
                        for source in sentiment_data['sources']:
                            source_score = source['score'] * 100
                            st.markdown(f"""
                            - **{source['name']}**
                                - Score: {source_score:+.1f}%
                                - Samples: {source['samples']}
                                - Confidence: {source['confidence']*100:.1f}%
                            """)
                    
                    # Display last updated time
                    st.caption(f"""
                    🕒 Last updated: {datetime.fromisoformat(sentiment_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')}
                    """)

def _get_sentiment_color(score: float) -> str:
    """Return color based on sentiment score."""
    if score >= 25:
        return "rgb(0, 255, 0)"  # Green for positive
    elif score <= -25:
        return "rgb(255, 0, 0)"  # Red for negative
    return "rgb(128, 128, 128)"  # Gray for neutral
