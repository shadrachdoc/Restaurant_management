"""
WebSocket server for real-time order notifications
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from shared.utils.logger import setup_logger

logger = setup_logger("websocket")


class ConnectionManager:
    """Manages WebSocket connections for real-time order notifications"""

    def __init__(self):
        # Store connections by restaurant_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, restaurant_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if restaurant_id not in self.active_connections:
            self.active_connections[restaurant_id] = set()

        self.active_connections[restaurant_id].add(websocket)
        logger.info(f"Client connected to restaurant {restaurant_id}. Total connections: {len(self.active_connections[restaurant_id])}")

    def disconnect(self, websocket: WebSocket, restaurant_id: str):
        """Remove a WebSocket connection"""
        if restaurant_id in self.active_connections:
            self.active_connections[restaurant_id].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[restaurant_id]:
                del self.active_connections[restaurant_id]

            logger.info(f"Client disconnected from restaurant {restaurant_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast_to_restaurant(self, message: dict, restaurant_id: str):
        """Broadcast a message to all connections for a specific restaurant"""
        if restaurant_id not in self.active_connections:
            logger.debug(f"No active connections for restaurant {restaurant_id}")
            return

        disconnected = []
        connections = list(self.active_connections[restaurant_id])

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, restaurant_id)

        logger.info(f"Broadcasted message to {len(connections) - len(disconnected)} clients for restaurant {restaurant_id}")

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        for restaurant_id in list(self.active_connections.keys()):
            await self.broadcast_to_restaurant(message, restaurant_id)


# Global connection manager instance
manager = ConnectionManager()
