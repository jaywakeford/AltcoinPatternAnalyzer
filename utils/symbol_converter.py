import logging
import re
from typing import Optional, Tuple, Dict, Set, List, Any
from datetime import datetime, timedelta
from cachetools import TTLCache

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
        
        self.valid_base_currencies = {
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 
            'AVAX', 'DOT', 'MATIC', 'LINK', 'UNI', 'LTC'
        }
        self.valid_quote_currencies = {'USDT', 'USD', 'EUR', 'BTC'}
        
        # Enhanced exchange-specific format mappings
        self.exchange_formats = {
            'kraken': {
                'format': lambda base, quote: f"{base}/{quote}",
                'special_cases': {
                    'BTC': 'XBT',    # Kraken uses XBT instead of BTC
                    'USDT': 'USD',   # Kraken uses USD instead of USDT
                    'DOGE': 'XDG',   # Kraken uses XDG for Dogecoin
                    'BCH': 'BAB'     # Kraken uses BAB for Bitcoin Cash
                },
                'separator': '/',
                'case': 'upper',
                'description': 'Kraken uses XBT instead of BTC and USD instead of USDT',
                'example': 'XBT/USD',
                'validation_rules': [
                    "Must use XBT instead of BTC",
                    "Must use USD instead of USDT",
                    "Pairs must be separated by /",
                    "All characters must be uppercase"
                ],
                'pattern': r'^[A-Z]{3,5}/[A-Z]{3,4}$'
            },
            'kucoin': {
                'format': lambda base, quote: f"{base}-{quote}",
                'special_cases': {},
                'separator': '-',
                'case': 'upper',
                'description': 'KuCoin uses dash (-) as separator',
                'example': 'BTC-USDT',
                'validation_rules': [
                    "Pairs must be separated by -",
                    "All characters must be uppercase",
                    "Uses standard currency codes",
                    "USDT is preferred over USD"
                ],
                'pattern': r'^[A-Z]{3,5}-[A-Z]{3,4}$'
            },
            'binance': {
                'format': lambda base, quote: f"{base}{quote}",
                'special_cases': {},
                'separator': '',
                'case': 'upper',
                'description': 'Binance uses no separator between pairs',
                'example': 'BTCUSDT',
                'validation_rules': [
                    "No separator between pairs",
                    "All characters must be uppercase",
                    "Uses standard currency codes",
                    "USDT is standard quote currency"
                ],
                'pattern': r'^[A-Z]{3,5}[A-Z]{3,4}$'
            }
        }
        
        # Initialize cache
        self.cache_ttl = timedelta(hours=24)
        self.max_cache_size = 1000
        self._symbol_cache = TTLCache(
            maxsize=self.max_cache_size,
            ttl=self.cache_ttl.total_seconds()
        )
        
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_cache_clear = datetime.now()
        
        self._preload_cache()
        logger.info("SymbolConverter initialized with enhanced exchange formats")

    def validate_symbol(self, symbol: str, exchange: str) -> Tuple[bool, str]:
        """Validate symbol format for specific exchange with enhanced validation."""
        try:
            if not symbol or exchange.lower() not in self.exchange_formats:
                return False, "Invalid symbol or exchange"

            format_info = self.exchange_formats[exchange.lower()]
            
            # Check against regex pattern
            if not re.match(format_info['pattern'], symbol):
                return False, f"Symbol does not match required pattern for {exchange}"

            separator = format_info['separator']
            special_cases = format_info['special_cases']

            # Split symbol based on exchange format
            if separator:
                if separator not in symbol:
                    return False, f"Symbol must contain separator: {separator}"
                base, quote = symbol.split(separator)
            else:
                # Handle formats without separators
                for quote_curr in self.valid_quote_currencies:
                    if symbol.endswith(quote_curr):
                        base = symbol[:-len(quote_curr)]
                        quote = quote_curr
                        break
                else:
                    return False, "Invalid quote currency"

            # Check case formatting
            if format_info['case'] == 'upper' and not (base.isupper() and quote.isupper()):
                return False, "Symbol must be in uppercase"

            # Validate special cases
            reverse_special_cases = {v: k for k, v in special_cases.items()}
            standard_base = reverse_special_cases.get(base, base)
            standard_quote = reverse_special_cases.get(quote, quote)

            # Additional validation for exchange-specific rules
            if exchange.lower() == 'kraken' and standard_base == 'BTC':
                if base != 'XBT':
                    return False, "Kraken requires XBT instead of BTC"
                    
            if exchange.lower() == 'kraken' and standard_quote == 'USDT':
                if quote != 'USD':
                    return False, "Kraken requires USD instead of USDT"

            if standard_base not in self.valid_base_currencies:
                return False, f"Invalid base currency: {base}"

            if standard_quote not in self.valid_quote_currencies:
                return False, f"Invalid quote currency: {quote}"

            return True, "Valid symbol format"

        except Exception as e:
            logger.error(f"Error validating symbol: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def convert_to_exchange_format(self, symbol: str, exchange: str) -> Optional[str]:
        """Convert standard symbol format to exchange-specific format with validation."""
        try:
            if not symbol or exchange.lower() not in self.exchange_formats:
                return None

            format_info = self.exchange_formats[exchange.lower()]
            
            if '/' in symbol:
                base, quote = symbol.split('/')
            else:
                return None

            # Apply special cases if any
            base = format_info['special_cases'].get(base, base)
            quote = format_info['special_cases'].get(quote, quote)

            # Format using exchange-specific formatter
            formatted_symbol = format_info['format'](base, quote)
            
            # Validate the formatted symbol
            is_valid, _ = self.validate_symbol(formatted_symbol, exchange)
            return formatted_symbol if is_valid else None

        except Exception as e:
            logger.error(f"Error converting to exchange format: {str(e)}")
            return None

    def get_exchange_formats(self) -> Dict[str, Dict[str, Any]]:
        """Get all supported exchange formats."""
        return self.exchange_formats

    def get_exchange_format_info(self, exchange: str) -> Dict[str, Any]:
        """Get format information for a specific exchange."""
        if exchange.lower() in self.exchange_formats:
            format_info = self.exchange_formats[exchange.lower()]
            return {
                'description': format_info['description'],
                'example': format_info['example'],
                'validation_rules': format_info['validation_rules'],
                'special_cases': format_info['special_cases']
            }
        return {}

    def convert_from_coin_name(self, coin_name: str, quote_currency: str = 'USDT') -> Optional[str]:
        """Convert full coin name to standard trading symbol."""
        try:
            if not coin_name:
                return None
            
            cache_key = f"coin_{coin_name.lower()}_{quote_currency.lower()}"
            
            # Check cache first
            if cache_key in self._symbol_cache:
                self.cache_hits += 1
                return self._symbol_cache[cache_key]
            
            self.cache_misses += 1
            symbol = self.symbol_mapping.get(coin_name.lower())
            
            if symbol:
                trading_pair = f"{symbol}/{quote_currency}"
                self._symbol_cache[cache_key] = trading_pair
                return trading_pair
                
            return None
            
        except Exception as e:
            logger.error(f"Error converting from coin name: {str(e)}")
            return None

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self._symbol_cache),
            'max_cache_size': self.max_cache_size,
            'hit_rate': hit_rate,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'last_clear': self.last_cache_clear.isoformat()
        }

    def _preload_cache(self):
        """Preload cache with frequently used trading pairs."""
        try:
            frequent_pairs = {
                f"{base}/{'USDT' if quote == 'USD' else quote}" 
                for base in {'BTC', 'ETH', 'SOL', 'ADA', 'BNB'}
                for quote in {'USDT', 'USD'}
            }
            
            preloaded_count = 0
            for pair in frequent_pairs:
                cache_key = f"std_{pair.lower()}"
                self._symbol_cache[cache_key] = pair
                preloaded_count += 1
                
            logger.info(f"Preloaded cache with {preloaded_count} frequent pairs")
            
        except Exception as e:
            logger.error(f"Error preloading cache: {str(e)}")
