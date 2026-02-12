"""
Assessment WebSocket Handler

Handles real-time event logging from candidates during assessments.
"""

import asyncio
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import json

from app.api.websocket.manager import manager
from app.services import (
    get_attempt_by_token,
    log_event,
)
from app.services.live_metrics_service import compute_live_metrics
from app.schemas import EventCreate, EventType


async def handle_assessment_websocket(websocket: WebSocket, token: str):
    """
    Handle WebSocket connection for a candidate's assessment.
    
    Messages from client:
    {
        "type": "event",
        "event_type": "option_selected",
        "task_id": "...",
        "payload": {...},
        "client_timestamp": "ISO8601"
    }
    
    Messages to client:
    {
        "type": "event_logged",
        "event_id": "...",
        "event_type": "...",
        "timestamp": "ISO8601",
        "payload": {...}
    }
    """
    await websocket.accept()
    print(f"[WS] Connection attempt received for token: {token}")
    # Validate token
    attempt = await get_attempt_by_token(token)
    if not attempt:
        print(f"[WS] Validation failed: Invalid token {token}")
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    print(f"[WS] Token validated for assessment: {attempt.id}")
    
    if attempt.status.value not in ["pending", "in_progress"]:
        print(f"[WS] Connection rejected: Assessment {attempt.id} is in status {attempt.status.value}")
        await websocket.close(code=4002, reason="Assessment not active")
        return
    
    attempt_id = str(attempt.id)
    
    # Connect
    try:
        await manager.connect_assessment(websocket, attempt_id)
        print(f"[WS] Connected and accepted: {attempt_id}")
    except Exception as e:
        print(f"[WS] Error during connect_assessment: {e}")
        raise e
    
    # Notify monitors that candidate connected
    await manager.broadcast_to_monitors(attempt_id, {
        "type": "candidate_connected",
        "attempt_id": attempt_id,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    # Significant events that trigger metrics broadcast
    SIGNIFICANT_EVENTS = [
        EventType.TASK_COMPLETED,
        EventType.TASK_SKIPPED,
        EventType.OPTION_SELECTED,
        EventType.OPTION_CHANGED,
        EventType.PASTE_DETECTED,
        EventType.FOCUS_LOST,
        EventType.COPY_DETECTED,
    ]
    
    try:
        while True:
            # Receive message from candidate
            data = await websocket.receive_json()
            
            if data.get("type") == "event":
                # Log the event
                try:
                    event_type = EventType(data.get("event_type"))
                    event_data = EventCreate(
                        task_id=data.get("task_id"),
                        event_type=event_type,
                        payload=data.get("payload", {}),
                        client_timestamp=data.get("client_timestamp"),
                    )
                    
                    # Get client info from websocket
                    user_agent = None
                    ip_address = None
                    if hasattr(websocket, "headers"):
                        user_agent = websocket.headers.get("user-agent")
                    if websocket.client:
                        ip_address = websocket.client.host
                    
                    logged_event = await log_event(
                        attempt_id=attempt_id,
                        event_data=event_data,
                        user_agent=user_agent,
                        ip_address=ip_address,
                    )
                    
                    # Confirm to candidate
                    try:
                        await websocket.send_json({
                            "type": "event_logged",
                            "event_id": logged_event.id,
                            "event_type": logged_event.event_type.value,
                            "timestamp": logged_event.timestamp.isoformat(),
                            "sequence_number": logged_event.sequence_number,
                        })
                    except (RuntimeError, WebSocketDisconnect):
                        # Client disconnected during send, break loop to cleanup
                        break
                    
                    # Broadcast to monitoring recruiters
                    await manager.broadcast_to_monitors(attempt_id, {
                        "type": "event_logged",
                        "event_id": logged_event.id,
                        "event_type": logged_event.event_type.value,
                        "task_id": logged_event.task_id,
                        "timestamp": logged_event.timestamp.isoformat(),
                        "payload": logged_event.payload,
                        "sequence_number": logged_event.sequence_number,
                    })
                    
                    # On significant events, compute and broadcast live metrics in BACKGROUND
                    # This prevents blocking the websocket loop, keeping candidate UI responsive
                    if event_type in SIGNIFICANT_EVENTS:
                        asyncio.create_task(broadcast_metrics_task(attempt_id))
                    
                except Exception as e:
                    import traceback
                    error_msg = f"WS Event Error: {e}\n{traceback.format_exc()}"
                    print(error_msg)
                    try:
                        with open("backend_error.log", "a") as f:
                            f.write(f"{datetime.utcnow().isoformat()} - {error_msg}\n")
                    except: pass

                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e),
                        })
                    except (RuntimeError, WebSocketDisconnect):
                        break
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect_assessment(websocket, attempt_id)
        
        # Notify monitors that candidate disconnected
        await manager.broadcast_to_monitors(attempt_id, {
            "type": "candidate_disconnected",
            "attempt_id": attempt_id,
            "timestamp": datetime.utcnow().isoformat(),
        })


async def broadcast_metrics_task(attempt_id: str):
    """
    Background task to compute and broadcast live metrics.
    Decoupled from the main websocket loop to prevent blocking.
    """
    try:
        live_metrics = await compute_live_metrics(attempt_id)
        if live_metrics:
            await manager.broadcast_to_monitors(attempt_id, {
                "type": "metrics_update",
                "attempt_id": attempt_id,
                "metrics": live_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            })
    except Exception as e:
        # Log error entirely in background, don't affect main loop
        print(f"Background Metrics Error: {e}")
        try:
            with open("backend_error.log", "a") as f:
                f.write(f"{datetime.utcnow().isoformat()} - Background Metrics Error: {e}\n")
        except: pass

