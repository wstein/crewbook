# Material limitations

Record a limitation when a concrete constraint affects the delivered behavior,
capacity or verification enough to matter to a future decision. Put it in an
existing issue, design record or nearby comment where the consuming project
already records that decision. Do not create a debt ledger, require branded
markers or add boilerplate to every shortcut.

Describe the boundary, the evidence for it, a measurable condition that would
justify revisiting it, and a plausible next step. Choose the trigger from the
project's requirements and operating conditions; “later” and “if needed” do
not tell the next reader when to act. Identify invented thresholds as
illustrative and unmeasured. A missing measurement is a verification limit,
not evidence that a design is adequate.

The consuming project's design owner decides acceptable tradeoffs under its
security policy and acceptance criteria. A limitation note cannot waive a
security defect, missing authorization or isolation, a failed required check,
or an unmet acceptance criterion. Report those as findings or incomplete work
and route them to the responsible owner. Keep an accepted tradeoff distinct
from an open defect even when both concern the same component.

## Examples

These examples illustrate useful records; they are not CrewBook measurements
or default thresholds for consuming projects.

- **Lock contention:** “The single-writer queue preserves ordering. In the
  named 20-writer load test, p95 lock wait was 8 ms; the project's budget is
  20 ms. Revisit if the same test at the required concurrency exceeds that
  budget. First profile lock hold time and propose moving independent work
  outside the lock to the design owner.” The test configuration and result
  belong beside this note. If the ordering criterion fails, report that
  failure rather than accepting it as contention debt.
- **Dataset size:** “The implementation loads the dataset into memory. The
  largest tested input contains 100,000 records; larger inputs are unverified.
  An illustrative, unmeasured revisit trigger is a supported input exceeding
  250,000 records or peak memory exceeding the deployment's agreed budget.
  Confirm the supported range and measure memory before choosing a streaming
  interface.” If today's required dataset exceeds the tested range, state
  which acceptance evidence remains missing; do not claim completion from
  this note.

Use relevant repository evidence and omit hypothetical limits that have no
bearing on the task. A nearby comment may link to the existing issue for the
measurement rather than repeat it. Retain enough detail to reproduce the
result: setup, input or concurrency, metric, observation and its uncertainty.

## Implementation, review and handover

Implement the smallest complete solution that preserves the stated behavior,
readability, validation, authorization, isolation, error handling and required
checks. This follows the [#11 starting prompt](https://github.com/wstein/crewbook/issues/11);
that issue remains a design input, not proof that its broader guidance is
complete or effective. A material limitation is a reasoned boundary of that
solution, not permission to omit a requirement.

Authors report the outcome, decisive verification, remaining limitation and
next action. Reviewers check the evidence and trigger, preserve location,
scenario and consequence for defects, and report criteria met or unmet.
Follow the [#13 reporting contract](https://github.com/wstein/crewbook/issues/13)
when composing the handover: prefer repository-relative paths, exact commits
and durable evidence links; keep necessary conditions and uncertainty. This
reference does not claim #13 has been implemented. Distinguish committed,
tested, independently reviewed and measured work.

This is reusable guidance for both [generic](profile-generic.md) and
[managed-container](profile-workharbor.md) workflows. Use available authorized
native-session tools in generic mode; managed provisioning and enforcement
remain host responsibilities. Evaluate transfer and benefit through
[#14](https://github.com/wstein/crewbook/issues/14) before making effectiveness
claims, and route gaps with a shared cause through
[#12](https://github.com/wstein/crewbook/issues/12). Drafting this guidance
requires neither live measurement nor a new tool or parser.
