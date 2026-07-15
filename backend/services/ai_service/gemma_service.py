"""
reasoning/gemma_engine.py

Loads a 4-bit quantized Gemma 2 model and turns a (timeline, severity_score)
pair into a grounded natural-language forensic report. The severity score
is passed in as authoritative context -- Gemma explains it, it does not
compute it independently.
"""

import json
import re

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import Optional
import ai.config as config
from backend.services.ai_service.reasoning.prompts import (
    JSON_SCHEMA_INSTRUCTION,
    SYSTEM_INSTRUCTION,
)


class GemmaReasoningEngine:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.GEMMA_MODEL_NAME
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=quantization_config,
            device_map="auto",
        )

    def analyze_timeline(self, json_timeline: str, severity_report: dict) -> str:
        user_content = (
            f"{SYSTEM_INSTRUCTION}\n{JSON_SCHEMA_INSTRUCTION}\n\n"
            f"Event Timeline:\n{json_timeline}\n\n"
            f"Rule-Based Severity Score (authoritative -- do not override):\n"
            f"{json.dumps(severity_report, indent=2)}"
        )
        messages = [{"role": "user", "content": user_content}]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(  # type: ignore[reportAttributeAccessIssue]
                **inputs,
                max_new_tokens=1024,
                temperature=0.1,
                do_sample=False,
            )
        return self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True
        )

    @staticmethod
    def extract_json_block(report_text: str):
        """Pulls the trailing ```json block back out for automated alerting.
        Returns None if the model didn't produce valid JSON -- callers should
        fall back to the original symbolic severity_report in that case."""
        match = re.search(r"```json\s*(\{.*?\})\s*```", report_text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
