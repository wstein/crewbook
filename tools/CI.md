# Maintenance CI

Ordinary push/PR validation runs the same `crewbook-package check` entrypoint
as local maintainers, behavioural/nonzero-exit fixtures, Go race tests, vet
and formatting checks. Internal/package-root GFM links are validated there,
without network requests. Security uses the separate full-history Gitleaks
job and offline synthetic history/tree/message/redaction fixtures described
in `tools/SECURITY.md`. No instruction text, agent, board, credential store or
runtime executable is invoked by the package checker.

CodeQL initializes `languages: go`, `build-mode: manual`, then actually builds
`go build ./...` before analysis. This covers `cmd/` and `internal/` maintenance
source, not an invented runtime package or an absent Python language. Local
Go builds/tests and actionlint check the source and workflow wiring. A hosted
CodeQL database, upload and successful hosted run remain unverified until
publication and execution. Only its job receives security-events write;
other jobs receive contents read. Each checkout disables persisted credentials.
Workflows have bounded job timeouts and ref-scoped concurrency cancellation.

External HTTP(S) links are checked on Monday or manual workflow_dispatch,
separately from PR checks. Lychee 0.24.2 uses 20-second request timeouts and two
retries inside a 10-minute job. The action receives no access token. Internal
links are not rechecked by that job. Offline fixtures for reference links,
images, missing headings, relative escapes, host declarations, tables and code
examples are in the Go suite. To reproduce external checking when authorized:

```sh
lychee --scheme https --scheme http --timeout 20 --max-retries 2 --no-progress '**/*.md' '.agents/*.md' '.claude/**/*.md'
```

Do not run that command as part of ordinary offline validation. Local workflow
validation uses the existing `actionlint .github/workflows/*.yml`, plus
`bash -n tools/install-gitleaks.sh tools/scan-secrets.sh` and `shellcheck` on
those files where installed. Local checks are documented in `tools/README.md`.
Dependencies are the actual Go module and pinned GitHub Actions; weekly
Dependabot PRs require human review and retain immutable pins. No auto-merge,
release, deployment or native settings mutation is configured.

## Official upstream pin evidence

REST reads on 2026-10-04 verified each version's commit from the official
upstream repository (not a search snippet or a guessed SHA):

| Action | Version | Commit | Official source |
| --- | --- | --- | --- |
| actions/checkout | v7.0.1 | 3d3c42e5aac5ba805825da76410c181273ba90b1 | [upstream](https://github.com/actions/checkout/tree/v7.0.1) |
| actions/setup-go | v7.0.0 | b7ad1dad31e06c5925ef5d2fc7ad053ef454303e | [upstream](https://github.com/actions/setup-go/tree/v7.0.0) |
| github/codeql-action | v4.38.2 | 2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2 | [upstream](https://github.com/github/codeql-action/tree/v4.38.2) |
| lycheeverse/lychee-action | v2.9.0 | e7477775783ea5526144ba13e8db5eec57747ce8 | [upstream](https://github.com/lycheeverse/lychee-action/tree/v2.9.0) |

The sole parser dependency is Goldmark v1.7.13, verified at upstream commit
`9a7f4c9419f73381f0e7fa6899554fe21c4074cf` with module sums committed. Go's
module checksum verification applies locally and in CI. This dependency is
justified by actual GFM parsing; it does not introduce an interpreter or agent.
Gitleaks archives are separately checksum-pinned as documented in SECURITY.md.
All CI sources/configuration, scanner tools, module files and fixtures remain
excluded by `tools/package-policy.json`; source and export policies retain the
same distributed set. No production manifest or live compatibility assertion
is supplied by this integration.
