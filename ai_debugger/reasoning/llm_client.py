import json
import os
import time
from typing import Dict, Optional


class LLMResponseError(Exception):
    pass


class LLMClient:
    """
    Abstract LLM client.
    Supports API-based LLMs now and local models later.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        timeout_seconds: int = 30,
        max_retries: int = 2,
    ):
        self.provider = provider
        self.model = model
        self.timeout = timeout_seconds
        self.max_retries = max_retries

    def run(self, prompt: str) -> Dict:
        """
        Main entry point.
        Always returns parsed JSON.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                raw = self._call_llm(prompt)
                parsed = self._parse_json(raw)
                self._validate(parsed)
                return parsed
            except Exception as e:
                if attempt >= self.max_retries:
                    raise LLMResponseError(
                        f"LLM failed after {attempt} attempts: {e}"
                    )
                time.sleep(1)

        raise LLMResponseError("Unreachable")

    # ------------------------
    # Internal methods
    # ------------------------

    def _call_llm(self, prompt: str) -> str:
        if self.provider == "openai":
            return self._call_openai(prompt)

        if self.provider == "mock":
            return self._mock_response()

        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _call_openai(self, prompt: str) -> str:
        """
        Deferred import so VS Code side has no dependency issues.
        """
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not set")

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You must respond in STRICT JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            timeout=self.timeout,
        )

        return response.choices[0].message.content

    def _parse_json(self, raw: str) -> Dict:
        """
        Ensures the response is valid JSON.
        """
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise LLMResponseError("Model response is not valid JSON")

    def _validate(self, payload: Dict):
        """
        Minimal schema validation.
        """
        required_fields = {
            "summary",
            "root_cause",
            "causal_chain",
            "supporting_evidence",
            "recommended_actions",
            "confidence",
        }

        missing = required_fields - payload.keys()
        if missing:
            raise LLMResponseError(f"Missing required fields: {missing}")

        confidence = payload.get("confidence")
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            raise LLMResponseError("Invalid confidence score")

    def _mock_response(self) -> str:
        """
        Used for local testing without any API calls.
        """
        return json.dumps({
            "summary": "The service experienced increased latency due to pod restarts.",
            "root_cause": "Memory limit too low caused OOMKilled events.",
            "causal_chain": [
                "Memory usage exceeded limit",
                "Pod was OOMKilled",
                "Pod restart caused cold start latency"
            ],
            "supporting_evidence": [
                "OOMKilled Kubernetes event",
                "Increased restart count",
                "Error rate spike"
            ],
            "recommended_actions": [
                "Increase memory limits",
                "Add HPA based on memory",
                "Tune readiness probes"
            ],
            "confidence": 0.82
        })
