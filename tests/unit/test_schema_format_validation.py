from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolve_route  # noqa: E402


def request(timestamp: str) -> dict[str, object]:
    return {
        "request_id": "format-check",
        "timestamp": timestamp,
        "task": "code_review",
    }


def test_route_request_accepts_valid_rfc3339_timestamp() -> None:
    resolve_route.assert_valid(
        request("2026-09-11T23:45:00Z"),
        resolve_route.REQUEST_SCHEMA,
        "RouteRequest",
        request=True,
    )


def test_route_request_rejects_invalid_rfc3339_timestamp() -> None:
    with pytest.raises(resolve_route.CliError, match="date-time"):
        resolve_route.assert_valid(
            request("not-a-date"),
            resolve_route.REQUEST_SCHEMA,
            "RouteRequest",
            request=True,
        )
