# Root cause and coherent changes

For a bug, trace the reproduced trigger through the responsible behavior and
identify affected callers before editing. Keep the investigation proportional
to the failure and authorized scope: follow the affected flow, inspect relevant
repository examples and search for callers of the implicated contract. An
exhaustive repository audit is not a prerequisite. If reproduction is unavailable,
state the missing setup and distinguish observed evidence from a proposed cause.

Fix shared behavior at the layer that owns its contract. Check the callers
required by the task and retain their adapter contracts, validation,
authorization, isolation and error handling. A central fix does not remove
necessary checks at distinct trust or representation boundaries. Conversely,
copying a symptom patch into several adapters may leave the shared defect
and other callers intact. Correctness and coherent scope matter more than
the number of files changed or lines deleted.

Use the smallest complete solution described by the
[canonical simplicity prompt](simplicity.md#canonical-prompt).
Follow consuming-project design ownership and applicable host/user/repository
instructions. Refer consequential rule changes to the design owner rather
than expanding the task's authority through this guidance.

## Examples

These examples are illustrative reasoning checks, not measured Crewbook
behavior or prescriptions for a particular repository.

- **Shared cause:** Two adapters render an expired session as active because
  the shared session predicate ignores expiry. Reproduce with a clock and an
  expired session, inspect the predicate's callers and fix that predicate.
  Verify both required adapters and the just-before/at-expiry cases. Changing
  only one adapter would leave the other caller broken; a changed file count
  cannot establish completeness.
- **Necessary boundaries:** HTTP and batch callers share a validated domain
  operation, but parse different input representations. Keep HTTP size and
  authentication checks and batch record validation in their owning layers.
  A shared domain fix should preserve those contracts. Test malformed inputs
  at each required boundary and valid inputs through the shared operation;
  moving every check into a common helper could omit boundary-specific data.
- **Deferred caller:** “Fixed the shared expiry predicate and verified the HTTP
  adapter with expired and boundary-time sessions. The batch caller also uses
  it, but its integration setup is unavailable; that caller remains unverified.
  Existing issue #N records the missing setup, its owner and the next check.”
  If batch verification is an acceptance criterion, report it as unmet. If the
  project owner accepts a narrower supported scope, record that decision and
  a measurable revisit trigger in the existing issue or design record under
  [material limitations](material-limitations.md). A limitation note cannot
  waive a security defect or failed required criterion.

Before claiming the shared fix is sufficient, compare the discovered callers
with the task's supported cases and the contract's invariants. Investigate a
new caller when it changes that conclusion; avoid unrelated cleanup that
adds review scope without helping the fix. Tests should exercise the trigger,
correct behavior and relevant boundaries. Generated expectations that merely
repeat the implementation are not an independent oracle; use the requirements,
existing contract and observed failure to assess the result.

## Independent review and reporting

The independent reviewer checks the trigger and evidence for the cause, the
preserved invariants, affected required callers and meaningful verification.
Inspect whether a local patch leaves shared behavior broken, whether a central
change bypasses an adapter contract, and whether the author honestly reports
unverified callers or unmet criteria. Preserve existing security checks and
exact-revision author/reviewer separation. A plausible cause or passing test
alone does not establish authorization or correctness across every caller.

Apply the [precise reporting contract](team.md#precise-issues-handovers-and-review-reports)
and [handover examples](handover-examples.md): report the result, decisive
checks, remaining limitations and next action. Findings retain location,
trigger, consequence, evidence and correction; distinguish committed, tested,
independently reviewed and measured work. Put deferred work in existing
records rather than creating a new ledger or mandatory per-change boilerplate.

Both [generic native sessions](profile-generic.md) and
[managed containers](profile-workharbor.md) use this guidance with their
available authorized tools. Managed provisioning and enforcement remain host
responsibilities. Evaluate transfer and benefit through
[#14](https://github.com/wstein/crewbook/issues/14) before claiming improved
results. This reference adds no prompt parser, commands or runtime enforcement.
