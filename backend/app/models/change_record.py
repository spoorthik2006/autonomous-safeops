from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class ChangeRecord(Base):
    __tablename__ = "change_records"

    id = Column(String(50), primary_key=True, index=True) # CHG-YYYY-XXXX
    incident_id = Column(String(50), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    service = Column(String(100), nullable=False, index=True)
    host = Column(String(100), nullable=False)
    change_type = Column(String(50), default="STANDARD") # STANDARD (Tier 0/1), NORMAL (Tier 2 Approved), EMERGENCY
    trigger_reason = Column(Text, nullable=False)
    risk_tier = Column(Integer, default=1)
    approver_type = Column(String(50), default="POLICY_ENGINE") # POLICY_ENGINE, HUMAN
    approver_name = Column(String(100), default="PolicyEngine/Autonomous")
    planned_actions = Column(Text, default="[]")
    execution_result = Column(String(50), default="SUCCESS") # SUCCESS, ROLLED_BACK, FAILED
    verification_outcome = Column(Text, default="Verified within nominal operating thresholds")
    rollback_executed = Column(Boolean, default=False)
    rollback_details = Column(Text, default="None")
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "title": self.title,
            "service": self.service,
            "host": self.host,
            "change_type": self.change_type,
            "trigger_reason": self.trigger_reason,
            "risk_tier": self.risk_tier,
            "approver_type": self.approver_type,
            "approver_name": self.approver_name,
            "planned_actions": json.loads(self.planned_actions or "[]"),
            "execution_result": self.execution_result,
            "verification_outcome": self.verification_outcome,
            "rollback_executed": self.rollback_executed,
            "rollback_details": self.rollback_details,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
