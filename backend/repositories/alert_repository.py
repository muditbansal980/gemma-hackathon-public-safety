import uuid

from sqlalchemy.orm import Session

from backend.models.alert import Alert
from backend.models.enums import AlertStatus, RiskLevel


class AlertRepository:
    def create(self, db: Session, data: dict) -> Alert:
        alert = Alert(**data)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def get_all(self, db: Session, *, limit: int = 50) -> list[Alert]:
        return db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()

    def get_by_id(self, db: Session, alert_id: uuid.UUID) -> Alert | None:
        return db.query(Alert).filter(Alert.id == alert_id).first()

    def update_status(self, db: Session, alert: Alert, status: AlertStatus) -> Alert:
        alert.status = status
        db.commit()
        db.refresh(alert)
        return alert
