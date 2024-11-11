import os
import tweepy
import nltk
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import streamlit as st

class SentimentAnalyzer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except Exception as e:
            st.warning(f"Warning: Could not download NLTK data. Some features might be limited. {str(e)}")

        # Initialize Twitter API client
        try:
            auth = tweepy.OAuth1UserHandler(
                os.environ.get('TWITTER_API_KEY', ''),
                os.environ.get('TWITTER_API_SECRET', ''),
                os.environ.get('TWITTER_ACCESS_TOKEN', ''),
                os.environ.get('TWITTER_ACCESS_TOKEN_SECRET', '')
            )
            self.twitter_api = tweepy.API(auth)
            self.vader = SentimentIntensityAnalyzer()
        except Exception as e:
            st.error(f"Error initializing Twitter API: {str(e)}")
            self.twitter_api = None
            self.vader = None

    def get_twitter_sentiment(self, keyword: str, count: int = 100) -> dict:
        """Analyze sentiment from recent tweets about a cryptocurrency."""
        return self._get_cached_sentiment(keyword, count)

    @st.cache_data(ttl=300)
    def _get_cached_sentiment(_self, keyword: str, count: int = 100) -> dict:
        """Cached version of sentiment analysis."""
        if not _self.twitter_api or not _self.vader:
            return {
                'score': 0,
                'samples': 0,
                'timestamp': datetime.now().isoformat(),
                'sentiment_category': 'neutral',
                'error': 'Twitter API not initialized'
            }

        try:
            tweets = _self.twitter_api.search_tweets(
                q=f"#{keyword} OR {keyword} crypto",
                lang="en",
                count=count,
                tweet_mode="extended"
            )
            
            vader_scores = []
            textblob_scores = []
            
            for tweet in tweets:
                # Clean tweet text
                text = tweet.full_text.lower()
                
                # VADER sentiment
                vader_score = _self.vader.polarity_scores(text)
                vader_scores.append(vader_score['compound'])
                
                # TextBlob sentiment
                blob = TextBlob(text)
                textblob_scores.append(blob.sentiment.polarity)
            
            # Calculate average sentiments
            avg_vader = sum(vader_scores) / len(vader_scores) if vader_scores else 0
            avg_textblob = sum(textblob_scores) / len(textblob_scores) if textblob_scores else 0
            
            # Normalize to -100 to 100 scale
            normalized_sentiment = (avg_vader + avg_textblob) * 50
            
            return {
                'score': normalized_sentiment,
                'samples': len(tweets),
                'timestamp': datetime.now().isoformat(),
                'sentiment_category': _self._categorize_sentiment(normalized_sentiment)
            }
        except Exception as e:
            st.error(f"Error fetching Twitter sentiment: {str(e)}")
            return {
                'score': 0,
                'samples': 0,
                'timestamp': datetime.now().isoformat(),
                'sentiment_category': 'neutral',
                'error': str(e)
            }

    def _categorize_sentiment(self, score: float) -> str:
        """Categorize sentiment score into categories."""
        if score >= 25:
            return 'bullish'
        elif score <= -25:
            return 'bearish'
        else:
            return 'neutral'
