from datetime import datetime, timedelta, timezone
from kubernetes import client, config
from typing import Dict, List, Optional
import os

class KubernetesEventCollector:
    def __init__(self, namespace: str):
        self.namespace = namespace
        
        # Try in-cluster config first, then kubeconfig
        try:
            config.load_incluster_config()
        except config.ConfigException:
            kubeconfig_path = os.getenv('KUBECONFIG', os.path.expanduser('~/.kube/config'))
            if os.path.exists(kubeconfig_path):
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                # Try default location
                config.load_kube_config()
        
        self.core_v1 = client.CoreV1Api()
    
    def _within_time_window(self, event_time: Optional[datetime], window_minutes: int) -> bool:
        if not event_time:
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        # Ensure event_time is timezone-aware
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        return event_time >= cutoff
    
    def collect_pod_events(self, window_minutes: int = 10) -> Dict:
        """Collect pod events within time window"""
        try:
            events = self.core_v1.list_namespaced_event(self.namespace)
        except client.exceptions.ApiException as e:
            return {
                "namespace": self.namespace,
                "error": str(e),
                "pod_events": []
            }
        
        relevant_reasons = {
            "OOMKilled",
            "BackOff",
            "CrashLoopBackOff",
            "Failed",
            "FailedMount",
            "FailedScheduling",
            "Unhealthy",
            "Killing",
            "Created",
            "Started"
        }
        
        pod_events = []
        
        for event in events.items:
            if not event.involved_object or event.involved_object.kind != "Pod":
                continue
            
            if event.reason not in relevant_reasons:
                continue
            
            # Get the correct timestamp
            event_time = (
                event.event_time or
                event.last_timestamp or
                event.first_timestamp or
                event.metadata.creation_timestamp
            )
            
            if not event_time or not self._within_time_window(event_time, window_minutes):
                continue
            
            pod_events.append({
                "pod": event.involved_object.name,
                "reason": event.reason,
                "message": event.message,
                "count": event.count or 1,
                "last_seen": event_time.isoformat() if hasattr(event_time, 'isoformat') else str(event_time),
                "type": event.type
            })
        
        return {
            "namespace": self.namespace,
            "time_window_minutes": window_minutes,
            "pod_events": pod_events
        }
    
    def collect_pod_restarts(self) -> List[Dict]:
        """Collect pod restart counts"""
        try:
            pods = self.core_v1.list_namespaced_pod(self.namespace)
        except client.exceptions.ApiException:
            return []
        
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
                    "status": pod.status.phase
                })
        
        return restart_summary
    
    def collect_all(self, window_minutes: int = 10) -> Dict:
        """Collect all signals"""
        return {
            "events": self.collect_pod_events(window_minutes),
            "restarts": self.collect_pod_restarts()
        }
