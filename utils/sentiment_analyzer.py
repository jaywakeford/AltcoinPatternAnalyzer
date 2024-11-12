import os
import feedparser
import cryptocompare
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit as st
from datetime import datetime
import tweepy
from typing import Dict, Optional
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
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        # Extended list of RSS feeds for crypto news
        self.rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://www.newsbtc.com/feed/",
            "https://bitcoinmagazine.com/.rss/full/",
            "https://cryptopotato.com/feed/",
            "https://cryptonews.com/news/feed/",
            "https://decrypt.co/feed",
            "https://blog.coinbase.com/feed",
            "https://coinjournal.net/feed/",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://beincrypto.com/feed/"
        ]
        
        # Initialize Twitter client
        self.twitter_client = None
        self._init_twitter_client()
    
    def _init_twitter_client(self):
        """Initialize Twitter API client with proper error handling."""
        try:
            auth = tweepy.OAuthHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET')
            )
            auth.set_access_token(
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            self.twitter_client = tweepy.API(auth, wait_on_rate_limit=True)
        except Exception as e:
            st.warning(f"Twitter client initialization error: {str(e)}")
            self.twitter_client = None

    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_crypto_news_sentiment(self, keyword: str) -> Dict:
        """Get aggregated sentiment from multiple sources."""
        try:
            # Collect sentiment from different sources
            sources = []
            failed_sources = []
            total_confidence = 0
            weighted_sentiment = 0
            total_samples = 0
            
            # Try RSS feeds with increased weight
            try:
                rss_sentiment = self._analyze_rss_feeds(keyword)
                if rss_sentiment:
                    rss_sentiment['confidence'] = 0.8  # Increased weight for RSS feeds
                    sources.append(rss_sentiment)
                    weight = rss_sentiment['confidence']
                    total_confidence += weight
                    weighted_sentiment += rss_sentiment['score'] * weight
                    total_samples += rss_sentiment['samples']
            except Exception as e:
                failed_sources.append("RSS Feeds")
                st.warning(f"Error analyzing RSS feeds: {str(e)}")
            
            # Try market data with increased weight
            try:
                market_sentiment = self._analyze_market_data(keyword)
                if market_sentiment:
                    market_sentiment['confidence'] = 0.9  # Increased weight for market data
                    sources.append(market_sentiment)
                    weight = market_sentiment['confidence']
                    total_confidence += weight
                    weighted_sentiment += market_sentiment['score'] * weight
                    total_samples += market_sentiment['samples']
            except Exception as e:
                failed_sources.append("Market Data")
                st.warning(f"Error analyzing market data: {str(e)}")
            
            # Try Twitter with reduced weight
            if self.twitter_client:
                try:
                    twitter_sentiment = self._analyze_twitter_sentiment(keyword)
                    if twitter_sentiment:
                        sources.append(twitter_sentiment)
                        weight = twitter_sentiment['confidence']
                        total_confidence += weight
                        weighted_sentiment += twitter_sentiment['score'] * weight
                        total_samples += twitter_sentiment['samples']
                except Exception as e:
                    failed_sources.append("Twitter")
                    st.warning(f"Error analyzing Twitter data: {str(e)}")
            
            if not sources:
                return self._create_error_response("No sentiment data available from any source")
            
            # Calculate final sentiment
            final_sentiment = weighted_sentiment / total_confidence if total_confidence > 0 else 0
            
            return {
                'score': final_sentiment * 100,  # Scale to -100 to 100
                'samples': total_samples,
                'timestamp': datetime.now().isoformat(),
                'sentiment_category': self._categorize_sentiment(final_sentiment * 100),
                'confidence': min(1.0, total_confidence / len(sources)),
                'sources': sources,
                'failed_sources': failed_sources if failed_sources else None
            }
            
        except Exception as e:
            return self._create_error_response(str(e))

    def _analyze_rss_feeds(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from RSS feeds."""
        scores = []
        successful_feeds = 0
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                if not feed.entries:
                    continue
                
                relevant_entries = [
                    entry for entry in feed.entries[:10]
                    if keyword.lower() in (entry.title + 
                        getattr(entry, 'summary', '')).lower()
                ]
                
                if relevant_entries:
                    for entry in relevant_entries:
                        text = f"{entry.title} {getattr(entry, 'summary', '')}"
                        sentiment = self.vader.polarity_scores(text)
                        scores.append(sentiment['compound'])
                    successful_feeds += 1
                    
            except Exception as e:
                st.warning(f"Error processing feed {feed_url}: {str(e)}")
                continue
        
        if not scores:
            return None
            
        return {
            'name': 'RSS Feeds',
            'score': sum(scores) / len(scores),
            'samples': len(scores),
            'confidence': min(1.0, successful_feeds / len(self.rss_feeds))
        }

    def _analyze_market_data(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from market data."""
        try:
            symbol = keyword.upper()
            price_data = cryptocompare.get_price(
                symbol,
                'USD',
                full=True
            )
            
            if not price_data or 'RAW' not in price_data:
                return None
                
            raw_data = price_data['RAW'].get(symbol, {}).get('USD', {})
            if not raw_data:
                return None
                
            # Calculate sentiment indicators
            price_change = float(raw_data.get('CHANGEPCT24HOUR', 0))
            volume_change = (
                float(raw_data.get('VOLUMEDAYTO', 0)) / 
                float(raw_data.get('VOLUMEDAYFROM', 1)) - 1
            )
            
            # Normalize scores to [-1, 1] range
            normalized_scores = [
                max(min(value/100, 1), -1) 
                for value in [price_change, volume_change * 100]
            ]
            
            if not normalized_scores:
                return None
                
            return {
                'name': 'Market Data',
                'score': sum(normalized_scores) / len(normalized_scores),
                'samples': len(normalized_scores),
                'confidence': 0.9  # Increased confidence for market data
            }
            
        except Exception as e:
            st.warning(f"Error analyzing market data: {str(e)}")
            return None

    @rate_limit(calls=15, period=900)  # 15 calls per 15 minutes for basic tier
    def _analyze_twitter_sentiment(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from Twitter using v1.1 API."""
        if not self.twitter_client:
            return None
        try:
            search_query = f"#{keyword.lower()} OR ${keyword.upper()} -filter:retweets"
            tweets = self.twitter_client.search_tweets(
                q=search_query,
                lang="en",
                count=10,  # Reduced count for basic tier
                tweet_mode="extended"
            )
            
            if not tweets:
                return None
            
            scores = []
            for tweet in tweets:
                sentiment = self.vader.polarity_scores(tweet.full_text)
                scores.append(sentiment['compound'])
            
            if not scores:
                return None
            
            return {
                'name': 'Twitter',
                'score': sum(scores) / len(scores),
                'samples': len(tweets),
                'confidence': 0.5  # Reduced confidence due to limited data
            }
            
        except Exception as e:
            st.warning(f"Error analyzing Twitter data: {str(e)}")
            return None

    def _create_error_response(self, error_message: str) -> Dict:
        """Create a standardized error response."""
        return {
            'score': 0,
            'samples': 0,
            'timestamp': datetime.now().isoformat(),
            'sentiment_category': 'neutral',
            'confidence': 0,
            'error': error_message,
            'sources': []
        }

    def _categorize_sentiment(self, score: float) -> str:
        """Categorize sentiment score into categories."""
        if score >= 25:
            return 'bullish'
        elif score <= -25:
            return 'bearish'
        return 'neutral'
