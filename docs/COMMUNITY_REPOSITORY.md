# Community Repository Boundary

`modolia-community` is the public reusable core of Modolia. It is not a mirror of any private deployment repository.

## Public here

- resolver and integrity/replay implementation;
- generic JSON schemas and stable contracts;
- public architecture and threat-model documentation;
- synthetic examples and tests;
- offline developer tooling.

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

Compatibility between private consumers and this public core should be maintained through versioned schemas, package versions, and conformance tests rather than copying private configuration into the community repository.
