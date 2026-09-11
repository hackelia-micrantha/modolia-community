# Modolia Community

Modolia is a deterministic, host-independent model-surface resolver.

It evaluates explicit `RouteRequest` facts and trusted `RouteConstraints` against a versioned `ModelSurfaceRegistry`, then emits an auditable `RouteDecision`. Modolia does not proxy inference requests, own provider credentials, or invent governance policy.

```text
host / policy authority
    |  RouteRequest + RouteConstraints
    v
  Modolia
    |  deterministic eligibility + ranking
    v
RouteDecision
    |
    v
runtime adapter / gateway
```

## Design boundary

Modolia Community owns the reusable mechanism:

- deterministic eligibility and ranking;
- route request, constraint, registry, decision, and replay contracts;
- stable rejection reasons and fail-closed behavior;
- content-addressed integrity/replay records;
- offline validation and a bounded CLI;
- synthetic examples suitable for public use.

Deployment owners retain concrete configuration such as provider inventories, credentials, organization policy, runtime health, GPU/process state, and live fallback behavior.

## Quick start

Requires Python 3.12+ for library development.

```bash
python -m pip install -e '.[validation,test]'
pytest

python scripts/resolve_route.py \
  examples/route-request.json \
  examples/route-constraints.json \
  --registry examples/model-surfaces.yaml
```

The Python API is intentionally small:

```python
from model_router import resolve

decision = resolve(request, constraints, registry)
```

The historical `model_router` import package is retained in the first Modolia release for compatibility. The distribution/project name is `modolia`.

## Nix CLI distribution

The initial supported `modolia` executable is distributed by the repository flake. This keeps the Python library dependency-free while the CLI can use its validation dependencies and public schema/example assets.

```bash
nix run . -- --help
nix run . -- --version
```

The CLI reports release/package identity separately from resolver protocol identity:

```text
modolia 0.1.0 (resolver 0.1.0)
```

Public consumers should pin a reviewed release in their own `flake.lock`, for example after `v0.1.0` is published:

```nix
modolia = {
  url = "github:hackelia-micrantha/modolia-community/v0.1.0";
  inputs.nixpkgs.follows = "nixpkgs";
};
```

The flake exposes `packages.<system>.modolia` and `apps.<system>.modolia` for `x86_64-linux` and `aarch64-linux`. Consumers should use this artifact rather than manufacturing local wrappers around repository scripts.

## Validation

Python quality/test checks run in CI, and the public Nix surface is validated with:

```bash
nix flake check --print-build-logs
```

Before a release tag is published, `flake.lock` must be committed so the public artifact has a reviewed Nix input pin rather than resolving a moving branch at install time.

## Security model

Hard restrictions always run before preferences. Missing or uncertain authority must never broaden eligibility. Runtime adapters may narrow the resolver's eligible set, but must not reintroduce a rejected source.

Integrity records prove deterministic input/output binding, not publisher identity or execution authorization. See `docs/threat-model.md`.

## Repository relationship

This public repository contains the reusable community core. It is promoted deliberately from the private canonical Modolia repository rather than mirrored blindly. Private deployment repositories own concrete inventories, policies, integrations, and operational state. See `UPSTREAM.md` and `docs/COMMUNITY_REPOSITORY.md`.

## License

Apache License 2.0.
