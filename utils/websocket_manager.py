import asyncio
import json
import logging
import websockets
from typing import Dict, Optional, Callable, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.running = False
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        self.last_heartbeat: Dict[str, float] = {}
        self.heartbeat_interval = 30  # seconds

    async def connect(self, symbol: str, exchange: str, callback: Callable[[Dict[Any, Any]], None]) -> None:
        """Connect to exchange websocket and set up message handling."""
        try:
            # Get appropriate websocket URL and subscription message
            ws_url, subscription = self._get_exchange_config(exchange, symbol)
            
            connection_id = f"{exchange}_{symbol}"
            self.callbacks[connection_id] = callback

            # Connect to websocket with error handling
            try:
                websocket = await websockets.connect(ws_url, ping_interval=20)
                self.connections[connection_id] = websocket
                
                # Send subscription message
                await websocket.send(json.dumps(subscription))
                logger.info(f"Connected to {exchange} websocket for {symbol}")
                
                # Start message handling
                asyncio.create_task(self._handle_messages(connection_id, websocket))
                # Start heartbeat
                asyncio.create_task(self._heartbeat(connection_id))
                
            except Exception as e:
                logger.error(f"Error establishing websocket connection: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            raise

    def _get_exchange_config(self, exchange: str, symbol: str) -> tuple:
        """Get exchange-specific websocket configuration."""
        if exchange.lower() == 'kraken':
            return (
                "wss://ws.kraken.com",
                {
                    "event": "subscribe",
                    "pair": [symbol],
                    "subscription": {
                        "name": "ticker"
                    }
                }
            )
        elif exchange.lower() == 'kucoin':
            return (
                "wss://ws-api.kucoin.com/endpoint",
                {
                    "type": "subscribe",
                    "topic": f"/market/ticker:{symbol}",
                    "privateChannel": False,
                    "response": True
                }
            )
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    async def _handle_messages(self, connection_id: str, websocket: websockets.WebSocketClientProtocol) -> None:
        """Handle incoming websocket messages with improved error handling."""
        try:
            while True:
                try:
                    message = await websocket.recv()
                    self.last_heartbeat[connection_id] = time.time()
                    
                    try:
                        data = json.loads(message)
                        if self.callbacks.get(connection_id):
                            await self.callbacks[connection_id](data)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received from {connection_id}")
                    except Exception as e:
                        logger.error(f"Error processing message from {connection_id}: {str(e)}")
                        
                except websockets.ConnectionClosed:
                    logger.warning(f"Connection closed for {connection_id}")
                    await self._handle_connection_error(connection_id)
                    break
                    
        except Exception as e:
            logger.error(f"Error in message handling for {connection_id}: {str(e)}")
            await self._handle_connection_error(connection_id)

    async def _heartbeat(self, connection_id: str) -> None:
        """Monitor connection health and reconnect if necessary."""
        while connection_id in self.connections:
            await asyncio.sleep(self.heartbeat_interval)
            
            if connection_id not in self.last_heartbeat:
                self.last_heartbeat[connection_id] = time.time()
                continue
                
            last_heartbeat = self.last_heartbeat[connection_id]
            if time.time() - last_heartbeat > self.heartbeat_interval * 2:
                logger.warning(f"Connection {connection_id} appears stale, reconnecting...")
                await self._handle_connection_error(connection_id)

    async def _handle_connection_error(self, connection_id: str) -> None:
        """Handle connection errors with retry logic."""
        if connection_id in self.connections:
            try:
                await self.connections[connection_id].close()
            except:
                pass
            del self.connections[connection_id]

        exchange, symbol = connection_id.split('_', 1)
        
        for delay in self.retry_delays:
            try:
                await self.connect(symbol, exchange, self.callbacks[connection_id])
                logger.info(f"Successfully reconnected to {connection_id}")
                break
            except Exception as e:
                logger.error(f"Retry failed for {connection_id}: {str(e)}")
                await asyncio.sleep(delay)

    async def disconnect(self, symbol: str, exchange: str) -> None:
        """Disconnect from a specific websocket connection."""
        connection_id = f"{exchange}_{symbol}"
        if connection_id in self.connections:
            try:
                await self.connections[connection_id].close()
                del self.connections[connection_id]
                del self.callbacks[connection_id]
                logger.info(f"Disconnected from {connection_id}")
            except Exception as e:
                logger.error(f"Error disconnecting from {connection_id}: {str(e)}")

    async def disconnect_all(self) -> None:
        """Disconnect from all websocket connections."""
        for connection_id in list(self.connections.keys()):
            try:
                await self.connections[connection_id].close()
            except:
                pass
        self.connections.clear()
        self.callbacks.clear()
        logger.info("Disconnected from all websockets")

# Create singleton instance
websocket_manager = WebSocketManager()
