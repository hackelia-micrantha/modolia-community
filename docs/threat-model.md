# Threat Model

## Assets and security properties

Modolia aims to preserve:

- confidentiality boundaries expressed by trusted constraints;
- residency and source restrictions;
- deterministic, explainable eligibility decisions;
- non-widening downstream behavior;
- replayable evidence of exactly which normalized inputs produced a decision.

## Trust boundaries

`RouteConstraints` are authority-bearing input. JSON Schema validation establishes shape, not provenance. The embedding host must authenticate or otherwise trust the producer before resolution.

`ModelSurfaceRegistry` is also security-relevant configuration. A malicious or stale registry can misdescribe a model surface. Hosts should version, review, and protect the registry source used for security-sensitive routing.

## Representative threats

### Caller self-authorization

A caller attempts to label private content as cloud-safe or claim approval. Mitigation: trusted constraints are constructed outside the resolver; caller claims do not grant authority.

### Preference-based widening

A preferred cheap/fast/provider-specific source violates a hard restriction. Mitigation: hard filtering precedes ranking and preferences operate only within the eligible set.

### Fallback bypass

A runtime failure is used to route to a source rejected for privacy, residency, approval, or budget reasons. Mitigation: fallback targets remain bounded to the resolver's eligible set and policy denials are not operational fallback reasons.

### Registry substitution

An attacker changes source metadata to make a disallowed runtime look eligible. Mitigation: protect/version registry provenance and bind the exact registry digest into a resolution record.

### Evidence tampering

A recorded decision or its inputs are changed after the fact. Mitigation: content-addressed resolution records bind request, constraints, registry, resolver version, and decision digests.

### Forged integrity record

An untrusted producer recomputes all hashes for malicious inputs. Mitigation: integrity is not authentication. Hosts must separately establish publisher/trust provenance.

## Out of scope

Modolia does not protect provider credentials, secure network transport, sandbox model execution, schedule GPUs, attest model binaries, or authenticate users. Those responsibilities belong to the embedding runtime and governance layers.
