from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base, SessionLocal
from app.models.safety import SafetyState
from app.websocket_manager import ws_manager
from app.engine.runbook_loader import runbook_registry
from app.api import (
    routes_incidents,
    routes_approvals,
    routes_safety,
    routes_runbooks,
    routes_simulator,
    routes_audit,
    routes_metrics,
    routes_tests
)

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    Base.metadata.create_all(bind=engine)

    # Ensure default Safety State row exists
    db = SessionLocal()
    try:
        safety = db.query(SafetyState).filter(SafetyState.id == 1).first()
        if not safety:
            safety = SafetyState(
                id=1,
                kill_switch_active=False,
                max_hosts_per_action=2,
                max_actions_per_hour=5,
                paused_services_json="[]"
            )
            db.add(safety)
            db.commit()
    finally:
        db.close()

    # Preload runbooks
    runbook_registry.reload()
    yield

app = FastAPI(
    title="NightShift Policy-Governed Remediation Engine",
    description="Problem AO-04: Automation that is safe enough to leave switched on. Unified single-build service delivering the Frontend Ops Dashboard, Interactive API Docs, WebSocket Real-Time Stream, and Backend Tests in one package.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(routes_incidents.router)
app.include_router(routes_approvals.router)
app.include_router(routes_safety.router)
app.include_router(routes_runbooks.router)
app.include_router(routes_simulator.router)
app.include_router(routes_audit.router)
app.include_router(routes_metrics.router)
app.include_router(routes_tests.router)

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "NightShift Unified App",
        "runbooks_loaded": len(runbook_registry.list_runbooks()),
        "frontend_mounted": FRONTEND_DIST.exists(),
        "websocket_endpoint": "/ws/events",
        "api_docs_endpoint": "/docs"
    }

@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keepalive listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event": "pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# Mount Frontend SPA static build
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa_fallback(full_path: str):
        # Let API routes pass through if unmatched
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return None
        candidate = FRONTEND_DIST / full_path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
