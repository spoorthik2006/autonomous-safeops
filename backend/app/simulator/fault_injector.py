import uuid
from typing import Dict, Any, Tuple
from app.simulator.infra_sandbox import sandbox

class FaultInjector:
    def __init__(self, sandbox_instance=sandbox):
        self.sb = sandbox_instance

    def inject_fault(
        self,
        fault_type: str,
        host_id: str = "host-01",
        service_id: str = None,
        custom_params: Dict[str, Any] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Injects a fault into the sandbox.
        Returns: (incident_metadata, diagnostic_data)
        """
        custom_params = custom_params or {}
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

        if fault_type == "routine_log_overflow":
            host = self.sb.get_host(host_id)
            if host:
                host["disks"]["/var/log"]["utilization_pct"] = 92.4
                host["disks"]["/var/log"]["used_gb"] = 92.4
                host["disks"]["/var/log"]["cause"] = "logs"
            return {
                "id": incident_id,
                "title": f"Disk Space Critical: /var/log at 92.4% on {host_id}",
                "service": "host-system",
                "host": host_id,
                "trigger_type": "disk_full",
                "runbook_id": "rb-disk-full",
                "risk_tier": 0
            }, {
                "disk_utilization_pct": 92.4,
                "target_path": "/var/log",
                "cause": "logs",
                "confidence": 0.98,
                "details": "Rapid stdout/stderr append from debug logging in application container."
            }

        elif fault_type == "ambiguous_disk_full":
            host = self.sb.get_host(host_id)
            if host:
                host["disks"]["/data/core"]["utilization_pct"] = 94.8
                host["disks"]["/data/core"]["used_gb"] = 189.6
                host["disks"]["/data/core"]["cause"] = "core_dump"
            return {
                "id": incident_id,
                "title": f"Disk Space Critical: /data/core at 94.8% on {host_id} (Ambiguous Cause)",
                "service": "host-system",
                "host": host_id,
                "trigger_type": "disk_full",
                "runbook_id": "rb-disk-full",
                "risk_tier": 3
            }, {
                "disk_utilization_pct": 94.8,
                "target_path": "/data/core",
                "cause": "core_dump",
                "confidence": 0.95,
                "details": "Multiple unanalyzed ELF 64-bit core dumps detected. Deletion would erase crash diagnostics."
            }

        elif fault_type == "unknown_disk_full":
            host = self.sb.get_host(host_id)
            if host:
                host["disks"]["/var/log"]["utilization_pct"] = 89.0
                host["disks"]["/var/log"]["cause"] = "unknown"
            return {
                "id": incident_id,
                "title": f"Disk Space Spike: Unknown consumer on {host_id}",
                "service": "host-system",
                "host": host_id,
                "trigger_type": "disk_full",
                "runbook_id": "rb-disk-full",
                "risk_tier": 2
            }, {
                "disk_utilization_pct": 89.0,
                "target_path": "/var/log",
                "cause": "unknown",
                "confidence": 0.45,
                "details": "Root directory saturation by unrecognized sparse file handle."
            }

        elif fault_type == "protected_path_tamper":
            return {
                "id": incident_id,
                "title": f"Security Alert: Remediation requested on protected path /etc/sudoers on {host_id}",
                "service": "prod-db-primary",
                "host": host_id,
                "trigger_type": "security_violation",
                "runbook_id": "rb-disk-full",
                "risk_tier": 3
            }, {
                "target_path": "/etc/sudoers",
                "service": "prod-db-primary",
                "cause": "protected_target_mutation",
                "details": "Attempted automated modification of immutable OS credential configuration or production DB."
            }

        elif fault_type == "stuck_worker":
            host = self.sb.get_host(host_id)
            if host:
                host["workers"]["worker_process"]["status"] = "UNRESPONSIVE"
                host["workers"]["worker_process"]["heartbeat_age_sec"] = 145.0
            return {
                "id": incident_id,
                "title": f"Background Worker Hung (Heartbeat Missed > 140s) on {host_id}",
                "service": "worker-cluster",
                "host": host_id,
                "trigger_type": "stuck_worker",
                "runbook_id": "rb-stuck-worker",
                "risk_tier": 1
            }, {
                "worker_status": "UNRESPONSIVE",
                "worker_heartbeat_age_sec": 145.0,
                "threads_hung": 8,
                "will_fail": False
            }

        elif fault_type == "failed_fix_worker":
            host = self.sb.get_host(host_id)
            if host:
                host["workers"]["worker_process"]["status"] = "UNRESPONSIVE"
                host["workers"]["worker_process"]["heartbeat_age_sec"] = 190.0
            return {
                "id": incident_id,
                "title": f"Deadlocked Worker (Failing Remediation Test) on {host_id}",
                "service": "worker-cluster",
                "host": host_id,
                "trigger_type": "stuck_worker",
                "runbook_id": "rb-stuck-worker",
                "risk_tier": 1
            }, {
                "worker_status": "UNRESPONSIVE",
                "worker_heartbeat_age_sec": 190.0,
                "threads_hung": 12,
                "will_fail": True,
                "failure_reason": "Kernel port bind conflict on worker respawn; post-verification fails"
            }

        elif fault_type == "queue_backlog":
            svc = self.sb.get_service("worker-cluster")
            if svc:
                svc["queue"]["queue_depth"] = 14200
                svc["queue"]["drain_rate"] = 40
            return {
                "id": incident_id,
                "title": "Kafka Task Queue Lag: 14,200 messages pending (Drain rate 40/s)",
                "service": "worker-cluster",
                "host": host_id,
                "trigger_type": "queue_backlog",
                "runbook_id": "rb-queue-scaling",
                "risk_tier": 1
            }, {
                "queue_depth": 14200,
                "consumer_lag_sec": 185.0
            }

        elif fault_type == "cert_expiring":
            svc = self.sb.get_service("api-gateway")
            if svc:
                svc["tls"]["cert_days_remaining"] = 5
            return {
                "id": incident_id,
                "title": "TLS Wildcard Ingress Certificate Expiring in 5 Days (*.api.internal)",
                "service": "api-gateway",
                "host": host_id,
                "trigger_type": "cert_expiring",
                "runbook_id": "rb-cert-rotation",
                "risk_tier": 2
            }, {
                "cert_days_remaining": 5,
                "domain": "*.api.internal",
                "issuer": "Internal Vault CA"
            }

        elif fault_type == "db_pool_leak":
            svc = self.sb.get_service("database-cluster")
            if svc:
                svc["pool_utilization_pct"] = 97.5
                svc["idle_connections"] = 38
                svc["locks"] = 4
            return {
                "id": incident_id,
                "title": "PostgreSQL Connection Pool Starvation: 97.5% utilized on database-cluster",
                "service": "database-cluster",
                "host": host_id,
                "trigger_type": "db_pool_leak",
                "runbook_id": "rb-db-pool-reset",
                "risk_tier": 2
            }, {
                "db_pool_utilization_pct": 97.5,
                "idle_connections": 38,
                "exclusive_locks": 0
            }

        elif fault_type == "cache_herd":
            svc = self.sb.get_service("cache-cluster")
            if svc:
                svc["fragmentation_pct"] = 79.2
                svc["cache_hit_ratio"] = 44.1
            return {
                "id": incident_id,
                "title": "Redis Cache Memory Fragmentation Spike (79.2%) & Cache Miss Storm",
                "service": "cache-cluster",
                "host": host_id,
                "trigger_type": "cache_fragmentation",
                "runbook_id": "rb-cache-flush",
                "risk_tier": 1
            }, {
                "cache_fragmentation_pct": 79.2,
                "cache_hit_ratio": 44.1
            }

        elif fault_type == "zombie_leak":
            host = self.sb.get_host(host_id)
            if host:
                host["zombies"]["count"] = 28
                host["zombies"]["pids"] = list(range(9100, 9128))
            return {
                "id": incident_id,
                "title": f"Process Table Saturation: 28 Defunct/Zombie Processes on {host_id}",
                "service": "host-system",
                "host": host_id,
                "trigger_type": "zombie_processes",
                "runbook_id": "rb-zombie-cleanup",
                "risk_tier": 0
            }, {
                "zombie_process_count": 28,
                "parent_pid": 1042
            }

        elif fault_type == "cron_failed":
            svc = self.sb.get_service("cron-scheduler")
            if svc:
                svc["last_exit_code"] = 137
                svc["failure_count"] = 1
                svc["locked"] = True
            return {
                "id": incident_id,
                "title": "Nightly Financial Reconciliation Cron Failed (Exit Code 137 OOM-Killed)",
                "service": "cron-scheduler",
                "host": host_id,
                "trigger_type": "cron_failure",
                "runbook_id": "rb-failed-cron-retry",
                "risk_tier": 1
            }, {
                "cron_last_exit_code": 137,
                "cron_failure_count": 1,
                "can_retry": True
            }

        elif fault_type == "service_5xx_spike":
            svc = self.sb.get_service("api-gateway")
            if svc:
                svc["http_5xx_rate_pct"] = 24.5
                svc["latency_p95_ms"] = 3200.0
            return {
                "id": incident_id,
                "title": "API Gateway 5xx Error Spike (24.5%) and Latency Degradation (>3s)",
                "service": "api-gateway",
                "host": host_id,
                "trigger_type": "service_5xx_spike",
                "runbook_id": "rb-service-restart",
                "risk_tier": 2
            }, {
                "http_5xx_rate_pct": 24.5,
                "latency_p95_ms": 3200.0,
                "upstreams_healthy": True
            }

        # Default fallback fault
        return {
            "id": incident_id,
            "title": f"Custom Alert: {fault_type} on {host_id}",
            "service": service_id or "host-system",
            "host": host_id,
            "trigger_type": fault_type,
            "runbook_id": "rb-disk-full",
            "risk_tier": 1
        }, {"details": "Custom fault injection", "confidence": 0.9}

fault_injector = FaultInjector()
