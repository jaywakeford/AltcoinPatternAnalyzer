import streamlit as st
import plotly.graph_objects as go
from utils.sentiment_analyzer import SentimentAnalyzer

def render_sentiment_analysis(selected_coins):
    """Render sentiment analysis section."""
    st.subheader("Social Media & News Sentiment Analysis")
    
    if not selected_coins:
        st.warning("Please select at least one cryptocurrency to analyze sentiment.")
        return

    # Initialize analyzer with error handling
    try:
        analyzer = SentimentAnalyzer()
    except Exception as e:
        st.error(f"Error initializing sentiment analyzer: {str(e)}")
        return
    
    # Create columns for each selected coin
    cols = st.columns(min(len(selected_coins), 3))  # Limit to 3 columns per row
    
    for idx, coin in enumerate(selected_coins):
        col_idx = idx % 3
        with cols[col_idx]:
            with st.spinner(f"Analyzing sentiment for {coin}..."):
                sentiment_data = analyzer.get_crypto_news_sentiment(coin)
                
                if 'error' in sentiment_data and sentiment_data['error']:
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
                
                # Display sentiment sources
                if sentiment_data.get('sources'):
                    for source in sentiment_data['sources']:
                        source_color = "normal"
                        if source['name'] == 'Twitter':
                            source_color = "off" if source['score'] < 0 else "normal"
                        
                        st.metric(
                            f"{source['name']} ({source['samples']} {'tweets' if source['name'] == 'Twitter' else 'articles'})",
                            value=f"Score: {source['score']*100:.1f}",
                            delta=sentiment_data['sentiment_category'].title(),
                            delta_color=source_color
                        )

                    # Add total samples and timestamp
                    st.caption(f"Total samples analyzed: {sentiment_data['samples']}")
                    st.caption(f"Last updated: {sentiment_data['timestamp']}")
                else:
                    st.info(f"No recent data found for {coin}")
                
                # Add source attribution
                with st.expander("Data Sources"):
                    st.markdown("""
                    - Twitter API
                    - CoinTelegraph RSS Feed
                    - CoinDesk RSS Feed
                    - Bitcoin.com RSS Feed
                    - CryptoCompare News API
                    """)

def _get_sentiment_color(score: float) -> str:
    """Return color based on sentiment score."""
    if score >= 25:
        return "rgb(0, 255, 0)"  # Green for positive
    elif score <= -25:
        return "rgb(255, 0, 0)"  # Red for negative
    return "rgb(128, 128, 128)"  # Gray for neutral
