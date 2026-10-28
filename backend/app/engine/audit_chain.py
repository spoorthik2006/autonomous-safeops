import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent, compute_hash

GENESIS_HASH = "0" * 64

def get_latest_audit_hash(db: Session) -> str:
    latest = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
    return latest.curr_hash if latest else GENESIS_HASH

def record_audit_event(
    db: Session,
    event_type: str,
    incident_id: Optional[str] = None,
    service: Optional[str] = None,
    host: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    actor: str = "SYSTEM"
) -> AuditEvent:
    prev_hash = get_latest_audit_hash(db)
    now = datetime.now(timezone.utc)
    timestamp_str = now.isoformat()
    payload_json = json.dumps(payload or {}, sort_keys=True)
    curr_hash = compute_hash(prev_hash, timestamp_str, event_type, payload_json)

    event = AuditEvent(
        event_id=f"evt-{uuid.uuid4().hex[:12]}",
        timestamp_iso=timestamp_str,
        timestamp=now,
        event_type=event_type,
        incident_id=incident_id,
        service=service,
        host=host,
        actor=actor,
        payload_json=payload_json,
        prev_hash=prev_hash,
        curr_hash=curr_hash
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def verify_chain_integrity(db: Session) -> Dict[str, Any]:
    events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    if not events:
        return {
            "valid": True,
            "total_events": 0,
            "broken_at_id": None,
            "error": "Audit chain empty - pristine state"
        }

    expected_prev = GENESIS_HASH
    for ev in events:
        if ev.prev_hash != expected_prev:
            return {
                "valid": False,
                "total_events": len(events),
                "broken_at_id": ev.id,
                "error": f"Chain link broken at event #{ev.id}: prev_hash {ev.prev_hash} does not match expected {expected_prev}"
            }
        timestamp_str = ev.timestamp_iso or (ev.timestamp.isoformat() if ev.timestamp else "")
        recomputed = compute_hash(
            ev.prev_hash,
            timestamp_str,
            ev.event_type,
            ev.payload_json
        )
        if recomputed != ev.curr_hash:
            return {
                "valid": False,
                "total_events": len(events),
                "broken_at_id": ev.id,
                "error": f"Cryptographic integrity failure at event #{ev.id}: computed {recomputed} != recorded {ev.curr_hash}"
            }
        expected_prev = ev.curr_hash

    return {
        "valid": True,
        "total_events": len(events),
        "latest_hash": expected_prev,
        "broken_at_id": None,
        "error": None
    }

def export_audit_csv(db: Session) -> str:
    events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "event_id", "timestamp", "event_type", "incident_id",
        "service", "host", "actor", "payload", "prev_hash", "curr_hash"
    ])
    for e in events:
        writer.writerow([
            e.id, e.event_id, e.timestamp.isoformat() if e.timestamp else "",
            e.event_type, e.incident_id or "", e.service or "", e.host or "",
            e.actor, e.payload_json, e.prev_hash, e.curr_hash
        ])
    return output.getvalue()
