from datetime import datetime, timezone
from ai_debugger.tests.test_signals import synthetic_signals
from ai_debugger.correlator.incident_window import detect_incident_window


def parse(ts):
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


if __name__ == "__main__":
    signals = synthetic_signals()

    window = detect_incident_window(signals)

    print("Incident Window:")
    print("Start:", parse(window["start"]))
    print("End  :", parse(window["end"]))
