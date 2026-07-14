# AI Service

This directory contains the AI capabilities for the Public Safety platform. It currently houses the `action` recognition module, the `context` engine module, and an end-to-end `inference_demo.py` script.

## Modules

- `vision/action_recognition/`: Contains `action_recognition.py` which extracts MediaPipe Pose keypoints from cropped bounding boxes and runs MVP heuristics to detect actions like `walking`, `running`, `falling`, `reaching`, and `climbing`. Note: this was moved from `ai-service/action/`.
- `context/`: Contains `context_engine.py` which loads metadata from `context_config.yaml` to deduce `time_context` (morning, night, working_hours, holiday) and risk weights based on `camera_id` and timestamps.

## Inference Demo

`inference_demo.py` simulates the complete pipeline: it wires the tracking module (currently mocked with a stationary dummy tracker for demo purposes), the Action Recognition module (from `vision/action_recognition`), and the Context Engine into a single combined event per frame, per tracked person. 

This JSON event is the final object that feeds into the Risk Engine.

### Running the Demo

1. Ensure you have the necessary dependencies installed in your Python environment by referencing the requirements file:
   ```bash
   pip install -r ../vision/action_recognition/requirements.txt
   ```
2. Run the demo script from the `ai-service` directory, providing a path to a sample video:
   ```bash
   python inference_demo.py --video path/to/sample.mp4 --camera_id cam_001
   ```
   *(If no video is provided, it defaults to looking for `sample.mp4` in the current directory).*

### Output Schema

The demo logs a combined JSON event per tracked person, per frame. The schema looks like this:

```json
{
  "track_id": "person_001",
  "action": "walking",
  "action_confidence": 0.75,
  "context": {
    "location_type": "office",
    "time_context": "working_hours",
    "zone": "entrance",
    "zone_risk_weight": 20
  },
  "timestamp": "2026-07-14T15:30:00.123456"
}
```

- `track_id`: Unique string identifier from the tracking module.
- `action`: The classified action (`standing`, `walking`, `running`, `falling`, `reaching`, `climbing`).
- `action_confidence`: Confidence score (0.0 to 1.0) derived from the heuristics.
- `context`: The environmental context data containing the camera location type, semantic time category, zone name, and the predefined zone risk weight.
- `timestamp`: ISO-8601 formatted timestamp of the event execution.
