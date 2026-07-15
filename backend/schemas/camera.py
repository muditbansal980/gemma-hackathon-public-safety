from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class CameraCreate(BaseModel):
    name: str
    location: str
    zone: str | None = None
    rtsp_url: str | None = None


class CameraUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    zone: str | None = None
    rtsp_url: str | None = None
    is_active: bool | None = None


class CameraResponse(BaseModel):
    id: UUID
    name: str
    location: str
    zone: str | None
    rtsp_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True