from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    service = Column(String(100), nullable=False, index=True)
    host = Column(String(100), nullable=False, index=True)
    trigger_type = Column(String(100), nullable=False)
    status = Column(String(50), default="DETECTED", index=True)
    risk_tier = Column(Integer, default=1)
    decision = Column(String(50), default="EVALUATING")
    decision_reason = Column(Text, default="")
    runbook_id = Column(String(100), nullable=True)
    diagnostic_details = Column(Text, default="{}") # JSON
    snapshot_data = Column(Text, default="{}")       # JSON
    execution_details = Column(Text, default="{}")   # JSON
    rollback_status = Column(String(50), default="NONE") # NONE, PENDING, EXECUTED, FAILED
    rollback_reason = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "service": self.service,
            "host": self.host,
            "trigger_type": self.trigger_type,
            "status": self.status,
            "risk_tier": self.risk_tier,
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "runbook_id": self.runbook_id,
            "diagnostic_details": json.loads(self.diagnostic_details or "{}"),
            "snapshot_data": json.loads(self.snapshot_data or "{}"),
            "execution_details": json.loads(self.execution_details or "{}"),
            "rollback_status": self.rollback_status,
            "rollback_reason": self.rollback_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
