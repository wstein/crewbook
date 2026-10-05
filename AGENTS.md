# Crewbook repository guidance

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

Preserve user work. Keep at most two authors and two independent reviewers within
actual host capacity, one editor per checkout, isolated concurrent editing and
disjoint scopes including generated files. Allocate only eligible work. The
assigned author alone edits, runs checks and commits; obtain independent fresh
review of the exact immutable revision through the coordinator.

This repository uses linear, fast-forward-only integration into main. No merge
commits, non-fast-forward integration, cherry-picks into main or rewriting
existing main history. A diverged author rebases only their own commits onto
current main, reruns checks and obtains fresh independent review of the rewritten
SHA **before** fast-forward integration. Stop on conflicts outside the assigned
scope. This is this repository's current policy, not a universal target policy.

Use focused Conventional Commits with accurate assistance trailers. Commit and
publication require authorization; no push or publication unless explicitly
authorized. For an authorized blocked operation use approved scoped host
escalation; never delete locks or weaken controls to bypass a permission failure.
Follow the [team manual](docs/team.md) for coordinator ownership, exact review
evidence and honest handoffs.
