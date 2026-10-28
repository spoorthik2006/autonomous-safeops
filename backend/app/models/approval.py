from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class ApprovalRequest(Base):
    __tablename__ = "approvals"

    id = Column(String(50), primary_key=True, index=True)
    incident_id = Column(String(50), ForeignKey("incidents.id"), nullable=False, index=True)
    runbook_id = Column(String(100), nullable=False)
    service = Column(String(100), nullable=False)
    host = Column(String(100), nullable=False)
    proposed_action = Column(String(255), nullable=False)
    action_steps_json = Column(Text, default="[]")
    risk_tier = Column(Integer, default=2)
    blast_radius_summary = Column(Text, default="")
    rollback_plan_summary = Column(Text, default="")
    status = Column(String(50), default="PENDING", index=True) # PENDING, APPROVED, REJECTED, EXECUTED
    approver = Column(String(100), nullable=True)
    approval_rationale = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    decided_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "runbook_id": self.runbook_id,
            "service": self.service,
            "host": self.host,
            "proposed_action": self.proposed_action,
            "action_steps": json.loads(self.action_steps_json or "[]"),
            "risk_tier": self.risk_tier,
            "blast_radius_summary": self.blast_radius_summary,
            "rollback_plan_summary": self.rollback_plan_summary,
            "status": self.status,
            "approver": self.approver,
            "approval_rationale": self.approval_rationale,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }
