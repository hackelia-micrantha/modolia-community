# Documentation maintenance contract

**Adoption:** The [Micrantha shared documentation-sync skill](https://github.com/hackelia-micrantha/.github/blob/main/skills/documentation-sync/SKILL.md), unchanged. This document records Modolia-specific publication authority, validation, and claim discipline; it does not duplicate the shared skill.

## Source and contract authority

- `modolia-community` is the authoritative **public reusable resolver core**: deterministic routing, validated generic schemas, content-addressed replay/conformance, generic CLI, and public fixtures. Published reusable semantics must not silently diverge from consumers.
- `hackelia-micrantha/modolia` is the private canonical/deployment engineering and release-staging repository. Concrete provider and workstation registries, organization constraints and approvals, identities, credentials, live capacity/pricing, and operational runtime state are **not public inputs** to mirror.
- [Community boundary](COMMUNITY_REPOSITORY.md) and [provenance](../UPSTREAM.md) define deliberate promotion and the public-first contract change path: generic public conformance/release contract first, then pinned private/downstream consumption and native verification. An accepted public spec is not redefined by a private runtime observation without a versioned reconciliation.

Review the [README](../README.md), [public architecture](architecture.md), [threat model](threat-model.md), [versioned conformance fixture](../conformance/public-v1/), [generic schemas](../schemas/), [synthetic examples](../examples/), and [CI](../.github/workflows/ci.yml) together when facts change.

## Release, trust, and capability claims

- The current source/package identity reports `modolia 0.1.0 (resolver 0.1.0)` and the public flake supports `x86_64-linux` and `aarch64-linux`. A runnable source tree or green packaging CI is **not** proof of a published immutable GitHub release, tag, or downstream flake pin; verify the actual public tag/artifact and clean consumer independently before stating release availability.
- The historical `model_router` Python import and `model-router` Nix package alias are compatibility affordances, not distinct current product/project identities.
- Resolver decisions are deterministic under trusted inputs. JSON/schema validation does **not** authenticate a constraint producer or registry. Content hashes bind facts; they are not signing, authority, policy grant, or model execution proof.
- The host/runtime owns inference, provider credentials, health/capacity, eligibility narrowing, and enforced fallbacks. The resolver cannot authorize or run provider requests and must not be described as a gateway.
- A successful synthetic `conformance/public-v1` check proves bounded public resolver parity, not real provider availability, production authorization, or private host configuration.

## Exact-head validation

Use the repository's existing [CI](../.github/workflows/ci.yml), not a copied pipeline. For applicable source or CLI changes, the following are its public gates:

```sh
python -m pip install '.[validation,test,dev]'
ruff check model_router scripts tests
mypy model_router scripts/resolve_route.py
pytest -q tests/unit
pytest -q -m integration tests/integration
python scripts/validate-community-conformance.py
pytest -q --cov --cov-report=term-missing tests/unit tests/integration
pytest -q -m e2e tests/e2e
```

The same CI separately runs locked-flake validation and executable smoke tests:

```sh
nix flake lock --no-update-lock-file
nix flake show --no-write-lock-file
nix build .#modolia --no-write-lock-file --print-build-logs
nix run .#modolia --no-write-lock-file -- --version
nix flake check --print-build-logs --no-write-lock-file
```

Source/packaging checks do not substitute for a live public artifact/anonymous consumer test, a verified production deployment, or security-policy acceptance. No real provider keys, network inference, private inventories or authorization effects are required for this public validation.

## Event-driven maintenance and decisions

Re-evaluate README and contracts when the public resolver, schema namespace, conformance fixture, CLI package/name/version, release tag, or private-to-public publication boundary changes. Reconcile provider/runtime capability claims with the owning implementation rather than importing deployment facts into public examples. Maintain the shared `DOC-Q*` human decision queue for unsupported security, license, release, or public/private claim decisions.

A documentation PR does not authorize a release, private-source publication, signing, deployment, or changing governance authority. No further shared-skill specialization is currently needed.
