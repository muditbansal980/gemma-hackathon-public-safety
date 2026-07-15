
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db

router = APIRouter(
    prefix="/detection",
    tags=["Detection"]
)

@router.post("/detect")
def detect(
    request:DetectionRequest
):
    return start_detection(
        request.video_path
    )