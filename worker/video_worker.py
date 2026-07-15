import logging
import os
import sys
import uuid
from pathlib import Path

# Ensure project root is on sys.path when run as a module
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.models.alert import Alert
from backend.models.enums import AlertStatus, EventType, RiskLevel
from backend.models.event import Event
from backend.services.ai_service.pipeline_service import run_pipeline
from backend.services.alert_service.alert_broadcaster import alert_broadcaster
from backend.services.event_service.event_broadcaster import event_broadcaster
from backend.services.redis_service.redis_service import redis_client

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [worker] %(message)s")


def _parse_job(raw: str) -> dict:
    import json

    return json.loads(raw)


def _save_results(db, camera_id: str | None, result: dict) -> None:
    severity = result["severity_report"]
    risk = RiskLevel(result["risk_level"])

    event = Event(
        camera_id=uuid.UUID(camera_id) if camera_id else None,
        event_type=EventType.DETECTION,
        action_label=severity.get("overall_level", "LOW"),
        risk_level=risk,
        metadata_={
            "timeline": result["timeline"],
            "severity_report": severity,
            "forensic_report": result.get("forensic_report"),
        },
    )
    db.add(event)

    alert: Alert | None = None
    if severity.get("flags") or severity.get("overall_level") in ("HIGH", "CRITICAL"):
        if not camera_id:
            logger.warning("High severity detected but no camera_id — skipping alert row")
        else:
            title = f"Security alert: {severity.get('overall_level', 'HIGH')} severity detected"
            description = result.get("forensic_report") or str(severity.get("per_entity", {}))
            alert = Alert(
                camera_id=uuid.UUID(camera_id),
                risk_level=risk,
                action_type="automated_detection",
                title=title,
                description=description[:4000] if description else None,
                reasoning=description,
                status=AlertStatus.PENDING,
            )
            db.add(alert)

    db.commit()
    db.refresh(event)
    event_broadcaster.broadcast_from_event(event)
    if alert:
        db.refresh(alert)
        alert_broadcaster.broadcast_from_alert(alert)


def process_queue() -> None:
    logger.info("Video worker started — waiting on queue '%s'", settings.redis_video_queue)

    while True:
        item = redis_client.brpop(settings.redis_video_queue, timeout=0)
        if not item:
            continue

        raw_payload = item[1]
        try:
            job = _parse_job(raw_payload)
        except Exception:
            job = {"video_path": raw_payload, "camera_id": None}

        video_path = job.get("video_path")
        camera_id = job.get("camera_id")

        if not video_path or not os.path.exists(video_path):
            logger.warning("Skipping missing video: %s", video_path)
            continue

        logger.info("Processing %s (camera=%s)", video_path, camera_id)
        db = SessionLocal()
        try:
            result = run_pipeline(video_path)
            _save_results(db, camera_id, result)
            logger.info(
                "Done — severity=%s flags=%s",
                result["severity_report"].get("overall_level"),
                result["severity_report"].get("flags"),
            )
        except Exception:
            logger.exception("Failed processing %s", video_path)
            db.rollback()
        finally:
            db.close()
            try:
                os.remove(video_path)
            except OSError:
                pass


if __name__ == "__main__":
    process_queue()
