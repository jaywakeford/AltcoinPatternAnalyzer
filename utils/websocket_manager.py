import asyncio
import json
import logging
import os
from typing import Dict, Optional, Callable, Any, Union, Tuple
from datetime import datetime
import time
from enum import Enum
import websockets
import re

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """Enum for connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

class SymbolConverter:
    def __init__(self):
        self.valid_base_currencies = {
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 
            'AVAX', 'DOT', 'MATIC', 'LINK', 'UNI', 'LTC'
        }
        self.valid_quote_currencies = {'USDT', 'USD', 'EUR', 'BTC'}

    def convert_to_exchange_format(self, symbol: str, exchange: str) -> Optional[str]:
        """Convert standard symbol to exchange-specific format."""
        if exchange.lower() == 'kraken':
            return symbol
        elif exchange.lower() == 'kucoin':
            return symbol.replace('/', '-')
        else:
            return None

    def convert_from_exchange_format(self, symbol: str, exchange: str) -> Optional[str]:
        """Convert exchange-specific symbol to standard format."""
        if exchange.lower() == 'kraken':
            return symbol
        elif exchange.lower() == 'kucoin':
            return symbol.replace('-', '/')
        else:
            return None

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.running = False
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        self.last_heartbeat: Dict[str, float] = {}
        self.heartbeat_interval = 30  # seconds
        self.connection_states: Dict[str, ConnectionState] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.max_reconnect_attempts = 5
        self.connection_pools: Dict[str, asyncio.Queue] = {}
        self.pool_size = 2  # Number of backup connections per symbol
        self._cleanup_lock = asyncio.Lock()
        self.valid_base_currencies = {
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 
            'AVAX', 'DOT', 'MATIC', 'LINK', 'UNI', 'LTC'
        }
        self.valid_quote_currencies = {'USDT', 'USD', 'EUR', 'BTC'}
        self._loop = None

        # Add exchange-specific websocket configurations
        self.exchange_configs = {
            'kraken': {
                'url': 'wss://ws.kraken.com',
                'subscribe_format': lambda symbol: {
                    "event": "subscribe",
                    "pair": [symbol],
                    "subscription": {"name": "ticker"}
                },
                'requires_auth': True,
                'ping_interval': 30,
                'connection_timeout': 10000
            },
            'kucoin': {
                'url': 'wss://ws-api.kucoin.com/endpoint',
                'subscribe_format': lambda symbol: {
                    "type": "subscribe",
                    "topic": f"/market/ticker:{symbol}",
                    "privateChannel": False,
                    "response": True
                },
                'requires_auth': False,
                'ping_interval': 20,
                'connection_timeout': 5000
            },
            'binance': {
                'url': 'wss://stream.binance.com:9443/ws',
                'subscribe_format': lambda symbol: {
                    "method": "SUBSCRIBE",
                    "params": [f"{symbol.lower()}@ticker"],
                    "id": 1
                },
                'requires_auth': False,
                'ping_interval': 30,
                'connection_timeout': 5000
            }
        }
        
        # Create SymbolConverter instance for format conversion
        self.symbol_converter = SymbolConverter()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _validate_symbol(self, symbol: str, exchange: str = 'default') -> bool:
        """Validate symbol format with exchange-specific checks."""
        try:
            if not symbol or not isinstance(symbol, str):
                logger.warning(f"Invalid symbol: {symbol} - Must be a non-empty string")
                return False
                
            # First convert to standard format if it's in exchange format
            standard_symbol = self.symbol_converter.convert_from_exchange_format(symbol, exchange)
            if not standard_symbol:
                standard_symbol = symbol  # Try with original symbol if conversion fails
                
            # Check format using regex for standard format
            if not re.match(r'^[A-Z0-9]+/[A-Z0-9]+$', standard_symbol):
                logger.warning(f"Invalid symbol format: {standard_symbol}")
                return False
                
            base, quote = standard_symbol.split('/')
            
            # Validate currencies using symbol converter's valid sets
            if base not in self.symbol_converter.valid_base_currencies:
                logger.warning(f"Invalid base currency: {base}")
                return False
                
            if quote not in self.symbol_converter.valid_quote_currencies:
                logger.warning(f"Invalid quote currency: {quote}")
                return False
                
            logger.info(f"Symbol validated successfully: {symbol} for exchange {exchange}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {str(e)}")
            return False

    async def _get_exchange_config(self, exchange: str, symbol: str) -> Tuple[str, dict]:
        """Get exchange-specific websocket configuration with proper symbol format."""
        try:
            if exchange.lower() not in self.exchange_configs:
                raise ValueError(f"Unsupported exchange: {exchange}")

            config = self.exchange_configs[exchange.lower()]
            
            # Convert symbol to exchange-specific format
            exchange_symbol = self.symbol_converter.convert_to_exchange_format(symbol, exchange)
            if not exchange_symbol:
                raise ValueError(f"Could not convert symbol {symbol} to {exchange} format")

            # Get API key for authentication if needed
            api_key = os.getenv(f"{exchange.upper()}_API_KEY")
            api_secret = os.getenv(f"{exchange.upper()}_SECRET")
            
            # Generate subscription message
            subscription = config['subscribe_format'](exchange_symbol)
            
            # Add authentication if available
            if api_key and api_secret:
                subscription.update({
                    "apiKey": api_key,
                    "nonce": int(time.time() * 1000)
                })

            return config['url'], subscription

        except Exception as e:
            logger.error(f"Error getting exchange config: {str(e)}")
            raise

    async def connect(self, symbol: str, exchange: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Connect to exchange websocket with enhanced connection lifecycle management."""
        if not self._validate_symbol(symbol, exchange):
            logger.error(f"Invalid symbol format: {symbol}")
            raise ValueError(f"Invalid symbol format: {symbol}. Symbol must be in BASE/QUOTE format (e.g., BTC/USDT)")
            
        connection_id = f"{exchange}_{symbol}"
        
        try:
            if connection_id in self.connections:
                # Close existing connection if any
                await self.disconnect(symbol, exchange)

            self.connection_states[connection_id] = ConnectionState.CONNECTING
            
            # Get appropriate websocket URL and subscription message
            ws_url, subscription = await self._get_exchange_config(exchange, symbol)
            self.callbacks[connection_id] = callback

            # Establish main connection
            websocket = await websockets.connect(ws_url, ping_interval=20)
            self.connections[connection_id] = websocket
            
            # Send subscription message
            await websocket.send(json.dumps(subscription))
            logger.info(f"Connected to {exchange} websocket for {symbol}")
            
            # Create and store management task using the same loop
            management_task = self.loop.create_task(
                self._manage_connection(connection_id, websocket)
            )
            self.connection_tasks[connection_id] = management_task
            
            # Create connection pool in background using the same loop
            pool_task = self.loop.create_task(
                self.create_connection_pool(connection_id, ws_url)
            )
            self.connection_tasks[f"{connection_id}_pool"] = pool_task
            
            # Update state
            self.connection_states[connection_id] = ConnectionState.CONNECTED

        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            self.connection_states[connection_id] = ConnectionState.ERROR
            raise

    async def _manage_connection(self, connection_id: str, websocket: Any) -> None:
        """Manage connection lifecycle including message handling and heartbeat monitoring."""
        message_task = None
        heartbeat_task = None
        
        try:
            # Create tasks using the same loop
            message_task = self.loop.create_task(self._handle_messages(connection_id, websocket))
            heartbeat_task = self.loop.create_task(self._heartbeat(connection_id))
            
            # Wait for either task to complete or fail
            done, pending = await asyncio.wait(
                [message_task, heartbeat_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Process completed tasks
            for task in done:
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task cancelled for {connection_id}")
                except Exception as e:
                    logger.error(f"Task error in connection management: {str(e)}")
                    raise

        except Exception as e:
            logger.error(f"Error in connection management: {str(e)}")
            raise

        finally:
            # Cleanup tasks
            for task in [message_task, heartbeat_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Error cleaning up task: {str(e)}")

            await self._handle_connection_error(connection_id)

    async def _handle_messages(self, connection_id: str, websocket: Any) -> None:
        """Handle incoming websocket messages with comprehensive error handling."""
        try:
            while True:
                message = await websocket.recv()
                self.last_heartbeat[connection_id] = time.time()
                
                try:
                    data = json.loads(message)
                    callback = self.callbacks.get(connection_id)
                    if callback:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                            
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from {connection_id}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Connection closed for {connection_id}")
            raise
        except asyncio.CancelledError:
            logger.info(f"Message handling cancelled for {connection_id}")
            raise
        except Exception as e:
            logger.error(f"Error in message handling: {str(e)}")
            raise

    async def _heartbeat(self, connection_id: str) -> None:
        """Monitor connection health with enhanced error detection."""
        try:
            while connection_id in self.connections:
                await asyncio.sleep(self.heartbeat_interval)
                
                if connection_id not in self.last_heartbeat:
                    self.last_heartbeat[connection_id] = time.time()
                    continue
                    
                last_heartbeat = self.last_heartbeat[connection_id]
                current_time = time.time()
                
                if current_time - last_heartbeat > self.heartbeat_interval * 2:
                    logger.warning(f"Connection {connection_id} appears stale")
                    raise ConnectionError(f"Connection {connection_id} stale")
                    
        except asyncio.CancelledError:
            logger.info(f"Heartbeat monitoring cancelled for {connection_id}")
            raise
        except Exception as e:
            logger.error(f"Heartbeat error: {str(e)}")
            raise

    async def create_connection_pool(self, connection_id: str, ws_url: str) -> None:
        """Create a pool of backup connections."""
        if connection_id not in self.connection_pools:
            self.connection_pools[connection_id] = asyncio.Queue(maxsize=self.pool_size)
            
        while self.connection_pools[connection_id].qsize() < self.pool_size:
            try:
                websocket = await websockets.connect(ws_url, ping_interval=20)
                await self.connection_pools[connection_id].put(websocket)
                logger.info(f"Added backup connection to pool for {connection_id}")
            except Exception as e:
                logger.warning(f"Failed to create backup connection: {str(e)}")
                break

    async def _handle_connection_error(self, connection_id: str) -> None:
        """Handle connection errors with enhanced recovery mechanisms."""
        if connection_id in self.connections:
            self.connection_states[connection_id] = ConnectionState.RECONNECTING
            
            # Close existing connection
            try:
                await self.connections[connection_id].close()
            except:
                pass
            
            del self.connections[connection_id]

            # Try to get a backup connection
            try:
                if connection_id in self.connection_pools:
                    backup = await self.connection_pools[connection_id].get_nowait()
                    self.connections[connection_id] = backup
                    self.connection_states[connection_id] = ConnectionState.CONNECTED
                    logger.info(f"Switched to backup connection for {connection_id}")
                    return
            except (asyncio.QueueEmpty, KeyError):
                pass

            # If no backup available, try reconnecting
            exchange, symbol = connection_id.split('_', 1)
            for attempt, delay in enumerate(self.retry_delays):
                try:
                    await self.connect(symbol, exchange, self.callbacks[connection_id])
                    logger.info(f"Successfully reconnected to {connection_id}")
                    return
                except Exception as e:
                    logger.error(f"Reconnection attempt {attempt + 1} failed: {str(e)}")
                    if attempt < len(self.retry_delays) - 1:
                        await asyncio.sleep(delay)
                    else:
                        self.connection_states[connection_id] = ConnectionState.ERROR
                        logger.error(f"All reconnection attempts failed")

    async def disconnect(self, symbol: str, exchange: str) -> None:
        """Disconnect from a specific websocket connection with proper cleanup."""
        connection_id = f"{exchange}_{symbol}"
        
        async with self._cleanup_lock:
            if connection_id in self.connections:
                self.connection_states[connection_id] = ConnectionState.DISCONNECTED
                
                # Cancel and clean up tasks
                tasks_to_cancel = []
                if connection_id in self.connection_tasks:
                    tasks_to_cancel.append(self.connection_tasks[connection_id])
                if f"{connection_id}_pool" in self.connection_tasks:
                    tasks_to_cancel.append(self.connection_tasks[f"{connection_id}_pool"])
                
                for task in tasks_to_cancel:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                
                # Close main connection
                try:
                    await self.connections[connection_id].close()
                except:
                    pass
                    
                # Clean up connection pool
                if connection_id in self.connection_pools:
                    while not self.connection_pools[connection_id].empty():
                        try:
                            ws = await self.connection_pools[connection_id].get_nowait()
                            await ws.close()
                        except:
                            pass
                    del self.connection_pools[connection_id]
                
                # Clean up resources
                self.connections.pop(connection_id, None)
                self.callbacks.pop(connection_id, None)
                self.last_heartbeat.pop(connection_id, None)
                self.connection_tasks.pop(connection_id, None)
                self.connection_tasks.pop(f"{connection_id}_pool", None)
                
                logger.info(f"Disconnected from {connection_id}")

    async def disconnect_all(self) -> None:
        """Disconnect from all websocket connections with proper cleanup."""
        async with self._cleanup_lock:
            for connection_id in list(self.connections.keys()):
                exchange, symbol = connection_id.split('_', 1)
                await self.disconnect(symbol, exchange)
            
            self.connections.clear()
            self.callbacks.clear()
            self.connection_states.clear()
            self.connection_tasks.clear()
            self.connection_pools.clear()
            logger.info("Disconnected from all websockets")

    def get_connection_state(self, symbol: str, exchange: str) -> ConnectionState:
        """Get the current state of a connection."""
        connection_id = f"{exchange}_{symbol}"
        return self.connection_states.get(connection_id, ConnectionState.DISCONNECTED)

# Create singleton instance
websocket_manager = WebSocketManager()