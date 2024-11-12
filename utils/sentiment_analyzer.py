import os
import feedparser
import cryptocompare
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit as st
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import time
from functools import wraps
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from bs4 import BeautifulSoup

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

    @st.cache_data(ttl=300, show_spinner=False)
    def get_crypto_news_sentiment(_self, keyword: str) -> Dict:
        """Get aggregated sentiment from multiple sources with improved error handling and fallbacks."""
        try:
            # Initialize sentiment collection
            sources: List[Dict] = []
            failed_sources: List[str] = []
            total_confidence = 0
            weighted_sentiment = 0
            total_samples = 0
            
            # Track source availability
            available_sources = ['RSS Feeds', 'Yahoo Finance', 'Market Data']
            successful_sources = []
            
            # Try RSS feeds first
            try:
                rss_sentiment = _self._analyze_rss_feeds(keyword)
                if rss_sentiment:
                    rss_sentiment['confidence'] = 0.8  # Updated weight
                    sources.append(rss_sentiment)
                    successful_sources.append('RSS Feeds')
                    weight = rss_sentiment['confidence']
                    total_confidence += weight
                    weighted_sentiment += rss_sentiment['score'] * weight
                    total_samples += rss_sentiment['samples']
            except Exception as e:
                failed_sources.append("RSS Feeds")
                st.warning(f"Error analyzing RSS feeds: {str(e)}")
            
            # Try Yahoo Finance
            try:
                yahoo_sentiment = _self._analyze_yahoo_finance(keyword)
                if yahoo_sentiment:
                    sources.append(yahoo_sentiment)
                    successful_sources.append('Yahoo Finance')
                    weight = yahoo_sentiment['confidence']
                    total_confidence += weight
                    weighted_sentiment += yahoo_sentiment['score'] * weight
                    total_samples += yahoo_sentiment['samples']
            except Exception as e:
                failed_sources.append("Yahoo Finance")
                st.warning(f"Error analyzing Yahoo Finance data: {str(e)}")
            
            # Try market data
            try:
                market_sentiment = _self._analyze_market_data(keyword)
                if market_sentiment:
                    market_sentiment['confidence'] = 0.9  # Updated weight
                    sources.append(market_sentiment)
                    successful_sources.append('Market Data')
                    weight = market_sentiment['confidence']
                    total_confidence += weight
                    weighted_sentiment += market_sentiment['score'] * weight
                    total_samples += market_sentiment['samples']
            except Exception as e:
                failed_sources.append("Market Data")
                st.warning(f"Error analyzing market data: {str(e)}")
            
            if not sources:
                return _self._create_error_response(
                    "No sentiment data available. All data sources temporarily unavailable.",
                    available_sources,
                    successful_sources
                )
            
            # Calculate success rate
            success_rate = (len(successful_sources) / len(available_sources)) * 100
            
            # Calculate final sentiment
            final_sentiment = weighted_sentiment / total_confidence if total_confidence > 0 else 0
            
            return {
                'score': final_sentiment * 100,  # Scale to -100 to 100
                'samples': total_samples,
                'timestamp': datetime.now().isoformat(),
                'sentiment_category': _self._categorize_sentiment(final_sentiment * 100),
                'confidence': min(1.0, total_confidence / len(sources)),
                'sources': sources,
                'failed_sources': failed_sources if failed_sources else None,
                'available_sources': available_sources,
                'successful_sources': successful_sources,
                'success_rate': success_rate,
                'status': (
                    "All sources available and working" if not failed_sources else
                    f"Some sources unavailable ({', '.join(failed_sources)}). Analysis continues with available sources."
                )
            }
            
        except Exception as e:
            return _self._create_error_response(
                str(e),
                available_sources=['RSS Feeds', 'Yahoo Finance', 'Market Data'],
                successful_sources=[]
            )

    def _analyze_yahoo_finance(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from Yahoo Finance news."""
        try:
            # Use requests to fetch Yahoo Finance news
            url = f"https://finance.yahoo.com/quote/{keyword.upper()}/news"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('h3', {'class': 'Mb(5px)'})
            
            if not news_items:
                return None
            
            scores = []
            for item in news_items[:10]:  # Analyze up to 10 recent headlines
                headline = item.text.strip()
                sentiment = self.vader.polarity_scores(headline)
                scores.append(sentiment['compound'])
            
            if not scores:
                return None
            
            return {
                'name': 'Yahoo Finance',
                'score': sum(scores) / len(scores),
                'samples': len(scores),
                'confidence': 0.8  # High confidence for financial news
            }
            
        except Exception as e:
            st.warning(f"Error analyzing Yahoo Finance data: {str(e)}")
            return None

    def _analyze_rss_feeds(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from RSS feeds with improved error handling and timeouts."""
        scores = []
        successful_feeds = 0
        total_feeds = len(self.rss_feeds)
        timeout = 10  # seconds
        
        def process_feed(feed_url: str) -> Tuple[bool, List[float]]:
            try:
                # Use requests with timeout for initial fetch
                response = requests.get(feed_url, timeout=timeout)
                response.raise_for_status()
                
                # Parse feed content
                feed = feedparser.parse(response.content)
                if not feed.entries:
                    return False, []
                
                feed_scores = []
                relevant_entries = [
                    entry for entry in feed.entries[:10]
                    if keyword.lower() in (entry.title + 
                        getattr(entry, 'summary', '')).lower()
                ]
                
                if relevant_entries:
                    for entry in relevant_entries:
                        text = f"{entry.title} {getattr(entry, 'summary', '')}"
                        sentiment = self.vader.polarity_scores(text)
                        feed_scores.append(sentiment['compound'])
                    return True, feed_scores
                
                return False, []
                
            except (requests.Timeout, requests.RequestException) as e:
                st.warning(f"Timeout or error processing feed {feed_url}: {str(e)}")
                return False, []
        
        # Process feeds in parallel with timeout
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {
                executor.submit(process_feed, url): url 
                for url in self.rss_feeds
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success, feed_scores = future.result()
                    if success:
                        successful_feeds += 1
                        scores.extend(feed_scores)
                except TimeoutError:
                    st.warning(f"Feed processing timed out for {url}")
                except Exception as e:
                    st.warning(f"Error processing feed {url}: {str(e)}")
        
        if not scores:
            return None
            
        return {
            'name': 'RSS Feeds',
            'score': sum(scores) / len(scores),
            'samples': len(scores),
            'confidence': min(1.0, successful_feeds / total_feeds)
        }

    def _analyze_market_data(self, keyword: str) -> Optional[Dict]:
        """Analyze sentiment from market data with improved error handling."""
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
            metrics = []
            
            # Price change sentiment
            price_change = float(raw_data.get('CHANGEPCT24HOUR', 0))
            metrics.append(max(min(price_change/100, 1), -1))
            
            # Volume change sentiment
            volume_to = float(raw_data.get('VOLUMEDAYTO', 0))
            volume_from = float(raw_data.get('VOLUMEDAYFROM', 1))
            if volume_from > 0:
                volume_change = (volume_to / volume_from - 1)
                metrics.append(max(min(volume_change, 1), -1))
            
            if not metrics:
                return None
                
            return {
                'name': 'Market Data',
                'score': sum(metrics) / len(metrics),
                'samples': len(metrics),
                'confidence': 0.9  # High confidence for market data
            }
            
        except Exception as e:
            st.warning(f"Error analyzing market data: {str(e)}")
            return None

    def _create_error_response(self, error_message: str, available_sources: List[str], successful_sources: List[str]) -> Dict:
        """Create a standardized error response with improved feedback."""
        success_rate = (len(successful_sources) / len(available_sources)) * 100 if available_sources else 0
        
        return {
            'score': 0,
            'samples': 0,
            'timestamp': datetime.now().isoformat(),
            'sentiment_category': 'neutral',
            'confidence': 0,
            'error': error_message,
            'sources': [],
            'available_sources': available_sources,
            'successful_sources': successful_sources,
            'success_rate': success_rate,
            'status': (
                'All data sources temporarily unavailable. ' +
                'Please try again in a few minutes. ' +
                f'Success rate: {success_rate:.1f}%'
            )
        }

    def _categorize_sentiment(self, score: float) -> str:
        """Categorize sentiment score into categories."""
        if score >= 25:
            return 'bullish'
        elif score <= -25:
            return 'bearish'
        return 'neutral'
