# Safety-preserving simplicity ladder

Use this canonical coding prompt under applicable host, user and repository
instructions, as described in [policy composition](policy-composition.md).
An absent AGENTS.md is valid. Alternative skill sets or an explicit selection
of none remain supported; loading Crewbook does not replace those choices or
supply permissions. The same guidance applies in [generic](profile-generic.md)
and [managed-container](profile-workharbor.md) sessions without assuming tools,
containers, boards or credentials that the selected operation does not need.

## Canonical prompt

> Implement the smallest complete solution to the stated requirements. Read the affected flow first. Reuse existing code and prefer standard-library or native features. Avoid speculative abstractions and dependencies. Preserve readability, validation, authorization, isolation, error handling and required tests. Report the result, verification and remaining limitations concisely.

Apply the prompt in this order:

1. Understand the affected flow: callers, inputs, outputs, state transitions,
   failure paths and trust boundaries. Read the requirements and relevant checks
   before choosing an implementation. Identify the behavior that must remain.
2. Look for repository code and examples that solve the same problem under the
   same constraints. Follow the relevant path through its callers; a matching
   function name or similar syntax does not establish that it is suitable.
3. Prefer existing standard-library or native features when they meet the
   contract and supported environments. Account for semantics, safety,
   compatibility and error handling before replacing an existing dependency.
4. Implement a focused complete change. Keep justified interfaces and
   abstractions when they make actual shared behavior or a trust boundary clear.
   Avoid infrastructure for hypothetical callers or dependencies without a
   concrete need. Verify the requirements and affected boundaries with the
   project's meaningful checks, then report the result and remaining limits.

Smallest means focused scope, not the fewest lines. Preserve behavior,
readability, accessibility, validation, authorization, isolation, error handling
and required checks. For user-facing changes, retain accessible interaction and
feedback as part of the behavior. Do not remove validation or collapse distinct
error paths to make a change shorter. If the requirements cannot be met safely
within the proposed scope, report the conflict to the responsible owner rather
than labeling the missing behavior a simplification.

## Select examples by relevance

Choose relevant, nonredundant repository examples that clarify the affected flow
and its boundaries. There is no fixed number to collect. Inspect enough context
to explain why an example applies; avoid searching for additional examples just
to fill a quota. These scenarios illustrate that reasoning, not runtime results.
The maintenance files referenced here exist in source and are deliberately not
part of the exported instruction package.

| Scenario | Decision and verification |
| --- | --- |
| Appropriate reuse | A CLI change needs to read a bounded strict JSON policy. Inspect the existing `load_policy` path in `tools/packagefmt.py` and its callers rather than adding a permissive second loader. Reuse it if the schema and safety contract match; retain malformed JSON and filesystem rejection checks. |
| Inapplicable lookalike | A directory-copy example resembles package export, but does not validate inventory, reject unsafe filesystem entries or write the validated snapshot bytes. A convenient copy call cannot replace the export path merely because both create a directory. Compare the actual contract and keep the existing safeguards. |
| Justified abstraction | Descriptor-relative directory and file reads share ownership, mode, no-follow and metadata checks. The existing `directory_fd` and `read_at` helpers make those repeated safety requirements explicit. Preserve that interface when adding a caller with the same contract; adding a framework for unknown future backends has no demonstrated need. |
| Missed boundary case | A new export destination works, but an existing destination or symlink replacement can exercise a different path. Keep the existing rejection/race checks and verify that an outside file cannot be changed in the covered scenario. A happy-path export alone does not establish the boundary. |

Generated tests can help expose cases, but are not an independent oracle: a test
can repeat the implementation's mistaken assumption. Derive expected results
from the stated requirements, trusted contracts and independent evidence where
available. Inspect the failing case, confirm that the test observes the relevant
behavior and retain required existing tests. Do not weaken the expected result,
remove a required check or claim complete coverage merely because generated
tests pass. Independent review remains a separate responsibility.

## Handover and evidence boundary

Use the [precise reporting contract](team.md#precise-issues-handovers-and-review-reports)
and record [material limitations](material-limitations.md) when they affect a
future decision. State the delivered behavior, decisive verification, remaining
limitations and next action. A limitation note cannot waive an unmet criterion
or a security defect. Distinguish committed, tested, independently reviewed and
measured work, and keep live runtime claims unverified unless measured.

This is reusable guidance, not a runtime adapter, permission control or prompt
parser. Transfer to Go and current native clients, quality improvements and
savings remain unmeasured pending the authorized evaluation in
[#14](https://github.com/wstein/crewbook/issues/14). Lines removed, one-line
implementations and passing generated tests are not measures of success.
