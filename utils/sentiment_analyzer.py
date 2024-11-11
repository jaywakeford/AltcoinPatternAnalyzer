import os
import feedparser
import cryptocompare
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import tweepy

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
        ]
        
        # Initialize Twitter client
        self.twitter_client = None
        self._init_twitter_client()

    def _init_twitter_client(self) -> None:
        """Initialize Twitter API client."""
        try:
            auth = tweepy.OAuthHandler(
                os.environ['TWITTER_API_KEY'],
                os.environ['TWITTER_API_SECRET']
            )
            auth.set_access_token(
                os.environ['TWITTER_ACCESS_TOKEN'],
                os.environ['TWITTER_ACCESS_TOKEN_SECRET']
            )
            
            self.twitter_client = tweepy.Client(
                consumer_key=os.environ['TWITTER_API_KEY'],
                consumer_secret=os.environ['TWITTER_API_SECRET'],
                access_token=os.environ['TWITTER_ACCESS_TOKEN'],
                access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET'],
                wait_on_rate_limit=True
            )
            st.success("Twitter API connection established successfully!")
        except Exception as e:
            st.warning(f"Twitter API initialization failed: {str(e)}")

    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_crypto_news_sentiment(_self, keyword: str) -> Dict:
        """Get aggregated sentiment from multiple sources."""
        sources_data = []
        all_scores = []
        all_samples = 0

        # Analyze RSS feeds
        rss_sentiment = _self._analyze_rss_feeds(keyword)
        if rss_sentiment:
            all_scores.extend(rss_sentiment['scores'])
            all_samples += rss_sentiment['samples']
            sources_data.append({
                'name': 'RSS Feeds',
                'score': rss_sentiment['average_score'],
                'samples': rss_sentiment['samples']
            })

        # Analyze CryptoCompare news
        cc_sentiment = _self._analyze_cryptocompare_news(keyword)
        if cc_sentiment:
            all_scores.extend(cc_sentiment['scores'])
            all_samples += cc_sentiment['samples']
            sources_data.append({
                'name': 'CryptoCompare',
                'score': cc_sentiment['average_score'],
                'samples': cc_sentiment['samples']
            })

        # Analyze Twitter sentiment if available
        if _self.twitter_client:
            twitter_sentiment = _self._analyze_twitter_sentiment(keyword)
            if twitter_sentiment:
                all_scores.extend(twitter_sentiment['scores'])
                all_samples += twitter_sentiment['samples']
                sources_data.append({
                    'name': 'Twitter',
                    'score': twitter_sentiment['average_score'],
                    'samples': twitter_sentiment['samples']
                })

        # Return neutral sentiment if no data available
        if not all_scores:
            return {
                'score': 0,
                'samples': 0,
                'timestamp': datetime.now().isoformat(),
                'sentiment_category': 'neutral',
                'error': None,
                'sources': []
            }

        # Calculate average sentiment
        avg_sentiment = sum(all_scores) / len(all_scores)
        
        return {
            'score': avg_sentiment * 100,  # Scale to -100 to 100
            'samples': all_samples,
            'timestamp': datetime.now().isoformat(),
            'sentiment_category': _self._categorize_sentiment(avg_sentiment * 100),
            'error': None,
            'sources': sources_data
        }

    def _analyze_twitter_sentiment(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from Twitter."""
        if not self.twitter_client:
            return None

        try:
            query = f"{keyword} crypto -is:retweet lang:en"
            tweets = []
            # Use tweepy.Paginator to handle pagination
            for tweet in tweepy.Paginator(
                self.twitter_client.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=['text']
            ).flatten(limit=100):
                tweets.append(tweet)
            
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
        """Analyze sentiment from RSS feeds."""
        scores = []
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                if feed.bozo:  # Check if there was an error parsing the feed
                    continue
                
                for entry in feed.entries[:10]:  # Analyze last 10 entries per feed
                    if hasattr(entry, 'title') and hasattr(entry, 'description'):
                        text = f"{entry.title}. {entry.description}"
                        if keyword.lower() in text.lower():
                            sentiment = self.vader.polarity_scores(text)
                            scores.append(sentiment['compound'])
            except Exception as e:
                st.warning(f"Error parsing RSS feed {feed_url}: {str(e)}")
                continue

        if not scores:
            return None

        return {
            'scores': scores,
            'average_score': sum(scores) / len(scores),
            'samples': len(scores)
        }

    def _analyze_cryptocompare_news(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from CryptoCompare news."""
        try:
            # Using cryptocompare's news endpoint correctly
            news_list = cryptocompare.get_latest_news()
            scores = []
            
            for article in news_list[:20]:  # Analyze last 20 news articles
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
