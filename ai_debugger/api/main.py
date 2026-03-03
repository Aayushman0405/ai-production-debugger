from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge

# Load environment variables
load_dotenv()

# Import local modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_debugger.correlator.incident_window import detect_incident_window
from ai_debugger.correlator.signal_ranker import rank_signals
from ai_debugger.reasoning.prompt_template import build_prompt
from ai_debugger.reasoning.llm_client import get_llm_client, LLMResponseError
from ai_debugger.reasoning.response_validator import validate_rca_response, InvalidRCAResponse
from ai_debugger.collector.events import KubernetesEventCollector

# -------------------------
# Prometheus Metrics
# -------------------------
ANALYZE_REQUESTS_TOTAL = Counter(
    "ai_debugger_analyze_requests_total",
    "Total number of analyze requests",
    ["status"]
)

HEALTH_REQUESTS_TOTAL = Counter(
    "ai_debugger_health_requests_total",
    "Total number of health check requests"
)

ANALYZE_LATENCY = Histogram(
    "ai_debugger_analyze_latency_seconds",
    "Latency of analyze endpoint",
    buckets=(0.1, 0.3, 0.5, 1, 2, 3, 5)
)

SIGNALS_PROCESSED = Counter(
    "ai_debugger_signals_processed_total",
    "Total number of signals processed"
)

app = FastAPI(
    title="AI Production Debugging Assistant",
    description="Automated Root Cause Analysis for Kubernetes",
    version="1.0.0"
)

# -------------------------
# Request Models
# -------------------------
class AnalyzeRequest(BaseModel):
    signals: List[Dict[str, Any]]
    llm_mode: str = "disabled"
    namespace: Optional[str] = None

class AutoAnalyzeRequest(BaseModel):
    namespace: str
    window_minutes: int = 10
    llm_mode: str = "disabled"

# -------------------------
# Health Endpoint
# -------------------------
@app.get("/health")
async def health():
    HEALTH_REQUESTS_TOTAL.inc()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# -------------------------
# Metrics Endpoint
# -------------------------
@app.get("/metrics")
async def metrics():
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# -------------------------
# Root Endpoint - Simple UI
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Production Debugger</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px; }
            .endpoint { background: #f5f5f5; padding: 10px; font-family: monospace; }
            button { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; }
            .result { background: #f0f0f0; padding: 10px; margin-top: 10px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>🤖 AI Production Debugger</h1>
        <div class="card">
            <h3>Quick Debug</h3>
            <p>Namespace: <input type="text" id="namespace" value="default"></p>
            <p>Minutes: <input type="number" id="minutes" value="10"></p>
            <button onclick="debug()">Analyze Now</button>
            <div id="result" class="result"></div>
        </div>
        
        <div class="card">
            <h3>Available Endpoints</h3>
            <div class="endpoint">GET  /health - Health check</div>
            <div class="endpoint">GET  /metrics - Prometheus metrics</div>
            <div class="endpoint">POST /analyze - Manual analysis</div>
            <div class="endpoint">POST /auto-analyze - Auto-collect & analyze</div>
        </div>

        <script>
            async function debug() {
                const ns = document.getElementById('namespace').value;
                const mins = document.getElementById('minutes').value;
                
                document.getElementById('result').innerHTML = 'Analyzing...';
                
                try {
                    const response = await fetch('/auto-analyze', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            namespace: ns,
                            window_minutes: parseInt(mins),
                            llm_mode: 'good'
                        })
                    });
                    
                    const data = await response.json();
                    document.getElementById('result').innerHTML = 
                        JSON.stringify(data, null, 2);
                } catch(e) {
                    document.getElementById('result').innerHTML = 'Error: ' + e;
                }
            }
        </script>
    </body>
    </html>
    """

# -------------------------
# Analyze Endpoint
# -------------------------
@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    start_time = time.time()
    
    try:
        # Validate signals
        signals = []
        for s in req.signals:
            if "name" not in s or "value" not in s:
                raise ValueError("Each signal must have name and value")
            
            signals.append({
                "name": s["name"],
                "value": s["value"],
                "signal_type": s.get("signal_type", "metric"),
                "severity": s.get("severity", 1),
                "timestamp": s.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "source": s.get("source", "manual")
            })
        
        SIGNALS_PROCESSED.inc(len(signals))
        
        # Detect incident window
        incident_result = detect_incident_window(signals)
        
        # Rank signals
        ranked = rank_signals(signals)
        
        # Add evidence IDs
        for idx, signal in enumerate(ranked, start=1):
            signal["id"] = f"E{idx}"
        
        # LLM reasoning (if enabled)
        if req.llm_mode != "disabled":
            prompt = build_prompt(ranked)
            llm = get_llm_client(mode=req.llm_mode)
            llm_response = llm.analyze(prompt)
            validated = validate_rca_response(llm_response, ranked)
            
            result = {
                "status": "success",
                "mode": "llm",
                "incident": incident_result,
                "signals_analyzed": len(signals),
                "rca": validated
            }
        else:
            result = {
                "status": "success",
                "mode": "rule-based",
                "incident": incident_result,
                "signals_analyzed": len(signals),
                "top_signals": ranked[:3]
            }
        
        ANALYZE_REQUESTS_TOTAL.labels(status="success").inc()
        return result
        
    except (LLMResponseError, InvalidRCAResponse, ValueError) as e:
        ANALYZE_REQUESTS_TOTAL.labels(status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        ANALYZE_LATENCY.observe(time.time() - start_time)

# -------------------------
# Auto-Analyze Endpoint
# -------------------------
@app.post("/auto-analyze")
async def auto_analyze(req: AutoAnalyzeRequest):
    try:
        # Collect signals from Kubernetes
        collector = KubernetesEventCollector(namespace=req.namespace)
        
        # Get pod events
        events = collector.collect_pod_events(window_minutes=req.window_minutes)
        
        # Get pod restarts
        restarts = collector.collect_pod_restarts()
        
        # Convert to signals
        signals = []
        
        # Add pod events
        for event in events["pod_events"]:
            signals.append({
                "name": event["reason"],
                "value": event["pod"],
                "signal_type": "pod_event",
                "severity": 9,
                "timestamp": event["last_seen"],
                "source": "kubernetes",
                "message": event.get("message", "")
            })
        
        # Add restarts
        for restart in restarts:
            signals.append({
                "name": "restart_count",
                "value": restart["restart_count"],
                "pod": restart["pod"],
                "signal_type": "restart",
                "severity": min(restart["restart_count"] * 2, 10),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "kubernetes"
            })
        
        if not signals:
            return {
                "status": "success",
                "message": f"No issues detected in namespace {req.namespace} in the last {req.window_minutes} minutes",
                "signals_found": 0
            }
        
        # Analyze the signals
        analyze_req = AnalyzeRequest(
            signals=signals,
            llm_mode=req.llm_mode,
            namespace=req.namespace
        )
        
        return await analyze(analyze_req)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# Quick Debug Endpoint
# -------------------------
@app.get("/quick-debug")
async def quick_debug(namespace: str = "default", minutes: int = 10):
    """Quick endpoint for kubectl alias"""
    req = AutoAnalyzeRequest(namespace=namespace, window_minutes=minutes)
    return await auto_analyze(req)
