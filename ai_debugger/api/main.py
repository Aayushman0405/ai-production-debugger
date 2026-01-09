from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

from ai_debugger.correlator.incident_window import detect_incident_window
from ai_debugger.correlator.signal_ranker import rank_signals
from ai_debugger.reasoning.prompt_template import build_prompt
from ai_debugger.reasoning.llm_client import MockLLMClient, LLMResponseError
from ai_debugger.reasoning.response_validator import (
    validate_rca_response,
    InvalidRCAResponse
)

app = FastAPI(title="AI Production Debugging Assistant")


class AnalyzeRequest(BaseModel):
    signals: List[Dict]
    llm_mode: str = "good"  # for testing


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        # 1. Incident window (validated but not used yet)
        detect_incident_window(req.signals)

        # 2. Rank signals
        ranked = rank_signals(req.signals)

        # 3. Build prompt
        prompt = build_prompt(ranked)

        # 4. Call LLM (mocked)
        llm = MockLLMClient(mode=req.llm_mode)
        response = llm.analyze(prompt)

        # 5. Validate response
        validated = validate_rca_response(response, ranked)

        return {
            "status": "success",
            "rca": validated
        }

    except (LLMResponseError, InvalidRCAResponse, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
