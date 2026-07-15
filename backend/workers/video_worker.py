from backend.services.redis_service.redis_service import redis_client
from backend.services.ai_service.yolo_service import run_yolo
from backend.services.ai_service.gemma_service import analyze
from backend.core.database import SessionLocal
from backend.models.event import Event

import os

while True:

    item = redis_client.brpop(
        "video_queue"
    )

    video_path = item[1]

    detections = run_yolo(video_path)

    summary = analyze(detections)

    db = SessionLocal()

    event = Event(
        summary=summary,
        severity="HIGH"
    )

    db.add(event)
    db.commit()

    os.remove(video_path)