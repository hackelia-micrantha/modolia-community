#!/usr/bin/env python3
"""Resolve RouteRequest + RouteConstraints + ModelSurfaceRegistry offline."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model_router import ResolutionError, resolve, serialize  # noqa: E402

REQUEST_SCHEMA = ROOT / "schemas" / "route-request.schema.json"
CLASSIFICATION_SCHEMA = ROOT / "schemas" / "classification.schema.json"
CONSTRAINTS_SCHEMA = ROOT / "schemas" / "route-constraints.schema.json"
REGISTRY_SCHEMA = ROOT / "schemas" / "source-registry.schema.json"
DECISION_SCHEMA = ROOT / "schemas" / "route-decision.schema.json"
DEFAULT_REGISTRY = ROOT / "examples" / "model-surfaces.yaml"


class CliError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CliError(f"{path}: expected JSON object")
    return data


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CliError(f"{path}: expected YAML object")
    return data


def validator(path: Path, *, request: bool = False) -> Draft202012Validator:
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    if request:
        classification = load_json(CLASSIFICATION_SCHEMA)
        Draft202012Validator.check_schema(classification)
        schema = copy.deepcopy(schema)
        schema["properties"]["classification"] = classification
    return Draft202012Validator(schema, format_checker=FormatChecker())


def assert_valid(instance: dict[str, Any], schema_path: Path, label: str, *, request: bool = False) -> None:
    errors = sorted(validator(schema_path, request=request).iter_errors(instance), key=lambda error: tuple(str(part) for part in error.absolute_path))
    if not errors:
        return
    formatted = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        formatted.append(f"{location}: {error.message}")
    raise CliError(f"{label}: {'; '.join(formatted)}")


def resolve_files(request_path: Path, constraints_path: Path, registry_path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    request = load_json(request_path)
    constraints = load_json(constraints_path)
    registry = load_yaml(registry_path)
    assert_valid(request, REQUEST_SCHEMA, "RouteRequest", request=True)
    assert_valid(constraints, CONSTRAINTS_SCHEMA, "RouteConstraints")
    assert_valid(registry, REGISTRY_SCHEMA, "ModelSurfaceRegistry")
    decision = resolve(request, constraints, registry)
    assert_valid(decision, DECISION_SCHEMA, "RouteDecision")
    return decision


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("constraints", type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        content = serialize(resolve_files(args.request, args.constraints, args.registry))
        if args.output is None:
            sys.stdout.write(content)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        return 0
    except (CliError, ResolutionError, OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"route resolution failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
