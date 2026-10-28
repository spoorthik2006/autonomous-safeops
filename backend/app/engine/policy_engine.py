from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.safety import SafetyState
from app.models.change_record import ChangeRecord
from app.config import (
    DEFAULT_MAX_HOSTS_PER_ACTION,
    DEFAULT_MAX_ACTIONS_PER_HOUR,
    VALID_CREDENTIAL_TOKENS
)
from app.engine.runbook_loader import runbook_registry

class PolicyDecision:
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    ESCALATE = "ESCALATE"

class PolicyEngine:
    def __init__(self):
        pass

    def evaluate(
        self,
        db: Session,
        incident: Dict[str, Any],
        diagnostics: Dict[str, Any],
        token_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates policy rules, blast radius, safety controls, and judgment logic.
        Returns:
            {
                "decision": "ALLOW" | "REQUIRE_APPROVAL" | "DENY" | "ESCALATE",
                "reason": str,
                "rule_name": str,
                "risk_tier": int,
                "scope_valid": bool,
                "blast_radius_ok": bool,
                "kill_switch_active": bool
            }
        """
        # 1. Check Global Kill-Switch & Paused Services
        safety = db.query(SafetyState).first()
        if not safety:
            safety = SafetyState(id=1, kill_switch_active=False)
            db.add(safety)
            db.commit()
            db.refresh(safety)

        safety_dict = safety.to_dict()
        if safety_dict.get("kill_switch_active"):
            return {
                "decision": PolicyDecision.DENY,
                "reason": f"HALTED: Global kill-switch is ENGAGED ({safety_dict.get('kill_switch_reason', 'Manual trigger')}). All automated actions blocked.",
                "rule_name": "GLOBAL_KILL_SWITCH_ACTIVE",
                "risk_tier": 3,
                "scope_valid": True,
                "blast_radius_ok": False,
                "kill_switch_active": True
            }

        service = incident.get("service", "")
        if service in safety_dict.get("paused_services", []):
            return {
                "decision": PolicyDecision.DENY,
                "reason": f"HALTED: Service '{service}' is temporarily PAUSED by operator. No remediation permitted.",
                "rule_name": "SERVICE_PAUSED",
                "risk_tier": 2,
                "scope_valid": True,
                "blast_radius_ok": False,
                "kill_switch_active": False
            }

        # 2. Check Protected Targets (Tier 3 strict DENY)
        target_path = diagnostics.get("target_path", "")
        protected_paths = ["/etc", "/boot", "/etc/sudoers", "/etc/passwd"]
        if any(target_path.startswith(p) for p in protected_paths) or service == "prod-db-primary":
            return {
                "decision": PolicyDecision.DENY,
                "reason": f"STRICT DENY (Tier 3 Protected Surface): Target path '{target_path}' or service '{service}' is strictly protected. Automated mutation is forbidden.",
                "rule_name": "PROTECTED_TARGET_TIER_3",
                "risk_tier": 3,
                "scope_valid": False,
                "blast_radius_ok": False,
                "kill_switch_active": False
            }

        # 3. Judgment Logic: Ambiguity & Cause Analysis
        trigger_type = incident.get("trigger_type", "")
        cause = diagnostics.get("cause", "")
        confidence = diagnostics.get("confidence", 1.0)

        if trigger_type == "disk_full":
            if cause == "core_dump" or "/data/core" in target_path:
                return {
                    "decision": PolicyDecision.ESCALATE,
                    "reason": "ESCALATE (Ambiguity & Safety Guard): Disk saturation is driven by crash core dumps (/data/core). Purging core dumps destroys vital diagnostic evidence of an unhandled panic. Human triage required.",
                    "rule_name": "JUDGMENT_CORE_DUMP_ESCALATE",
                    "risk_tier": 3,
                    "scope_valid": True,
                    "blast_radius_ok": True,
                    "kill_switch_active": False
                }
            elif cause == "unknown" or confidence < 0.80:
                return {
                    "decision": PolicyDecision.ESCALATE,
                    "reason": f"ESCALATE (Ambiguity Guard): Root cause of disk spike is unclassified (confidence: {confidence:.2f}). NightShift never guesses or removes unknown files. Escalate to human engineer.",
                    "rule_name": "JUDGMENT_AMBIGUOUS_CAUSE_ESCALATE",
                    "risk_tier": 2,
                    "scope_valid": True,
                    "blast_radius_ok": True,
                    "kill_switch_active": False
                }

        # 4. Runbook Lookup & Credential Scope Validation
        runbook_id = incident.get("runbook_id")
        runbook = runbook_registry.get_runbook(runbook_id)
        if not runbook:
            return {
                "decision": PolicyDecision.DENY,
                "reason": f"DENY: No approved runbook registered for ID '{runbook_id}'.",
                "rule_name": "UNKNOWN_RUNBOOK",
                "risk_tier": 3,
                "scope_valid": False,
                "blast_radius_ok": False,
                "kill_switch_active": False
            }

        required_scope = runbook.get("required_credential_scope")
        token_to_check = token_id or f"token-{required_scope.split(':')[0]}-{required_scope.split(':')[1] if ':' in required_scope else 'op'}"
        
        # Validate scoped mock token
        token_info = VALID_CREDENTIAL_TOKENS.get(token_to_check)
        if token_id and (not token_info or required_scope not in token_info.get("scopes", [])):
            return {
                "decision": PolicyDecision.DENY,
                "reason": f"DENY: Least-privilege violation. Credential token '{token_id}' lacks required scope '{required_scope}'.",
                "rule_name": "LEAST_PRIVILEGE_SCOPE_MISMATCH",
                "risk_tier": 3,
                "scope_valid": False,
                "blast_radius_ok": False,
                "kill_switch_active": False
            }

        # 5. Blast-Radius & Service Rate Limiting Checks
        max_hosts = safety_dict.get("max_hosts_per_action", DEFAULT_MAX_HOSTS_PER_ACTION)
        rb_hosts = runbook.get("blast_radius", {}).get("max_hosts", 1)
        if rb_hosts > max_hosts:
            return {
                "decision": PolicyDecision.DENY,
                "reason": f"DENY: Blast-radius limit breached. Action targets {rb_hosts} hosts simultaneously, exceeding system limit of {max_hosts}.",
                "rule_name": "BLAST_RADIUS_MAX_HOSTS_EXCEEDED",
                "risk_tier": 2,
                "scope_valid": True,
                "blast_radius_ok": False,
                "kill_switch_active": False
            }

        # Check hourly rate limit for service
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_actions_count = db.query(ChangeRecord).filter(
            ChangeRecord.service == service,
            ChangeRecord.created_at >= one_hour_ago
        ).count()
        
        max_actions = safety_dict.get("max_actions_per_hour", DEFAULT_MAX_ACTIONS_PER_HOUR)
        if recent_actions_count >= max_actions:
            return {
                "decision": PolicyDecision.DENY,
                "reason": f"DENY: Rate limit breached for service '{service}'. {recent_actions_count} changes executed in past hour (limit is {max_actions}/hr). Cooldown required.",
                "rule_name": "SERVICE_RATE_LIMIT_EXCEEDED",
                "risk_tier": 2,
                "scope_valid": True,
                "blast_radius_ok": False,
                "kill_switch_active": False
            }

        # 6. Risk Tier Evaluation
        risk_tier = runbook.get("risk_tier", 1)

        # Tier 0: Auto-run
        if risk_tier == 0:
            return {
                "decision": PolicyDecision.ALLOW,
                "reason": f"ALLOW (Tier 0 Autonomous Safe): Action '{runbook.get('name')}' is verified benign, isolated, and within blast-radius boundaries. Executing auto-remediation.",
                "rule_name": "TIER_0_AUTO_ALLOW",
                "risk_tier": 0,
                "scope_valid": True,
                "blast_radius_ok": True,
                "kill_switch_active": False
            }

        # Tier 1: Auto-run with rate limit
        elif risk_tier == 1:
            return {
                "decision": PolicyDecision.ALLOW,
                "reason": f"ALLOW (Tier 1 Autonomous with Telemetry): Action '{runbook.get('name')}' approved under rate limit ({recent_actions_count}/{max_actions} actions used). Automatic snapshot & verification enabled.",
                "rule_name": "TIER_1_AUTO_ALLOW",
                "risk_tier": 1,
                "scope_valid": True,
                "blast_radius_ok": True,
                "kill_switch_active": False
            }

        # Tier 2: Needs Human Approval
        elif risk_tier == 2:
            return {
                "decision": PolicyDecision.REQUIRE_APPROVAL,
                "reason": f"REQUIRE_APPROVAL (Tier 2 High-Impact Action): Action '{runbook.get('name')}' modifies production state. Mandatory human review required with rollback plan sign-off.",
                "rule_name": "TIER_2_APPROVAL_MANDATORY",
                "risk_tier": 2,
                "scope_valid": True,
                "blast_radius_ok": True,
                "kill_switch_active": False
            }

        # Tier 3: Never Touch
        else:
            return {
                "decision": PolicyDecision.DENY,
                "reason": f"DENY (Tier 3 Protected Surface): Action '{runbook.get('name')}' flagged as Tier 3 irreversible risk. Automation strictly blocked.",
                "rule_name": "TIER_3_STRICT_DENY",
                "risk_tier": 3,
                "scope_valid": False,
                "blast_radius_ok": False,
                "kill_switch_active": False
            }

policy_engine = PolicyEngine()
