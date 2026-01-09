from datetime import datetime
from typing import List, Dict


def detect_incident_window(signals: List[Dict]) -> Dict:
    """
    Detects the incident window based on signal timestamps.
    Assumes signals are already filtered to relevant ones.
    """

    if not signals:
        raise ValueError("No signals provided")

    sorted_signals = sorted(
        signals,
        key=lambda s: datetime.fromisoformat(s["timestamp"])
    )

    return {
        "start": sorted_signals[0]["timestamp"],
        "end": sorted_signals[-1]["timestamp"]
    }
