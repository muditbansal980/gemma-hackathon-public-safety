import cv2 

cap = cv2.VideoCapture(0)

width = int(cap.get(3))
height = int(cap.get(4))

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

out = cv2.VideoWriter(
    "security_footage.mp4",
    fourcc,
    20.0,
    (width, height)
)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    out.write(frame)

    cv2.imshow("Recording", frame)

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
out.release()
cv2.destroyAllWindows()