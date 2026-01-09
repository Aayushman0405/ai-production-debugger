from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, ISO_FORMAT).replace(tzinfo=timezone.utc)


class IncidentWindowDetector:
    """
    Determines when an incident started and defines the time window
    for analysis based on signal changes.
    """

    def __init__(self, window_padding_minutes: int = 5):
        self.window_padding = timedelta(minutes=window_padding_minutes)

    def _earliest_timestamp(self, timestamps: List[datetime]) -> Optional[datetime]:
        return min(timestamps) if timestamps else None

    def detect_incident_start(self, signals: Dict) -> Optional[datetime]:
        """
        Finds the earliest abnormal signal timestamp.
        """
        timestamps: List[datetime] = []

        for event in signals.get("events", []):
            timestamps.append(parse_ts(event["timestamp"]))

        for metric in signals.get("metrics", []):
            # Treat a metric spike as abnormal if value is high
            if metric.get("value", 0) > 0.05:
                timestamps.append(parse_ts(metric["timestamp"]))

        for restart in signals.get("restarts", []):
            if restart.get("count", 0) > 0:
                timestamps.append(parse_ts(restart["timestamp"]))

        return self._earliest_timestamp(timestamps)

    def build_incident_window(self, incident_start: datetime) -> Dict:
        """
        Builds an incident window around the detected start time.
        """
        start = incident_start - self.window_padding
        end = incident_start + self.window_padding

        duration = int((end - start).total_seconds() / 60)

        return {
            "incident_start": start.isoformat(),
            "incident_end": end.isoformat(),
            "duration_minutes": duration
        }

    def detect(self, signals: Dict) -> Optional[Dict]:
        """
        Main entry point.
        """
        incident_start = self.detect_incident_start(signals)

        if not incident_start:
            return None

        window = self.build_incident_window(incident_start)

        return {
            **window,
            "trigger_signal": self._infer_trigger(signals),
            "confidence": self._estimate_confidence(signals)
        }

    def _infer_trigger(self, signals: Dict) -> str:
        """
        Heuristic to guess what triggered the incident.
        """
        if any(m.get("value", 0) > 0.1 for m in signals.get("metrics", [])):
            return "metric_spike"

        if signals.get("events"):
            return "kubernetes_event"

        if signals.get("restarts"):
            return "pod_restarts"

        return "unknown"

    def _estimate_confidence(self, signals: Dict) -> float:
        """
        Simple confidence heuristic based on number of signals.
        """
        signal_count = (
            len(signals.get("events", [])) +
            len(signals.get("metrics", [])) +
            len(signals.get("restarts", []))
        )

        if signal_count >= 5:
            return 0.85
        if signal_count >= 3:
            return 0.7
        if signal_count >= 1:
            return 0.5
        return 0.0