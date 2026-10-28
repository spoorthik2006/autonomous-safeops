from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, Boolean, Text, DateTime
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class SafetyState(Base):
    __tablename__ = "safety_state"

    id = Column(Integer, primary_key=True) # Always 1
    kill_switch_active = Column(Boolean, default=False)
    kill_switch_engaged_at = Column(DateTime, nullable=True)
    kill_switch_reason = Column(Text, default="")
    paused_services_json = Column(Text, default="[]") # JSON list of paused service names
    max_hosts_per_action = Column(Integer, default=2)
    max_actions_per_hour = Column(Integer, default=5)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "kill_switch_active": self.kill_switch_active,
            "kill_switch_engaged_at": self.kill_switch_engaged_at.isoformat() if self.kill_switch_engaged_at else None,
            "kill_switch_reason": self.kill_switch_reason,
            "paused_services": json.loads(self.paused_services_json or "[]"),
            "max_hosts_per_action": self.max_hosts_per_action,
            "max_actions_per_hour": self.max_actions_per_hour,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
