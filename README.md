# 🧠 AI Production Debugging Assistant

An **AI-assisted root cause analysis (RCA) system** for Kubernetes production incidents.  
Designed to help SREs and DevOps engineers **debug failures faster** using structured signal correlation + LLM reasoning.

> This is **not** a “paste logs into ChatGPT” project.  
> It is an **AI-powered SRE system** that decides *what evidence matters* before invoking an LLM.

---

## ❓ Why This Project Exists

In real production environments:

- Incidents involve **multiple weak signals**
- Logs, events, and restarts are scattered
- Engineers manually correlate information under pressure
- ChatGPT alone cannot:
  - Understand incident windows
  - Rank signals
  - Avoid hallucinating causes

This project automates the **thinking process of a senior SRE**.

---

## 🏗️ High-Level Architecture

   ┌────────────┐
   │ Kubernetes │
   │ Cluster    │
   └─────┬──────┘
         │
         ▼
┌────────────────────────┐
│ Signal Collectors      │
│ - Pod Events           │
│ - Restart Counts       │
│ (metrics/logs later)   │
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ Incident Window        │
│ Detection              │
│ - Time-bound analysis  │
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ Signal Ranking         │   
│ - Severity             │
│ - Frequency            │
│ - Relevance            │
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ Prompt Builder         │
│ - Evidence locked      │
│ - Anti-hallucination   │
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ LLM Reasoning Engine   │
│ - Structured RCA JSON  │
│ - Confidence score     │  
└────────────────────────┘



---

## 🧩 Core Features

### ✅ Evidence-Based RCA
- Uses **only observed signals**
- Explicitly forbids speculation
- Separates symptoms vs root cause

### ✅ Incident Window Detection
- Focuses on *when* the incident happened
- Avoids analyzing irrelevant historical noise

### ✅ Signal Ranking
- Kubernetes events > restarts > metrics (extensible)
- Prevents low-signal noise from confusing analysis

### ✅ LLM Abstraction Layer
- Mock provider for safe local testing
- API-based LLMs supported (OpenAI, etc.)
- JSON-only output enforced

### ✅ Kubernetes-Native
- Read-only RBAC
- Non-root container
- Health probes
- Cluster-ready design

---

## 📂 Repository Structure

ai_production_debugger/
├── ai_debugger/
│ ├── api/ # FastAPI entrypoint
│ ├── collector/ # Kubernetes signal collectors
│ ├── correlator/ # Incident window & ranking logic
│ └── reasoning/ # Prompt + LLM client
│
├── k8s/ # Kubernetes manifests
├── Dockerfile
├── requirements.txt
└── README.md


## ▶️ Running Locally (Mock Mode)

```bash
python -m uvicorn ai_debugger.api.main:app


Health check:
GET /health

