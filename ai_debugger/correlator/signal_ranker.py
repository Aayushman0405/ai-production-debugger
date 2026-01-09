from typing import Dict, List


class SignalRanker:
    """
    Ranks incident signals by importance so that
    downstream reasoning (LLM) focuses on the right evidence.
    """

    EVENT_WEIGHTS = {
        "OOMKilled": 1.0,
        "CrashLoopBackOff": 0.9,
        "BackOff": 0.7,
        "Failed": 0.8
    }

    METRIC_WEIGHTS = {
        "error_rate": 0.9,
        "latency_p95": 0.8,
        "cpu_usage": 0.6,
        "memory_usage": 0.6
    }

    def rank(self, signals: Dict, top_k: int = 5) -> List[Dict]:
        scored_signals: List[Dict] = []

        # Rank events
        for event in signals.get("events", []):
            score = self.EVENT_WEIGHTS.get(event.get("type"), 0.5)
            scored_signals.append({
                "category": "event",
                "signal": event,
                "score": score,
                "reason": f"Kubernetes event: {event.get('type')}"
            })

        # Rank metrics
        for metric in signals.get("metrics", []):
            base_score = self.METRIC_WEIGHTS.get(metric.get("name"), 0.5)
            severity_multiplier = min(metric.get("value", 0) * 5, 1.0)

            scored_signals.append({
                "category": "metric",
                "signal": metric,
                "score": round(base_score * severity_multiplier, 2),
                "reason": f"Metric spike detected: {metric.get('name')}"
            })

        # Rank restarts
        for restart in signals.get("restarts", []):
            count = restart.get("count", 0)
            score = min(0.4 + (count * 0.1), 0.9)

            scored_signals.append({
                "category": "restart",
                "signal": restart,
                "score": round(score, 2),
                "reason": f"Pod restarted {count} times"
            })

        # Sort by score descending
        scored_signals.sort(key=lambda x: x["score"], reverse=True)

        return scored_signals[:top_k]
