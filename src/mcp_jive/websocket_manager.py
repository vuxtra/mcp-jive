"""WebSocket connection manager for real-time event broadcasting."""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket
from weakref import WeakSet

logger = logging.getLogger(__name__)

class WebSocketConnectionManager:
    """Manages WebSocket connections and handles broadcasting events to all connected clients."""
    
    def __init__(self):
        # Use a regular set to track active connections
        # We'll handle cleanup manually in disconnect method
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None) -> None:
        """Register a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_info: Optional metadata about the client
        """
        async with self._lock:
            self.active_connections.add(websocket)
            self.connection_metadata[websocket] = {
                "connected_at": datetime.now().isoformat(),
                "client_info": client_info or {},
                "last_ping": datetime.now().isoformat()
            }
            
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        async with self._lock:
            self.active_connections.discard(websocket)
            self.connection_metadata.pop(websocket, None)
            
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any], exclude: Optional[WebSocket] = None) -> int:
        """Broadcast an event to all connected WebSocket clients.
        
        Args:
            event_type: Type of event (e.g., 'work_item_update', 'progress_update')
            data: Event data to broadcast
            exclude: Optional WebSocket connection to exclude from broadcast
            
        Returns:
            Number of clients that received the event
        """
        if not self.active_connections:
            logger.debug(f"No active WebSocket connections to broadcast {event_type} event")
            return 0
        
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        message_str = json.dumps(message)
        successful_sends = 0
        failed_connections = set()
        
        # Create a copy of connections to avoid modification during iteration
        connections_to_broadcast = self.active_connections.copy()
        if exclude:
            connections_to_broadcast.discard(exclude)
        
        for connection in connections_to_broadcast:
            try:
                await connection.send_text(message_str)
                successful_sends += 1
                logger.debug(f"Sent {event_type} event to WebSocket client")
            except Exception as e:
                logger.warning(f"Failed to send {event_type} event to WebSocket client: {e}")
                failed_connections.add(connection)
        
        # Clean up failed connections
        if failed_connections:
            async with self._lock:
                for failed_connection in failed_connections:
                    self.active_connections.discard(failed_connection)
                    self.connection_metadata.pop(failed_connection, None)
            
            logger.info(f"Cleaned up {len(failed_connections)} failed WebSocket connections")
        
        logger.info(f"Broadcasted {event_type} event to {successful_sends} clients")
        return successful_sends
    
    async def send_to_connection(self, websocket: WebSocket, event_type: str, data: Dict[str, Any]) -> bool:
        """Send an event to a specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection
            event_type: Type of event
            data: Event data
            
        Returns:
            True if sent successfully, False otherwise
        """
        if websocket not in self.active_connections:
            logger.warning("Attempted to send to inactive WebSocket connection")
            return False
        
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await websocket.send_text(json.dumps(message))
            logger.debug(f"Sent {event_type} event to specific WebSocket client")
            return True
        except Exception as e:
            logger.warning(f"Failed to send {event_type} event to specific client: {e}")
            await self.disconnect(websocket)
            return False
    
    async def ping_all_connections(self) -> int:
        """Send ping to all active connections to check health.
        
        Returns:
            Number of connections that responded successfully
        """
        return await self.broadcast_event("ping", {"message": "heartbeat"})
    
    def get_connection_count(self) -> int:
        """Get the number of active WebSocket connections.
        
        Returns:
            Number of active connections
        """
        return len(self.active_connections)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about all active connections.
        
        Returns:
            Dictionary with connection statistics and metadata
        """
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "client": str(ws.client) if hasattr(ws, 'client') else "unknown",
                    "metadata": self.connection_metadata.get(ws, {})
                }
                for ws in self.active_connections
            ]
        }
    
    async def cleanup_stale_connections(self) -> int:
        """Remove connections that are no longer active.
        
        Returns:
            Number of connections cleaned up
        """
        stale_connections = set()
        
        for connection in self.active_connections.copy():
            try:
                # Try to send a ping to check if connection is alive
                await connection.ping()
            except Exception:
                stale_connections.add(connection)
        
        if stale_connections:
            async with self._lock:
                for stale_connection in stale_connections:
                    self.active_connections.discard(stale_connection)
                    self.connection_metadata.pop(stale_connection, None)
            
            logger.info(f"Cleaned up {len(stale_connections)} stale WebSocket connections")
        
        return len(stale_connections)

# Global instance to be used across the application
websocket_manager = WebSocketConnectionManager()