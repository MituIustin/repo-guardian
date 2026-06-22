import uuid
from collections import defaultdict

from fastapi import WebSocket


class RepositoryRealtimeHub:
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

    async def notify(self, user_id: uuid.UUID, reason: str) -> None:
        failed: list[WebSocket] = []
        for websocket in tuple(self._connections.get(user_id, ())):
            try:
                await websocket.send_json(
                    {"type": "repositories.changed", "reason": reason}
                )
            except Exception:
                failed.append(websocket)
        for websocket in failed:
            self.disconnect(user_id, websocket)


repository_realtime_hub = RepositoryRealtimeHub()
