# Maintenance CI

Ordinary push/PR validation runs the standard-library Python suite and
`tools/crewbook-package.py check` on Ubuntu and macOS. macOS checks explicitly
use `/usr/bin/python3`, with no Python installer, pip or Go step. The suite
covers CLI errors, file safety, inventory, exports, layout and runtime contracts;
Markdown prose and link validation are outside the package checker.

The separate secret job installs checksum-pinned Gitleaks and scans full history,
tree and messages. Python fixtures test clean success, empty history rejection,
historical/tree/message findings and redaction using isolated Git. See
[SECURITY.md](SECURITY.md). These scanner jobs require an external binary;
the package maintenance CLI itself has only standard-library dependencies.

CodeQL uses `languages: python` and `build-mode: none` to analyze actual Python
maintenance source. Hosted analysis/upload/results remain unverified until a
GitHub run. Only that job receives security-events write; ordinary jobs receive
contents read. Checkout disables persisted credentials. Existing immutable
Action pins, timeouts and ref-scoped concurrency cancellation remain in place.
No agents, board operations, automatic merge, release or deployment are invoked.

External HTTP(S) links remain a separate Monday/manual Lychee job, bounded by
20-second request timeouts, two retries and a ten-minute job. It is not part
of offline package validation. To reproduce when authorized:

```sh
lychee --scheme https --scheme http --timeout 20 --max-retries 2 --no-progress '**/*.md' '.agents/*.md' '.claude/**/*.md'
```

Local workflow checks use `actionlint .github/workflows/*.yml` and
`bash -n tools/install-gitleaks.sh tools/scan-secrets.sh`, plus ShellCheck when
available. Dependabot covers the pinned GitHub Actions; no language package
manager or dependency lockfile is needed by the Python tools.

The unchanged official-upstream action pins were recorded on 2026-10-04:

| Action | Version | Commit |
| --- | --- | --- |
| actions/checkout | v7.0.1 | 3d3c42e5aac5ba805825da76410c181273ba90b1 |
| github/codeql-action | v4.38.2 | 2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2 |
| lycheeverse/lychee-action | v2.9.0 | e7477775783ea5526144ba13e8db5eec57747ce8 |

Gitleaks archive checksums remain documented in SECURITY.md. All maintenance
sources, fixtures and workflows remain outside the distributed text artifact.
