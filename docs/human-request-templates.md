# Human request templates

These optional requests help make an outcome and its scope explicit. Ordinary
short requests such as “finish #N” or “where are we?” are sufficient when the
conversation already supplies the context. No exact phrase is required, and
the human is not responsible for repairing agent coordination through wording.
Replace bracketed placeholders with the relevant issue, option, date or evidence.
For a local task, replace “#N” with its description; no issue, board or
`AGENTS.md` is required. The templates apply to both
[generic native sessions](profile-generic.md) and
[managed containers](profile-workharbor.md). Explicit `$crewbook` or `$cb-desk`
in Codex, or `/cb-desk` in Claude, starts or reuses dispatch automatically
when the client supports it. No root variable or separate dispatch start
is needed; ordinary task requests require no command syntax.

Use the [concise reporting contract](team.md#precise-issues-handovers-and-review-reports)
and its [handover examples](handover-examples.md) for the resulting reports.
Use the existing [ownership and workflow contract](team.md#coordinator-and-leaf-execution-contract)
and [project configuration](project-config.md). These examples grant no new
permissions, tools or decision authority. Continue within existing authorization;
ask only when a material choice or required authorization is still missing.
Local landing and publication are separate outcomes: a local commit does not
establish either, and a request to land locally does not authorize a push.

## Optional copyable requests

| Situation | Request |
| --- | --- |
| Finish an issue | Finish #N through the configured checks, independent review and local landing. Reuse its existing assignment. Report the resulting commits and remaining blockers. |
| Audit progress | Show actual progress since [time]: active owners, commits, check results, independent reviews and locally landed changes. Separate requested actions from confirmed outcomes. |
| Recover dispatch | Drain completed handbacks first, reconcile ownership and available capacity, then start the highest-priority eligible work. Report the next concrete action or named dependency. |
| Discuss options | Discuss [question] with the relevant roles. Give five options rated out of five, evidence and one recommendation. Discussion only. |
| Approve selected options | Adopt options [1–3] from [discussion]. Reuse existing issues and assignments; implement, test, obtain independent review and land locally within the agreed scope. |
| Set a test target | Target [date] for one real end-to-end run of [workflow] on [authorized setup]. Separate human decisions from agent work. Report readiness with evidence and unmet prerequisites. |
| Claim human ownership | I own #N and its workspace until handover. Agents may review read-only; do not edit or run probes. Route findings back to me. |
| Hand back evidence | Published [branch] at [full SHA]. Verified: [test and setup]. Unmeasured: [limitations]. Review this revision and advance eligible dependent work within existing authorization. |

For discussion, ratings compare the stated options against the requested
outcome; they are judgments, not measured success rates. An implementation
approval selects only the referenced options. Keep other options unselected
and preserve human ownership until an explicit handoff. A test target names a
desired result, not evidence that the setup or workflow is ready. A human's
publication handback reports an action already taken; it does not authorize
agents to publish additional changes.

## Four-line status

Ask “Four lines: outcome, evidence, blocker, next action.” Use longer detail
when needed to preserve a finding's location, trigger, consequence or uncertainty.
Repository-relative paths, exact commit SHAs and durable links keep the report
usable outside the current session. Keep credentials, machine paths, local
thread identifiers and command transcripts out of public reports.

```text
Outcome: [attained result and issue; distinguish committed, reviewed, landed and published]
Evidence: [full SHA, repository-relative file, checks and exact review revision]
Blocker: [specific missing artifact, unresolved finding or none]
Next action: [owner and concrete action within existing authorization]
```

For example, after an author returns a commit and successful checks, but before
independent review or landing:

```text
Outcome: #N is committed locally; independent review and landing remain pending.
Evidence: [full SHA]; docs/guide.md; configured documentation checks passed.
Blocker: Independent review of [full SHA] has not returned.
Next action: The designated coordinator assigns an eligible independent reviewer.
```

“Done” would overstate this example. A scheduled check is not a passed check;
a reviewer request is not a review result. A clean review of an older revision
does not clear a changed commit. Report an unavailable landing procedure as
unavailable, even when implementation and checks are complete.

## Routing and reporting walkthrough

**Static documentation comparison**, evaluated against the linked
ownership and configuration contracts. The cases below record concrete inputs,
expected actions and the conclusion of that comparison. They do not measure
live model routing, dispatch recovery or native client support. Missing runtime
measurements remain **unverified**; these examples cannot establish production
Codex support. Evaluate the action and attained state, rather than whether an
answer repeats words from a template.

| Input and existing state | Expected route and observable outcome | Walkthrough result |
| --- | --- | --- |
| “Finish #N”; the coordinator already assigned an active author, checks are pending | Desk routes to the existing coordinator; the author continues the assignment. Report pending checks until their results arrive. | Consistent with single ownership. Reject another claim, duplicate author or a completion claim based only on the request. |
| Finish template; a topic commit has passed checks, but the supplied landing procedure is unavailable | Author returns the exact SHA and passed checks; coordinator owns independent review. Report committed, unlanded work and the unavailable procedure. | Consistent with the configuration contract. Reject fabricated landing or publication; the requested outcome remains unmet. |
| “Where are we?” and the audit template; one author is active, commit S passed checks, a review is requested, nothing landed | Desk reports the active owner, committed/tested S, pending review and no confirmed landing or publication. | Both wordings route to status reporting. Reject treating a requested review as a completed review or silence as a released author slot. |
| “Unstick dispatch” and the recovery template; a completed handback is available, another author remains active | Designated coordinator preserves the handback, reconciles its confirmed state, arranges needed independent review and reuses capacity only after completion is established. | Compatible with coordinator ownership and #16's recovery scope. This is an expected recovery trace, not an observed live recovery. Reject a duplicate start or abandonment inferred from silence. |
| “Let's discuss [question]”; a design-owned decision may be involved | Desk gathers options and routes rule questions to the design owner; returns evidence, ratings and a recommendation without implementing. | Discussion does not assign an implementation worker. Reject edits or treating a recommendation as approval. |
| “Go with 1 and 3”; the preceding numbered discussion is clear, the human owns option 3's workspace | Coordinator reuses the eligible issue/assignment for option 1; option 2 remains unselected. Option 3 waits for the human's handoff before agent edits. | Existing approval is reused without a repeated approval question. Reject scope expansion or overlapping editors. If the referenced discussion is ambiguous, resolve that selection first. |
| Test-target template; the date is set but the authorized reference setup is absent and no end-to-end result exists | Coordinator routes readiness work to the assigned author/verification owner; reports the missing setup and unmeasured run, with human decisions separated from agent tasks. | Target and attained state remain distinct. Reject declaring readiness, provisioning a substitute host or treating a mocked check as a real run. |
| “I'll take #N”; the human explicitly reserves its workspace and allows read-only review without probes | Coordinator records the human's ownership; reviewers return findings from permitted reads. Agents wait for an explicit handoff before edits or probes. | Preserves ownership even if an agent has spare capacity. Reject a competing author or an allegedly read-only test that executes probes. |
| Evidence-handback template; human reports published S and a named test, but independent review covers older T | Coordinator preserves the evidence with its source and limitations and assigns independent review of S; dependent work advances only when its actual prerequisites are met. | Publication and human-reported measurement do not imply review of S. Reject carrying T's approval forward or marking dependent work complete from the handback alone. |

The dispatcher recovery trace uses [issue 16's acceptance scope](https://github.com/wstein/crewbook/issues/16),
while report brevity follows [issue 13's evidence requirements](https://github.com/wstein/crewbook/issues/13).
Those issue descriptions are task references, not new policy authority. This
walkthrough does not assert that their whole acceptance criteria are complete.
