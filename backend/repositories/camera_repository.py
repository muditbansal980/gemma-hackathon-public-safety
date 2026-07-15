from sqlalchemy.orm import Session
from backend.models.camera import Camera


class CameraRepository:

    def create(self, db: Session, data: dict):
        camera = Camera(**data)
        db.add(camera)
        db.commit()
        db.refresh(camera)
        return camera

    def get_by_id(self, db: Session, camera_id):
        return db.query(Camera).filter(Camera.id == camera_id).first()

    def get_all(self, db: Session):
        return db.query(Camera).all()

    def get_by_name(self, db: Session, name: str):
        return db.query(Camera).filter(Camera.name == name).first()

    def delete(self, db: Session, camera):
        db.delete(camera)
        db.commit()

    def update(self, db: Session, camera, data):
        for key, value in data.items():
            setattr(camera, key, value)

        db.commit()
        db.refresh(camera)

        return camera