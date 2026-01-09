from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import os
import uuid

# ------------------------
# Collectors
# ------------------------
from ai_debugger.collector.events import KubernetesEventCollector

# ------------------------
# Correlator
# ------------------------
from ai_debugger.correlator.incident_window import IncidentWindowDetector
from ai_debugger.correlator.signal_ranker import SignalRanker

# ------------------------
# Reasoning
# ------------------------
from ai_debugger.reasoning.prompt_template import PromptTemplateBuilder
from ai_debugger.reasoning.llm_client import LLMClient, LLMResponseError



app = FastAPI(
    title="AI Production Debugging Assistant",
    description="AI-assisted root cause analysis for Kubernetes incidents",
    version="0.1.0",
)


# ------------------------
# Request / Response Models
# ------------------------

class AnalyzeRequest(BaseModel):
    service_name: str
    namespace: str
    window_minutes: int = 10


# ------------------------
# Dependency Setup
# ------------------------

incident_detector = IncidentWindowDetector()
signal_ranker = SignalRanker()
prompt_builder = PromptTemplateBuilder()

# ✅ Respect env var
llm_client = LLMClient(
    provider=os.getenv("LLM_PROVIDER", "mock")
)


# ------------------------
# API Endpoint
# ------------------------

@app.post("/analyze")
def analyze_incident(req: AnalyzeRequest) -> Dict:
    """
    Analyze a production incident for a given service.
    """

    incident_id = str(uuid.uuid4())

    # 1️⃣ Collect signals
    collector = KubernetesEventCollector(namespace=req.namespace)

    events_data = collector.collect_pod_events(
        window_minutes=req.window_minutes
    )
    restart_data = collector.collect_pod_restarts()

    signals = {
        "events": events_data.get("pod_events", []),
        "restarts": restart_data,
        "metrics": [],
    }

    # ✅ Safety: no signals at all
    if not signals["events"] and not signals["restarts"]:
        raise HTTPException(
            status_code=404,
            detail="No relevant signals found in the given time window",
        )

    # 2️⃣ Detect incident window
    incident_context = incident_detector.detect(signals)
    if not incident_context:
        raise HTTPException(
            status_code=404,
            detail="No incident detected in the given time window",
        )

    # 3️⃣ Rank signals
    ranked_signals = signal_ranker.rank(signals)

    # 4️⃣ Build prompt
    prompt = prompt_builder.build(
        service_name=req.service_name,
        namespace=req.namespace,
        incident_window=incident_context,
        ranked_signals=ranked_signals,
    )

    # 5️⃣ Run LLM reasoning
    try:
        rca = llm_client.run(prompt)
    except LLMResponseError as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM reasoning failed: {e}",
        )

    # 6️⃣ Return structured result
    return {
        "incident_id": incident_id,
        "service": req.service_name,
        "namespace": req.namespace,
        "incident": incident_context,
        "analysis": rca,
    }


# ------------------------
# Health Check
# ------------------------

@app.get("/health")
def health():
    return {"status": "ok"}
