"""
LAYA OS - System Security & Permission Policy Engine
Enforces least-privilege action dispatching and user confirmation for sensitive tasks.
"""

from enum import Enum
from typing import Dict, Any, Tuple, Optional, Set
import logging

logger = logging.getLogger("laya.security")


class ActionRiskLevel(Enum):
    SAFE = "safe"
    SENSITIVE = "sensitive"
    FORBIDDEN = "forbidden"


class SecurityPolicyEngine:
    """
    Security validator for system actions requested by Laya AI Core or user apps.
    Guarantees no arbitrary shell execution and mandates confirmation for destructive tasks.
    """

    SAFE_ACTIONS: Set[str] = {
        "get_system_stats",
        "get_audio_volume",
        "set_audio_volume",
        "set_audio_mute",
        "get_brightness",
        "set_brightness",
        "list_applications",
        "launch_application",
        "search_files",
        "get_active_window",
        "close_active_window",
    }

    SENSITIVE_ACTIONS: Set[str] = {
        "system_poweroff",
        "system_reboot",
        "system_lock",
        "system_suspend",
        "kill_process",
        "delete_file",
        "modify_network_connection",
    }

    FORBIDDEN_PATTERNS: Set[str] = {
        "rm -rf",
        "mkfs",
        "dd if=",
        ":(){ :|:& };:",
        "chmod -R 777",
        "> /dev/sd",
        "wget http",
        "curl http",
    }

    def __init__(self, require_confirmation_for_sensitive: bool = True):
        self.require_confirmation_for_sensitive = require_confirmation_for_sensitive

    def classify_action(self, action_name: str, params: Optional[Dict[str, Any]] = None) -> ActionRiskLevel:
        """Determines risk level of a requested action."""
        if not action_name or not isinstance(action_name, str):
            return ActionRiskLevel.FORBIDDEN

        clean_name = action_name.strip().lower()

        # Check for forbidden patterns in any string argument
        if params and isinstance(params, dict):
            for key, val in params.items():
                if isinstance(val, str):
                    val_lower = val.lower()
                    for pattern in self.FORBIDDEN_PATTERNS:
                        if pattern in val_lower:
                            logger.warning(f"[Security] Blocked forbidden pattern '{pattern}' in param '{key}'")
                            return ActionRiskLevel.FORBIDDEN

        if clean_name in self.SAFE_ACTIONS:
            return ActionRiskLevel.SAFE

        if clean_name in self.SENSITIVE_ACTIONS:
            return ActionRiskLevel.SENSITIVE

        logger.warning(f"[Security] Action '{action_name}' is not in allowlist. Denying execution.")
        return ActionRiskLevel.FORBIDDEN

    def validate_and_authorize(self, action_name: str, params: Optional[Dict[str, Any]] = None, confirmed_by_user: bool = False) -> Tuple[bool, str]:
        """
        Validates action against security rules.
        Returns (is_authorized, reason_or_status).
        """
        risk = self.classify_action(action_name, params)

        if risk == ActionRiskLevel.FORBIDDEN:
            return False, f"Action '{action_name}' is prohibited by LAYA OS security policy."

        if risk == ActionRiskLevel.SAFE:
            return True, "Authorized: safe operation."

        if risk == ActionRiskLevel.SENSITIVE:
            if not self.require_confirmation_for_sensitive or confirmed_by_user:
                return True, "Authorized: sensitive operation confirmed by user."
            return False, f"Confirmation Required: '{action_name}' is a sensitive system action."

        return False, "Unauthorized: Unknown security state."
