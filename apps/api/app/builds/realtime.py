import uuid
from collections import defaultdict

from fastapi import WebSocket


class BuildRealtimeHub:
    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def broadcast(self, user_ids: set[uuid.UUID], message: dict[str, object]) -> None:
        failed: list[tuple[uuid.UUID, WebSocket]] = []
        for user_id in user_ids:
            for websocket in tuple(self._connections.get(user_id, ())):
                try:
                    await websocket.send_json(message)
                except Exception:
                    failed.append((user_id, websocket))
        for user_id, websocket in failed:
            self.disconnect(user_id, websocket)


build_realtime_hub = BuildRealtimeHub()
