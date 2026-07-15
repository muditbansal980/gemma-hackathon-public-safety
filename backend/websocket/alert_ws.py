import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from backend.core.config import settings
from backend.services.redis_service.redis_service import redis_client

logger = logging.getLogger(__name__)


class AlertWebSocketManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def listen_redis(self) -> None:
        pubsub = redis_client.pubsub()
        pubsub.subscribe(settings.redis_alert_channel)
        logger.info("Subscribed to Redis channel %s", settings.redis_alert_channel)

        while True:
            message = await asyncio.to_thread(
                pubsub.get_message,
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if message and message.get("type") == "message":
                try:
                    payload = json.loads(message["data"])
                    await self.broadcast(payload)
                except json.JSONDecodeError:
                    logger.warning("Invalid alert payload on Redis channel")
            await asyncio.sleep(0.05)


alert_ws_manager = AlertWebSocketManager()
