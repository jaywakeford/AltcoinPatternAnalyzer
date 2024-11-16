import asyncio
import json
import logging
import os
from typing import Dict, Optional, Callable, Any, Union, Tuple
from datetime import datetime
import time
from enum import Enum
import websockets

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """Enum for connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

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

    def _safe_task_callback(self, task: asyncio.Task) -> None:
        """Safe callback for completed tasks."""
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Task error: {str(e)}")

    async def connect(self, symbol: str, exchange: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Connect to exchange websocket with enhanced connection lifecycle management."""
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
            
            # Create connection pool in background
            pool_task = asyncio.create_task(self.create_connection_pool(connection_id, ws_url))
            pool_task.add_done_callback(self._safe_task_callback)
            
            # Update state and start management tasks
            self.connection_states[connection_id] = ConnectionState.CONNECTED
            management_task = asyncio.create_task(self._manage_connection(connection_id, websocket))
            management_task.add_done_callback(self._safe_task_callback)
            self.connection_tasks[connection_id] = management_task

        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            self.connection_states[connection_id] = ConnectionState.ERROR
            raise

    async def _manage_connection(self, connection_id: str, websocket: Any) -> None:
        """Manage connection lifecycle including message handling and heartbeat monitoring."""
        try:
            message_task = asyncio.create_task(self._handle_messages(connection_id, websocket))
            heartbeat_task = asyncio.create_task(self._heartbeat(connection_id))
            
            tasks = [message_task, heartbeat_task]
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check for errors in completed tasks
            for task in done:
                try:
                    await task
                except Exception as e:
                    logger.error(f"Task error in connection management: {str(e)}")
                    await self._handle_connection_error(connection_id)
                    break

        except Exception as e:
            logger.error(f"Error in connection management: {str(e)}")
            await self._handle_connection_error(connection_id)

    async def _handle_messages(self, connection_id: str, websocket: Any) -> None:
        """Handle incoming websocket messages with comprehensive error handling."""
        while True:
            try:
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
            except Exception as e:
                logger.error(f"Error in message handling: {str(e)}")
                raise

    async def _heartbeat(self, connection_id: str) -> None:
        """Monitor connection health with enhanced error detection."""
        while connection_id in self.connections:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if connection_id not in self.last_heartbeat:
                    self.last_heartbeat[connection_id] = time.time()
                    continue
                    
                last_heartbeat = self.last_heartbeat[connection_id]
                current_time = time.time()
                
                if current_time - last_heartbeat > self.heartbeat_interval * 2:
                    logger.warning(f"Connection {connection_id} appears stale")
                    raise ConnectionError(f"Connection {connection_id} stale")
                    
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
                break  # Stop trying if we can't create backup connections

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

    async def _get_exchange_config(self, exchange: str, symbol: str) -> Tuple[str, dict]:
        """Get exchange-specific websocket configuration."""
        if exchange.lower() == 'kraken':
            # Get API key for authentication
            api_key = os.getenv("KRAKEN_API_KEY")
            api_secret = os.getenv("KRAKEN_SECRET")
            
            # Generate authentication token if credentials are available
            auth = {}
            if api_key and api_secret:
                nonce = int(time.time() * 1000)
                auth = {
                    "apiKey": api_key,
                    "nonce": nonce
                }
            
            return (
                "wss://ws.kraken.com",
                {
                    "event": "subscribe",
                    "pair": [symbol],
                    "subscription": {
                        "name": "ticker"
                    },
                    **auth
                }
            )
        elif exchange.lower() == 'kucoin':
            # Add KuCoin authentication if needed
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

    async def disconnect(self, symbol: str, exchange: str) -> None:
        """Disconnect from a specific websocket connection with proper cleanup."""
        connection_id = f"{exchange}_{symbol}"
        
        if connection_id in self.connections:
            self.connection_states[connection_id] = ConnectionState.DISCONNECTED
            
            # Cancel management tasks
            if connection_id in self.connection_tasks:
                self.connection_tasks[connection_id].cancel()
                try:
                    await self.connection_tasks[connection_id]
                except asyncio.CancelledError:
                    pass
                del self.connection_tasks[connection_id]
            
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
            del self.connections[connection_id]
            self.callbacks.pop(connection_id, None)
            self.last_heartbeat.pop(connection_id, None)
            
            logger.info(f"Disconnected from {connection_id}")

    async def disconnect_all(self) -> None:
        """Disconnect from all websocket connections with proper cleanup."""
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
