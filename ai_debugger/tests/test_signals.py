from datetime import datetime, timedelta, timezone


def synthetic_signals():
    base_time = datetime.now(timezone.utc)

    return [
        {
            "id": "E1",
            "signal_type": "pod_event",
            "pod": "api-7c9d",
            "namespace": "production",
            "reason": "CrashLoopBackOff",
            "message": "Back-off restarting failed container",
            "timestamp": base_time.isoformat(),
            "severity": 9,
            "source": "kubernetes"
        },
        {
            "id": "E2",
            "signal_type": "restart",
            "pod": "api-7c9d",
            "namespace": "production",
            "restart_count": 5,
            "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
            "severity": 8,
            "source": "kubernetes"
        }
    ]


if __name__ == "__main__":
    for s in synthetic_signals():
        print(s)
