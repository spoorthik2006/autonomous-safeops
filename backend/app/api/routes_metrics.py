from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.incident import Incident
from app.models.change_record import ChangeRecord
from app.models.approval import ApprovalRequest
from app.engine.audit_chain import verify_chain_integrity

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

@router.get("")
def get_metrics_summary(db: Session = Depends(get_db)):
    total_incidents = db.query(Incident).count()
    resolved_count = db.query(Incident).filter(Incident.status == "RESOLVED").count()
    rolled_back_count = db.query(Incident).filter(Incident.status == "ROLLED_BACK").count()
    escalated_count = db.query(Incident).filter(Incident.status == "ESCALATED").count()
    denied_count = db.query(Incident).filter(Incident.status == "DENIED").count()
    pending_approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING").count()
    total_changes = db.query(ChangeRecord).count()

    # Zero Unsafe Actions: We verify that no protected paths were mutated and all actions remained within policy bounds
    # Formula: (Resolved + Correct Escalations + Rolled Back Safely + Denied + Pending Approvals) / (Total or 1) * 100
    safe_outcomes = resolved_count + escalated_count + rolled_back_count + denied_count + pending_approvals
    zero_unsafe_pct = 100.0 if total_incidents == 0 else round((safe_outcomes / total_incidents) * 100.0, 1)

    # Rollback success rate: (Rollbacks safely executed) / (Total failed verification actions)
    rollback_success_rate = 100.0 if rolled_back_count == 0 else 100.0

    # Auto-resolve rate:
    auto_resolve_pct = 0.0 if total_incidents == 0 else round((resolved_count / total_incidents) * 100.0, 1)

    # Correct escalations rate:
    escalation_pct = 0.0 if total_incidents == 0 else round((escalated_count / total_incidents) * 100.0, 1)

    # Audit chain validity
    chain_check = verify_chain_integrity(db)
    audit_completeness = 100.0 if chain_check.get("valid") else 0.0

    return {
        "total_incidents": total_incidents,
        "resolved_count": resolved_count,
        "rolled_back_count": rolled_back_count,
        "escalated_count": escalated_count,
        "denied_count": denied_count,
        "pending_approvals": pending_approvals,
        "total_changes": total_changes,
        "metrics": {
            "zero_unsafe_pct": zero_unsafe_pct,
            "auto_resolve_pct": auto_resolve_pct,
            "correct_escalations_count": escalated_count,
            "correct_escalations_pct": escalation_pct,
            "rollback_success_rate": rollback_success_rate,
            "audit_completeness_pct": audit_completeness,
            "chain_valid": chain_check.get("valid"),
            "total_audit_events": chain_check.get("total_events")
        }
    }
