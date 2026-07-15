import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.enums import AlertStatus
from backend.repositories.alert_repository import AlertRepository


class AlertService:
    def __init__(self) -> None:
        self.repo = AlertRepository()

    def list_alerts(self, db: Session, limit: int = 50):
        return self.repo.get_all(db, limit=limit)

    def update_status(self, db: Session, alert_id: uuid.UUID, status: AlertStatus):
        alert = self.repo.get_by_id(db, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return self.repo.update_status(db, alert, status)
