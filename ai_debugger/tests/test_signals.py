from datetime import datetime, timedelta, timezone

def synthetic_signals():
    base_time = datetime.now(timezone.utc)
    
    return [
        {
            "name": "CrashLoopBackOff",
            "value": "api-7c9d",
            "signal_type": "pod_event",
            "severity": 9,
            "timestamp": base_time.isoformat(),
            "source": "kubernetes",
            "message": "Back-off restarting failed container"
        },
        {
            "name": "restart_count",
            "value": 5,
            "pod": "api-7c9d",
            "signal_type": "restart",
            "severity": 8,
            "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
            "source": "kubernetes"
        },
        {
            "name": "OOMKilled",
            "value": "api-7c9d",
            "signal_type": "pod_event",
            "severity": 10,
            "timestamp": (base_time + timedelta(minutes=1)).isoformat(),
            "source": "kubernetes",
            "message": "Container killed due to memory limit"
        }
    ]

if __name__ == "__main__":
    for s in synthetic_signals():
        print(s)
