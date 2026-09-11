# Community Repository Boundary

`modolia-community` is the public reusable core of Modolia. It is not a mirror of any private deployment repository.

## Public here

- resolver and integrity/replay implementation;
- generic JSON schemas and stable contracts;
- public architecture and threat-model documentation;
- synthetic examples and tests;
- offline developer tooling.

The public repository is authoritative for reusable contract publication. Private Modolia may carry deployment integration around that contract, but reusable resolver/schema/integrity semantics must remain behaviorally aligned.

## Behavioral parity surface

Private and public repositories must agree on:

- `model_router` resolver API and stable rejection/reason semantics;
- integrity/replay behavior and canonicalization identity;
- generic schemas and versioned compatibility rules;
- the versioned `conformance/public-v1` fixture and `scripts/validate-community-conformance.py`.

CI and packaging are allowed to differ operationally. Public PRs remain on GitHub-hosted Actions; private consumers may use Nix/self-hosted deployment validation. Different infrastructure must not imply different resolver semantics.

## Private / deployment-owned

- concrete provider or workstation inventories;
- credentials, endpoints, account identifiers, aliases, and secrets;
- organization-specific routing and approval policy;
- live pricing/configuration not deliberately published as generic examples;
- runtime health, capacity, queue, GPU, retry, and process state;
- internal roadmaps, incident material, or private operational evidence;
- deployment CI/workflows that expose internal environment assumptions.

## Synchronization rule

Promotion from a private implementation into this repository is deliberate review, not blind mirroring. Material should be classified and generalized before publication. If classification is uncertain, do not publish it.

For reusable changes:

1. classify and generalize the change;
2. preserve compatibility/versioning rules;
3. update the versioned public conformance fixture when behavior intentionally changes;
4. validate the public PR with GitHub-hosted CI;
5. land the public contract first;
6. update/pin private consumers to the reviewed public revision or release and run their native integration gates.

No automation should push an arbitrary private tree into this repository.

## Public conformance fixture

`conformance/public-v1` freezes one synthetic request + constraints + registry scenario, its expected `RouteDecision`, and its content-addressed resolution record. The validator proves the same decision, digests, `resolution_sha256`, `record_id`, and replay behavior in both repositories.

The fixture is public-safe by design. Concrete deployment registries or organization policy are not valid substitutes.

## Versioned migrations

Schema namespace or schema-version changes must be published here first with compatibility/conformance evidence, then consumed by private Modolia and downstream hosts. Coordinate schema `$id` namespace work with issue #3.

`model-router-canonical-json-v1` remains a protocol identifier until canonicalization semantics themselves change. A canonicalization change requires an explicit version transition and a new/updated conformance fixture; it is not a branding edit.

Compatibility between private consumers and this public core should be maintained through versioned schemas, package/revision pins, and conformance tests rather than copying private configuration into the community repository.
