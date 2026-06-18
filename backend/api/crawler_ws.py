"""
WebSocket进度推送
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def broadcast(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except:
                    dead_connections.add(connection)
            
            for dead in dead_connections:
                self.active_connections[task_id].discard(dead)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except:
            pass


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        await manager.send_personal(websocket, {
            "event": "connected",
            "task_id": task_id,
            "message": "WebSocket连接成功"
        })
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {
                        "event": "pong",
                        "task_id": task_id
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        manager.disconnect(websocket, task_id)


async def push_progress(
    task_id: str,
    event: str,
    current: int = None,
    total: int = None,
    message: str = None,
    data: dict = None
):
    payload = {
        "event": event,
        "task_id": task_id
    }
    
    if current is not None:
        payload["current"] = current
    if total is not None:
        payload["total"] = total
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    
    await manager.broadcast(task_id, payload)
