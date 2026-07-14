import cv2
import mediapipe as mp
import time
import atexit
from collections import deque
from typing import Dict, Any, List, Optional

mp_pose = mp.solutions.pose
# For MVP, initialize a global pose estimator. static_image_mode=True is safer 
# here because we might feed it cropped bounding boxes which vary in size and context.
pose_estimator = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)
atexit.register(pose_estimator.close)

def detect_action(
    track_id: str, 
    frame: Any, 
    bbox: List[int], 
    history: Dict[str, deque], 
    interaction_zone: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Detects actions based on simple heuristics using MediaPipe Pose keypoints.
    
    Args:
        track_id: Unique identifier for the tracked person.
        frame: The full image/frame (BGR format from cv2).
        bbox: The bounding box of the person [x1, y1, x2, y2].
        history: A dictionary mapping track_id to a deque of past keypoints (for temporal heuristics).
        interaction_zone: Optional bounding box [x1, y1, x2, y2] representing an area of interest (e.g. door handle).
        
    Returns:
        Dict containing {track_id, action, confidence, timestamp}
    """
    # Initialize history for new tracks
    if track_id not in history:
        # Keep last ~15 frames as requested
        history[track_id] = deque(maxlen=15)
        
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = frame.shape[:2]
    
    # Clip bbox to frame dimensions
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    
    # Fallback default
    result = {
        "track_id": track_id, 
        "action": "standing", 
        "confidence": 0.0, 
        "timestamp": time.time()
    }
    
    if x2 <= x1 or y2 <= y1:
        return result

    # Crop the person from the frame to focus mediapipe
    crop = frame[y1:y2, x1:x2]
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    
    pose_results = pose_estimator.process(crop_rgb)
    
    if not pose_results.pose_landmarks:
        # Cannot detect pose, return default
        return result
        
    landmarks = pose_results.pose_landmarks.landmark
    
    # Helper to convert normalized coordinates (0-1) within crop to absolute frame coordinates
    def get_pt(lm_id):
        lm = landmarks[lm_id]
        return (x1 + lm.x * (x2 - x1), y1 + lm.y * (y2 - y1))
        
    left_hip = get_pt(mp_pose.PoseLandmark.LEFT_HIP.value)
    right_hip = get_pt(mp_pose.PoseLandmark.RIGHT_HIP.value)
    hip = ((left_hip[0] + right_hip[0])/2, (left_hip[1] + right_hip[1])/2)
    
    left_shoulder = get_pt(mp_pose.PoseLandmark.LEFT_SHOULDER.value)
    right_shoulder = get_pt(mp_pose.PoseLandmark.RIGHT_SHOULDER.value)
    shoulder = ((left_shoulder[0] + right_shoulder[0])/2, (left_shoulder[1] + right_shoulder[1])/2)
    
    left_ankle = get_pt(mp_pose.PoseLandmark.LEFT_ANKLE.value)
    right_ankle = get_pt(mp_pose.PoseLandmark.RIGHT_ANKLE.value)
    ankle = ((left_ankle[0] + right_ankle[0])/2, (left_ankle[1] + right_ankle[1])/2)
    
    left_wrist = get_pt(mp_pose.PoseLandmark.LEFT_WRIST.value)
    right_wrist = get_pt(mp_pose.PoseLandmark.RIGHT_WRIST.value)
    
    current_kps = {
        "hip": hip,
        "shoulder": shoulder,
        "ankle": ankle,
        "left_wrist": left_wrist,
        "right_wrist": right_wrist,
        "time": time.time()
    }
    
    history[track_id].append(current_kps)
    
    action = "standing"
    confidence = 0.5
    
    # 1. Reaching/Touching
    # High priority since it relies on explicit spatial interaction
    if interaction_zone:
        ix1, iy1, ix2, iy2 = interaction_zone
        for wrist in [left_wrist, right_wrist]:
            # Expand interaction zone slightly for tolerance
            tolerance = 20
            if (ix1 - tolerance) <= wrist[0] <= (ix2 + tolerance) and \
               (iy1 - tolerance) <= wrist[1] <= (iy2 + tolerance):
                result.update({"action": "reaching", "confidence": 0.9, "timestamp": time.time()})
                return result
                
    # Evaluate temporal heuristics only when history reaches maxlen (15 frames)
    # This ensures a consistent time window for reliable velocity calculations.
    if len(history[track_id]) == history[track_id].maxlen:
        # Compare current frame with an older frame in history (e.g., the oldest one available)
        past_kps = history[track_id][0]
        
        dx_hip = hip[0] - past_kps["hip"][0]
        dy_hip = hip[1] - past_kps["hip"][1]
        
        dy_ankle = ankle[1] - past_kps["ankle"][1]
        
        box_height = y2 - y1
        box_width = x2 - x1
        
        # 2. Falling: sudden vertical drop + near-horizontal shoulder-hip line
        # dy_hip > 0 means moving downwards in pixel coordinates
        if dy_hip > 0.25 * box_height:  
            sh_dy = abs(shoulder[1] - hip[1])
            sh_dx = abs(shoulder[0] - hip[0]) + 1e-5
            if sh_dy / sh_dx < 1.5:  # slope indicates they are relatively horizontal
                result.update({"action": "falling", "confidence": 0.85, "timestamp": time.time()})
                return result
                
        # 3. Climbing: sustained vertical movement of ankle/hip (usually upwards)
        # Climbing usually involves vertical motion and little horizontal motion
        # TODO: This threshold is unvalidated against real footage and may misfire on a 
        # person walking directly toward/away from the camera due to perspective. Needs manual tuning.
        if abs(dy_hip) > 0.1 * box_height and abs(dx_hip) < 0.1 * box_width:
            result.update({"action": "climbing", "confidence": 0.75, "timestamp": time.time()})
            return result
            
        # 4. Walking/Running: hip horizontal velocity
        if abs(dx_hip) > 0.05 * box_width:
            if abs(dx_hip) > 0.15 * box_width:
                action = "running"
                confidence = 0.85
            else:
                action = "walking"
                confidence = 0.75
            result.update({"action": action, "confidence": confidence, "timestamp": time.time()})
            return result
            
    result.update({"action": action, "confidence": confidence, "timestamp": time.time()})
    return result
