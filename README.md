🚀 AI Production Debugger

An intelligent, AI-powered root cause analysis (RCA) system designed specifically for Kubernetes production environments. It automates the detective work of an SRE by correlating signals, ranking evidence, and providing explainable insights.

🎯 Why This Project?
In production environments, debugging is hard:
Too many signals - Logs, events, metrics scattered everywhere
Time pressure - Every minute of downtime costs money
Human error - Tired engineers miss critical evidence
LLM hallucinations - ChatGPT makes up causes when given raw logs

This project solves these problems by:
Collecting real Kubernetes signals (pod events, restarts)
Correlating them to find incident windows
Ranking evidence by importance (pod_events > restarts > metrics)
Constraining LLM reasoning to only use actual evidence
Validating responses to prevent hallucinations

🏗️ Architecture


┌─────────────────────────────────────────────────────────────┐
│                     KUBERNETES CLUSTER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Pod Events │  │   Restarts   │  │   Metrics    │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            ▼                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              AI PRODUCTION DEBUGGER                    │ │
│  │  ┌──────────────┐     ┌──────────────┐                 │ │
│  │  │   Collector  │───▶│  Correlator  │                 │ │
│  │  │  (K8s API)   │     │(Incident Win)│                 │ │
│  │  └──────────────┘     └──────┬───────┘                 │ │
│  │                              ▼                         │ │
│  │  ┌──────────────┐     ┌──────────────┐                 │ │
│  │  │Signal Ranker │───▶│Prompt Builder│                 │  │
│  │  │ (Priority)   │     │(Evidence-lock)│               │  │
│  │  └──────────────┘     └──────┬───────┘                │  │
│  │                              ▼                        │  │
│  │  ┌──────────────┐     ┌──────────────┐                │  │
│  │  │   LLM Engine │───▶│  Validator    │               │  │
│  │  │(OpenAI/Mock) │     │(JSON Schema) │                │  │
│  │  └──────────────┘     └──────────────┘                │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 RESPONSE (JSON)                       │  │
│  │  {                                                    │  │
│  │    "root_cause": "OOMKilled due to memory limit",     │  │
│  │    "confidence": 0.85,                                │  │
│  │    "evidence_ids": ["E1", "E3"]                       │  │
│  │  }                                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘




💻 Tech Stack
Component	        Technology	            Purpose
API Framework	    FastAPI	                High-performance async endpoints
Kubernetes Client	official Python client	Fetch pod events and status
LLM Integration	  OpenAI GPT-4o-mini	    Root cause analysis
Metrics	          Prometheus Client	      Monitoring and observability
Validation       	Pydantic	              Request/response validation
Container	        Docker                	Packaging and deployment
Orchestration	    Kubernetes	            Production deployment
Web UI	          HTML/JS	                Simple interface for testing


🔄 How It Works
1. Signal Collection

# Collects from Kubernetes API
- Pod events (CrashLoopBackOff, OOMKilled, Failed)
- Container restarts
- Pod status changes2. Incident Window Detection

2. Incident Window Detection
# Automatically determines time boundaries
- Finds earliest and latest signal timestamps
- Creates focused time window for analysis
- Prevents analyzing irrelevant historical data

3. Signal Ranking
Priority hierarchy (higher = more important):
10 - Pod events (OOMKilled, CrashLoopBackOff)
5 - Container restarts
1 - Metrics (CPU, memory, latency)

4. Evidence-Locked Prompting
{
  "E1": {"signal_type": "pod_event", "reason": "OOMKilled", "severity": 10},
  "E2": {"signal_type": "restart", "restart_count": 5, "severity": 8}
}

The LLM can ONLY reference these evidence IDs - no hallucinations!


5. Response Validation
# Enforces strict schema
- Must include root_cause, evidence_ids, confidence
- Evidence IDs must exist in original signals
- Confidence must be between 0 and 1


Quick Test
# Port forward the service
kubectl port-forward -n ai-debugger service/ai-debugger 8080:80

# In another terminal, test health
curl http://localhost:8080/health

# Debug a namespace
curl -X POST http://localhost:8080/auto-analyze \
  -H "Content-Type: application/json" \
  -d '{"namespace": "default", "window_minutes": 10}'


📚 API Documentation
Interactive API Docs
Once deployed, visit:

Swagger UI: http://localhost:8080/docs
ReDoc: http://localhost:8080/redoc

## 🚀 Shell Configuration

After deployment, add these helpful aliases to your `~/.bashrc`:

```bash
# AI Debugger Commands
alias ai-debug='/usr/local/bin/kubectl-ai-debug'
alias kubectl-ai-debug='/usr/local/bin/kubectl-ai-debug'

aidebug() {
    namespace="${1:-default}"
    minutes="${2:-10}"
    echo "┌─────────────────────────────────────────┐"
    echo "│ 🤖  AI PRODUCTION DEBUGGER              │"
    echo "├─────────────────────────────────────────┤"
    echo "│ Namespace: $namespace"
    echo "│ Time window: $minutes minutes"
    echo "└─────────────────────────────────────────┘"
    /usr/local/bin/kubectl-ai-debug "$namespace" "$minutes"
}

ai-check() {
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ AI Debugger is running"
    else
        echo "❌ Not reachable - run: ai-start"
    fi
}

ai-start() {
    nohup kubectl port-forward -n ai-debugger service/ai-debugger 8080:80 > /tmp/ai-debugger.log 2>&1 &
    echo "✅ Port-forward started"
}
ai-stop() {
    pkill -f "kubectl.*port-forward.*8080:80" && echo "✅ Stopped"
}
ai-logs() {
    kubectl logs -n ai-debugger deployment/ai-debugger -f
}
ai-restart() {
    kubectl rollout restart -n ai-debugger deployment/ai-debugger
}
ai-openai() {
    kubectl exec -n ai-debugger deployment/ai-debugger -- env | grep -E "OPENAI|LLM"
}


Usage:
ai-start        # Start port-forward
aidebug default # Debug namespace
ai-logs         # View logs
ai-stop         # Stop port-forward


🎉 What's Been Accomplished
✅ Complete Kubernetes Integration
Real-time pod event collection
Restart count monitoring
RBAC-secured access

✅ Intelligent Signal Processing
Incident window detection
Priority-based ranking
Evidence ID system

✅ Safe LLM Integration
Mock mode for testing
OpenAI GPT-4o-mini support
JSON-only responses
Hallucination prevention

✅ Production-Ready Deployment
Docker containerization
Kubernetes manifests
Health checks
Prometheus metrics
Rolling updates

✅ Developer Experience
kubectl plugin
Web UI interface
Comprehensive API docs
Local testing support
Secret management

✅ Security
RBAC least privilege
Input validation
Output schema enforcement
