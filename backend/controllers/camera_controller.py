from backend.services.camera_service.camera_service import (
    CameraService
)

camera_service = CameraService()


def create_camera(
    db,
    payload
):
    return camera_service.create_camera(
        db,
        payload
    )


def get_camera(
    db,
    camera_id
):
    return camera_service.get_camera(
        db,
        camera_id
    )


def get_all_cameras(db):
    return camera_service.get_all_cameras(
        db
    )


def update_camera(
    db,
    camera_id,
    payload
):
    return camera_service.update_camera(
        db,
        camera_id,
        payload
    )


def delete_camera(
    db,
    camera_id
):
    return camera_service.delete_camera(
        db,
        camera_id
    )