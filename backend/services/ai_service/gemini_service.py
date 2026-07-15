"""
Gemini API reasoning engine — replaces local Gemma for hackathon-friendly cloud inference.
"""

import json
import logging
import re
from typing import Optional

import google.generativeai as genai

from backend.core.config import settings
from backend.services.ai_service.reasoning.prompts import (
    JSON_SCHEMA_INSTRUCTION,
    SYSTEM_INSTRUCTION,
)

logger = logging.getLogger(__name__)


class GeminiReasoningEngine:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def analyze_timeline(self, json_timeline: str, severity_report: dict) -> str:
        user_content = (
            f"{SYSTEM_INSTRUCTION}\n{JSON_SCHEMA_INSTRUCTION}\n\n"
            f"Event Timeline:\n{json_timeline}\n\n"
            f"Rule-Based Severity Score (authoritative -- do not override):\n"
            f"{json.dumps(severity_report, indent=2)}"
        )
        response = self.model.generate_content(
            user_content,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1024,
            ),
        )
        return response.text or ""

    @staticmethod
    def extract_json_block(report_text: str):
        """Pulls the trailing ```json block for automated alerting."""
        match = re.search(r"```json\s*(\{.*?\})\s*```", report_text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    @staticmethod
    def fallback_report(severity_report: dict) -> str:
        return (
            "Automated LLM narrative unavailable. "
            f"Rule-based severity: {json.dumps(severity_report, indent=2)}"
        )
