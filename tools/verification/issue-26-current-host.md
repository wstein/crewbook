# Issue 26: current tool-host supervision evidence

This is a partial measurement for [issue 26](https://github.com/wstein/crewbook/issues/26),
recorded on 2026-10-11. It is source maintenance evidence, excluded from the
distributed skill by the existing `tools/` classification. It changes no runtime
behavior. Missing verification is not a successful fix.

## Setup and scope

- Initial source revision: `9150e358bbae9fd413cd3ea8b6448094efa03f36`.
- Source context: the assigned isolated issue-26 checkout. Commands below use
  `$CHECKOUT` for its canonical root; private paths and session handles are
  retained only in the coordinator's evidence record.
- Stable role labels: issue-26 author and retained dispatcher. The assignment
  reports `gpt-6.1-sol/medium`.
- Observed shell setup: Python 3.13.5; Linux
  `7.0.14-orbstack-00380-ga7e0a2dc9535 aarch64`.
- Reference execution surface: the current API tool host exposing
  `collaboration.send_message`, `collaboration.wait_agent`,
  `functions.exec`, `clock.sleep`, and UTC clock observations. No native
  Codex CLI/app build version was supplied or measured. Installed CLI discovery
  would not identify this tool host or establish another client's behavior.
- No builds, settings changes, credential-store access, provisioning, real
  containers, forge writes, or forced capacity exhaustion were part of this
  measurement. The coordinator retained claim/card/registry ownership.

The shell sandbox initially returned `bwrap: Can't mount proc on /proc:
Operation not permitted` before executing commands. Scoped host escalation
then permitted the already-authorized reads and source checks. This records a
local tool failure and recovery, not a universal client permission guarantee.

## Bounded native handshake

The coordinator issued H1 to the existing author handle. The author observed
the nonce, waited with a bounded sleep, and returned a channel message bearing
the same nonce, owner and initial revision. The coordinator preserved the
result and selected H2 through the retained handle. No replacement claim or
author was requested by this protocol.

The coordinator retains the unedited H1 receipt privately. This public table
summarizes its measured fields using stable role labels; it is not raw output.
The nonce and initial revision identify the bounded observation, without
publishing private paths, session handles or a full transcript.

| H1 observation | Recorded value |
| --- | --- |
| Nonce | `CB26-H1-20261011T095540Z` |
| Candidate | `9150e358bbae9fd413cd3ea8b6448094efa03f36` |
| Owner | Same issue-26 author |
| Coordinator issued challenge | `2026-10-11T09:55:40Z` |
| Author receipt clock | `2026-10-11T09:55:52Z` |
| Sleep elapsed | 5.0198 seconds |
| Author handback clock | `2026-10-11T09:56:01Z` |
| Coordinator recorded result | `2026-10-11T09:56:47.148337+00:00` |
| Next action | Same-owner coordinator steering H2 |

The UTC values are separate clock observations. The measured sleep tool output
was `Wall time: 5.0198 seconds` and `Sleep completed.` for
`clock.sleep({"duration_ms":5000})`. The coordinator's recording timestamp is
not a precise message-arrival timestamp. These observations do not establish
completion-to-review latency, scheduler latency, idle time or token use.

H1 returned using `collaboration.send_message` while the author was active.
It is a retained-channel delayed handback, not a child-completion notification,
a child returning after a parent turn ended, or an observed desk safety-net
resume. The private receipt's handback label does not broaden the observation.

H2 was coordinator steering with nonce `CB26-H2-20261011T095643Z`:
hold acceptance pending independent review and preserve the unverified client
boundaries. At `2026-10-11 09:57:59 UTC` the same author acknowledged that
nonce and the unchanged initial revision through `collaboration.send_message`.
The observed next action was to write this evidence candidate in the assigned
scope, then return it for exact independent review. This is coordinator
steering; no direct human-steering event was injected or measured.

## Source checks, separately measured

These authorized checks ran on the initial revision before this documentation
edit. They execute offline fixtures, not native clients or forge operations.
No executable behavior changed, so no artificial failing regression was added.

| Command in the assigned checkout | Exit | Observed output |
| --- | --- | --- |
| `python3 -B -m unittest discover -s tools -p 'test_dispatch_recovery.py'` | 0 | `Ran 33 tests in 0.004s`; `OK` |
| `python3 -B -m unittest discover -s tools -p 'test_*.py'` | 0 | `Ran 311 tests in 5.309s`; `OK (skipped=1)` |
| `python3 -B tools/crewbook-package.py check --root "$CHECKOUT"` | 0 | `source layout and inventory valid; runtime compatibility not established` |

The recovery suite covers retained owners, exact review continuations,
same-author and same-reviewer corrections, capacity states, steering, blocked
dependencies and the complete drain gate in its synthetic model. Passing it
does not turn those scenarios into native observations.

## Obligations and remaining measurements

At the evidence-author handback, this assignment is review-ready, not drained.
The coordinator must initiate independent review of the exact committed
revision and retain the author for any corrections. This document cannot
self-certify its own final review, completion processing or future actions.
The new evidence file's candidate SHA is the author handback's SHA, not the
initial source revision above.

| Claim | Result and next owner/action |
| --- | --- |
| Delayed retained-channel handback on this API tool host | Observed H1; coordinator retained the result and sent H2. |
| Same-owner coordinator steering | Observed H2 acknowledgment; independent review remains required. |
| Required independent review prevents drain | Active obligation retained at handback. Coordinator must obtain exact review and process findings; no successful final drain is asserted. |
| Actual child-completion processing and exact same-owner fix/re-review | Not established by H1/H2. Coordinator must preserve the final author-completion and actual reviewer/correction events separately. |
| Second-reviewer admission, full pool, release and reuse | Unmeasured. Coordinator reports host limit 17 and session role caps four authors/three reviewers; configured caps do not establish free capacity or release semantics. Measure actual admission when the next authorized review needs it. |
| Direct user steering and blocked-versus-drained native backlog | Unmeasured. Review-pending is active work; no synthetic dependency was presented as a real external blocker. Coordinator must record actual dependency owner/next action and the completed drain gate when they occur. |
| Unexpected dispatcher yield and active desk resuming the same handle | Unmeasured by this handshake. Desk owns a future bounded observation using the retained dispatcher and continuation evidence. |
| Native CLI/app versions, other clients and platforms | Unavailable in this measurement. The authorized host owner must supply a concrete reference client/setup before measuring it. |
| Continuation after the parent ends | Unverified. No daemon, automatic restart, forge polling or parent-independent execution is supplied or inferred. Host-event integration requires separate authorized measurement. |

Issue acceptance, checklist changes, board readiness and closure remain the
coordinator's evidence-based decisions after independent exact-revision review.
This partial record does not clear the remaining native criteria.
