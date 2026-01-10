🧠 AI Production Debugging Assistant

An AI-assisted Root Cause Analysis (RCA) system for Kubernetes production incidents.
Built to help SREs and DevOps engineers debug failures faster using structured signal correlation and guarded LLM reasoning.

⚠️ This is not a “paste logs into ChatGPT” project.
This system decides what evidence matters first, then allows an LLM to reason only within those constraints.


❓ Why This Project Exists

In real production environments:
Incidents involve multiple weak signals
Logs, events, and restarts are scattered across systems
Engineers manually correlate data under pressure

Naive LLM usage leads to:
hallucinated causes
unverifiable explanations
unsafe conclusions

A plain LLM cannot:
detect an incident window
rank signals by importance
distinguish symptoms from root cause
enforce evidence-based reasoning

This project automates the thinking process of a senior SRE.

🎯 Design Goals
✅ Evidence-first, not LLM-first
✅ Deterministic and auditable RCA
✅ Kubernetes-native and production-safe
✅ LLMs are optional, constrained, and replaceable

🏗️ High-Level Architecture
┌──────────────┐
│ Kubernetes   │
│ Cluster      │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ Signal Collectors        │
│ - Pod Events             │
│ - Restart Counts         │
│ - (Metrics / Logs later) │
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│ Incident Window          │
│ Detection                │
│ - Time-bounded analysis  │
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│ Signal Ranking           │
│ - Type priority          │
│ - Severity               │
│ - Frequency              │
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│ Prompt Builder           │
│ - Evidence locked        │
│ - Anti-hallucination     │
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│ LLM Reasoning Engine     │
│ - JSON-only RCA          │
│ - Confidence score       │
└──────────────────────────┘

🧩 Core Features
✅ Evidence-Based RCA
Uses only observed signals
Explicitly forbids speculation
Every RCA must reference explicit evidence IDs
Responses are rejected if evidence is invalid

✅ Incident Window Detection
Automatically determines when the incident occurred
Prevents analysis of irrelevant historical noise

✅ Signal Ranking
Signals are ranked by importance:
Kubernetes events
Pod restarts
Metrics (extensible)
High-impact signals surface first

✅ LLM Abstraction Layer
Mock LLM for safe local testing
API-based LLMs supported (OpenAI, extensible)
JSON-only output enforced
Schema validation before returning results

✅ Kubernetes-Native & Production-Safe
Read-only RBAC
Non-root container
Health & readiness probes
Prometheus metrics exposed
Safe rolling deployments

📂 Repository Structure
ai_production_debugger/
├── ai_debugger/
│   ├── api/          # FastAPI entrypoint
│   ├── collector/   # Kubernetes signal collectors
│   ├── correlator/  # Incident window & signal ranking
│   └── reasoning/   # Prompt templates & LLM clients
│
├── k8s/              # Kubernetes manifests (RBAC, deploy, ingress)
├── Dockerfile
├── requirements.txt
└── README.md

▶️ Running Locally (Mock Mode)
python -m uvicorn ai_debugger.api.main:app --reload

Health Check
curl http://localhost:8000/health

▶️ Example RCA Request
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "llm_mode": "good",
    "signals": [
      {"name": "latency", "value": 1200},
      {"name": "error_rate", "value": 0.18},
      {"name": "cpu", "value": 92}
    ]
  }'

Example Response
{
  "status": "success",
  "mode": "llm",
  "incident": {
    "start": "2026-01-10T16:20:00Z",
    "end": "2026-01-10T16:20:01Z"
  },
  "rca": {
    "root_cause": "high_cpu_usage leading to increased latency and error rate",
    "supporting_evidence_ids": ["E1", "E2", "E3"],
    "confidence": 0.9
  }
}

🔐 Why This Is Not a Toy LLM Project
Typical LLM Debugging	        This Project
Free-text reasoning	          Structured JSON only
Hallucinated causes	          Evidence-locked reasoning
No validation	                Strict schema validation
Manual correlation	          Automated signal ranking
Unsafe for prod	              Production-safe by design

🛣️ Roadmap
 Automatic Prometheus metric ingestion
 Kubernetes events → evidence pipeline
 Multi-LLM fallback strategy

 Confidence-based remediation hooks

 Incident history & RCA persistence
