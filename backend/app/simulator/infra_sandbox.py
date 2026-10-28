import copy
from typing import Dict, Any, Optional

def get_initial_infra_state() -> Dict[str, Any]:
    return {
        "hosts": {
            "host-01": {
                "id": "host-01",
                "hostname": "prod-app-01.us-east.internal",
                "status": "ONLINE",
                "cpu_pct": 28.4,
                "memory_pct": 52.1,
                "disks": {
                    "/var/log": {"total_gb": 100.0, "used_gb": 35.0, "utilization_pct": 35.0, "cause": "nominal", "files": ["app.log", "syslog.1"]},
                    "/data/core": {"total_gb": 200.0, "used_gb": 12.0, "utilization_pct": 6.0, "cause": "nominal", "files": []},
                    "/etc": {"total_gb": 20.0, "used_gb": 2.1, "utilization_pct": 10.5, "protected": True, "files": ["hosts", "passwd", "sudoers"]},
                    "/boot": {"total_gb": 2.0, "used_gb": 0.4, "utilization_pct": 20.0, "protected": True, "files": ["vmlinuz"]}
                },
                "workers": {
                    "worker_process": {"pid": 1042, "status": "HEALTHY", "heartbeat_age_sec": 4.0, "threads": 8}
                },
                "zombies": {
                    "count": 0,
                    "pids": []
                }
            },
            "host-02": {
                "id": "host-02",
                "hostname": "prod-worker-02.us-east.internal",
                "status": "ONLINE",
                "cpu_pct": 34.1,
                "memory_pct": 61.0,
                "disks": {
                    "/var/log": {"total_gb": 100.0, "used_gb": 42.0, "utilization_pct": 42.0, "cause": "nominal", "files": ["worker.log"]},
                    "/data/core": {"total_gb": 200.0, "used_gb": 15.0, "utilization_pct": 7.5, "cause": "nominal", "files": []},
                    "/etc": {"total_gb": 20.0, "used_gb": 2.1, "utilization_pct": 10.5, "protected": True, "files": ["hosts"]},
                },
                "workers": {
                    "worker_process": {"pid": 2055, "status": "HEALTHY", "heartbeat_age_sec": 3.0, "threads": 12}
                },
                "zombies": {
                    "count": 0,
                    "pids": []
                }
            },
            "host-03": {
                "id": "host-03",
                "hostname": "prod-db-03.us-east.internal",
                "status": "ONLINE",
                "cpu_pct": 45.2,
                "memory_pct": 70.8,
                "disks": {
                    "/var/log": {"total_gb": 150.0, "used_gb": 55.0, "utilization_pct": 36.6, "cause": "nominal", "files": ["db.log"]},
                    "/data/core": {"total_gb": 500.0, "used_gb": 40.0, "utilization_pct": 8.0, "cause": "nominal", "files": []},
                    "/etc": {"total_gb": 20.0, "used_gb": 2.1, "utilization_pct": 10.5, "protected": True, "files": ["hosts"]}
                },
                "workers": {
                    "worker_process": {"pid": 3088, "status": "HEALTHY", "heartbeat_age_sec": 5.0, "threads": 16}
                },
                "zombies": {
                    "count": 0,
                    "pids": []
                }
            }
        },
        "services": {
            "api-gateway": {
                "name": "api-gateway",
                "status": "HEALTHY",
                "http_5xx_rate_pct": 0.12,
                "latency_p95_ms": 34.0,
                "replicas": 4,
                "tls": {
                    "cert_days_remaining": 78,
                    "tls_handshake_status": "SUCCESS",
                    "cert_serial": "A7F9-8802-BC14"
                }
            },
            "worker-cluster": {
                "name": "worker-cluster",
                "status": "HEALTHY",
                "queue": {
                    "queue_depth": 240,
                    "queue_drain_rate": 280,
                    "replicas": 2
                }
            },
            "cache-cluster": {
                "name": "cache-cluster",
                "status": "HEALTHY",
                "fragmentation_pct": 14.5,
                "cache_hit_ratio": 94.2,
                "key_count": 48200
            },
            "database-cluster": {
                "name": "database-cluster",
                "status": "HEALTHY",
                "pool_utilization_pct": 32.0,
                "idle_connections": 12,
                "active_connections": 18,
                "locks": 0
            },
            "cron-scheduler": {
                "name": "cron-scheduler",
                "status": "HEALTHY",
                "last_exit_code": 0,
                "failure_count": 0,
                "locked": False
            }
        }
    }

class InfraSandbox:
    def __init__(self):
        self._state = get_initial_infra_state()

    def reset(self):
        self._state = get_initial_infra_state()

    def get_state(self) -> Dict[str, Any]:
        return copy.deepcopy(self._state)

    def get_host(self, host_id: str) -> Optional[Dict[str, Any]]:
        return self._state["hosts"].get(host_id)

    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        return self._state["services"].get(service_id)

    def snapshot(self, host_id: str, target: str) -> Dict[str, Any]:
        state = copy.deepcopy(self._state)
        host = state["hosts"].get(host_id, {})
        
        if target in host.get("disks", {}):
            return {"type": "disk", "target": target, "data": copy.deepcopy(host["disks"][target])}
        elif target == "worker_process":
            return {"type": "worker", "target": target, "data": copy.deepcopy(host.get("workers", {}).get("worker_process", {}))}
        elif target == "queue_replicas":
            return {"type": "queue", "target": target, "data": copy.deepcopy(state["services"]["worker-cluster"]["queue"])}
        elif target == "tls_certificate":
            return {"type": "tls", "target": target, "data": copy.deepcopy(state["services"]["api-gateway"]["tls"])}
        elif target == "/var/log/apps" or target == "/var/log":
            return {"type": "disk", "target": target, "data": copy.deepcopy(host.get("disks", {}).get("/var/log", {}))}
        elif target == "cache_instance":
            return {"type": "cache", "target": target, "data": copy.deepcopy(state["services"]["cache-cluster"])}
        elif target == "db_connection_pool":
            return {"type": "db_pool", "target": target, "data": copy.deepcopy(state["services"]["database-cluster"])}
        elif target == "process_table":
            return {"type": "zombies", "target": target, "data": copy.deepcopy(host.get("zombies", {}))}
        elif target == "cron_job":
            return {"type": "cron", "target": target, "data": copy.deepcopy(state["services"]["cron-scheduler"])}
        elif target == "service_deployment":
            return {"type": "service", "target": target, "data": copy.deepcopy(state["services"]["api-gateway"])}
        
        return {"type": "generic", "target": target, "data": {}}

    def restore_snapshot(self, host_id: str, target: str, snapshot: Dict[str, Any]):
        if not snapshot or "data" not in snapshot:
            return
        
        data = copy.deepcopy(snapshot["data"])
        host = self._state["hosts"].get(host_id)
        
        if snapshot.get("type") == "disk" and host:
            disk_key = snapshot.get("target", "/var/log")
            if disk_key in host["disks"]:
                host["disks"][disk_key] = data
        elif snapshot.get("type") == "worker" and host:
            host["workers"]["worker_process"] = data
        elif snapshot.get("type") == "queue":
            self._state["services"]["worker-cluster"]["queue"] = data
        elif snapshot.get("type") == "tls":
            self._state["services"]["api-gateway"]["tls"] = data
        elif snapshot.get("type") == "cache":
            self._state["services"]["cache-cluster"] = data
        elif snapshot.get("type") == "db_pool":
            self._state["services"]["database-cluster"] = data
        elif snapshot.get("type") == "zombies" and host:
            host["zombies"] = data
        elif snapshot.get("type") == "cron":
            self._state["services"]["cron-scheduler"] = data
        elif snapshot.get("type") == "service":
            self._state["services"]["api-gateway"] = data

sandbox = InfraSandbox()
