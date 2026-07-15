from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.repositories.event_repository import EventRepository
from backend.schemas.event import EventResponse

router = APIRouter(prefix="/events", tags=["Events"])
event_repo = EventRepository()


@router.get("/", response_model=list[EventResponse])
def list_events(db: Session = Depends(get_db), limit: int = 50):
    return event_repo.get_all(db, limit=limit)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: UUID, db: Session = Depends(get_db)):
    event = event_repo.get_by_id(db, event_id)
    if not event:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Event not found")
    return event
