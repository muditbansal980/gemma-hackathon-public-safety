"""
tools/zone_calibrator.py

Local-only helper -- needs a display, so this works when run from VS Code /
a local machine, not on headless Kaggle. Opens a frame of your video and
lets you click to build a zone polygon interactively, then prints a
ready-to-paste numpy array for config.py.

Usage:
    python tools/zone_calibrator.py --video data/security_footage.mp4 \
        --zone-name Restricted_Zone_Alpha

Controls:
    Left click   - add a polygon point
    'u'          - undo last point
    'r'          - reset all points
    's'          - save current points to zones.json and print a config.py snippet
    'q' / ESC    - quit without saving
"""

import argparse
import json
import sys

import cv2

points = []


def _mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))


def _draw(frame):
    display = frame.copy()
    for i, pt in enumerate(points):
        cv2.circle(display, pt, 4, (0, 0, 255), -1)
        if i > 0:
            cv2.line(display, points[i - 1], pt, (0, 255, 0), 2)
    if len(points) > 2:
        cv2.line(display, points[-1], points[0], (0, 255, 0), 1)
    cv2.putText(display, f"points: {len(points)}  [u]ndo [r]eset [s]ave [q]uit",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return display


def main():
    parser = argparse.ArgumentParser(description="Interactive zone polygon calibrator")
    parser.add_argument("--video", required=True, help="Path to a sample video file")
    parser.add_argument("--zone-name", default="Restricted_Zone_Alpha")
    parser.add_argument("--frame-index", type=int, default=0,
                         help="Which frame to calibrate against (default: first frame)")
    parser.add_argument("--out", default="zones.json", help="Where to save picked points")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Could not open video: {args.video}")
        sys.exit(1)

    frame, success = None, False
    for _ in range(args.frame_index + 1):
        success, frame = cap.read()
    cap.release()

    if not success or frame is None:
        print("Could not read the requested frame -- check --frame-index and the video path.")
        sys.exit(1)

    window = "Zone Calibrator"
    cv2.namedWindow(window)
    cv2.setMouseCallback(window, _mouse_callback)

    print("Click to add polygon points. Press 's' to save, 'q' to quit.")
    while True:
        cv2.imshow(window, _draw(frame))
        key = cv2.waitKey(20) & 0xFF

        if key == ord("u") and points:
            points.pop()
        elif key == ord("r"):
            points.clear()
        elif key == ord("s"):
            if len(points) < 3:
                print("Need at least 3 points to save a polygon.")
                continue
            payload = {args.zone_name: points}
            with open(args.out, "w") as f:
                json.dump(payload, f, indent=2)
            array_literal = ",\n        ".join(f"[{x}, {y}]" for x, y in points)
            print(f"\nSaved to {args.out}. Paste this into config.py:\n")
            print(f'    "{args.zone_name}": np.array([\n        {array_literal}\n    ], dtype=np.int32),\n')
        elif key in (ord("q"), 27):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
