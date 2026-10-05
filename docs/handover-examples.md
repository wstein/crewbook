# Precise handover examples

These are fictional examples for human review, not execution evidence. Their
file locations, revisions and results belong to the examples. Replace them
with the actual task's identifiers and evidence before reporting work. The
[team manual](team.md) governs ownership, independent review and publication;
[tool preflight](tool-preflight.md) governs command evidence.

The [precise reporting contract](team.md#precise-issues-handovers-and-review-reports)
sets length defaults, evidence requirements and privacy rules. Apply it without
omitting security findings or material uncertainty. These examples use placeholder
revision/evidence slots because their results are fictional. Real reports replace
them with exact SHAs and durable versioned evidence links; private evidence stays
in its authorized channel.

## Familiar task: issue description

> The CLI currently accepts an existing export destination, so rerunning an
> export can overwrite an operator's previous package. Change export to require
> a new destination and preserve the previous package on rejection. Keep the
> existing filesystem safety checks and snapshot export behavior.
>
> The expected result is a clear nonzero exit with a diagnostic when the
> destination already exists. A successful export to a new child directory must
> still contain the validated snapshot bytes. Do not make a shared or symlinked
> parent acceptable to accommodate this change. This task covers the maintenance
> CLI; it does not add a runtime permission mechanism or authorize publication.
>
> Completion criteria:
>
> - An existing destination is rejected without changing its files.
> - A new destination receives the exact validated package bytes.
> - Shared-parent and symlink rejection checks continue to pass.
> - The package check and focused export tests pass on the supported Python version.
>
> Dependency: the current export contract and test fixtures must be available.
> Resolve any contract conflict with the design owner before changing behavior.
> Independent review must cover the final revision before publication.

This description has four observable criteria. In a real issue, link its export
contract at the reviewed revision rather than pasting the entire runbook.

## Familiar task: author handover

> Committed the destination-rejection change in `<exact SHA>`; export now refuses
> an existing destination without modifying its contents. The focused export
> tests and package check passed on Python 3.9; the unchanged shared-parent and
> symlink checks passed too. Evidence is in the versioned export-test record at
> that SHA. No independent review has occurred, and native permission enforcement
> was not measured. Next: coordinator assigns review of this exact revision.
> Publication remains unauthorized.

`<exact SHA>` is a template slot, not a usable revision. A real public report
includes the full SHA and a durable link to the evidence record. A passed test
is evidence for its observed behavior; it does not prove every runtime property.

## Exploration and security: fuller review report

> Review of `<exact SHA>` has one open high finding. In `src/export.py:84`, when
> the destination is replaced with a symlink between the existence check and
> the write, the writer can follow the replacement and overwrite a file outside
> the selected destination. The deterministic replacement fixture reproduced
> the outside write; its command, exit status and redacted output are recorded
> in the versioned review evidence for this revision. This establishes the
> fixture's behavior, not exploitability in every deployment.
>
> Correct the race by using the project's approved descriptor-relative,
> no-follow creation procedure and retaining existing-destination rejection.
> Add a regression that attempts the same replacement and verifies that the
> outside file is unchanged. The author must return a new revision and test
> evidence; the coordinator then assigns fresh independent review. No correction
> is committed yet. Live hostile-process behavior and native client isolation
> remain unmeasured. Do not publish while the finding remains open.

The extra detail preserves location, trigger, consequence, decisive evidence
and correction. Include additional findings even if the report exceeds the
normal comment length. Necessary security information belongs in the report,
with sensitive evidence handled through the approved disclosure channel.

## Shortening without changing meaning

Longer source report:

> The change has been committed, and the deterministic tests passed in the
> named Python setup. Those tests cover rejection only when the destination
> already exists before export begins. They do not cover concurrent replacement
> of the parent. Independent review has not started. The reference-host
> measurement could not run because the required adapter was unavailable; this
> is a measurement blocker, not a failing test or evidence of enforcement.
> The coordinator should arrange independent review of the exact commit, and
> the measurement owner should rerun the live check when the adapter is available.

Meaning-preserving short report:

> Committed `<exact SHA>`; deterministic tests passed in the named Python setup
> for destinations that exist before export begins. Concurrent parent replacement
> is untested; independent review has not started. Reference-host measurement
> was blocked by the unavailable adapter, so enforcement remains unverified.
> Next: coordinator assigns review of this SHA; measurement owner reruns the live
> check when the adapter is available.

“Export is safe; all checks passed” would lose the timing condition, untested
case, review state and measurement blocker. Human review should compare those
facts rather than rewarding fewer words on their own.

## Keep status claims separate

| Claim | Required evidence / limit |
| --- | --- |
| Committed | Exact commit SHA; does not imply tested, reviewed, landed or published |
| Tested | Named setup, command, outcome and evidence; report failures and skips separately |
| Reviewed | Independent reviewer, exact unchanged revision, scope and open findings; does not imply every test or live measurement ran |
| Measured | Authorized live setup and recorded observations; offline fixtures or prose do not establish native runtime behavior |

These examples propose a reporting practice. Improved comprehension, reduced
omissions or reduced verbosity bias remain hypotheses pending the authorized
human-rubric evaluation tracked in #14. No prompt-content parser or runtime
adapter is supplied. Generic and managed sessions use the same reporting
principles while retaining their actual tools, permissions and evidence limits.
