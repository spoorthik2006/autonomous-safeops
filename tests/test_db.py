from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import Base
from app.models.safety import SafetyState

def create_test_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    safety = SafetyState(
        id=1,
        kill_switch_active=False,
        max_hosts_per_action=2,
        max_actions_per_hour=5,
        paused_services_json="[]"
    )
    db.add(safety)
    db.commit()
    return db
