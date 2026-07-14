import unittest
from datetime import datetime
import os
import yaml
from context_engine import ContextEngine

class TestContextEngine(unittest.TestCase):
    def setUp(self):
        # Create a temporary config file for testing
        self.config_path = "test_config.yaml"
        self.config_data = {
            "cameras": {
                "cam_test_01": {
                    "location_type": "office",
                    "zones": [
                        {"name": "reception", "zone_risk_weight": 20},
                        {"name": "server_room", "zone_risk_weight": 90}
                    ]
                }
            }
        }
        with open(self.config_path, "w") as f:
            yaml.dump(self.config_data, f)
            
        self.engine = ContextEngine(config_path=self.config_path)

    def tearDown(self):
        # Clean up temporary config file
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_morning_context(self):
        ts = datetime(2024, 1, 25, 10, 0, 0) # Normal day, 10 AM (morning)
        ctx = self.engine.get_context("cam_test_01", ts)
        self.assertEqual(ctx["time_context"], "morning")
        self.assertEqual(ctx["location_type"], "office")
        self.assertEqual(ctx["zone"], "reception")
        self.assertEqual(ctx["zone_risk_weight"], 20)

    def test_working_hours_context(self):
        ts = datetime(2024, 1, 25, 14, 0, 0) # Normal day, 2 PM (working hours)
        ctx = self.engine.get_context("cam_test_01", ts)
        self.assertEqual(ctx["time_context"], "working_hours")

    def test_night_context(self):
        ts = datetime(2024, 1, 25, 23, 0, 0) # Normal day, 11 PM (night)
        ctx = self.engine.get_context("cam_test_01", ts)
        self.assertEqual(ctx["time_context"], "night")

    def test_holiday_context(self):
        ts = datetime(2026, 1, 26, 10, 0, 0) # Republic Day, 10 AM (holiday)
        ctx = self.engine.get_context("cam_test_01", ts)
        self.assertEqual(ctx["time_context"], "holiday")

    def test_unknown_camera(self):
        ts = datetime(2024, 1, 25, 10, 0, 0)
        ctx = self.engine.get_context("unknown_cam_007", ts)
        self.assertEqual(ctx["location_type"], "unknown")
        self.assertEqual(ctx["zone"], "unclassified")
        self.assertEqual(ctx["zone_risk_weight"], 50)
        self.assertEqual(ctx["time_context"], "morning")

if __name__ == "__main__":
    unittest.main()
