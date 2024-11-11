import os
import feedparser
import cryptocompare
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit as st
from datetime import datetime
import tweepy
from typing import Dict, List, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from functools import partial

class SentimentAnalyzer:
    def __init__(self):
        # Initialize VADER sentiment analyzer
        self.vader = SentimentIntensityAnalyzer()
        
        # Download required NLTK data with proper error handling
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            try:
                with st.spinner('Downloading required NLTK data...'):
                    nltk.download('punkt', quiet=True)
            except Exception as e:
                st.warning(f"Could not download NLTK data: {str(e)}")
        
        # RSS feeds for major crypto news sites
        self.rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://coindesk.com/arc/outboundfeeds/rss/",
            "https://news.bitcoin.com/feed/",
            "https://cryptopotato.com/feed/",
            "https://cryptonews.com/news/feed/"
        ]
        
        # Initialize Twitter client
        self.twitter_client = None
        self._init_twitter_client()

    def _init_twitter_client(self) -> None:
        """Initialize Twitter API client with proper error handling."""
        try:
            auth = tweepy.OAuthHandler(
                os.environ.get('TWITTER_API_KEY'),
                os.environ.get('TWITTER_API_SECRET')
            )
            auth.set_access_token(
                os.environ.get('TWITTER_ACCESS_TOKEN'),
                os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
            )
            
            self.twitter_client = tweepy.Client(
                consumer_key=os.environ.get('TWITTER_API_KEY'),
                consumer_secret=os.environ.get('TWITTER_API_SECRET'),
                access_token=os.environ.get('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET'),
                wait_on_rate_limit=True
            )
            st.success("Twitter API connection established successfully!")
        except KeyError:
            st.warning("Twitter API credentials not found. Twitter sentiment analysis will be disabled.")
        except Exception as e:
            st.warning(f"Twitter API initialization failed: {str(e)}")

    @st.cache_data(ttl=300)
    def get_crypto_news_sentiment(self, keyword: str) -> Dict:
        """Get aggregated sentiment from multiple sources with improved error handling."""
        sources_data = []
        all_scores = []
        all_samples = 0

        with ThreadPoolExecutor() as executor:
            # Start all analysis tasks
            rss_future = executor.submit(self._analyze_rss_feeds, keyword)
            cc_future = executor.submit(self._analyze_cryptocompare_news, keyword)
            twitter_future = executor.submit(self._analyze_twitter_sentiment, keyword) if self.twitter_client else None

            # RSS Feeds Analysis
            try:
                rss_sentiment = rss_future.result(timeout=10)  # 10 second timeout
                if rss_sentiment:
                    all_scores.extend(rss_sentiment['scores'])
                    all_samples += rss_sentiment['samples']
                    sources_data.append({
                        'name': 'RSS Feeds',
                        'score': rss_sentiment['average_score'],
                        'samples': rss_sentiment['samples']
                    })
            except TimeoutError:
                st.warning("RSS feed analysis timed out")

            # CryptoCompare Analysis
            try:
                cc_sentiment = cc_future.result(timeout=5)  # 5 second timeout
                if cc_sentiment:
                    all_scores.extend(cc_sentiment['scores'])
                    all_samples += cc_sentiment['samples']
                    sources_data.append({
                        'name': 'CryptoCompare',
                        'score': cc_sentiment['average_score'],
                        'samples': cc_sentiment['samples']
                    })
            except TimeoutError:
                st.warning("CryptoCompare analysis timed out")

            # Twitter Analysis
            if twitter_future:
                try:
                    twitter_sentiment = twitter_future.result(timeout=10)  # 10 second timeout
                    if twitter_sentiment:
                        all_scores.extend(twitter_sentiment['scores'])
                        all_samples += twitter_sentiment['samples']
                        sources_data.append({
                            'name': 'Twitter',
                            'score': twitter_sentiment['average_score'],
                            'samples': twitter_sentiment['samples']
                        })
                except TimeoutError:
                    st.warning("Twitter analysis timed out")

        # Return neutral sentiment if no data available
        if not all_scores:
            return {
                'score': 0,
                'samples': 0,
                'timestamp': datetime.now().isoformat(),
                'sentiment_category': 'neutral',
                'error': "No sentiment data available from any source",
                'sources': []
            }

        # Calculate average sentiment
        avg_sentiment = sum(all_scores) / len(all_scores)
        
        return {
            'score': avg_sentiment * 100,  # Scale to -100 to 100
            'samples': all_samples,
            'timestamp': datetime.now().isoformat(),
            'sentiment_category': self._categorize_sentiment(avg_sentiment * 100),
            'error': None,
            'sources': sources_data
        }

    def _analyze_twitter_sentiment(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from Twitter with enhanced error handling."""
        if not self.twitter_client:
            return None

        try:
            query = f"{keyword} crypto -is:retweet lang:en"
            tweets = []
            
            try:
                for tweet in tweepy.Paginator(
                    self.twitter_client.search_recent_tweets,
                    query=query,
                    max_results=100,
                    tweet_fields=['text']
                ).flatten(limit=100):
                    tweets.append(tweet)
            except tweepy.TooManyRequests:
                st.warning("Twitter API rate limit reached. Using cached or alternative data sources.")
                return None
            except tweepy.Unauthorized:
                st.error("Twitter API authentication failed. Please check your credentials.")
                return None
            
            if not tweets:
                return None
            
            scores = []
            for tweet in tweets:
                sentiment = self.vader.polarity_scores(tweet.text)
                scores.append(sentiment['compound'])

            if not scores:
                return None

            return {
                'scores': scores,
                'average_score': sum(scores) / len(scores),
                'samples': len(scores)
            }

        except Exception as e:
            st.warning(f"Error analyzing Twitter sentiment: {str(e)}")
            return None

    def _analyze_rss_feeds(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from RSS feeds with enhanced error handling and timeouts."""
        scores = []
        successful_feeds = 0
        
        def process_feed(feed_url):
            try:
                feed = feedparser.parse(feed_url, timeout=5)  # 5 second timeout per feed
                if feed.bozo:
                    return None
                
                feed_scores = []
                for entry in feed.entries[:10]:
                    if hasattr(entry, 'title') and hasattr(entry, 'description'):
                        text = f"{entry.title}. {entry.description}"
                        if keyword.lower() in text.lower():
                            sentiment = self.vader.polarity_scores(text)
                            feed_scores.append(sentiment['compound'])
                return feed_scores
            except Exception:
                return None

        with ThreadPoolExecutor() as executor:
            feed_results = list(executor.map(process_feed, self.rss_feeds))

        for result in feed_results:
            if result:
                successful_feeds += 1
                scores.extend(result)

        if not scores:
            if successful_feeds == 0:
                st.warning("All RSS feeds failed. Please check your internet connection.")
            return None

        return {
            'scores': scores,
            'average_score': sum(scores) / len(scores),
            'samples': len(scores)
        }

    def _analyze_cryptocompare_news(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from CryptoCompare news with improved error handling."""
        try:
            news_list = cryptocompare.get_news()
            if not news_list:
                return None

            scores = []
            for article in news_list[:20]:
                if 'title' in article and 'body' in article:
                    text = f"{article['title']}. {article['body']}"
                    if keyword.lower() in text.lower():
                        sentiment = self.vader.polarity_scores(text)
                        scores.append(sentiment['compound'])

            if not scores:
                return None

            return {
                'scores': scores,
                'average_score': sum(scores) / len(scores),
                'samples': len(scores)
            }

        except Exception as e:
            st.warning(f"Error fetching CryptoCompare news: {str(e)}")
            return None

    def _categorize_sentiment(self, score: float) -> str:
        """Categorize sentiment score into categories."""
        if score >= 25:
            return 'bullish'
        elif score <= -25:
            return 'bearish'
        return 'neutral'
