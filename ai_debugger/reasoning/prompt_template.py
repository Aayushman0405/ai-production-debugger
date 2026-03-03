import json
from typing import List, Dict

def build_prompt(ranked_signals: List[Dict]) -> str:
    evidence_block = json.dumps(ranked_signals, indent=2)
    
    return f"""You are an AI assistant performing production incident root cause analysis.

RULES:
- Use ONLY the evidence provided below
- Do NOT assume missing information
- Do NOT speculate
- If evidence is insufficient, set root_cause to "insufficient_evidence"
- You MUST reference evidence using evidence IDs only

EVIDENCE:
{evidence_block}

TASK:
Determine the most likely root cause based ONLY on the evidence.

RESPONSE FORMAT (JSON ONLY):
{{
  "root_cause": "short factual statement or 'insufficient_evidence'",
  "supporting_evidence_ids": ["E1", "E2"],
  "confidence": 0.85
}}

DO NOT include explanations or markdown.
"""
