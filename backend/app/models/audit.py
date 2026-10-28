from datetime import datetime, timezone
import hashlib
import json
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

def compute_hash(prev_hash: str, timestamp_str: str, event_type: str, payload_str: str) -> str:
    raw = f"{prev_hash}|{timestamp_str}|{event_type}|{payload_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, index=True)
    timestamp_iso = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=utcnow, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    incident_id = Column(String(50), nullable=True, index=True)
    service = Column(String(100), nullable=True)
    host = Column(String(100), nullable=True)
    actor = Column(String(100), default="SYSTEM")
    payload_json = Column(Text, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    curr_hash = Column(String(64), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp_iso or (self.timestamp.isoformat() if self.timestamp else None),
            "event_type": self.event_type,
            "incident_id": self.incident_id,
            "service": self.service,
            "host": self.host,
            "actor": self.actor,
            "payload": json.loads(self.payload_json or "{}"),
            "prev_hash": self.prev_hash,
            "curr_hash": self.curr_hash,
        }
