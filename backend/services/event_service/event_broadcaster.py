from datetime import datetime

from backend.models.event import Event
from backend.services.redis_service.redis_service import publish_event


class EventBroadcaster:
    def broadcast_from_event(self, event: Event) -> None:
        payload = {
            "id": str(event.id),
            "camera_id": str(event.camera_id) if event.camera_id else None,
            "event_type": event.event_type.value,
            "action_label": event.action_label,
            "risk_level": event.risk_level.value if event.risk_level else None,
            "occurred_at": event.occurred_at.isoformat()
            if isinstance(event.occurred_at, datetime)
            else datetime.utcnow().isoformat(),
            "metadata": event.metadata_ or {},
        }
        publish_event(payload)


event_broadcaster = EventBroadcaster()
