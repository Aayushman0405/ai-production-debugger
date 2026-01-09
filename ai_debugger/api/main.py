from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Dict
import time

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from ai_debugger.metrics import (
    ANALYZE_REQUESTS_TOTAL,
    ANALYZE_LATENCY,
    HEALTH_REQUESTS_TOTAL
)

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


# -------------------------
# Health endpoint (instrumented)
# -------------------------
@app.get("/health")
def health():
    HEALTH_REQUESTS_TOTAL.inc()
    return {"status": "ok"}


# -------------------------
# Metrics endpoint (Prometheus)
# -------------------------
@app.get("/metrics")
def metrics():
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# -------------------------
# Analyze endpoint (instrumented)
# -------------------------
@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    start_time = time.time()

    try:
        # 1. Detect incident window
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

        ANALYZE_REQUESTS_TOTAL.labels(status="success").inc()

        return {
            "status": "success",
            "rca": validated
        }

    except (LLMResponseError, InvalidRCAResponse, ValueError) as e:
        ANALYZE_REQUESTS_TOTAL.labels(status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        ANALYZE_LATENCY.observe(time.time() - start_time)
