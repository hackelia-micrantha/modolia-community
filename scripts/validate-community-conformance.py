#!/usr/bin/env python3
"""Validate the versioned public Modolia cross-repository conformance fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model_router import (  # noqa: E402
    build_resolution_record,
    canonical_json_bytes,
    replay_resolution,
    resolve,
)

FIXTURE = ROOT / "conformance" / "public-v1"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML object")
    return value


def assert_canonical_equal(actual: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    if canonical_json_bytes(actual) != canonical_json_bytes(expected):
        raise AssertionError(f"public-v1 {label} drifted from the committed conformance contract")


def main() -> int:
    request = load_json(FIXTURE / "request.json")
    constraints = load_json(FIXTURE / "constraints.json")
    registry = load_yaml(FIXTURE / "registry.yaml")
    expected_record = load_json(FIXTURE / "expected-record.json")
    expected_decision = expected_record.get("decision")
    if not isinstance(expected_decision, dict):
        raise ValueError("expected-record.json: decision must be an object")

    decision = resolve(request, constraints, registry)
    assert_canonical_equal(decision, expected_decision, "RouteDecision")

    record = build_resolution_record(request, constraints, registry, decision)
    assert_canonical_equal(record, expected_record, "resolution record")

    replayed = replay_resolution(expected_record, request, constraints, registry)
    assert_canonical_equal(replayed, expected_decision, "replay")

    print(f"public-v1 conformance ok: {record['record_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
