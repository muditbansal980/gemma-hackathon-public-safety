import cv2
import sys
import argparse
from collections import deque
from action_recognition import detect_action

def main():
    parser = argparse.ArgumentParser(description="Test Action Recognition Module")
    parser.add_argument("--video", type=str, default="sample.mp4", help="Path to sample video file")
    parser.add_argument("--zone", type=str, default=None, help="Interaction zone as x1,y1,x2,y2")
    args = parser.parse_args()

    video_path = args.video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file '{video_path}'.")
        print("Please provide a valid video file using --video <path>")
        sys.exit(1)
        
    print(f"Processing video: {video_path}")
    
    # Parse interaction zone if provided
    interaction_zone = None
    if args.zone:
        try:
            interaction_zone = [int(v) for v in args.zone.split(",")]
            print(f"Using interaction zone: {interaction_zone}")
        except ValueError:
            print("Invalid zone format. Use x1,y1,x2,y2")
            
    history = {}
    track_id = "test_person_1"
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        h, w = frame.shape[:2]
        
        # Simulate a tracking bounding box (using the whole frame for testing)
        # In a real integration, this would come from ai-service/tracking/
        bbox = [0, 0, w, h]
        
        # Detect action
        result = detect_action(
            track_id=track_id,
            frame=frame,
            bbox=bbox,
            history=history,
            interaction_zone=interaction_zone
        )
        
        action = result.get("action", "unknown")
        confidence = result.get("confidence", 0.0)
        
        # Print detected action per frame as requested for live tuning
        print(f"Frame {frame_count:04d} | Action: {action.upper():<10} | Confidence: {confidence:.2f}")

    cap.release()
    print("Finished processing video.")

if __name__ == "__main__":
    main()
