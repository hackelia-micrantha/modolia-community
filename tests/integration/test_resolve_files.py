from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.integration


def load_resolve_route() -> ModuleType:
    path = ROOT / "scripts" / "resolve_route.py"
    spec = importlib.util.spec_from_file_location("modolia_resolve_route", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_files_validates_public_examples() -> None:
    module = load_resolve_route()
    decision = module.resolve_files(
        ROOT / "examples" / "route-request.json",
        ROOT / "examples" / "route-constraints.json",
    )

    assert decision["decision_outcome"] == "selected"
    assert decision["selected_source"] == "local-reviewer"
    assert decision["eligible_sources"] == ["local-reviewer"]
    assert set(decision["rejected_sources"]) == {
        "trusted-cloud-reviewer",
        "public-utility",
    }
