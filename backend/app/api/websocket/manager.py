"""
WebSocket Connection Manager

Manages WebSocket connections for real-time event broadcasting.
"""

from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # Map of attempt_id -> set of connected websockets (for candidates)
        self.assessment_connections: Dict[str, Set[WebSocket]] = {}
        
        # Map of attempt_id -> set of connected websockets (for recruiters monitoring)
        self.monitoring_connections: Dict[str, Set[WebSocket]] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect_assessment(self, websocket: WebSocket, attempt_id: str):
        """Connect a candidate's WebSocket for an assessment."""
        
        async with self._lock:
            if attempt_id not in self.assessment_connections:
                self.assessment_connections[attempt_id] = set()
            self.assessment_connections[attempt_id].add(websocket)

    async def connect_monitoring(self, websocket: WebSocket, attempt_id: str):
        """Connect a recruiter's WebSocket for live monitoring."""
        
        async with self._lock:
            if attempt_id not in self.monitoring_connections:
                self.monitoring_connections[attempt_id] = set()
            self.monitoring_connections[attempt_id].add(websocket)

    async def disconnect_assessment(self, websocket: WebSocket, attempt_id: str):
        """Disconnect a candidate's WebSocket."""
        async with self._lock:
            if attempt_id in self.assessment_connections:
                self.assessment_connections[attempt_id].discard(websocket)
                if not self.assessment_connections[attempt_id]:
                    del self.assessment_connections[attempt_id]

    async def disconnect_monitoring(self, websocket: WebSocket, attempt_id: str):
        """Disconnect a recruiter's monitoring WebSocket."""
        async with self._lock:
            if attempt_id in self.monitoring_connections:
                self.monitoring_connections[attempt_id].discard(websocket)
                if not self.monitoring_connections[attempt_id]:
                    del self.monitoring_connections[attempt_id]

    async def broadcast_to_monitors(self, attempt_id: str, message: dict):
        """Broadcast a message to all recruiters monitoring an assessment."""
        async with self._lock:
            connections = self.monitoring_connections.get(attempt_id, set()).copy()
        
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            await self.disconnect_monitoring(ws, attempt_id)

    async def send_to_assessment(self, attempt_id: str, message: dict):
        """Send a message to the candidate's assessment connection."""
        async with self._lock:
            connections = self.assessment_connections.get(attempt_id, set()).copy()
        
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            await self.disconnect_assessment(ws, attempt_id)

    def get_monitoring_count(self, attempt_id: str) -> int:
        """Get number of recruiters monitoring an assessment."""
        return len(self.monitoring_connections.get(attempt_id, set()))

    def get_assessment_connected(self, attempt_id: str) -> bool:
        """Check if a candidate is connected for an assessment."""
        return len(self.assessment_connections.get(attempt_id, set())) > 0


# Global connection manager instance
manager = ConnectionManager()
