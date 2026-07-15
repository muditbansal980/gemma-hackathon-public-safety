from fastapi import HTTPException

from backend.repositories.camera_repository import (
    CameraRepository
)


class CameraService:

    def __init__(self):
        self.repo = CameraRepository()

    def create_camera(self, db, payload):

        existing = self.repo.get_by_name(
            db,
            payload.name
        )

        if existing:
            raise HTTPException(
                400,
                "Camera already exists"
            )

        return self.repo.create(
            db,
            payload.model_dump()
        )

    def get_camera(self, db, camera_id):

        camera = self.repo.get_by_id(
            db,
            camera_id
        )

        if not camera:
            raise HTTPException(
                404,
                "Camera not found"
            )

        return camera

    def get_all_cameras(self, db):
        return self.repo.get_all(db)

    def update_camera(
        self,
        db,
        camera_id,
        payload
    ):

        camera = self.get_camera(
            db,
            camera_id
        )

        return self.repo.update(
            db,
            camera,
            payload.model_dump(
                exclude_unset=True
            )
        )

    def delete_camera(
        self,
        db,
        camera_id
    ):

        camera = self.get_camera(
            db,
            camera_id
        )

        self.repo.delete(db, camera)