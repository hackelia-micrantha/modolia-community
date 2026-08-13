"""Pure deterministic model-surface eligibility and ranking.

The resolver performs no I/O and consults no runtime health/capacity state. Hosts are
responsible for validating/authenticating RouteConstraints before calling it.
"""

from __future__ import annotations

import json
from typing import Any

RESOLVER_VERSION = "0.1.0"

PRIVACY_BOUNDARIES = {
    "local_only": {"local"},
    "unknown": {"local"},
    "trusted_cloud_ok": {"local", "trusted_cloud"},
    "public_cloud_ok": {"local", "trusted_cloud", "public_cloud"},
}
COST_RANK = {"free": 0, "low": 1, "medium": 2, "high": 3, "unknown": 4}
QUALITY_RANK = {
    "cheap": 0,
    "balanced": 1,
    "strong": 2,
    "reviewer": 3,
    "final_answer": 4,
}
DEFAULT_FORBIDDEN_FALLBACK_REASONS = [
    "privacy_violation",
    "forbidden_provider",
    "budget_hard_limit",
    "safety_policy_denial",
    "missing_approval_gate",
    "secret_scan_failed",
    "residency_violation",
    "unknown_classification",
    "unknown_source_quality",
]
DENIAL_PRIORITY = [
    "unknown_classification",
    "missing_approval_gate",
    "secret_scan_failed",
    "residency_violation",
    "forbidden_provider",
    "privacy_violation",
    "budget_hard_limit",
]
DENIAL_REASON = {
    "unknown_classification": "trusted classification evidence required by eligible sources was not satisfied",
    "missing_approval_gate": "required approval evidence was not satisfied",
    "secret_scan_failed": "required secret-scan evidence was not satisfied",
    "residency_violation": "no candidate satisfied the residency constraints",
    "forbidden_provider": "source restrictions removed the otherwise applicable candidates",
    "privacy_violation": "no candidate satisfied the privacy or remote-execution constraints",
    "budget_hard_limit": "no candidate could be proven within the hard budget constraints",
    "safety_policy_denial": "no source satisfied all hard route constraints",
}


class ResolutionError(ValueError):
    """Raised when normalized resolver inputs are internally inconsistent."""


def serialize(decision: dict[str, Any]) -> str:
    """Return stable JSON for a resolved decision."""
    return json.dumps(decision, indent=2, sort_keys=True) + "\n"


def _index_sources(registry: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    raw_sources = registry.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ResolutionError("registry must contain a non-empty sources array")
    order: list[str] = []
    sources: dict[str, dict[str, Any]] = {}
    for source in raw_sources:
        if not isinstance(source, dict):
            raise ResolutionError("registry sources must be objects")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            raise ResolutionError("registry source is missing a non-empty id")
        if source_id in sources:
            raise ResolutionError(f"duplicate source id {source_id!r}")
        order.append(source_id)
        sources[source_id] = source
    return order, sources


def _validate_inputs(request: dict[str, Any], constraints: dict[str, Any], registry: dict[str, Any], sources: dict[str, dict[str, Any]]) -> None:
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ResolutionError("request_id is required")
    if constraints.get("request_id") != request_id:
        raise ResolutionError("RouteRequest and RouteConstraints request_id must match")
    if not isinstance(request.get("timestamp"), str) or not request["timestamp"]:
        raise ResolutionError("request.timestamp is required for replayable RouteDecision output")
    if not isinstance(registry.get("version"), str) or not registry["version"]:
        raise ResolutionError("source registry version is required")
    if not isinstance(constraints.get("schema_version"), str) or not constraints["schema_version"]:
        raise ResolutionError("RouteConstraints schema_version is required")

    known = set(sources)
    allowed = set(constraints.get("allowed_sources", []))
    forbidden = set(constraints.get("forbidden_sources", []))
    overlap = allowed & forbidden
    if overlap:
        raise ResolutionError(f"allowed_sources and forbidden_sources overlap: {sorted(overlap)}")
    unknown_references = (allowed | forbidden) - known
    if unknown_references:
        raise ResolutionError(f"RouteConstraints references unknown sources: {sorted(unknown_references)}")
    preferred = request.get("preferred_sources", [])
    if isinstance(preferred, list):
        unknown_preferences = set(preferred) - known
        if unknown_preferences:
            raise ResolutionError(f"RouteRequest preferred_sources references unknown sources: {sorted(unknown_preferences)}")


def _add_rejection(details: list[dict[str, str]], code: str, reason: str) -> None:
    if not any(item["code"] == code and item["reason"] == reason for item in details):
        details.append({"code": code, "reason": reason})


def _verified_evidence(constraints: dict[str, Any], requirement: str) -> bool:
    evidence = constraints.get("evidence", {})
    if not isinstance(evidence, dict):
        return False
    fact = evidence.get(requirement)
    return isinstance(fact, dict) and fact.get("verified") is True and isinstance(fact.get("reference"), str) and bool(fact["reference"].strip())


def _evidence_rejection(requirement: str) -> tuple[str, str]:
    mapping = {
        "approval": ("missing_approval_gate", "required approval evidence is not verified"),
        "secret_scan": ("secret_scan_failed", "required secret-scan evidence is not verified"),
        "data_classification": ("unknown_classification", "required data-classification evidence is not verified"),
        "residency_review": ("residency_violation", "required residency-review evidence is not verified"),
        "budget_review": ("budget_hard_limit", "required budget-review evidence is not verified"),
    }
    return mapping.get(requirement, ("evidence_requirement_unsatisfied", f"required {requirement!r} evidence is not verified"))


def _estimated_cost_usd(source: dict[str, Any], request: dict[str, Any]) -> float | None:
    if source.get("cost_class") == "free":
        return 0.0
    estimate = request.get("context_estimate")
    pricing = source.get("pricing")
    if not isinstance(estimate, dict) or not isinstance(pricing, dict) or pricing.get("currency") != "USD":
        return None
    values = (estimate.get("input_tokens"), estimate.get("max_output_tokens"), pricing.get("input_per_million"), pricing.get("output_per_million"))
    if not all(isinstance(value, (int, float)) for value in values):
        return None
    input_tokens, output_tokens, input_rate, output_rate = values
    return (float(input_tokens) * float(input_rate) + float(output_tokens) * float(output_rate)) / 1_000_000.0


def _source_rejections(source_id: str, source: dict[str, Any], request: dict[str, Any], constraints: dict[str, Any]) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    boundary = source.get("privacy_boundary")
    residency = source.get("residency_boundary")
    privacy = constraints["privacy_class"]
    is_remote = boundary != "local"

    if source.get("enabled", True) is False:
        _add_rejection(details, "source_disabled", "source is disabled")
    allowed_sources = constraints.get("allowed_sources")
    if allowed_sources is not None and source_id not in set(allowed_sources):
        _add_rejection(details, "source_not_allowed", "source is outside the explicit allowed_sources set")
    if source_id in set(constraints.get("forbidden_sources", [])):
        _add_rejection(details, "forbidden_provider", "source is explicitly forbidden")
    if details:
        return details

    if boundary not in PRIVACY_BOUNDARIES.get(privacy, {"local"}):
        _add_rejection(details, "privacy_violation", f"source boundary {boundary!r} is not allowed for privacy class {privacy!r}")
    if is_remote and constraints.get("remote_allowed") is not True:
        _add_rejection(details, "remote_execution_forbidden", "RouteConstraints forbid remote execution")
    residency_requirement = constraints["residency_requirement"]
    if residency_requirement == "local_required" and residency != "local":
        _add_rejection(details, "residency_violation", "local_required excludes non-local residency")
    if residency_requirement == "ca_required_when_remote" and is_remote and residency != "ca":
        _add_rejection(details, "residency_violation", "CA-required remote execution excludes non-Canadian residency")
    if details:
        return details

    for requirement in constraints.get("required_evidence", []):
        if not _verified_evidence(constraints, requirement):
            code, reason = _evidence_rejection(requirement)
            _add_rejection(details, code, reason)
    if details:
        return details

    if is_remote:
        remote = source.get("remote_allowance")
        if isinstance(remote, dict):
            if remote.get("allowed") is not True:
                _add_rejection(details, "source_remote_disabled", "source registry disables remote use of this source")
            allowed_privacy = set(remote.get("allowed_privacy_classes", []))
            if allowed_privacy and privacy not in allowed_privacy:
                _add_rejection(details, "privacy_violation", f"source remote allowance does not permit privacy class {privacy!r}")
            if details:
                return details
            requirements = set(remote.get("evidence_required", []))
            if remote.get("requires_approval") is True:
                requirements.add("approval")
            for requirement in sorted(requirements):
                if not _verified_evidence(constraints, requirement):
                    code, reason = _evidence_rejection(requirement)
                    _add_rejection(details, code, reason)
            if details:
                return details

    required_capabilities = set(request.get("required_capabilities", []))
    missing = sorted(required_capabilities - set(source.get("capabilities", [])))
    if missing:
        _add_rejection(details, "missing_capability", f"missing required capabilities: {missing}")
    minimum_quality = constraints.get("minimum_quality_tier")
    if isinstance(minimum_quality, str):
        source_quality = source.get("quality_tier")
        minimum_rank = QUALITY_RANK.get(minimum_quality)
        source_rank = QUALITY_RANK.get(source_quality)
        if minimum_rank is None or source_rank is None or source_rank < minimum_rank:
            _add_rejection(details, "quality_requirement_unsatisfied", f"source quality tier {source_quality!r} is below required minimum {minimum_quality!r}")
    estimate = request.get("context_estimate", {})
    if isinstance(estimate, dict):
        requested_tokens = int(estimate.get("input_tokens", 0)) + int(estimate.get("max_output_tokens", 0))
        source_context = source.get("context_tokens")
        if requested_tokens and (not isinstance(source_context, int) or requested_tokens > source_context):
            _add_rejection(details, "context_capacity_exceeded", f"estimated context {requested_tokens} exceeds provable source capacity {source_context!r}")
    if details:
        return details

    hard_budget = constraints.get("hard_budget")
    if isinstance(hard_budget, dict):
        allowed_cost_classes = hard_budget.get("allowed_cost_classes")
        if isinstance(allowed_cost_classes, list) and source.get("cost_class") not in set(allowed_cost_classes):
            _add_rejection(details, "budget_hard_limit", f"source cost class {source.get('cost_class')!r} is outside the allowed hard-budget classes")
        max_cost = hard_budget.get("max_cost_usd")
        if isinstance(max_cost, (int, float)):
            estimate_usd = _estimated_cost_usd(source, request)
            if estimate_usd is None:
                _add_rejection(details, "budget_hard_limit", "source cost cannot be proven within max_cost_usd from versioned inputs")
            elif estimate_usd > float(max_cost):
                _add_rejection(details, "budget_hard_limit", f"estimated source cost {estimate_usd:.6f} USD exceeds max_cost_usd {float(max_cost):.6f}")
    return details


def _ranking_key(source_id: str, source: dict[str, Any], request: dict[str, Any], constraints: dict[str, Any], registry_index: int) -> tuple[int, int, int, int, int]:
    preferred = request.get("preferred_sources", [])
    preferred_rank = preferred.index(source_id) if isinstance(preferred, list) and source_id in preferred else 9999
    residency_rank = 0
    if constraints.get("residency_requirement") == "ca_preferred":
        residency_rank = 0 if source.get("residency_boundary") in {"local", "ca"} else 1
    cost_rank = 0
    if request.get("cost_preference") in {"prefer_free", "prefer_low"}:
        cost_rank = COST_RANK.get(source.get("cost_class", "unknown"), 4)
    return (residency_rank, 0 if preferred_rank != 9999 else 1, preferred_rank, cost_rank, registry_index)


def _denial(rejection_details: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    codes = {item["code"] for details in rejection_details.values() for item in details}
    normalized = set(codes)
    if "remote_execution_forbidden" in codes:
        normalized.add("privacy_violation")
    if "source_not_allowed" in codes:
        normalized.add("forbidden_provider")
    for code in DENIAL_PRIORITY:
        if code in normalized:
            return [{"code": code, "reason": DENIAL_REASON[code]}]
    return [{"code": "safety_policy_denial", "reason": DENIAL_REASON["safety_policy_denial"]}]


def _fallback_policy(constraints: dict[str, Any], ranked_sources: list[str]) -> dict[str, list[str]]:
    configured = constraints.get("operational_fallback")
    if not isinstance(configured, dict):
        return {"allowed_reasons": [], "forbidden_reasons": list(DEFAULT_FORBIDDEN_FALLBACK_REASONS)}
    allowed_reasons = list(configured.get("allowed_reasons", [])) if len(ranked_sources) > 1 else []
    forbidden_reasons = list(configured.get("forbidden_reasons", DEFAULT_FORBIDDEN_FALLBACK_REASONS))
    return {"allowed_reasons": allowed_reasons, "forbidden_reasons": forbidden_reasons}


def resolve(request: dict[str, Any], constraints: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """Resolve a normalized request against constraints and a model-surface registry."""
    registry_order, sources = _index_sources(registry)
    _validate_inputs(request, constraints, registry, sources)
    rejection_details: dict[str, list[dict[str, str]]] = {}
    eligible: list[str] = []
    for source_id in registry_order:
        details = _source_rejections(source_id, sources[source_id], request, constraints)
        if details:
            rejection_details[source_id] = details
        else:
            eligible.append(source_id)
    registry_rank = {source_id: index for index, source_id in enumerate(registry_order)}
    ranked = sorted(eligible, key=lambda source_id: _ranking_key(source_id, sources[source_id], request, constraints, registry_rank[source_id]))
    selected = ranked[0] if ranked else None
    rejected_sources = {source_id: [item["reason"] for item in details] for source_id, details in rejection_details.items()}
    decision: dict[str, Any] = {
        "request_id": request["request_id"],
        "timestamp": request["timestamp"],
        "constraints_version": constraints["schema_version"],
        "resolver_version": RESOLVER_VERSION,
        "source_registry_version": registry["version"],
        "task": request["task"],
        "required_capabilities": list(request.get("required_capabilities", [])),
        "privacy_class": constraints["privacy_class"],
        "data_classes": list(constraints["data_classes"]),
        "residency_requirement": constraints["residency_requirement"],
        "remote_allowed": constraints["remote_allowed"] if selected else False,
        "decision_outcome": "selected" if selected else "denied",
        "selected_source": selected,
        "candidate_sources": list(registry_order),
        "eligible_sources": list(eligible),
        "ranked_sources": list(ranked),
        "rejected_sources": rejected_sources,
        "rejection_details": rejection_details,
        "policy_denials": [] if selected else _denial(rejection_details),
        "decision_reasons": [],
        "fallback_policy": _fallback_policy(constraints, ranked if selected else []),
    }
    minimum_quality = constraints.get("minimum_quality_tier")
    if isinstance(minimum_quality, str):
        decision["quality_tier"] = minimum_quality
    if selected and constraints.get("remote_allowed") is True:
        decision["remote_allowance_reasons"] = list(constraints.get("remote_allowance_reasons", []))
    affinity_key = request.get("affinity_key")
    if isinstance(affinity_key, str) and affinity_key:
        decision["affinity_key"] = affinity_key
    estimate = request.get("context_estimate")
    if isinstance(estimate, dict):
        decision["token_estimate"] = {"input": int(estimate.get("input_tokens", 0)), "max_output": int(estimate.get("max_output_tokens", 0))}
    if selected:
        decision["decision_reasons"] = [
            f"{len(eligible)} of {len(registry_order)} sources satisfied all hard constraints",
            f"selected {selected!r} as the first deterministically ranked eligible source",
        ]
    else:
        decision["decision_reasons"] = ["no source satisfied all hard route constraints"]
    return decision
