import logging
import re
from typing import Optional, Tuple, Dict, Set
from datetime import datetime, timedelta
from cachetools import TTLCache
import json

logger = logging.getLogger(__name__)

class SymbolConverter:
    def __init__(self):
        # Standard symbol mappings
        self.symbol_mapping = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH',
            'litecoin': 'LTC',
            'ripple': 'XRP',
            'cardano': 'ADA',
            'polkadot': 'DOT',
            'solana': 'SOL',
            'binancecoin': 'BNB',
            'avalanche': 'AVAX',
            'polygon': 'MATIC',
            'chainlink': 'LINK',
            'uniswap': 'UNI'
        }
        
        # Valid currency sets
        self.valid_base_currencies = {
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 
            'AVAX', 'DOT', 'MATIC', 'LINK', 'UNI', 'LTC'
        }
        self.valid_quote_currencies = {'USDT', 'USD', 'EUR', 'BTC'}
        
        # Exchange-specific format mappings
        self.exchange_formats = {
            'kraken': lambda base, quote: f"{base}/{quote}",
            'kucoin': lambda base, quote: f"{base}-{quote}",
            'default': lambda base, quote: f"{base}/{quote}"
        }

        # Initialize TTL Cache with 1000 max items and 24-hour TTL
        self.cache_ttl = timedelta(hours=24)
        self.max_cache_size = 1000
        self._symbol_cache = TTLCache(
            maxsize=self.max_cache_size,
            ttl=self.cache_ttl.total_seconds()
        )
        
        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_cache_clear = datetime.now()
        
        # Initialize frequently used pairs
        self.frequent_pairs = {
            f"{base}/{quote}" 
            for base in {'BTC', 'ETH', 'SOL', 'ADA', 'BNB'}
            for quote in {'USDT', 'USD'}
        }
        
        # Initialize cache with frequent pairs
        self._preload_cache()
        logger.info("SymbolConverter initialized with preloaded cache")

    def _preload_cache(self):
        """Preload cache with frequently used trading pairs."""
        try:
            preloaded_count = 0
            for pair in self.frequent_pairs:
                if self.validate_symbol(pair)[0]:
                    cache_key = f"std_{pair.lower()}"
                    self._symbol_cache[cache_key] = pair
                    preloaded_count += 1
            logger.info(f"Preloaded cache with {preloaded_count} frequent pairs")
        except Exception as e:
            logger.error(f"Error preloading cache: {str(e)}")

    def convert_from_coin_name(self, coin_name: str, quote_currency: str = 'USDT') -> Optional[str]:
        """Convert full coin name to trading symbol with TTL caching."""
        try:
            if not coin_name:
                return None
            
            cache_key = f"coin_{coin_name.lower()}_{quote_currency.lower()}"
            
            # Check cache
            if cache_key in self._symbol_cache:
                self.cache_hits += 1
                logger.debug(f"Cache hit for coin name: {coin_name}")
                return self._symbol_cache[cache_key]
            
            self.cache_misses += 1
            logger.debug(f"Cache miss for coin name: {coin_name}")
            
            # Get symbol from mapping
            symbol = self.symbol_mapping.get(coin_name.lower())
            if not symbol:
                logger.warning(f"No symbol mapping found for coin: {coin_name}")
                return None
            
            # Create trading pair
            trading_pair = f"{symbol}/{quote_currency}"
            
            # Validate the trading pair
            if self.validate_symbol(trading_pair)[0]:
                self._symbol_cache[cache_key] = trading_pair
                logger.info(f"Converted {coin_name} to {trading_pair}")
                return trading_pair
                
            logger.warning(f"Invalid trading pair generated: {trading_pair}")
            return None
            
        except Exception as e:
            logger.error(f"Error converting from coin name: {str(e)}")
            return None

    def get_cache_stats(self) -> Dict:
        """Get detailed cache statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        active_pairs = [key.replace('std_', '').upper() 
                       for key in self._symbol_cache.keys() 
                       if key.startswith('std_')]
        
        return {
            'cache_size': len(self._symbol_cache),
            'max_cache_size': self.max_cache_size,
            'cache_ttl_hours': self.cache_ttl.total_seconds() / 3600,
            'active_pairs': active_pairs,
            'active_keys': list(self._symbol_cache.keys()),
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'last_clear': self.last_cache_clear.isoformat(),
            'frequently_used_pairs': list(self.frequent_pairs)
        }

    def convert_to_standard_format(self, symbol: str) -> Optional[str]:
        """Convert any symbol format to standard BASE/QUOTE format with TTL caching."""
        try:
            if not symbol:
                return None
                
            cache_key = f"std_{symbol.lower()}"
            
            # Check cache
            if cache_key in self._symbol_cache:
                self.cache_hits += 1
                logger.debug(f"Cache hit for {symbol}")
                return self._symbol_cache[cache_key]
            
            self.cache_misses += 1
            logger.debug(f"Cache miss for {symbol}")
            
            # If not in cache, perform conversion
            symbol = symbol.strip().upper()
            
            # Handle different separator formats
            separators = ['/', '-', '_', ' ']
            for sep in separators:
                if sep in symbol:
                    base, quote = symbol.split(sep)
                    if base in self.valid_base_currencies and quote in self.valid_quote_currencies:
                        result = f"{base}/{'USDT' if quote == 'USD' else quote}"
                        self._symbol_cache[cache_key] = result
                        return result
            
            # If no separator found, try to match known base currency
            for base in self.valid_base_currencies:
                if symbol.startswith(base):
                    remaining = symbol[len(base):]
                    for quote in self.valid_quote_currencies:
                        if remaining == quote:
                            result = f"{base}/{'USDT' if quote == 'USD' else quote}"
                            self._symbol_cache[cache_key] = result
                            return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error converting symbol format: {str(e)}")
            return None

    def add_frequent_pair(self, symbol: str) -> bool:
        """Add a new symbol to frequently used pairs."""
        try:
            if self.validate_symbol(symbol)[0]:
                self.frequent_pairs.add(symbol)
                cache_key = f"std_{symbol.lower()}"
                self._symbol_cache[cache_key] = symbol
                logger.info(f"Added {symbol} to frequent pairs")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding frequent pair: {str(e)}")
            return False

    def clear_cache(self):
        """Clear the symbol cache and reset statistics."""
        try:
            self._symbol_cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0
            self.last_cache_clear = datetime.now()
            # Reload frequent pairs after clearing
            self._preload_cache()
            logger.info("Cache cleared and reinitialized with frequent pairs")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

    def validate_symbol(self, symbol: str) -> Tuple[bool, str]:
        """Validate symbol format with comprehensive checks."""
        try:
            if not symbol or not isinstance(symbol, str):
                return False, "Symbol must be a non-empty string"
                
            # Check format using regex
            if not re.match(r'^[A-Z0-9]+/[A-Z0-9]+$', symbol):
                return False, f"Invalid symbol format: {symbol} - Must be in BASE/QUOTE format (e.g., BTC/USDT)"
                
            base, quote = symbol.split('/')
            
            if base not in self.valid_base_currencies:
                return False, f"Invalid base currency: {base} - Must be one of {', '.join(sorted(self.valid_base_currencies))}"
                
            if quote not in self.valid_quote_currencies:
                return False, f"Invalid quote currency: {quote} - Must be one of {', '.join(sorted(self.valid_quote_currencies))}"
                
            return True, "Symbol validation successful"
                
        except Exception as e:
            logger.error(f"Error in symbol validation: {str(e)}")
            return False, f"Validation error: {str(e)}"
