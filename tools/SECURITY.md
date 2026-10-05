# Repository protection and offline scans

GitHub secret scanning and push protection are repository settings, independent
of workflow jobs. Repository metadata was read on 2026-10-04 and both statuses
were enabled. No alert contents were queried and no settings were mutated.
Recheck these two metadata fields at final handover. Hosted workflow success
remains unverified until publication and actual GitHub execution.

Gitleaks 8.30.1 is pinned to official release archives and SHA-256 digests from
[the upstream release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1).
The tag resolved to `83d9cd684c87d95d656c1458ef04895a7f1cbd8e`.
The installer supports the CI Linux/x86_64 host and local macOS/arm64 host;
other platforms fail explicitly. Downloads use bounded timeouts and retries,
verify the committed digest before extraction, and never run an installer
fetched from the network. `tools/gitleaks.toml` extends the upstream default
rules unchanged, with no allowlists or ignored findings.

Run locally from the canonical repository root:

```sh
bash tools/install-gitleaks.sh /private/tmp/crewbook-gitleaks-8.30.1
bash tools/scan-secrets.sh "$(pwd -P)" /private/tmp/crewbook-gitleaks-8.30.1
GITLEAKS_TEST_BINARY=/private/tmp/crewbook-gitleaks-8.30.1 python3 -B -m unittest discover -s tools -p 'test_scanner.py'
```

The installer requires a new destination; reuse the verified binary for later
scans. Scans require a nonempty, nonshallow Git history and tracked tree, then
check all-ref full history, the current tree (including untracked source), and
all commit messages. Each command redacts 100% of matches. Diagnostics stay
in a private temporary directory, are checked for actual positive scanned
byte counts (and positive history commit counts) and errors, and are deleted
on exit. An upstream scanner that returns success after a Git error or a zero
scan is therefore rejected. Findings produce only a generic failure message.
Inline suppression comments and local ignore files cannot bypass these scans.
No raw reports or matches are published. Git uses disabled system/global configuration, empty credential
helpers, no prompt and no SSH agent. It never asks the host credential stores.
Offline integration fixtures use fresh isolated repositories and synthetic
markers to prove clean success, empty-history rejection and failures for a
deleted historical file, untracked content and commit-message-only content.
They also check that the marker is absent from diagnostics.

All files here are maintenance resources excluded from the instruction artifact.
Scanner installation and local checks do not provision runtime agent tools.
