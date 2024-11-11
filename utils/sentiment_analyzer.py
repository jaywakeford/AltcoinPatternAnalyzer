import os
import feedparser
import cryptocompare
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit as st
from datetime import datetime, timedelta
import tweepy
from typing import Dict, List, Optional
import requests
import time
from functools import wraps

def rate_limit(calls: int, period: int):
    """Rate limiter decorator"""
    intervals = []
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            intervals.append(now)
            
            # Remove old timestamps
            while intervals and intervals[0] < now - period:
                intervals.pop(0)
            
            if len(intervals) > calls:
                sleep_time = intervals[0] + period - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    intervals.clear()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

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
            "https://www.newsbtc.com/feed/",
            "https://bitcoinmagazine.com/.rss/full/",
            "https://cryptopotato.com/feed/",
            "https://cryptonews.com/news/feed/"
        ]
        
        # Initialize Twitter client
        self.twitter_client = None
        self._init_twitter_client()

        # Initialize rate limiters
        self.last_api_call = {}
        self.api_call_counts = {}
    
    def _init_twitter_client(self) -> None:
        """Initialize Twitter API client with proper error handling."""
        try:
            if not all(os.environ.get(key) for key in ['TWITTER_API_KEY', 'TWITTER_API_SECRET']):
                st.warning("Twitter API credentials incomplete. Twitter sentiment analysis will be disabled.")
                return

            auth = tweepy.OAuthHandler(
                os.environ['TWITTER_API_KEY'],
                os.environ['TWITTER_API_SECRET']
            )
            
            if all(os.environ.get(key) for key in ['TWITTER_ACCESS_TOKEN', 'TWITTER_ACCESS_TOKEN_SECRET']):
                auth.set_access_token(
                    os.environ['TWITTER_ACCESS_TOKEN'],
                    os.environ['TWITTER_ACCESS_TOKEN_SECRET']
                )
            
            self.twitter_client = tweepy.Client(auth=auth)
        except Exception as e:
            st.warning(f"Twitter API initialization failed: {str(e)}")
            self.twitter_client = None

    def get_crypto_news_sentiment(self, keyword: str) -> Optional[Dict]:
        """Get aggregated sentiment from multiple sources."""
        return self._get_cached_sentiment(keyword)

    @staticmethod
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def _get_cached_sentiment(keyword: str) -> Dict:
        """Cached method to get sentiment data."""
        analyzer = SentimentAnalyzer()
        return analyzer._analyze_all_sources(keyword)

    @rate_limit(calls=50, period=60)  # 50 calls per minute
    def _analyze_all_sources(self, keyword: str) -> Dict:
        """Analyze sentiment from all available sources with improved error handling."""
        sources_data = []
        all_scores = []
        all_samples = 0
        failed_sources = []

        # Process each source independently with proper error handling
        try:
            rss_data = self._get_cached_rss_sentiment(keyword)
            if rss_data:
                sources_data.append(rss_data)
                all_scores.extend(rss_data['scores'])
                all_samples += rss_data['samples']
        except Exception as e:
            failed_sources.append(("RSS Feeds", str(e)))

        try:
            cc_data = self._get_cached_cryptocompare_sentiment(keyword)
            if cc_data:
                sources_data.append(cc_data)
                all_scores.extend(cc_data['scores'])
                all_samples += cc_data['samples']
        except Exception as e:
            failed_sources.append(("CryptoCompare", str(e)))

        if self.twitter_client:
            try:
                twitter_data = self._get_cached_twitter_sentiment(keyword)
                if twitter_data:
                    sources_data.append(twitter_data)
                    all_scores.extend(twitter_data['scores'])
                    all_samples += twitter_data['samples']
            except Exception as e:
                failed_sources.append(("Twitter", str(e)))

        # Return neutral sentiment if no data available
        if not all_scores:
            error_message = None
            if failed_sources:
                error_message = "; ".join([f"{source}: {error}" for source, error in failed_sources])
            
            return {
                'score': 0,
                'samples': 0,
                'timestamp': datetime.now().isoformat(),
                'sentiment_category': 'neutral',
                'error': error_message,
                'confidence': 0,
                'sources': []
            }

        # Calculate weighted average sentiment based on confidence
        total_weight = sum(source.get('confidence', 0) for source in sources_data)
        weighted_sentiment = sum(
            source.get('score', 0) * source.get('confidence', 0)
            for source in sources_data
        ) / total_weight if total_weight > 0 else 0

        result = {
            'score': weighted_sentiment * 100,  # Scale to -100 to 100
            'samples': all_samples,
            'timestamp': datetime.now().isoformat(),
            'sentiment_category': self._categorize_sentiment(weighted_sentiment * 100),
            'confidence': min(1.0, total_weight / len(sources_data)) if sources_data else 0,
            'error': None if not failed_sources else f"Some sources failed: {'; '.join(f'{s[0]}' for s in failed_sources)}",
            'sources': sources_data
        }

        return result

    @staticmethod
    @st.cache_data(ttl=60)  # Cache Twitter results for 1 minute
    def _get_cached_twitter_sentiment(self, keyword: str) -> Optional[Dict]:
        """Cached wrapper for Twitter sentiment analysis."""
        return self._analyze_twitter_sentiment(keyword)

    @rate_limit(calls=180, period=900)  # Twitter rate limit: 180 calls per 15 minutes
    def _analyze_twitter_sentiment(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from Twitter with enhanced error handling."""
        if not self.twitter_client:
            return None

        try:
            query = f"{keyword} crypto -is:retweet lang:en"
            tweets = []
            
            response = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=['text']
            )
            
            if not response or not hasattr(response, 'data') or not response.data:
                return None
            
            scores = []
            for tweet in response.data:
                sentiment = self.vader.polarity_scores(tweet.text)
                scores.append(sentiment['compound'])

            if not scores:
                return None

            confidence = min(1.0, len(scores) / 20)  # Confidence based on sample size
            return {
                'name': 'Twitter',
                'scores': scores,
                'score': sum(scores) / len(scores),
                'samples': len(scores),
                'confidence': confidence
            }

        except Exception as e:
            raise Exception(f"Twitter API error: {str(e)}")

    @staticmethod
    @st.cache_data(ttl=300)  # Cache RSS results for 5 minutes
    def _get_cached_rss_sentiment(self, keyword: str) -> Optional[Dict]:
        """Cached wrapper for RSS sentiment analysis."""
        return self._analyze_rss_feeds(keyword)

    @rate_limit(calls=60, period=60)  # 60 calls per minute
    def _analyze_rss_feeds(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from RSS feeds with improved error handling."""
        scores = []
        successful_feeds = 0
        failed_feeds = []

        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                if feed.bozo:
                    failed_feeds.append((feed_url, "Invalid feed format"))
                    continue
                
                feed_scores = []
                for entry in feed.entries[:10]:
                    if (hasattr(entry, 'title') and hasattr(entry, 'description') and
                        keyword.lower() in f"{entry.title} {entry.description}".lower()):
                        text = f"{entry.title}. {entry.description}"
                        sentiment = self.vader.polarity_scores(text)
                        feed_scores.append(sentiment['compound'])
                
                if feed_scores:
                    scores.extend(feed_scores)
                    successful_feeds += 1
            except Exception as e:
                failed_feeds.append((feed_url, str(e)))

        if not scores:
            if failed_feeds:
                raise Exception(f"RSS feed errors: {'; '.join(f'{url}: {error}' for url, error in failed_feeds)}")
            return None

        confidence = min(1.0, successful_feeds / len(self.rss_feeds))
        return {
            'name': 'RSS Feeds',
            'scores': scores,
            'score': sum(scores) / len(scores),
            'samples': len(scores),
            'confidence': confidence
        }

    @staticmethod
    @st.cache_data(ttl=60)  # Cache CryptoCompare results for 1 minute
    def _get_cached_cryptocompare_sentiment(self, keyword: str) -> Optional[Dict]:
        """Cached wrapper for CryptoCompare sentiment analysis."""
        return self._analyze_cryptocompare_news(keyword)

    @rate_limit(calls=30, period=60)  # 30 calls per minute
    def _analyze_cryptocompare_news(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from CryptoCompare price data with improved error handling."""
        try:
            data = cryptocompare.get_price(
                keyword,
                'USD',
                full=True
            )
            
            if not data or 'RAW' not in data or keyword.upper() not in data['RAW']:
                raise Exception("No price data available")

            raw_data = data['RAW'][keyword.upper()]['USD']
            
            try:
                changes = [
                    float(raw_data.get('CHANGEPCT24HOUR', 0)),
                    float(raw_data.get('CHANGEPCTHOUR', 0))
                ]
            except (TypeError, ValueError) as e:
                raise Exception(f"Invalid price change data: {str(e)}")
            
            # Normalize changes to [-1, 1] range for sentiment
            scores = [min(max(change / 10, -1), 1) for change in changes]
            
            if not scores:
                return None

            return {
                'name': 'CryptoCompare',
                'scores': scores,
                'score': sum(scores) / len(scores),
                'samples': len(scores),
                'confidence': 0.8  # High confidence in price data
            }

        except Exception as e:
            raise Exception(f"CryptoCompare API error: {str(e)}")

    def _categorize_sentiment(self, score: float) -> str:
        """Categorize sentiment score into categories."""
        if score >= 25:
            return 'bullish'
        elif score <= -25:
            return 'bearish'
        return 'neutral'
