import logging
import re
from typing import Optional, Tuple, Dict

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

    def convert_to_standard_format(self, symbol: str) -> Optional[str]:
        """Convert any symbol format to standard BASE/QUOTE format."""
        try:
            # Remove any whitespace and convert to uppercase
            symbol = symbol.strip().upper()
            
            # Handle different separator formats
            separators = ['/', '-', '_', ' ']
            for sep in separators:
                if sep in symbol:
                    base, quote = symbol.split(sep)
                    if base in self.valid_base_currencies and quote in self.valid_quote_currencies:
                        return f"{base}/{'USDT' if quote == 'USD' else quote}"
            
            # If no separator found, try to match known base currency
            for base in self.valid_base_currencies:
                if symbol.startswith(base):
                    remaining = symbol[len(base):]
                    for quote in self.valid_quote_currencies:
                        if remaining == quote:
                            return f"{base}/{'USDT' if quote == 'USD' else quote}"
            
            return None
        except Exception as e:
            logger.error(f"Error converting symbol format: {str(e)}")
            return None

    def get_exchange_format(self, symbol: str, exchange: str = 'default') -> Optional[str]:
        """Convert standard format to exchange-specific format."""
        try:
            # First convert to standard format if not already
            std_symbol = self.convert_to_standard_format(symbol) or symbol
            
            if '/' not in std_symbol:
                return None
                
            base, quote = std_symbol.split('/')
            
            # Get exchange-specific formatter
            formatter = self.exchange_formats.get(exchange.lower(), self.exchange_formats['default'])
            return formatter(base, quote)
            
        except Exception as e:
            logger.error(f"Error converting to exchange format: {str(e)}")
            return None

    def convert_from_coin_name(self, coin_name: str, quote_currency: str = 'USDT') -> Optional[str]:
        """Convert full coin name to trading symbol."""
        try:
            if not coin_name:
                return None
                
            coin_lower = coin_name.lower()
            symbol = self.symbol_mapping.get(coin_lower)
            
            if not symbol:
                return None
                
            trading_pair = f"{symbol}/{quote_currency}"
            return trading_pair if self.validate_symbol(trading_pair)[0] else None
            
        except Exception as e:
            logger.error(f"Error converting from coin name: {str(e)}")
            return None

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
