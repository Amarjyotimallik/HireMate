"""
Live Monitoring WebSocket Handler

Allows recruiters to monitor assessments in real-time.
"""

from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from app.api.websocket.manager import manager
from app.services import get_attempt_by_id, get_first_active_user
from app.core import decode_token
from app.config import get_settings


async def handle_live_monitoring_websocket(websocket: WebSocket, attempt_id: str):
    """
    Handle WebSocket connection for recruiter live monitoring.
    
    Requires JWT authentication via query parameter or header.
    Also accepts demo token for development.
    
    Messages sent to recruiter:
    - candidate_connected / candidate_disconnected
    - event_logged (real-time events from candidate)
    - status_update (attempt status changes)
    - metrics_update (live metrics computed on significant events)
    """
    await websocket.accept()
    settings = get_settings()
    
    # Get token from query params or headers
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        await websocket.close(code=4001, reason="Missing authentication")
        return
    
    # Check for demo token first
    is_authenticated = False
    if settings.demo_auth_token and token == settings.demo_auth_token:
        # Demo token - check we have an active user
        dev_user = await get_first_active_user()
        if dev_user:
            is_authenticated = True
    
    # If not demo token, try to validate as JWT
    if not is_authenticated:
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            is_authenticated = True
    
    if not is_authenticated:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Validate attempt exists
    attempt = await get_attempt_by_id(attempt_id)
    if not attempt:
        await websocket.close(code=4004, reason="Attempt not found")
        return
    
    # Connect for monitoring
    await manager.connect_monitoring(websocket, attempt_id)
    
    # Send initial status
    await websocket.send_json({
        "type": "status_update",
        "attempt_id": attempt_id,
        "status": attempt.status.value,
        "current_task_index": attempt.current_task_index,
        "total_tasks": len(attempt.task_ids),
        "candidate_connected": manager.get_assessment_connected(attempt_id),
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    try:
        while True:
            # Keep connection alive, handle any recruiter messages
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif data.get("type") == "get_status":
                # Refresh attempt status
                attempt = await get_attempt_by_id(attempt_id)
                if attempt:
                    await websocket.send_json({
                        "type": "status_update",
                        "attempt_id": attempt_id,
                        "status": attempt.status.value,
                        "current_task_index": attempt.current_task_index,
                        "total_tasks": len(attempt.task_ids),
                        "candidate_connected": manager.get_assessment_connected(attempt_id),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect_monitoring(websocket, attempt_id)
