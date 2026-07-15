from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.alert import AlertResponse, AlertStatusUpdate
from backend.services.alert_service.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])
alert_service = AlertService()


@router.get("/", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db), limit: int = 50):
    return alert_service.list_alerts(db, limit=limit)


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert_status(
    alert_id: UUID,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
):
    return alert_service.update_status(db, alert_id, payload.status)
