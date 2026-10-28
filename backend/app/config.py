import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

DB_PATH = DATA_DIR / "nightshift.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

RUNBOOKS_DIR = BASE_DIR / "app" / "runbooks"
POLICY_FILE = BASE_DIR / "app" / "policy.yaml"

# Default Safety Configuration
DEFAULT_MAX_HOSTS_PER_ACTION = 2
DEFAULT_MAX_ACTIONS_PER_HOUR = 5

# Scoped mock tokens for least privilege
VALID_CREDENTIAL_TOKENS = {
    "token-disk-clean": {"service": "system-agent", "scopes": ["disk:clean_logs", "disk:clean_tmp"]},
    "token-worker-restart": {"service": "worker-manager", "scopes": ["worker:restart", "process:reap"]},
    "token-queue-scale": {"service": "k8s-autoscaler", "scopes": ["queue:scale"]},
    "token-cert-rotate": {"service": "cert-manager", "scopes": ["cert:rotate"]},
    "token-cache-flush": {"service": "cache-operator", "scopes": ["cache:flush"]},
    "token-db-pool": {"service": "dba-agent", "scopes": ["db:pool_reset"]},
    "token-cron-retry": {"service": "cron-scheduler", "scopes": ["cron:retry"]},
    "token-service-restart": {"service": "deploy-controller", "scopes": ["service:restart"]},
    "token-read-only": {"service": "read-only-monitor", "scopes": ["disk:read_only", "health:read"]}
}
