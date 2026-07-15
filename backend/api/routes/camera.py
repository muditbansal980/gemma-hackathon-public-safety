from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db

from backend.controllers.camera_controller import (
    create_camera,
    get_camera,
    get_all_cameras,
    update_camera,
    delete_camera,
)

from backend.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse
)

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"]
)


@router.post(
    "/",
    response_model=CameraResponse
)
def create_camera_route(
    payload: CameraCreate,
    db: Session = Depends(get_db)
):
    return create_camera(
        db,
        payload
    )


@router.get(
    "/",
    response_model=list[CameraResponse]
)
def get_all_cameras_route(
    db: Session = Depends(get_db)
):
    return get_all_cameras(db)


@router.get(
    "/{camera_id}",
    response_model=CameraResponse
)
def get_camera_route(
    camera_id: UUID,
    db: Session = Depends(get_db)
):
    return get_camera(
        db,
        camera_id
    )


@router.patch(
    "/{camera_id}",
    response_model=CameraResponse
)
def update_camera_route(
    camera_id: UUID,
    payload: CameraUpdate,
    db: Session = Depends(get_db)
):
    return update_camera(
        db,
        camera_id,
        payload
    )


@router.delete(
    "/{camera_id}"
)
def delete_camera_route(
    camera_id: UUID,
    db: Session = Depends(get_db)
):

    delete_camera(
        db,
        camera_id
    )

    return {
        "message":
        "Camera deleted successfully"
    }