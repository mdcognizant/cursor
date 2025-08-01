"""WebSocket route handlers for real-time communication."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()


@router.websocket("/agent/{agent_id}")
async def websocket_agent_communication(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time agent communication."""
    await websocket.accept()
    
    try:
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": f"Connected to agent {agent_id}",
            "agent_id": agent_id
        }))
        
        # Placeholder implementation - echo messages back
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back with agent response format
            response = {
                "type": "response",
                "agent_id": agent_id,
                "data": {
                    "message": f"Echo from agent {agent_id}: {message.get('content', '')}"
                }
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"WebSocket error: {str(e)}"
        }))


@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for subscribing to agent events."""
    await websocket.accept()
    
    try:
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "Connected to event stream"
        }))
        
        # Placeholder implementation - wait for disconnect
        while True:
            data = await websocket.receive_text()
            # Echo subscription confirmation
            await websocket.send_text(json.dumps({
                "type": "subscription",
                "message": "Event subscription confirmed"
            }))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"WebSocket error: {str(e)}"
        })) 