from fastapi import APIRouter, HTTPException
from app.engine.runbook_loader import runbook_registry

router = APIRouter(prefix="/api/runbooks", tags=["Runbooks & Policy"])

@router.get("")
def list_runbooks():
    return runbook_registry.list_runbooks()

@router.get("/{runbook_id}")
def get_runbook(runbook_id: str):
    rb = runbook_registry.get_runbook(runbook_id)
    if not rb:
        raise HTTPException(status_code=404, detail="Runbook not found")
    raw = runbook_registry.get_raw_runbook_yaml(runbook_id)
    return {
        "metadata": rb,
        "raw_yaml": raw
    }

@router.get("/policy/all")
def get_policy():
    policy = runbook_registry.get_policy()
    raw = runbook_registry.get_raw_policy_yaml()
    return {
        "policy": policy,
        "raw_yaml": raw
    }
