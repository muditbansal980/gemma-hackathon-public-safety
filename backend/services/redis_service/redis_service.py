import json
from typing import Any

import redis

from backend.core.config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)


def enqueue_video_job(payload: dict[str, Any]) -> None:
    redis_client.lpush(settings.redis_video_queue, json.dumps(payload))


def publish_alert(payload: dict[str, Any]) -> None:
    redis_client.publish(settings.redis_alert_channel, json.dumps(payload))


def publish_event(payload: dict[str, Any]) -> None:
    redis_client.publish(settings.redis_events_channel, json.dumps(payload))
