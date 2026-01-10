# ai_debugger/reasoning/llm_client.py

import os
import json
import time
from typing import Dict, Any

from openai import OpenAI


# -------------------------
# Exceptions
# -------------------------
class LLMResponseError(Exception):
    pass


# -------------------------
# Base interface
# -------------------------
class BaseLLMClient:
    def analyze(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError


# -------------------------
# Mock LLM (unchanged, for tests)
# -------------------------
class MockLLMClient(BaseLLMClient):
    def __init__(self, mode: str = "good"):
        self.mode = mode

    def analyze(self, prompt: str) -> Dict[str, Any]:
        if self.mode == "bad":
            return {"foo": "hallucination"}

        # deterministic, valid response
        return {
            "root_cause": "High latency caused cascading failures.",
            "confidence": 0.82,
            "recommended_actions": [
                "Increase replicas",
                "Check downstream dependency latency"
            ],
            "signals_used": ["latency", "error_rate"]
        }


# -------------------------
# OpenAI LLM Client (REAL)
# -------------------------
class OpenAILLMClient(BaseLLMClient):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=api_key)

        # Guardrails
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "10"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "300"))

    def analyze(self, prompt: str) -> Dict[str, Any]:
        start = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a production incident analysis engine. "
                            "You must ONLY use provided signals. "
                            "Respond strictly in JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # low randomness for RCA
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )

            content = response.choices[0].message.content

            # Hard JSON parse (no free text allowed)
            parsed = json.loads(content)

            # Cost / latency guard
            if time.time() - start > self.timeout:
                raise LLMResponseError("LLM response timeout")

            return parsed

        except json.JSONDecodeError:
            raise LLMResponseError("LLM returned invalid JSON")

        except Exception as e:
            raise LLMResponseError(str(e))


# -------------------------
# Factory (NO LOCK-IN)
# -------------------------
def get_llm_client(mode: str):
    provider = os.getenv("LLM_PROVIDER", "mock")

    if provider == "openai":
        return OpenAILLMClient()

    # fallback (safe)
    return MockLLMClient(mode=mode)
