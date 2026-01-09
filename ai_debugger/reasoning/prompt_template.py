from typing import Dict, List


class PromptTemplateBuilder:
    """
    Builds a strict, evidence-based prompt for LLM reasoning.
    """

    SYSTEM_INSTRUCTIONS = """
You are a senior Site Reliability Engineer assisting with a production incident.

Rules:
- Use ONLY the evidence provided.
- Do NOT speculate or invent causes.
- If evidence is insufficient, say so explicitly.
- Clearly separate symptoms from root cause.
- Provide actionable remediation steps.
- Assign a confidence score (0.0–1.0) for your conclusion.
"""

    def build(
        self,
        service_name: str,
        namespace: str,
        incident_window: Dict,
        ranked_signals: List[Dict]
    ) -> str:
        evidence_block = self._format_evidence(ranked_signals)
        window_block = self._format_incident_window(incident_window)

        prompt = f"""
{self.SYSTEM_INSTRUCTIONS}

Incident Context:
- Service: {service_name}
- Namespace: {namespace}

Incident Window:
{window_block}

Observed Evidence (ranked by importance):
{evidence_block}

Tasks:
1. Summarize the incident in 2–3 sentences.
2. Identify the most likely root cause.
3. Explain the causal chain step-by-step.
4. List supporting evidence (bullet points).
5. Recommend concrete remediation actions.
6. Provide a confidence score for your conclusion.

Output Format (STRICT JSON):
{{
  "summary": "...",
  "root_cause": "...",
  "causal_chain": ["...", "..."],
  "supporting_evidence": ["...", "..."],
  "recommended_actions": ["...", "..."],
  "confidence": 0.0
}}
"""
        return prompt.strip()

    def _format_incident_window(self, window: Dict) -> str:
        return (
            f"- Start: {window.get('incident_start')}\n"
            f"- End: {window.get('incident_end')}\n"
            f"- Duration: {window.get('duration_minutes')} minutes"
        )

    def _format_evidence(self, ranked_signals: List[Dict]) -> str:
        lines = []
        for idx, item in enumerate(ranked_signals, start=1):
            signal = item["signal"]
            lines.append(
                f"{idx}. [{item['category'].upper()}] "
                f"{item['reason']} | Details: {signal}"
            )
        return "\n".join(lines)
