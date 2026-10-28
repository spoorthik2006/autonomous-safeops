from pathlib import Path
from typing import Dict, Any, List
from ruamel.yaml import YAML
from app.config import RUNBOOKS_DIR, POLICY_FILE

yaml_parser = YAML(typ="safe")

class RunbookRegistry:
    def __init__(self, runbooks_dir: Path = RUNBOOKS_DIR, policy_file: Path = POLICY_FILE):
        self.runbooks_dir = runbooks_dir
        self.policy_file = policy_file
        self._runbooks: Dict[str, Dict[str, Any]] = {}
        self._policy: Dict[str, Any] = {}
        self.reload()

    def reload(self):
        self._runbooks.clear()
        if self.runbooks_dir.exists():
            for file_path in self.runbooks_dir.glob("*.yaml"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml_parser.load(f)
                        if data and "id" in data:
                            self._runbooks[data["id"]] = data
                except Exception as e:
                    print(f"Error loading runbook {file_path}: {e}")

        if self.policy_file.exists():
            try:
                with open(self.policy_file, "r", encoding="utf-8") as f:
                    self._policy = yaml_parser.load(f) or {}
            except Exception as e:
                print(f"Error loading policy {self.policy_file}: {e}")

    def get_runbook(self, runbook_id: str) -> Dict[str, Any]:
        return self._runbooks.get(runbook_id)

    def list_runbooks(self) -> List[Dict[str, Any]]:
        return list(self._runbooks.values())

    def get_policy(self) -> Dict[str, Any]:
        return self._policy

    def get_raw_policy_yaml(self) -> str:
        if self.policy_file.exists():
            with open(self.policy_file, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def get_raw_runbook_yaml(self, runbook_id: str) -> str:
        if self.runbooks_dir.exists():
            for file_path in self.runbooks_dir.glob("*.yaml"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if f'id: "{runbook_id}"' in content or f"id: '{runbook_id}'" in content or f"id: {runbook_id}" in content:
                        return content
        return ""

runbook_registry = RunbookRegistry()
