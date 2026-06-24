# -*- coding: utf-8 -*-
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter(prefix="/ws/clientes", tags=["websockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, id_usuario: int):
        await websocket.accept()
        if id_usuario not in self.active_connections:
            self.active_connections[id_usuario] = []
        self.active_connections[id_usuario].append(websocket)

    def disconnect(self, websocket: WebSocket, id_usuario: int):
        if id_usuario in self.active_connections:
            if websocket in self.active_connections[id_usuario]:
                self.active_connections[id_usuario].remove(websocket)
            if not self.active_connections[id_usuario]:
                del self.active_connections[id_usuario]

    async def send_personal_message(self, message: dict, id_usuario: int):
        if id_usuario in self.active_connections:
            # Copy connection list to iterate safely
            for connection in list(self.active_connections[id_usuario]):
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be closed, disconnect it
                    self.disconnect(connection, id_usuario)

manager = ConnectionManager()

@router.websocket("/{id_usuario}")
async def client_notifications_websocket(websocket: WebSocket, id_usuario: int):
    await manager.connect(websocket, id_usuario)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, id_usuario)
