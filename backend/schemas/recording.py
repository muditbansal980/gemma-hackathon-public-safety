from pydantic import BaseModel, Field


class RecordingStartRequest(BaseModel):
    source: str = Field(
        default="webcam",
        description='Use "webcam" for laptop camera or an RTSP URL / device index',
    )


class RecordingStatusResponse(BaseModel):
    camera_id: str
    is_recording: bool
    message: str


class ActiveRecordingsResponse(BaseModel):
    camera_ids: list[str]
