import uuid

from sqlalchemy.orm import Session

from backend.models.event import Event


class EventRepository:
    def get_all(self, db: Session, *, limit: int = 50) -> list[Event]:
        return db.query(Event).order_by(Event.occurred_at.desc()).limit(limit).all()

    def get_by_id(self, db: Session, event_id: uuid.UUID) -> Event | None:
        return db.query(Event).filter(Event.id == event_id).first()
