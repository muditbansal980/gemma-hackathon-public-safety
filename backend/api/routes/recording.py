from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.repositories.camera_repository import CameraRepository
from backend.schemas.recording import (
    ActiveRecordingsResponse,
    RecordingStartRequest,
    RecordingStatusResponse,
)
from backend.services.camera_service.camera_recorder_service import recorder_service

router = APIRouter(prefix="/recording", tags=["Recording"])
camera_repo = CameraRepository()


def _resolve_source(source: str) -> str | int:
    if source == "webcam":
        return "webcam"
    if source.isdigit():
        return int(source)
    return source


@router.post("/{camera_id}/start", response_model=RecordingStatusResponse)
def start_recording(
    camera_id: UUID,
    payload: RecordingStartRequest,
    db: Session = Depends(get_db),
):
    camera = camera_repo.get_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    source = payload.source or camera.rtsp_url or "webcam"
    if source == "webcam" and camera.rtsp_url and camera.rtsp_url != "webcam":
        source = camera.rtsp_url

    try:
        recorder_service.start_recording(str(camera_id), _resolve_source(source))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return RecordingStatusResponse(
        camera_id=str(camera_id),
        is_recording=True,
        message=f"Recording started from {source}",
    )


@router.post("/{camera_id}/stop", response_model=RecordingStatusResponse)
def stop_recording(camera_id: UUID):
    recorder_service.stop_recording(str(camera_id))
    return RecordingStatusResponse(
        camera_id=str(camera_id),
        is_recording=False,
        message="Recording stopped",
    )


@router.get("/active", response_model=ActiveRecordingsResponse)
def active_recordings():
    return ActiveRecordingsResponse(camera_ids=recorder_service.list_active_recordings())


@router.get("/{camera_id}/status", response_model=RecordingStatusResponse)
def recording_status(camera_id: UUID):
    is_recording = recorder_service.is_recording(str(camera_id))
    return RecordingStatusResponse(
        camera_id=str(camera_id),
        is_recording=is_recording,
        message="Recording" if is_recording else "Idle",
    )
