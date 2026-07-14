import cv2
import time
import json
import argparse
from datetime import datetime
from collections import deque

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vision.action_recognition.action_recognition import detect_action
from context.context_engine import ContextEngine

class MockTracker:
    """
    Mock tracker for the inference demo.
    In the real pipeline, this would be replaced by the actual vision/person_tracking module.
    """
    def __init__(self):
        self.track_id = "person_001"
        
    def update(self, frame):
        """
        Returns a mock list of tracked objects in the format: [(track_id, bbox)]
        where bbox is [x1, y1, x2, y2]. We just return a centralized dummy box.
        """
        h, w = frame.shape[:2]
        # Create a dummy bounding box in the center of the frame
        cx, cy = w // 2, h // 2
        box_w, box_h = min(w, 400), min(h, 800)
        x1 = max(0, cx - box_w // 2)
        y1 = max(0, cy - box_h // 2)
        x2 = min(w, cx + box_w // 2)
        y2 = min(h, cy + box_h // 2)
        
        return [(self.track_id, [x1, y1, x2, y2])]

def main():
    parser = argparse.ArgumentParser(description="AI Service Inference Demo")
    parser.add_argument("--video", type=str, default="sample.mp4", help="Path to sample video")
    parser.add_argument("--camera_id", type=str, default="cam_001", help="Camera ID for Context Engine")
    args = parser.parse_args()

    # Initialize components
    print("Initializing Context Engine...")
    context_engine = ContextEngine()
    
    print("Initializing Mock Tracker...")
    tracker = MockTracker()
    
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Error: Cannot open video '{args.video}'. Please provide a valid video file using --video")
        return

    history = {}
    frame_count = 0
    
    print("\n--- Starting Inference Demo ---\n")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        current_time = datetime.now()
        
        # 1. Run Tracking (Mocked for this script)
        tracked_objects = tracker.update(frame)
        
        for track_id, bbox in tracked_objects:
            # 2. Run Action Recognition
            # Assuming an interaction zone at the right side of the screen for demo purposes
            h, w = frame.shape[:2]
            demo_interaction_zone = [w - 100, 0, w, h] 
            
            action_result = detect_action(
                track_id=track_id,
                frame=frame,
                bbox=bbox,
                history=history,
                interaction_zone=demo_interaction_zone
            )
            
            # 3. Run Context Engine
            context_result = context_engine.get_context(
                camera_id=args.camera_id, 
                timestamp=current_time
            )
            
            # 4. Combine into final event object for the Risk Engine
            combined_event = {
                "track_id": track_id,
                "action": action_result.get("action", "unknown"),
                "action_confidence": round(action_result.get("confidence", 0.0), 2),
                "context": {
                    "location_type": context_result.get("location_type"),
                    "time_context": context_result.get("time_context"),
                    "zone": context_result.get("zone"),
                    "zone_risk_weight": context_result.get("zone_risk_weight")
                },
                "timestamp": current_time.isoformat()
            }
            
            # Print/Log the combined event
            print(json.dumps(combined_event, indent=2))
            
    cap.release()
    print("\n--- Inference Demo Complete ---")

if __name__ == "__main__":
    main()
