# Security policy

## Reporting a vulnerability

Please **do not open a public issue** for a security problem. Use GitHub's
[private vulnerability reporting form](https://github.com/wstein/crewbook/security/advisories/new).
Include the affected CrewBook commit or package version, what you found,
its impact and a minimal reproduction. Keep evidence bounded and sanitized;
do not include credentials, private machine paths or raw sensitive transcripts.

This is a small project. Reports are handled on a best-effort basis, without
a guaranteed response or fix timeline. Please allow reasonable time to investigate
and address a report before disclosing it publicly.

## Scope

CrewBook supplies declarative instructions and metadata, with source-only
maintenance tooling and CI workflows. Reports may concern security-relevant
flaws in that content, tooling or workflows, or secrets committed to this repository.
The package does not implement native agent isolation, credential handling or
permission enforcement; those controls belong to the host/client, as described
in the [policy composition contract](../docs/policy-composition.md#guidance-and-enforcement).
Report vulnerabilities in third-party clients or host systems to their maintainers.

The [scanner maintenance guide](../tools/SECURITY.md) describes local secret checks;
it is separate from this reporting policy.
