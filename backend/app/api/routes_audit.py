from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit import AuditEvent
from app.models.change_record import ChangeRecord
from app.engine.audit_chain import verify_chain_integrity, export_audit_csv

router = APIRouter(prefix="/api/audit", tags=["Audit & Change Records"])

@router.get("")
def list_audit_events(
    event_type: Optional[str] = Query(None),
    incident_id: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if incident_id:
        query = query.filter(AuditEvent.incident_id == incident_id)
    if service:
        query = query.filter(AuditEvent.service == service)

    events = query.order_by(AuditEvent.id.desc()).limit(limit).all()
    return [e.to_dict() for e in events]

@router.get("/verify")
def verify_audit_chain(db: Session = Depends(get_db)):
    """
    Cryptographically verifies the SHA-256 append-only chain for every recorded event.
    """
    result = verify_chain_integrity(db)
    return result

@router.get("/export/json")
def export_audit_json(db: Session = Depends(get_db)):
    events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    return [e.to_dict() for e in events]

@router.get("/export/csv")
def export_audit_csv_endpoint(db: Session = Depends(get_db)):
    csv_data = export_audit_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nightshift_audit_ledger.csv"}
    )

@router.get("/changes")
def list_change_records(
    service: Optional[str] = Query(None),
    change_type: Optional[str] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    query = db.query(ChangeRecord)
    if service:
        query = query.filter(ChangeRecord.service == service)
    if change_type:
        query = query.filter(ChangeRecord.change_type == change_type)

    changes = query.order_by(ChangeRecord.created_at.desc()).limit(limit).all()
    return [c.to_dict() for c in changes]

@router.get("/changes/{change_id}")
def get_change_record_detail(change_id: str, db: Session = Depends(get_db)):
    change = db.query(ChangeRecord).filter(ChangeRecord.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change record not found")
    return change.to_dict()
