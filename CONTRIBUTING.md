# Contributing

Contributions to Modolia Community should preserve the resolver's deterministic, host-independent boundary.

## Development

```bash
python -m pip install -e '.[validation,test]'
pytest
python -m compileall model_router scripts
```

## Design constraints

Changes should preserve these invariants:

- hard constraints dominate preferences;
- unknown or missing authority fails closed;
- rejected sources cannot reappear through fallback or adapter behavior;
- resolver output must not depend on live provider health, credentials, GPU state, wall-clock reads, network I/O, or mutable external state;
- concrete deployment inventories and organization-specific policy do not belong in this repository;
- public examples must be synthetic and must not encode private infrastructure.

New externally visible decision behavior should include tests and, when appropriate, schema changes with explicit versioning implications.

## Community UI

If this repository introduces or materially redesigns user-facing UI, it follows the shared Phyllotaxis community directive by default: **1990s in visual character, not in capability.** Prefer plain, direct, content-first interfaces with obvious browser-native affordances and minimal decorative chrome, while retaining modern accessibility, semantics, responsive behavior, and security.

See the organization-wide [community UI design directive](https://github.com/hackelia-micrantha/.github/blob/main/docs/standards/ui-design.md). Repository-specific deviations should be justified by a concrete product, usability, or accessibility requirement.
