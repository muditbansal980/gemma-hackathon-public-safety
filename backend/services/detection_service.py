from ai.perspection.detector import process_video_feed

class DetectionService:

    def start_detection(
        self,
        video_path:str
    ):
        return process_video_feed(video_path)