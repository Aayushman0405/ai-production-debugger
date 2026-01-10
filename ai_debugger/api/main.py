from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
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
from ai_debugger.reasoning.llm_client import (
    get_llm_client,
    LLMResponseError
)
from ai_debugger.reasoning.response_validator import (
    validate_rca_response,
    InvalidRCAResponse
)

app = FastAPI(title="AI Production Debugging Assistant")


# -------------------------
# Request model
# -------------------------
class AnalyzeRequest(BaseModel):
    signals: List[Dict[str, Any]]
    llm_mode: str = "disabled"  # disabled | good | bad (mock only)


# -------------------------
# Health endpoint
# -------------------------
@app.get("/health")
def health():
    HEALTH_REQUESTS_TOTAL.inc()
    return {"status": "ok"}


# -------------------------
# Metrics endpoint
# -------------------------
@app.get("/metrics")
def metrics():
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# -------------------------
# Analyze endpoint
# -------------------------
@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    start_time = time.time()

    try:
        # -------------------------------------------------
        # 1. Normalize & validate signals
        # -------------------------------------------------
        signals = []
        for s in req.signals:
            if "name" not in s or "value" not in s:
                raise ValueError("Each signal must have name and value")

            signals.append({
                "name": s["name"],
                "value": s["value"],
                "timestamp": s.get("timestamp") or datetime.utcnow().isoformat()
            })

        # -------------------------------------------------
        # 2. Detect incident window
        # -------------------------------------------------
        incident_result = detect_incident_window(signals)

        # -------------------------------------------------
        # 3. Rank signals
        # -------------------------------------------------
        ranked = rank_signals(signals)

        # -------------------------------------------------
        # 4. Optional LLM reasoning
        # -------------------------------------------------
        if req.llm_mode != "disabled":
            prompt = build_prompt(ranked)

            llm = get_llm_client(mode=req.llm_mode)
            llm_response = llm.analyze(prompt)

            validated = validate_rca_response(llm_response, ranked)

            result = {
                "status": "success",
                "mode": "llm",
                "incident": incident_result,
                "rca": validated
            }
        else:
            result = {
                "status": "success",
                "mode": "rule-based",
                "incident": incident_result,
                "top_signals": ranked[:3]
            }

        ANALYZE_REQUESTS_TOTAL.labels(status="success").inc()
        return result

    except (LLMResponseError, InvalidRCAResponse, ValueError) as e:
        ANALYZE_REQUESTS_TOTAL.labels(status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        ANALYZE_LATENCY.observe(time.time() - start_time)
