from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.incident import Incident
from app.models.audit import AuditEvent
from app.models.change_record import ChangeRecord
from app.schemas.schemas import ManualRollbackRequest
from app.engine.execution_engine import execution_engine
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

@router.get("")
def list_incidents(
    status: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    risk_tier: Optional[int] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if service:
        query = query.filter(Incident.service == service)
    if risk_tier is not None:
        query = query.filter(Incident.risk_tier == risk_tier)
    
    incidents = query.order_by(Incident.created_at.desc()).limit(limit).all()
    return [i.to_dict() for i in incidents]

@router.get("/{incident_id}")
def get_incident_detail(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Fetch all audit events for this incident to construct the explainability timeline
    audit_events = db.query(AuditEvent).filter(
        AuditEvent.incident_id == incident_id
    ).order_by(AuditEvent.id.asc()).all()

    # Associated change record if any
    change = db.query(ChangeRecord).filter(ChangeRecord.incident_id == incident_id).first()

    return {
        "incident": inc.to_dict(),
        "timeline": [ev.to_dict() for ev in audit_events],
        "change_record": change.to_dict() if change else None,
        "explainability": {
            "summary": inc.decision_reason,
            "decision": inc.decision,
            "risk_tier": inc.risk_tier,
            "can_rollback": inc.snapshot_data != "{}" and inc.status in ["RESOLVED", "VERIFYING", "EXECUTING"]
        }
    }

@router.post("/{incident_id}/rollback")
async def trigger_manual_rollback(
    incident_id: str,
    payload: ManualRollbackRequest,
    db: Session = Depends(get_db)
):
    result = execution_engine.manual_rollback(
        db=db,
        incident_id=incident_id,
        operator_name="ops-engineer",
        reason=payload.reason or "Manual rollback requested via dashboard"
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    await ws_manager.broadcast({
        "event": "INCIDENT_UPDATED",
        "data": inc.to_dict() if inc else {}
    })

    return result
