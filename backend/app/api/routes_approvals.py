from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.approval import ApprovalRequest
from app.models.incident import Incident
from app.schemas.schemas import ApprovalDecisionRequest
from app.engine.execution_engine import execution_engine
from app.engine.audit_chain import record_audit_event
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

@router.get("")
def list_approvals(
    status: Optional[str] = Query(None), # PENDING, APPROVED, REJECTED
    db: Session = Depends(get_db)
):
    query = db.query(ApprovalRequest)
    if status:
        query = query.filter(ApprovalRequest.status == status)
    approvals = query.order_by(ApprovalRequest.created_at.desc()).all()
    return [a.to_dict() for a in approvals]

@router.post("/{approval_id}/decide")
async def decide_approval(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db)
):
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if req.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Request is already decided ({req.status})")

    inc = db.query(Incident).filter(Incident.id == req.incident_id).first()
    now = datetime.now(timezone.utc)

    if payload.decision.upper() == "APPROVE":
        req.status = "APPROVED"
        req.approver = payload.approver
        req.approval_rationale = payload.rationale
        req.decided_at = now
        db.commit()

        record_audit_event(
            db,
            event_type="APPROVAL_DECIDED",
            incident_id=req.incident_id,
            service=req.service,
            host=req.host,
            actor=payload.approver,
            payload={
                "decision": "APPROVED",
                "approval_id": req.id,
                "rationale": payload.rationale
            }
        )

        # Trigger safe execution engine with human approver signature
        exec_result = execution_engine.execute_remediation(
            db=db,
            incident_id=req.incident_id,
            approver_name=payload.approver,
            approver_type="HUMAN"
        )

        await ws_manager.broadcast({
            "event": "APPROVAL_DECIDED",
            "data": req.to_dict()
        })
        if inc:
            await ws_manager.broadcast({
                "event": "INCIDENT_UPDATED",
                "data": inc.to_dict()
            })

        return {
            "success": True,
            "decision": "APPROVED",
            "execution": exec_result,
            "approval": req.to_dict()
        }

    else:
        req.status = "REJECTED"
        req.approver = payload.approver
        req.rejection_reason = payload.rationale
        req.decided_at = now
        if inc:
            inc.status = "DENIED"
            inc.decision_reason = f"Rejected by approver {payload.approver}: {payload.rationale}"
        db.commit()

        record_audit_event(
            db,
            event_type="APPROVAL_DECIDED",
            incident_id=req.incident_id,
            service=req.service,
            host=req.host,
            actor=payload.approver,
            payload={
                "decision": "REJECTED",
                "approval_id": req.id,
                "rationale": payload.rationale
            }
        )

        await ws_manager.broadcast({
            "event": "APPROVAL_DECIDED",
            "data": req.to_dict()
        })
        if inc:
            await ws_manager.broadcast({
                "event": "INCIDENT_UPDATED",
                "data": inc.to_dict()
            })

        return {
            "success": True,
            "decision": "REJECTED",
            "approval": req.to_dict()
        }
