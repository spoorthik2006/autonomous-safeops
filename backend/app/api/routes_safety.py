from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.safety import SafetyState
from app.schemas.schemas import KillSwitchRequest, PauseServiceRequest
from app.engine.audit_chain import record_audit_event
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/api/safety", tags=["Safety"])

def get_or_create_safety_state(db: Session) -> SafetyState:
    state = db.query(SafetyState).filter(SafetyState.id == 1).first()
    if not state:
        state = SafetyState(id=1, kill_switch_active=False)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state

@router.get("")
def get_safety_status(db: Session = Depends(get_db)):
    state = get_or_create_safety_state(db)
    return state.to_dict()

@router.post("/kill-switch")
async def toggle_kill_switch(payload: KillSwitchRequest, db: Session = Depends(get_db)):
    state = get_or_create_safety_state(db)
    state.kill_switch_active = payload.active
    state.kill_switch_reason = payload.reason
    state.kill_switch_engaged_at = datetime.now(timezone.utc) if payload.active else None
    db.commit()
    db.refresh(state)

    event_type = "KILL_SWITCH_ENGAGED" if payload.active else "KILL_SWITCH_DISENGAGED"
    record_audit_event(
        db,
        event_type=event_type,
        actor="OPS_DIRECTOR",
        payload={"active": payload.active, "reason": payload.reason}
    )

    await ws_manager.broadcast({
        "event": "SAFETY_UPDATED",
        "data": state.to_dict()
    })

    return {"success": True, "safety_state": state.to_dict()}

@router.post("/pause-service")
async def toggle_pause_service(payload: PauseServiceRequest, db: Session = Depends(get_db)):
    state = get_or_create_safety_state(db)
    paused = json.loads(state.paused_services_json or "[]")
    
    if payload.paused:
        if payload.service not in paused:
            paused.append(payload.service)
    else:
        if payload.service in paused:
            paused.remove(payload.service)
            
    state.paused_services_json = json.dumps(paused)
    db.commit()
    db.refresh(state)

    event_type = "SERVICE_PAUSED" if payload.paused else "SERVICE_RESUMED"
    record_audit_event(
        db,
        event_type=event_type,
        service=payload.service,
        actor="OPS_ENGINEER",
        payload={"service": payload.service, "paused": payload.paused}
    )

    await ws_manager.broadcast({
        "event": "SAFETY_UPDATED",
        "data": state.to_dict()
    })

    return {"success": True, "safety_state": state.to_dict()}
