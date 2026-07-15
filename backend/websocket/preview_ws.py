import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class PreviewWebSocketManager:
    """Per-camera WebSocket subscribers for live annotated preview frames."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[WebSocket]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, camera_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._subscribers.setdefault(camera_id, []).append(websocket)
        logger.info("Preview client connected for camera %s", camera_id)

    def disconnect(self, camera_id: str, websocket: WebSocket) -> None:
        clients = self._subscribers.get(camera_id, [])
        if websocket in clients:
            clients.remove(websocket)
        if not clients:
            self._subscribers.pop(camera_id, None)

    async def broadcast_frame(
        self,
        camera_id: str,
        jpeg_bytes: bytes,
        detections: list[dict[str, Any]],
    ) -> None:
        clients = list(self._subscribers.get(camera_id, []))
        if not clients:
            return

        payload = {
            "type": "frame",
            "camera_id": camera_id,
            "image": base64.b64encode(jpeg_bytes).decode("ascii"),
            "detections": detections,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        message = json.dumps(payload)
        dead: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(camera_id, ws)

    def schedule_broadcast(
        self,
        camera_id: str,
        jpeg_bytes: bytes,
        detections: list[dict[str, Any]],
    ) -> None:
        """Thread-safe entry point from the recorder loop."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self.broadcast_frame(camera_id, jpeg_bytes, detections),
            self._loop,
        )


preview_ws_manager = PreviewWebSocketManager()
