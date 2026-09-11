from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from model_router import RESOLVER_VERSION

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.e2e


def package_version() -> str:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    version = project["version"]
    assert isinstance(version, str)
    return version


def test_resolve_route_cli_reports_package_and_resolver_versions() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/resolve_route.py", "--version"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == (
        f"resolve_route.py {package_version()} (resolver {RESOLVER_VERSION})"
    )


def test_resolve_route_cli_returns_public_example_decision() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/resolve_route.py",
            "examples/route-request.json",
            "examples/route-constraints.json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    decision = json.loads(result.stdout)
    assert decision["decision_outcome"] == "selected"
    assert decision["selected_source"] == "local-reviewer"
