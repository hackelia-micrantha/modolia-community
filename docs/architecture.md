# Architecture

Modolia answers one bounded question:

> Given trusted routing constraints and a versioned inventory of model surfaces, which surfaces are eligible and how should the eligible set be deterministically ranked?

```text
RouteRequest -----------+
                        |
RouteConstraints -------+--> deterministic resolver --> RouteDecision
                        |
ModelSurfaceRegistry ---+
```

The host owns the trust decision behind `RouteConstraints`. Modolia validates and evaluates the normalized document but does not authenticate its producer.

## Resolution stages

Hard constraints are evaluated before preferences:

1. source availability and explicit allow/deny restrictions;
2. privacy, remote-execution, and residency boundaries;
3. host-required evidence;
4. source-specific remote/evidence gates;
5. capabilities, minimum quality, and context capacity;
6. hard budget constraints;
7. deterministic ranking of the remaining eligible set.

Soft preferences can reorder eligible sources but cannot make an ineligible source eligible.

## Runtime separation

Live health, queue depth, GPU capacity, rate limits, retry counters, credentials, transport, and provider telemetry are runtime concerns. Keeping them outside the resolver makes a decision replayable from versioned inputs.

A downstream adapter may narrow the eligible set for runtime compatibility. It must never widen it.
