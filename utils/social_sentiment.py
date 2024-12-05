import tweepy
import praw
import requests
from textblob import TextBlob
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go
from typing import Dict, List, Optional
import os
from dotenv import load_load_dotenv

load_dotenv()

class SocialSentimentAnalyzer:
    def __init__(self):
        # Twitter API credentials
        self.twitter_api = self._init_twitter()
        # Reddit API credentials
        self.reddit_api = self._init_reddit()
        
    def _init_twitter(self):
        """Initialize Twitter API client."""
        try:
            auth = tweepy.OAuthHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET')
            )
            auth.set_access_token(
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            return tweepy.API(auth)
        except Exception as e:
            st.warning(f"Twitter API initialization failed: {str(e)}")
            return None

    def _init_reddit(self):
        """Initialize Reddit API client."""
        try:
            return praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent="Crypto Sentiment Analyzer 1.0"
            )
        except Exception as e:
            st.warning(f"Reddit API initialization failed: {str(e)}")
            return None

    def analyze_text_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text using TextBlob."""
        analysis = TextBlob(text)
        return {
            'polarity': analysis.sentiment.polarity,
            'subjectivity': analysis.sentiment.subjectivity
        }

    def get_twitter_sentiment(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """Get sentiment from Twitter posts."""
        if not self.twitter_api:
            return pd.DataFrame()

        tweets = []
        try:
            # Search for tweets containing the symbol
            query = f"${symbol} OR #{symbol}crypto -filter:retweets"
            cursor = tweepy.Cursor(
                self.twitter_api.search_tweets,
                q=query,
                lang="en",
                tweet_mode="extended"
            ).items(limit)

            for tweet in cursor:
                sentiment = self.analyze_text_sentiment(tweet.full_text)
                tweets.append({
                    'date': tweet.created_at,
                    'text': tweet.full_text,
                    'polarity': sentiment['polarity'],
                    'subjectivity': sentiment['subjectivity'],
                    'likes': tweet.favorite_count,
                    'retweets': tweet.retweet_count,
                    'source': 'Twitter'
                })

        except Exception as e:
            st.error(f"Error fetching Twitter data: {str(e)}")

        return pd.DataFrame(tweets)

    def get_reddit_sentiment(self, symbol: str, subreddits: List[str] = None) -> pd.DataFrame:
        """Get sentiment from Reddit posts."""
        if not self.reddit_api:
            return pd.DataFrame()

        if not subreddits:
            subreddits = ['cryptocurrency', 'CryptoMarkets', symbol.lower()]

        posts = []
        try:
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit_api.subreddit(subreddit_name)
                    # Get hot posts and new posts
                    for submission in list(subreddit.hot(limit=50)) + list(subreddit.new(limit=50)):
                        if symbol.lower() in submission.title.lower() or symbol.lower() in submission.selftext.lower():
                            sentiment = self.analyze_text_sentiment(submission.title + " " + submission.selftext)
                            posts.append({
                                'date': datetime.fromtimestamp(submission.created_utc),
                                'title': submission.title,
                                'text': submission.selftext,
                                'polarity': sentiment['polarity'],
                                'subjectivity': sentiment['subjectivity'],
                                'score': submission.score,
                                'comments': submission.num_comments,
                                'source': 'Reddit'
                            })
                except Exception as e:
                    st.warning(f"Error fetching data from r/{subreddit_name}: {str(e)}")
                    continue

        except Exception as e:
            st.error(f"Error fetching Reddit data: {str(e)}")

        return pd.DataFrame(posts)

    def render_sentiment_dashboard(self, symbol: str):
        """Render sentiment analysis dashboard."""
        st.subheader(f"Social Media Sentiment Analysis for {symbol}")

        # Fetch sentiment data
        twitter_data = self.get_twitter_sentiment(symbol)
        reddit_data = self.get_reddit_sentiment(symbol)
        
        # Combine data
        all_data = pd.concat([twitter_data, reddit_data], ignore_index=True)
        
        if all_data.empty:
            st.warning("No sentiment data available. Please check your API credentials.")
            return

        # Overall sentiment metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_sentiment = all_data['polarity'].mean()
            sentiment_label = "Positive" if avg_sentiment > 0 else "Negative" if avg_sentiment < 0 else "Neutral"
            st.metric("Overall Sentiment", sentiment_label, f"{avg_sentiment:.2f}")
            
        with col2:
            avg_subjectivity = all_data['subjectivity'].mean()
            st.metric("Average Subjectivity", f"{avg_subjectivity:.2f}")
            
        with col3:
            total_posts = len(all_data)
            st.metric("Total Posts Analyzed", total_posts)

        # Sentiment over time
        st.subheader("Sentiment Trends")
        
        # Resample data to hourly averages
        all_data['date'] = pd.to_datetime(all_data['date'])
        hourly_sentiment = all_data.set_index('date').resample('H')['polarity'].mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly_sentiment.index,
            y=hourly_sentiment.values,
            mode='lines+markers',
            name='Sentiment'
        ))
        
        fig.update_layout(
            title='Sentiment Trend Over Time',
            xaxis_title='Time',
            yaxis_title='Sentiment Score',
            template='plotly_dark'
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Most influential posts
        st.subheader("Most Influential Posts")
        
        # Twitter
        if not twitter_data.empty:
            st.write("Top Twitter Posts")
            twitter_data['influence_score'] = twitter_data['likes'] + twitter_data['retweets']
            top_tweets = twitter_data.nlargest(5, 'influence_score')
            for _, tweet in top_tweets.iterrows():
                with st.expander(f"Tweet (Sentiment: {tweet['polarity']:.2f})"):
                    st.write(tweet['text'])
                    st.write(f"Likes: {tweet['likes']}, Retweets: {tweet['retweets']}")
        
        # Reddit
        if not reddit_data.empty:
            st.write("Top Reddit Posts")
            reddit_data['influence_score'] = reddit_data['score'] + reddit_data['comments']
            top_posts = reddit_data.nlargest(5, 'influence_score')
            for _, post in top_posts.iterrows():
                with st.expander(f"{post['title']} (Sentiment: {post['polarity']:.2f})"):
                    st.write(post['text'])
                    st.write(f"Score: {post['score']}, Comments: {post['comments']}")

def render_sentiment_section(symbol: str = None):
    analyzer = SocialSentimentAnalyzer()
    if symbol:
        analyzer.render_sentiment_dashboard(symbol)
    else:
        st.warning("Please select a cryptocurrency symbol to analyze sentiment.")
