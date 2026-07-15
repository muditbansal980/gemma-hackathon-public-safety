import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.models.enums import AlertStatus, RiskLevel


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camera_id: uuid.UUID
    person_id: uuid.UUID | None
    risk_level: RiskLevel
    action_type: str
    title: str
    description: str | None
    reasoning: str | None
    status: AlertStatus
    created_at: datetime


class AlertStatusUpdate(BaseModel):
    status: AlertStatus
