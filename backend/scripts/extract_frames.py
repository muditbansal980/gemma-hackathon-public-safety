import cv2
import os

os.makedirs("frames", exist_ok=True)

cap = cv2.VideoCapture(
    "security_footage.mp4"
)

count = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    cv2.imwrite(
        f"frames/frame_{count}.jpg",
        frame
    )

    count += 1

cap.release()

print(count)