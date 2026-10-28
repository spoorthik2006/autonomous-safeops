#!/usr/bin/env python3
"""
NightShift - Single-Command Unified Application Launcher
Serves:
  1. Frontend Ops Dashboard at http://localhost:8000
  2. Interactive API Documentation at http://localhost:8000/docs
  3. Real-Time WebSocket at ws://localhost:8000/ws/events
  4. Built-in Backend Test Suite via CLI & API at http://localhost:8000/api/tests/run
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
TESTS_DIR = BASE_DIR / "tests"

def main():
    print("=" * 75)
    print("   NIGHTSHIFT - POLICY-GOVERNED AUTOMATED REMEDIATION ENGINE")
    print("   Problem AO-04: Automation that is safe enough to leave switched on")
    print("=" * 75)

    # 1. Run Comprehensive Test Suite First
    print("\n[Step 1/3] Running Backend Verification Test Suite (18 Safety Invariants)...")
    test_proc = subprocess.run([sys.executable, str(TESTS_DIR / "run_tests.py")])
    if test_proc.returncode != 0:
        print("\n[ERROR] Tests failed! Halting launch for safety.")
        sys.exit(1)

    # 2. Check / Seed Database
    db_file = BACKEND_DIR / "data" / "nightshift.db"
    if not db_file.exists():
        print("\n[Step 2/3] Seeding pristine baseline state into SQLite database...")
        seed_proc = subprocess.run([sys.executable, str(BACKEND_DIR / "seed.py")])
        if seed_proc.returncode != 0:
            print("\n[ERROR] Database seed failed!")
            sys.exit(1)
    else:
        print("\n[Step 2/3] Database verified and intact.")

    # 3. Verify Frontend Static Build
    dist_index = FRONTEND_DIR / "dist" / "index.html"
    if not dist_index.exists():
        print("\n[Building Frontend Production Bundle] Running npm run build...")
        subprocess.run(["npm", "run", "build"], cwd=str(FRONTEND_DIR), shell=True, check=True)

    print("\n[Step 3/3] Launching Unified Full-Stack Application on http://localhost:8000...")
    print("-" * 75)
    print("  * Frontend Ops Dashboard:     http://localhost:8000")
    print("  * Interactive API Docs:       http://localhost:8000/docs")
    print("  * Alternative ReDoc:          http://localhost:8000/redoc")
    print("  * Real-Time WebSocket:        ws://localhost:8000/ws/events")
    print("  * Run Backend Tests (API):    POST http://localhost:8000/api/tests/run")
    print("-" * 75)
    print("Press CTRL+C to halt.")

    # Run Uvicorn directly
    sys.path.insert(0, str(BACKEND_DIR))
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()
