import os
import yaml
import logging
from datetime import datetime, date
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Hardcoded Indian holiday list
INDIAN_HOLIDAYS = {
    date(2026, 1, 26),  # Republic Day
    date(2026, 8, 15),  # Independence Day
    date(2026, 10, 2),  # Gandhi Jayanti
    date(2026, 12, 25), # Christmas
    date(2026, 11, 8),  # Diwali (example date)
    date(2024, 1, 26),
    date(2024, 8, 15),
    date(2024, 10, 2),
    date(2024, 12, 25),
}

class ContextEngine:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to the same directory as this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "context_config.yaml")
            
        self.config_path = config_path
        self.cameras = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Loads camera configuration from the YAML config file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config is None:
                    return {}
                return config.get('cameras', {})
        except FileNotFoundError:
            logger.warning(f"Config file not found at {self.config_path}. Using empty config.")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML from {self.config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading config file {self.config_path}: {e}")
            return {}

    def get_time_context(self, timestamp) -> str:
        """Derives time context from timestamp (night, morning, working_hours, evening, holiday)."""
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                logger.error(f"Invalid timestamp format: {timestamp}")
                return "unknown"
                
        if timestamp.date() in INDIAN_HOLIDAYS:
            return "holiday"
        
        hour = timestamp.hour
        # morning (6am-12pm)
        if 6 <= hour < 12:
            return "morning"
        # working_hours (12pm-8pm)
        elif 12 <= hour < 20:
            return "working_hours"
        # evening/night gap handling
        elif 20 <= hour < 22:
            return "evening"
        # night (10pm-6am)
        else:
            return "night"

    def get_context(self, camera_id: str, timestamp) -> Dict[str, Any]:
        """
        Returns location, time, and zone context for a given camera ID and timestamp.
        """
        time_context = self.get_time_context(timestamp)
        
        if camera_id not in self.cameras:
            logger.warning(f"Camera ID '{camera_id}' not found in config. Returning safe defaults.")
            return {
                "location_type": "unknown",
                "time_context": time_context,
                "zone": "unclassified",
                "zone_risk_weight": 50
            }
        
        camera_info = self.cameras[camera_id]
        location_type = camera_info.get("location_type", "unknown")
        
        zones = camera_info.get("zones", [])
        if zones and isinstance(zones, list):
            # Default to the first configured zone if multiple exist
            primary_zone = zones[0]
            zone_name = primary_zone.get("name", "unclassified")
            zone_weight = primary_zone.get("zone_risk_weight", 50)
        else:
            zone_name = "unclassified"
            zone_weight = 50
            
        return {
            "location_type": location_type,
            "time_context": time_context,
            "zone": zone_name,
            "zone_risk_weight": zone_weight
        }
