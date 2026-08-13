"""Modolia deterministic model-surface resolution core.

The ``model_router`` import path is retained for compatibility with the original
project while the distribution is renamed to Modolia.
"""

from .integrity import (
    CANONICALIZATION,
    RECORD_SCHEMA_VERSION,
    IntegrityError,
    build_resolution_record,
    canonical_json_bytes,
    replay_resolution,
    sha256_json,
    verify_record_integrity,
)
from .resolver import RESOLVER_VERSION, ResolutionError, resolve, serialize

__all__ = [
    "CANONICALIZATION",
    "RECORD_SCHEMA_VERSION",
    "IntegrityError",
    "RESOLVER_VERSION",
    "ResolutionError",
    "build_resolution_record",
    "canonical_json_bytes",
    "replay_resolution",
    "resolve",
    "serialize",
    "sha256_json",
    "verify_record_integrity",
]
