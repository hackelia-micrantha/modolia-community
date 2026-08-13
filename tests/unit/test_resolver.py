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
