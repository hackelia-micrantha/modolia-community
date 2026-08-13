# Upstream and provenance

`modolia-community` is the public reusable distribution of Modolia. It is maintained from a private canonical/deployment repository through deliberate, reviewed promotion rather than repository mirroring.

## Initial cutover

- Private canonical project: Modolia (renamed from `model-router`)
- Initial reviewed source snapshot: `8cc2254646b6c3146a9b49d17e2ad75199f25d40`
- Community extraction branch: `agent/community-core-split`
- Community repository starts with synthetic examples and public-safe documentation; concrete deployment inventories and policy are intentionally absent.

## Promotion policy

Only reusable, classified material is promoted. Deployment configuration, concrete provider/runtime inventories, organization policy, generated runtime state, internal evidence, and private CI configuration remain private.

Public contracts should preserve behavior and compatibility with the corresponding canonical implementation. Generalization is allowed for documentation and examples; it must not silently change resolver semantics or schema constraints.

Unknown or ambiguously classified material stays private until reviewed.
