# Contributing to Crew Book

Start with a small, focused issue or pull request explaining the problem and
expected result. For security problems, use the [private reporting policy](.github/SECURITY.md).
All participation follows the [code of conduct](.github/CODE_OF_CONDUCT.md).

This guide is for humans contributing to this source repository. Read the
[source instructions](AGENTS.md) before editing; host controls and the user's
authorized scope govern agent-assisted work. The reusable package does not
set policy for other repositories. See the [policy composition contract](docs/policy-composition.md).

## Prepare and check a change

Match the existing GitHub-flavored Markdown and keep maintained rules in their
existing documents, linking to them instead of copying them. For executable
bugs, add and demonstrate a failing regression before the fix, then run relevant
checks. Prose changes need proportionate checks rather than new tests.

The [maintenance guide](tools/README.md#checks) describes the Python 3.9+
standard-library suite and package checks; no dependency installation is needed.
From the source root:

```sh
python3 -B -m unittest discover -s tools -p 'test_*.py'
python3 -B tools/crewbook-package.py check --root "$(pwd -P)"
```

When changing distributed text, update its inventory using the
[distribution procedure](docs/distribution.md#deterministic-inventory-and-updates)
before checking. Community files and maintenance tooling remain source-only.
Check changed links and run the [secret scan](tools/SECURITY.md) using the pinned
scanner. Report what passed, what was skipped and remaining limitations;
static checks do not establish native client behavior.

## Submit and review

Use focused Conventional Commits and the actual work-item reference and assistance
trailers required by [AGENTS.md](AGENTS.md). Keep configured hooks active and
preserve other contributors' work. The team manual explains
[target contribution requirements](docs/team.md#target-contribution-requirements),
[independent review and local integration](docs/team.md#local-integration-and-publication),
and [precise handovers](docs/team.md#precise-issues-handovers-and-review-reports).
This repository integrates independently reviewed exact revisions by fast-forward;
push and publication remain with the human maintainer.

Include the problem, change, verification and remaining limitations in a pull
request. Use minimal sanitized examples in public issues and reviews: omit
credentials, private machine paths and raw sensitive transcripts.

## Licence and attribution

Contributions use the existing [EUPL-1.2 licence](LICENSE). Preserve its terms,
notices and the attribution recorded in [PROVENANCE.md](PROVENANCE.md); do not
relabel imported material as newly authored.
