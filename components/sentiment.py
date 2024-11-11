import streamlit as st
import plotly.graph_objects as go
from utils.sentiment_analyzer import SentimentAnalyzer
from datetime import datetime

def render_sentiment_analysis(selected_coins):
    """Render sentiment analysis section with detailed source attribution and loading states."""
    st.subheader("Social Media & News Sentiment Analysis")
    
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
            try:
                st.markdown(f"### {coin.upper()}")
                
                # Create placeholders for loading states
                gauge_placeholder = st.empty()
                metrics_placeholder = st.empty()
                sources_placeholder = st.empty()
                
                with st.spinner(f"🔄 Analyzing sentiment for {coin}..."):
                    sentiment_data = analyzer.get_crypto_news_sentiment(coin.lower())
                    
                    if sentiment_data.get('error'):
                        st.error(f"⚠️ Error analyzing {coin}: {sentiment_data['error']}")
                        st.help("""
                        Some data sources might be temporarily unavailable. 
                        The analysis will continue with available sources.
                        Try refreshing in a few minutes if the issue persists.
                        """)
                        continue
                    
                    if sentiment_data['samples'] == 0:
                        st.info(f"ℹ️ No recent sentiment data found for {coin}")
                        continue
                    
                    # Create gauge chart
                    with gauge_placeholder:
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=sentiment_data['score'],
                            title={'text': f"Market Sentiment"},
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
                    
                    # Display sentiment metrics with tooltips
                    with metrics_placeholder:
                        if 'confidence' in sentiment_data:
                            confidence = sentiment_data['confidence'] * 100
                            confidence_color = (
                                "green" if confidence >= 70 else 
                                "yellow" if confidence >= 40 else 
                                "red"
                            )
                            st.markdown(f"""
                            <div title="Confidence score indicates the reliability of the sentiment analysis based on data quality and quantity">
                                **Overall Confidence:** :{confidence_color}[{confidence:.1f}%]
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Display source-specific metrics
                    with sources_placeholder:
                        st.markdown("#### Data Sources")
                        for source in sentiment_data.get('sources', []):
                            confidence = source.get('confidence', 0) * 100
                            confidence_indicator = (
                                "🟢" if confidence >= 70 else
                                "🟡" if confidence >= 40 else
                                "🔴"
                            )
                            
                            source_type = (
                                "tweets" if source['name'] == 'Twitter' else
                                "articles" if source['name'] == 'RSS Feeds' else
                                "indicators"
                            )
                            
                            st.markdown(f"""
                            <div title="Hover for source details">
                                {confidence_indicator} **{source['name']}**  
                                - Score: {source['score']*100:.1f}  
                                - Samples: {source['samples']} {source_type}  
                                - Confidence: {confidence:.1f}%  
                                {_get_source_tooltip(source['name'])}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Display analysis timestamp and totals
                        last_updated = datetime.fromisoformat(sentiment_data['timestamp'])
                        st.caption(f"""
                        📊 Analysis based on {sentiment_data['samples']} total samples
                        🕒 Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S UTC')}
                        """)
                
                    # Add detailed source information
                    with st.expander("ℹ️ Data Source Details"):
                        st.markdown("""
                        #### How We Calculate Sentiment
                        
                        This analysis combines multiple data sources with different weights:
                        
                        🔹 **RSS Feeds** (Medium Confidence)
                        - Major cryptocurrency news sources
                        - Article sentiment analysis
                        - Updated every 5 minutes
                        
                        🔹 **Price Data** (High Confidence)
                        - CryptoCompare market data
                        - 24h price changes
                        - Hourly price movements
                        - Real-time updates
                        
                        🔹 **Social Media** (Variable Confidence)
                        - Twitter sentiment analysis
                        - Recent tweet analysis
                        - May be rate-limited
                        
                        #### Confidence Scores
                        - 🟢 High (70-100%): Reliable data from multiple sources
                        - 🟡 Medium (40-69%): Limited or partially available data
                        - 🔴 Low (0-39%): Minimal data or source issues
                        
                        *Note: Sources and availability may vary based on API limits and market conditions.*
                        """)
            
            except Exception as e:
                st.error(f"⚠️ Error processing sentiment for {coin}")
                st.info("💡 Try refreshing the page or selecting fewer coins to analyze.")

def _get_sentiment_color(score: float) -> str:
    """Return color based on sentiment score."""
    if score >= 25:
        return "rgb(0, 255, 0)"  # Green for positive
    elif score <= -25:
        return "rgb(255, 0, 0)"  # Red for negative
    return "rgb(128, 128, 128)"  # Gray for neutral

def _get_source_tooltip(source_name: str) -> str:
    """Return tooltip text for different data sources."""
    tooltips = {
        'RSS Feeds': "Analysis of recent cryptocurrency news articles",
        'CryptoCompare': "Market data and price movement analysis",
        'Twitter': "Sentiment from recent cryptocurrency-related tweets"
    }
    return f'<span title="{tooltips.get(source_name, "")}"></span>'
