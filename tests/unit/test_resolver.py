from __future__ import annotations

import copy

import pytest

from model_router import (
    IntegrityError,
    ResolutionError,
    build_resolution_record,
    replay_resolution,
    resolve,
    serialize,
    verify_record_integrity,
)


def registry() -> dict[str, object]:
    return {
        "version": "test-1",
        "sources": [
            {
                "id": "local-reviewer",
                "provider": "local-runtime",
                "model": "reviewer",
                "privacy_boundary": "local",
                "residency_boundary": "local",
                "capabilities": ["reasoning", "code_review"],
                "context_tokens": 32768,
                "quality_tier": "reviewer",
                "cost_class": "free",
            },
            {
                "id": "cloud-reviewer",
                "provider": "example-cloud",
                "model": "reviewer",
                "privacy_boundary": "trusted_cloud",
                "residency_boundary": "ca",
                "remote_allowance": {
                    "allowed": True,
                    "requires_approval": True,
                    "allowed_privacy_classes": ["trusted_cloud_ok", "public_cloud_ok"],
                    "evidence_required": ["approval", "data_classification"],
                },
                "capabilities": ["reasoning", "code_review", "long_context"],
                "context_tokens": 128000,
                "quality_tier": "reviewer",
                "cost_class": "medium",
            },
        ],
    }


def request(request_id: str = "r1") -> dict[str, object]:
    return {
        "request_id": request_id,
        "timestamp": "2026-01-01T00:00:00Z",
        "task": "code_review",
        "required_capabilities": ["reasoning", "code_review"],
        "context_estimate": {"input_tokens": 1000, "max_output_tokens": 500},
        "cost_preference": "prefer_free",
    }


def local_constraints(request_id: str = "r1") -> dict[str, object]:
    return {
        "schema_version": "0.1.0",
        "request_id": request_id,
        "privacy_class": "local_only",
        "data_classes": ["private_source_code"],
        "residency_requirement": "local_required",
        "remote_allowed": False,
        "minimum_quality_tier": "reviewer",
    }


def cloud_constraints(request_id: str = "r1", *, approval: bool = True) -> dict[str, object]:
    evidence: dict[str, object] = {
        "data_classification": {"verified": True, "reference": "classification:test"}
    }
    if approval:
        evidence["approval"] = {"verified": True, "reference": "approval:test"}
    return {
        "schema_version": "0.1.0",
        "request_id": request_id,
        "privacy_class": "trusted_cloud_ok",
        "data_classes": ["cloud_allowed_source_code"],
        "residency_requirement": "ca_preferred",
        "remote_allowed": True,
        "remote_allowance_reasons": ["test-approved"],
        "evidence": evidence,
        "minimum_quality_tier": "reviewer",
    }


def test_private_code_selects_local_and_rejects_cloud() -> None:
    decision = resolve(request(), local_constraints(), registry())
    assert decision["selected_source"] == "local-reviewer"
    assert decision["eligible_sources"] == ["local-reviewer"]
    assert "cloud-reviewer" in decision["rejected_sources"]
    assert any(
        item["code"] == "privacy_violation"
        for item in decision["rejection_details"]["cloud-reviewer"]
    )


def test_verified_cloud_can_be_preferred_within_eligible_set() -> None:
    req = request()
    req["preferred_sources"] = ["cloud-reviewer"]
    decision = resolve(req, cloud_constraints(), registry())
    assert decision["selected_source"] == "cloud-reviewer"
    assert set(decision["eligible_sources"]) == {"local-reviewer", "cloud-reviewer"}


def test_missing_source_approval_does_not_make_cloud_eligible() -> None:
    reg = registry()
    reg["sources"] = [reg["sources"][1]]
    decision = resolve(request(), cloud_constraints(approval=False), reg)
    assert decision["decision_outcome"] == "denied"
    assert decision["selected_source"] is None
    assert decision["policy_denials"][0]["code"] == "missing_approval_gate"


def test_resolution_record_replays_and_detects_mutation() -> None:
    req = request()
    constraints = local_constraints()
    reg = registry()
    decision = resolve(req, constraints, reg)
    record = build_resolution_record(req, constraints, reg, decision)
    verify_record_integrity(record)
    assert replay_resolution(record, req, constraints, reg) == decision

    modified = copy.deepcopy(record)
    modified["decision"]["selected_source"] = "tampered"
    with pytest.raises(IntegrityError):
        verify_record_integrity(modified)


def test_serialization_is_stable() -> None:
    decision = resolve(request(), local_constraints(), registry())
    assert serialize(decision) == serialize(copy.deepcopy(decision))
    assert serialize(decision).endswith("\n")


def test_duplicate_source_ids_fail_closed() -> None:
    reg = registry()
    reg["sources"] = [reg["sources"][0], copy.deepcopy(reg["sources"][0])]
    with pytest.raises(ResolutionError, match="duplicate source id"):
        resolve(request(), local_constraints(), reg)


def test_request_and_constraint_identity_must_match() -> None:
    with pytest.raises(ResolutionError, match="request_id must match"):
        resolve(request("request-a"), local_constraints("request-b"), registry())


def test_overlapping_source_allow_and_deny_lists_fail_closed() -> None:
    constraints = local_constraints()
    constraints["allowed_sources"] = ["local-reviewer"]
    constraints["forbidden_sources"] = ["local-reviewer"]
    with pytest.raises(ResolutionError, match="allowed_sources and forbidden_sources overlap"):
        resolve(request(), constraints, registry())


def test_unknown_preferred_source_fails_closed() -> None:
    req = request()
    req["preferred_sources"] = ["missing-source"]
    with pytest.raises(ResolutionError, match="preferred_sources references unknown sources"):
        resolve(req, local_constraints(), registry())


def test_disabled_source_is_rejected_before_policy_evaluation() -> None:
    reg = registry()
    local = reg["sources"][0]
    local["enabled"] = False
    decision = resolve(request(), local_constraints(), reg)
    assert decision["decision_outcome"] == "denied"
    assert decision["rejection_details"]["local-reviewer"][0]["code"] == "source_disabled"


def test_missing_capability_and_context_overflow_are_rejected() -> None:
    req = request()
    req["required_capabilities"] = ["vision"]
    req["context_estimate"] = {"input_tokens": 40000, "max_output_tokens": 1000}
    decision = resolve(req, local_constraints(), registry())
    codes = {item["code"] for item in decision["rejection_details"]["local-reviewer"]}
    assert "missing_capability" in codes
    assert "context_capacity_exceeded" in codes


def test_numeric_hard_budget_uses_versioned_pricing_and_fails_closed() -> None:
    reg = registry()
    cloud = reg["sources"][1]
    cloud["pricing"] = {
        "currency": "USD",
        "input_per_million": 2.0,
        "output_per_million": 8.0,
    }
    reg["sources"] = [cloud]
    constraints = cloud_constraints()
    constraints["hard_budget"] = {"max_cost_usd": 0.000001}
    decision = resolve(request(), constraints, reg)
    assert decision["decision_outcome"] == "denied"
    assert decision["policy_denials"][0]["code"] == "budget_hard_limit"


def test_operational_fallback_is_exposed_only_with_multiple_eligible_sources() -> None:
    constraints = cloud_constraints()
    constraints["operational_fallback"] = {
        "allowed_reasons": ["temporary_unavailable"],
        "forbidden_reasons": ["policy_denial"],
    }
    decision = resolve(request(), constraints, registry())
    assert decision["fallback_policy"] == {
        "allowed_reasons": ["temporary_unavailable"],
        "forbidden_reasons": ["policy_denial"],
    }


def test_resolution_record_rejects_identity_and_replay_drift() -> None:
    req = request()
    constraints = local_constraints()
    reg = registry()
    decision = resolve(req, constraints, reg)

    invalid_decision = copy.deepcopy(decision)
    invalid_decision["request_id"] = "other"
    with pytest.raises(IntegrityError, match="decision request_id"):
        build_resolution_record(req, constraints, reg, invalid_decision)

    record = build_resolution_record(req, constraints, reg, decision)
    modified_record = copy.deepcopy(record)
    modified_record["resolution_sha256"] = "0" * 64
    with pytest.raises(IntegrityError, match="resolution identity digest mismatch"):
        verify_record_integrity(modified_record)

    changed_request = copy.deepcopy(req)
    changed_request["task"] = "summarize"
    with pytest.raises(IntegrityError, match="request drift"):
        replay_resolution(record, changed_request, constraints, reg)
