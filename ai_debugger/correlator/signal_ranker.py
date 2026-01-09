from typing import List, Dict


# Higher number = more important
SIGNAL_TYPE_PRIORITY = {
    "pod_event": 3,
    "restart": 2,
    "metric": 1,
}


def rank_signals(signals: List[Dict]) -> List[Dict]:
    """
    Ranks signals by importance for incident analysis.
    Most important signal comes first.
    """

    if not signals:
        return []

    def score(signal: Dict) -> tuple:
        """
        Ranking score:
        1. Signal type priority
        2. Severity
        """
        type_score = SIGNAL_TYPE_PRIORITY.get(signal.get("signal_type"), 0)
        severity = signal.get("severity", 0)

        # Higher is better → sort descending
        return (type_score, severity)

    ranked = sorted(
        signals,
        key=score,
        reverse=True
    )

    return ranked
