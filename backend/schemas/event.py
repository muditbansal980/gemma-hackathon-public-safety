import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.models.enums import EventType, RiskLevel


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    camera_id: uuid.UUID | None
    person_id: uuid.UUID | None
    event_type: EventType
    action_label: str | None
    risk_level: RiskLevel | None
    location: str | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    human_intervention: bool
    occurred_at: datetime
    created_at: datetime
