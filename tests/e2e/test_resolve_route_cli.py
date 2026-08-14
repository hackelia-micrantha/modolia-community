from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.e2e


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
