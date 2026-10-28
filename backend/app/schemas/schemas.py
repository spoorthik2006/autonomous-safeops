from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class KillSwitchRequest(BaseModel):
    active: bool
    reason: Optional[str] = "Manual operator intervention"

class PauseServiceRequest(BaseModel):
    service: str
    paused: bool

class ApprovalDecisionRequest(BaseModel):
    decision: str # "APPROVE" or "REJECT"
    approver: str = "ops-lead"
    rationale: Optional[str] = "Approved after reviewing blast radius and rollback plan"

class ManualRollbackRequest(BaseModel):
    reason: Optional[str] = "Operator initiated manual rollback"

class FaultInjectionRequest(BaseModel):
    fault_type: str # e.g. "log_overflow", "ambiguous_disk", "protected_path", "stuck_worker", "failed_fix_worker", "queue_backlog", "cert_expiring", "db_pool_leak", "cache_herd", "zombie_leak", "kill_switch_test"
    host: Optional[str] = "host-01"
    service: Optional[str] = None
    custom_params: Optional[Dict[str, Any]] = None

class IncidentFilter(BaseModel):
    status: Optional[str] = None
    service: Optional[str] = None
    risk_tier: Optional[int] = None
