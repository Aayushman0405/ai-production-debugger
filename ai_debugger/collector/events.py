from datetime import datetime, timedelta, timezone
from kubernetes import client, config
from typing import Dict, List


class KubernetesEventCollector:
    def __init__(self, namespace: str):
        self.namespace = namespace

        # ✅ Support both in-cluster and local dev
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        self.core_v1 = client.CoreV1Api()

    def _within_time_window(self, event_time: datetime, window_minutes: int) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        return event_time >= cutoff

    def collect_pod_events(self, window_minutes: int = 10) -> Dict:
        events = self.core_v1.list_namespaced_event(self.namespace)

        relevant_reasons = {
            "OOMKilled",
            "BackOff",
            "CrashLoopBackOff",
            "Failed",
        }

        pod_events: List[Dict] = []

        for event in events.items:
            if not event.involved_object or event.involved_object.kind != "Pod":
                continue

            if event.reason not in relevant_reasons:
                continue

            # ✅ Correct timestamp precedence
            event_time = (
                event.event_time
                or event.last_timestamp
                or event.first_timestamp
            )

            if not event_time:
                continue

            if not self._within_time_window(event_time, window_minutes):
                continue

            pod_events.append({
                "pod": event.involved_object.name,
                "reason": event.reason,
                "message": event.message,
                "count": event.count or 1,
                "last_seen": event_time.isoformat(),
            })

        return {
            "namespace": self.namespace,
            "time_window_minutes": window_minutes,
            "pod_events": pod_events,
        }

    def collect_pod_restarts(self) -> List[Dict]:
        pods = self.core_v1.list_namespaced_pod(self.namespace)

        restart_summary = []

        for pod in pods.items:
            total_restarts = 0

            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    total_restarts += cs.restart_count

            if total_restarts > 0:
                restart_summary.append({
                    "pod": pod.metadata.name,
                    "restart_count": total_restarts,
                })

        return restart_summary
