from backend.services.detection_service import DetectionService

detection_service=DetectionService()

def start_detection(video_path):
    return detection_service.start_detection(
        video_path
    )