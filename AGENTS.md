# Crew Book repository guidance

This file applies only to development in this source repository. It is host
project guidance, excluded from the distributed skill and exported package;
it supplies no authority in a consuming repository. Follow system/developer
instructions, actual host controls and the user's authorized scope first.
Read scoped instructions before editing their files. Package roles remain
resources under the [policy composition contract](docs/policy-composition.md).

## Practical test-first changes

For a reproducible executable bug, add a meaningful regression and demonstrate
that it fails against the unfixed behavior for the intended reason **before**
implementing the smallest coherent fix. Then demonstrate it passes and run
relevant existing checks. Trace the trigger and affected contracts proportionately
using [root-cause guidance](docs/root-cause.md) and the
[simplicity ladder](docs/simplicity.md).

For new executable behavior, write focused acceptance examples and failing tests
first where practical. If reproduction or test-first verification is infeasible,
record why, the evidenced alternative and the remaining coverage gap. Do not
manufacture a failure, weaken assertions or make expectations mirror the
implementation. Trivial prose or metadata changes need proportionate existing
checks, not new tests. Synthetic/static checks do not establish native runtime
behavior; report that boundary. Do not add prompt-content parsers.

Use the existing maintenance checks described in [tools/README.md](tools/README.md).
Preserve Python 3.9+ standard-library compatibility on stock macOS; no dependency
installation is required for the maintenance suite.

## Ownership and integration

Preserve user work and respect actual host controls. Follow the
[team manual](docs/team.md) for shared ownership, concurrency and review workflow.
Keep one editor per checkout and isolate concurrent editing in disjoint scopes,
including generated files.

For assigned work, the designated coordinator is authorized to move board cards
under the [team workflow](docs/team.md#coordinator-and-leaf-execution-contract)
without asking for approval for each move. The coordinator remains the sole card
writer and must retain the required ownership, status and review evidence.
Actual host controls and the user's authorized scope still apply.

This repository uses linear, fast-forward-only integration into main. No merge
commits, non-fast-forward integration, cherry-picks into main or rewriting
existing main history. A diverged author rebases only their own commits onto
current main, reruns checks and obtains fresh independent review of the rewritten
SHA **before** fast-forward integration. Stop on conflicts outside the assigned
scope. This is this repository's current policy, not a universal target policy.

Use focused Conventional Commits with the actual WI. A commit written by an
agent ends with one `Co-Authored-By: <model display name> <noreply@<vendor domain>>`
trailer per agent, using the exact line the host's attribution guidance supplies
(for example `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`); never
invent an address. It is a normal git trailer: keep it in the same trailer block as
`Refs:` with no blank line between them, otherwise git does not parse it. For
Codex or other tools whose exact line the host does not supply, use only a
host-supplied line; if none exists, record the open point instead of guessing.
This replaces `Assisted-by: <tool>:<model-id>` for new commits; existing commits
are kept as they are and are not rewritten.

```text
docs: clarify work-item commit footers

Refs: #29
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```

For an authorized repository assignment, the assigned author may create local commits
and fast-forward independently reviewed exact revisions into local main under
the procedure above. This established local authorization does not require a
new permission question for each commit or fast-forward. Push and publication
remain the human's responsibility; return the reviewed local result for that step.
For an authorized blocked operation use approved scoped host
escalation; never delete locks or weaken controls to bypass a permission failure.
Follow the [team manual](docs/team.md) for coordinator ownership, exact review
evidence and honest handoffs.
