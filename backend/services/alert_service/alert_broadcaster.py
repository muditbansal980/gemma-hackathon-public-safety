import uuid
from datetime import datetime

from backend.models.alert import Alert
from backend.services.redis_service.redis_service import publish_alert


class AlertBroadcaster:
    def broadcast_from_alert(self, alert: Alert) -> None:
        payload = {
            "id": str(alert.id),
            "camera_id": str(alert.camera_id),
            "risk_level": alert.risk_level.value,
            "action_type": alert.action_type,
            "title": alert.title,
            "description": alert.description,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat()
            if isinstance(alert.created_at, datetime)
            else datetime.utcnow().isoformat(),
        }
        publish_alert(payload)


alert_broadcaster = AlertBroadcaster()
