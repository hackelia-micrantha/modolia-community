# Upstream and provenance

`modolia-community` is the public reusable distribution of Modolia. It is maintained from a private canonical/deployment repository through deliberate, reviewed promotion rather than repository mirroring.

## Initial cutover

- Private canonical project: Modolia (renamed from `model-router`)
- Initial reviewed source snapshot: `8cc2254646b6c3146a9b49d17e2ad75199f25d40`
- Community extraction branch: `agent/community-core-split`
- Community repository starts with synthetic examples and public-safe documentation; concrete deployment inventories and policy are intentionally absent.

## v0.1.0 release provenance

- Canonical repository: `hackelia-micrantha/modolia`
- Canonical CLI/release-contract PR: `#86`
- Reviewed canonical merge commit: `d5ee965153716798a690d0c2f9339b2a930d4d14`
- Public release preparation issue: `hackelia-micrantha/modolia-community#7`
- Public release preparation PR: `#8`

The v0.1.0 public artifact promotes only the reusable resolver/CLI contract from the reviewed canonical revision. Concrete Dubnium registries, provider/runtime inventories, organization policy, credentials, generated runtime state, and private evidence remain outside the community release.

## Promotion policy

Only reusable, classified material is promoted. Deployment configuration, concrete provider/runtime inventories, organization policy, generated runtime state, internal evidence, and private CI configuration remain private.

Public contracts should preserve behavior and compatibility with the corresponding canonical implementation. Generalization is allowed for documentation and examples; it must not silently change resolver semantics or schema constraints.

`conformance/public-v1` is the executable provenance/compatibility bridge for the current reusable resolver contract. Changes to that contract are reviewed in the public repository first, then consumed and revalidated by private Modolia; the fixture is not evidence that the repositories are mirrors.

Unknown or ambiguously classified material stays private until reviewed.
