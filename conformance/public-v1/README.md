# public-v1 cross-repository conformance fixture

This directory is a synthetic, public-safe compatibility contract shared with `hackelia-micrantha/modolia`.

It freezes one deterministic request + constraints + registry scenario and the complete expected resolution record. The embedded `decision` is the expected `RouteDecision`; the record also freezes canonical input/output digests, `resolution_sha256`, and `record_id`.

Run:

```bash
python scripts/validate-community-conformance.py
```

A deliberate reusable contract change may update this fixture only with corresponding versioning/compatibility review in both repositories. Concrete deployment inventories, policies, endpoints, credentials, or operational evidence do not belong here.
