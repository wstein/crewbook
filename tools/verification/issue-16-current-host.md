# Issue 16: bounded current-host supervision evidence

> **Historical evidence, not a current claim.** This file documents the host state and source revision of 2026-10-11 (source `9150e358bbae9fd413cd3ea8b6448094efa03f36`). That revision is behind current `main`, and the quoted commit hashes are not ancestors of it; later changes may have altered the sources, procedures and host this file describes. Re-measure before relying on it. The evidence below is preserved unchanged. The stale allocation criterion it flags for design-owner reconciliation may since have been reconciled; check current `docs/team.md` and `.agents/crewbook-desk.md`.

This is partial evidence for [issue 16](https://github.com/wstein/crewbook/issues/16),
recorded on 2026-10-11. It is maintenance evidence excluded from the distributed
skill by the existing `tools/` policy. Missing verification is not a successful
fix. No executable behavior changes, so no artificial failing test was added.

## Reference surface and evidence sources

The source base is `9150e358bbae9fd413cd3ea8b6448094efa03f36` in the assigned
isolated issue-16 checkout. Commands use `$CHECKOUT` for its canonical root.
Stable labels below identify desk, retained dispatcher, issue-16 verifier,
issue-26 author and issue-26 independent reviewer. Private paths, handles and
unedited transport receipts remain in the coordinator's session record.

The actual execution surface is this API tool host, exposing collaboration
message, follow-up, list and wait tools. No native Codex CLI/app version or
build was supplied or measured. Observed shell setup is Python 3.13.5 and Linux
`7.0.14-orbstack-00380-ga7e0a2dc9535 aarch64`. These shell details do not identify
the client implementation. No builds, logins, provisioning, parent shutdown,
forced saturation or host settings changes were performed.

The shell sandbox failed before executing the first command with
`bwrap: Can't mount proc on /proc: Operation not permitted`. Scoped host
escalation allowed the authorized reads and checks. This is an observed tool
failure and bounded recovery, not a general permission guarantee.

There are three distinct evidence classes: direct verifier observations,
compact coordinator receipts for earlier live events, and static source or
offline checks. A coordinator receipt is attributed testimony rather than a
fresh independent replay. Timing is unknown unless an actual clock is given.

## Direct retained-channel observation

The retained dispatcher sent a fresh challenge to the already assigned verifier.
The same verifier acknowledged it with a clock reading and the next named
artifact, this file. No new worker or claim was requested for this exchange.

| Observation | Value |
| --- | --- |
| Nonce | `CB16-H1-20261011T102016Z` |
| Dispatcher issue clock, supplied in its message | `2026-10-11 10:20:16 UTC` |
| Verifier receipt clock, measured with `clock__curr_time` | `2026-10-11 10:20:29 UTC` |
| Acknowledgment | Same assigned verifier, nonce and next named artifact returned with `collaboration.send_message` |

The 13-second difference includes delivery, scheduling and time until the
verifier clock call. It is not a precise message-arrival measurement, round-trip
time, completion-to-review latency, queue wait or idle time. This exchange
establishes active retained-channel communication only; it does not demonstrate
resuming a dispatcher after a parent turn ends.

## Coordinator receipts for actual supervision

The retained dispatcher supplied these compact receipts from the current host.
No retrospective timestamps or exact latency claims are assigned to them.

| Event | Attributed observation and boundary |
| --- | --- |
| Dispatcher identity | The coordinator confirms desk has retained the same dispatcher since session startup. Identity retention is reported; the direct challenge above measures its channel to this verifier. |
| Actual desk follow-up | The dispatcher reports receipt of desk's real `followup_task` nonce `crewbook16-root-resume-20261011-a` through its unchanged handle, with receipt clock `2026-10-11 10:22:44 UTC`. Claims remained owned; the named next actions were forwarding this receipt and continuing the same issue-50 author. The dispatcher was running when it received the follow-up. Desk's issuance clock is unavailable, so no round-trip or delivery latency is calculated. |
| Issue-26 completion | The coordinator processed the existing author's candidate `d4a1da`, then routed a fresh independent exact review. This is a reported completed handback, distinct from the live message handshake. |
| Findings and correction | That review returned NOT CLEAR for a Medium commit-rationale finding and a Low private-path finding; the same author corrected to `37397761b71a669de7db6ed19e665d11874353b6`, and the same independent reviewer returned SOURCE CLEAR on that revision. The correction commit identity and subject were independently read with Git. |
| Authorized handoff | The coordinator reports the same author opened [draft PR 125](https://github.com/wstein/crewbook/pull/125), checked its exact remote head, base PR 121 and one-file scope. This record does not itself revalidate the forge head or claim merge/publication authorization. |
| Board ownership | The coordinator reports its approved board move read back `#16 Blocked -> In progress`, with issue OPEN, and confirms it is the sole card writer. This verifier made no card write and did not independently read the board. The issue itself was directly read OPEN. |

The completion-to-review order is reported by the coordinator; it supports
processing that particular handback and routing its findings to retained owners.
There are no measured event timestamps to quantify “as soon as a slot is free.”
It does not demonstrate automatic handoff across both repositories, every
review-ready completion, idle drain or recovery after the parent ends.

## Capacity and stale-criterion reconciliation

Actual host metadata advertises 17 concurrency slots including this agent, and
provides message, follow-up, list and wait operations. It exposes no close or
release operation. Metadata is a supported ceiling, not measured admission at
saturation; retained or completed handle counts do not establish free slots.

The latest coordinator receipt relays the user's explicit session limits:
four authors total, at most two per repository, and three independent reviewers.
This supersedes the earlier receipt of two reviewers. The current issue body
still asks for three source workers total and at most two per repository.
The inspected canonical role guidance also still describes lower generic caps.
These are stale criteria requiring explicit reconciliation through the design
owner, who owns the canonical changes in issue 50. This evidence records the
session-specific authorization and conflict; it creates no new global rule,
raises no cap itself and claims no capacity-release measurement.

## Source checks and remaining gates

Canonical [supervision guidance](../../docs/team.md#dispatch-supervision-and-recovery)
already describes completion draining, retained ownership, exact review,
same-author and same-reviewer corrections, bounded named waits, full-pool
handling, stop conditions and resume notes. Static inspection establishes that
guidance exists, not that a live client always follows it. Existing offline
recovery scenarios are reference-model checks, not native runtime evidence.

The following existing checks ran successfully on this evidence candidate in
the assigned checkout. Outputs below are sanitized summaries; tool receipts
retain the original stdout, stderr and exit status in the private session.

| Command | Exit | Observed output |
| --- | --- | --- |
| `python3 -B tools/crewbook-package.py check --root "$CHECKOUT"` | 0 | `source layout and inventory valid; runtime compatibility not established` |
| `git diff --check` | 0 | No diagnostics. |
| `lychee --offline --no-progress tools/verification/issue-16-current-host.md` | 0 | Three unique links, one OK, zero errors, two excluded external links. |
| `bash tools/scan-secrets.sh "$CHECKOUT" /opt/bundledock/toolbox/bin/gitleaks` | 0 | `nonempty full history, working tree and commit messages scanned with redaction` |

The existing scanner reported version 8.30.1, matching the repository pin.
External HTTP checks and native lifecycle benchmarks were not run. Package
validation is not a documentation build; no artifact was built or exported.

The assignment remains review-ready at handback, with independent exact-revision
review and any corrections owned by the coordinator. This record cannot certify
its own future review or a fully drained queue. Issue 16 remains open.

| Remaining claim | Next evidence or owner |
| --- | --- |
| Repeated desk requests actually resume the same dispatcher | One actual same-handle desk follow-up is reported above. Preserve further request/resume receipts and distinguish active steering from idle activation; this subset does not establish every startup or idle-resume case. |
| Unexpected yield recovered by active desk | Observe an actual yield and continuation registry, followed by a successful same-handle resume while desk remains active. No forced parent shutdown is needed or claimed. |
| Native capacity admission, full pool and release | Record actual supported admission outcomes when authorized work needs them. Do not force saturation or assume a release tool. |
| All review-ready completions, both repositories, actual reviewer model and exact SHA | Coordinator must preserve independent exact-review receipts and actual model evidence for each item; one attributed issue-26 sequence is insufficient for the general criterion. |
| Registry reconstruction and board automation | Preserve and validate actual issue/card/registry ownership evidence. A reported board move is not reconstruction or automation verification. |
| Empty versus blocked/full, once-only empty request and completed drain | Observe a real resolved queue transition with all remaining obligations and next actions recorded. This active assignment is not empty. |
| Slot-limit criterion | Design owner reconciles stale issue text and canonical guidance with the explicit current session instruction. |
| Cross-client/platform lifecycle, parent turnover and Workharbor runtime recovery | Require separately authorized reference setups and measurements; this API tool-host subset supplies none. |
| Milestone queue, report via issue 13 and matched comparison with issue 14 | Coordinator retains these separate acceptance obligations; no comparison, milestone readiness or benefit is measured here. |

No daemon, unattended timer, forge polling or parent-independent restart is
supplied or inferred. Partial evidence does not close the issue or clear its
remaining native gates.
