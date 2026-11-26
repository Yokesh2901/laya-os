"""
Unit tests for LAYA OS Security Policy Engine.
"""

import pytest
from system.permissions.policy import SecurityPolicyEngine, ActionRiskLevel


def test_safe_action_allowed():
    policy = SecurityPolicyEngine()
    risk = policy.classify_action("get_system_stats")
    assert risk == ActionRiskLevel.SAFE

    authorized, msg = policy.validate_and_authorize("get_system_stats")
    assert authorized is True


def test_sensitive_action_requires_confirmation():
    policy = SecurityPolicyEngine(require_confirmation_for_sensitive=True)
    risk = policy.classify_action("system_poweroff")
    assert risk == ActionRiskLevel.SENSITIVE

    # Without confirmation -> denied
    authorized, msg = policy.validate_and_authorize("system_poweroff", confirmed_by_user=False)
    assert authorized is False
    assert "Confirmation Required" in msg

    # With confirmation -> approved
    authorized, msg = policy.validate_and_authorize("system_poweroff", confirmed_by_user=True)
    assert authorized is True


def test_forbidden_patterns_blocked():
    policy = SecurityPolicyEngine()
    risk = policy.classify_action("launch_application", {"app": "bash -c 'rm -rf /'"})
    assert risk == ActionRiskLevel.FORBIDDEN

    authorized, msg = policy.validate_and_authorize("launch_application", {"app": "rm -rf /"})
    assert authorized is False


def test_unlisted_action_denied():
    policy = SecurityPolicyEngine()
    risk = policy.classify_action("arbitrary_unknown_shell_hack")
    assert risk == ActionRiskLevel.FORBIDDEN
    authorized, msg = policy.validate_and_authorize("arbitrary_unknown_shell_hack")
    assert authorized is False
