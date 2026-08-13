"""Canonical integrity and replay records for deterministic route resolution.

Integrity binds exact normalized inputs and output. It does not authenticate the
publisher of a record and must never be treated as execution authorization.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .resolver import RESOLVER_VERSION, resolve

CANONICALIZATION = "model-router-canonical-json-v1"
RECORD_SCHEMA_VERSION = "0.1.0"


class IntegrityError(ValueError):
    """Raised when a resolution record is inconsistent or cannot be replayed."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _identity_manifest(record: dict[str, Any]) -> dict[str, str]:
    return {
        "canonicalization": record["canonicalization"],
        "resolver_version": record["resolver_version"],
        "constraints_version": record["constraints_version"],
        "source_registry_version": record["source_registry_version"],
        "request_sha256": record["request_sha256"],
        "constraints_sha256": record["constraints_sha256"],
        "registry_sha256": record["registry_sha256"],
        "decision_sha256": record["decision_sha256"],
    }


def build_resolution_record(request: dict[str, Any], constraints: dict[str, Any], registry: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise IntegrityError("request must contain a non-empty request_id")
    if constraints.get("request_id") != request_id:
        raise IntegrityError("request and constraints request_id must match")
    if decision.get("request_id") != request_id:
        raise IntegrityError("decision request_id must match recorded request")
    constraints_version = constraints.get("schema_version")
    resolver_version = decision.get("resolver_version")
    registry_version = registry.get("version")
    if not all(isinstance(value, str) and value for value in (constraints_version, resolver_version, registry_version)):
        raise IntegrityError("constraints, resolver decision, and registry must carry versions")
    if decision.get("constraints_version") != constraints_version:
        raise IntegrityError("decision constraints_version does not match recorded constraints")
    if decision.get("source_registry_version") != registry_version:
        raise IntegrityError("decision source_registry_version does not match recorded registry")
    record: dict[str, Any] = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "canonicalization": CANONICALIZATION,
        "request_id": request_id,
        "resolver_version": resolver_version,
        "constraints_version": constraints_version,
        "source_registry_version": registry_version,
        "request_sha256": sha256_json(request),
        "constraints_sha256": sha256_json(constraints),
        "registry_sha256": sha256_json(registry),
        "decision_sha256": sha256_json(decision),
        "decision": decision,
    }
    resolution_sha256 = sha256_json(_identity_manifest(record))
    record["resolution_sha256"] = resolution_sha256
    record["record_id"] = f"route-resolution:sha256:{resolution_sha256}"
    return record


def verify_record_integrity(record: dict[str, Any]) -> None:
    if record.get("schema_version") != RECORD_SCHEMA_VERSION:
        raise IntegrityError("unsupported resolution-record schema version")
    if record.get("canonicalization") != CANONICALIZATION:
        raise IntegrityError("unsupported canonicalization algorithm")
    decision = record.get("decision")
    if not isinstance(decision, dict):
        raise IntegrityError("resolution record decision must be an object")
    if sha256_json(decision) != record.get("decision_sha256"):
        raise IntegrityError("resolution record decision digest mismatch")
    if decision.get("request_id") != record.get("request_id"):
        raise IntegrityError("resolution record request_id does not match decision")
    if decision.get("resolver_version") != record.get("resolver_version"):
        raise IntegrityError("resolution record resolver_version does not match decision")
    if decision.get("constraints_version") != record.get("constraints_version"):
        raise IntegrityError("resolution record constraints_version does not match decision")
    if decision.get("source_registry_version") != record.get("source_registry_version"):
        raise IntegrityError("resolution record source_registry_version does not match decision")
    expected_resolution = sha256_json(_identity_manifest(record))
    if record.get("resolution_sha256") != expected_resolution:
        raise IntegrityError("resolution identity digest mismatch")
    if record.get("record_id") != f"route-resolution:sha256:{expected_resolution}":
        raise IntegrityError("resolution record_id does not match identity digest")


def replay_resolution(record: dict[str, Any], request: dict[str, Any], constraints: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    verify_record_integrity(record)
    if sha256_json(request) != record["request_sha256"]:
        raise IntegrityError("request drift: request digest does not match record")
    if sha256_json(constraints) != record["constraints_sha256"]:
        raise IntegrityError("constraints drift: RouteConstraints digest does not match record")
    if sha256_json(registry) != record["registry_sha256"]:
        raise IntegrityError("registry drift: ModelSurfaceRegistry digest does not match record")
    if record["resolver_version"] != RESOLVER_VERSION:
        raise IntegrityError(f"resolver version drift: record uses {record['resolver_version']!r}, current resolver is {RESOLVER_VERSION!r}")
    replayed = resolve(request, constraints, registry)
    if sha256_json(replayed) != record["decision_sha256"]:
        raise IntegrityError("decision replay drift: identical recorded inputs and resolver version did not reproduce the recorded RouteDecision")
    if canonical_json_bytes(replayed) != canonical_json_bytes(record["decision"]):
        raise IntegrityError("decision replay drift: decision digest matched but canonical output differed")
    return replayed
