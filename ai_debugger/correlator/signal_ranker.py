from typing import List, Dict

# Priority: higher number = more important
SIGNAL_TYPE_PRIORITY = {
    "pod_event": 10,
    "restart": 5,
    "metric": 1,
}

def rank_signals(signals: List[Dict]) -> List[Dict]:
    """
    Ranks signals by importance for incident analysis.
    """
    if not signals:
        return []
    
    def score(signal: Dict) -> tuple:
        # Signal type priority
        type_score = SIGNAL_TYPE_PRIORITY.get(signal.get("signal_type", "metric"), 0)
        
        # Severity (1-10)
        severity = signal.get("severity", 1)
        
        # Recency - newer signals slightly higher
        try:
            ts = datetime.fromisoformat(signal.get("timestamp", "").replace('Z', '+00:00'))
            recency = ts.timestamp()  # Higher = newer
        except:
            recency = 0
        
        return (type_score, severity, recency)
    
    from datetime import datetime
    ranked = sorted(signals, key=score, reverse=True)
    return ranked
