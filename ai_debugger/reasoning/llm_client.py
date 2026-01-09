class LLMResponseError(Exception):
    pass


class MockLLMClient:
    """
    Mock LLM client simulating multiple LLM behaviors.
    """

    def __init__(self, mode: str = "good"):
        self.mode = mode

    def analyze(self, prompt: str):
        if self.mode == "good":
            return {
                "root_cause": "Application container repeatedly crashing",
                "supporting_evidence_ids": ["E1", "E2"],
                "confidence": 0.85
            }

        if self.mode == "insufficient":
            return {
                "root_cause": "insufficient_evidence",
                "supporting_evidence_ids": [],
                "confidence": 0.2
            }

        if self.mode == "invalid_json":
            raise LLMResponseError("Invalid JSON returned by LLM")

        if self.mode == "hallucination":
            return {
                "root_cause": "Database outage due to network partition",
                "supporting_evidence_ids": ["E99"],
                "confidence": 0.9
            }

        raise ValueError(f"Unknown mode: {self.mode}")
