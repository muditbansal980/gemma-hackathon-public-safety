import cv2
import tempfile
import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


class CameraStreamService:

    def stream(self, rtsp_url):

        cap = cv2.VideoCapture(rtsp_url)

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(3))
        height = int(cap.get(4))

        while True:

            filename = tempfile.NamedTemporaryFile(
                suffix=".mp4",
                delete=False
            ).name

            writer = cv2.VideoWriter(
                filename,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (width, height),
            )

            frame_count = fps * 5

            for _ in range(frame_count):

                success, frame = cap.read()

                if not success:
                    break

                writer.write(frame)

            writer.release()

            r.lpush(
                "video_queue",
                filename
            )