from datetime import datetime
from typing import List, Dict

def detect_incident_window(signals: List[Dict]) -> Dict:
    """
    Detects the incident window based on signal timestamps.
    """
    if not signals:
        return {
            "start": None,
            "end": None,
            "duration_seconds": 0
        }
    
    # Extract timestamps and sort
    timestamps = []
    for s in signals:
        try:
            ts = datetime.fromisoformat(s["timestamp"].replace('Z', '+00:00'))
            timestamps.append(ts)
        except (ValueError, KeyError):
            continue
    
    if not timestamps:
        return {
            "start": None,
            "end": None,
            "duration_seconds": 0
        }
    
    start_time = min(timestamps)
    end_time = max(timestamps)
    
    return {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds()
    }
