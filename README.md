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
- offline validation and a small reference CLI;
- synthetic examples suitable for public use.

Deployment owners retain concrete configuration such as provider inventories, credentials, organization policy, runtime health, GPU/process state, and live fallback behavior.

## Quick start

Requires Python 3.12+.

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

## Security model

Hard restrictions always run before preferences. Missing or uncertain authority must never broaden eligibility. Runtime adapters may narrow the resolver's eligible set, but must not reintroduce a rejected source.

Integrity records prove deterministic input/output binding, not publisher identity or execution authorization. See `docs/threat-model.md`.

## Repository relationship

This public repository contains the reusable community core. Private deployment repositories may consume it while owning concrete inventories, policies, integrations, and operational state. See `docs/COMMUNITY_REPOSITORY.md`.

## License

Apache License 2.0.
