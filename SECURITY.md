# Security Policy

## Reporting vulnerabilities

Please report security vulnerabilities privately through GitHub Security Advisories for this repository rather than opening a public issue.

Include enough information to reproduce and assess the issue, including affected versions, relevant inputs, expected behavior, observed behavior, and any security impact you have identified.

## Security boundary

Modolia is a deterministic decision mechanism, not an authorization authority or inference proxy. Hosts are responsible for authenticating trusted `RouteConstraints`, protecting concrete model inventories and credentials, and enforcing the resulting decision at the runtime boundary.

A successful integrity/replay verification demonstrates consistency with recorded inputs and resolver behavior. It does not authenticate the producer or authorize execution.
