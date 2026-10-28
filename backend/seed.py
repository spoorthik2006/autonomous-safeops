import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import asyncio
from app.database import engine, Base, SessionLocal
from app.models.safety import SafetyState
from app.api.routes_simulator import process_fault_injection
from app.engine.audit_chain import record_audit_event, verify_chain_integrity

async def seed_data():
    print("Initializing NightShift database schema...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Ensure Safety state
        safety = db.query(SafetyState).filter(SafetyState.id == 1).first()
        if not safety:
            safety = SafetyState(id=1, kill_switch_active=False)
            db.add(safety)
            db.commit()

        # Seed initial genesis audit event
        record_audit_event(
            db,
            event_type="SYSTEM_BOOTSTRAP",
            actor="SYSTEM_INIT",
            payload={"message": "NightShift autonomous safety engine initialized with active policy engine"}
        )

        print("Simulating 3 initial baseline events...")
        # 1. Routine log overflow (Auto-resolved)
        await process_fault_injection(db, "routine_log_overflow", host="host-01")

        # 2. Zombie processes (Auto-resolved)
        await process_fault_injection(db, "zombie_leak", host="host-02")

        # 3. Ambiguous core dump (Escalated)
        await process_fault_injection(db, "ambiguous_disk_full", host="host-03")

        # Verify integrity
        integrity = verify_chain_integrity(db)
        print(f"Audit chain verification: Valid={integrity.get('valid')}, Total={integrity.get('total_events')} events.")
        print("Database seed completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
