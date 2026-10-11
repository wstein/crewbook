# Issue #107: current-host command audit

> **Historical evidence, not a current claim.** This file documents the host state and source revision of 2026-10-11 (source `897483f26b901521875d1d469c682ddafc8eb6bb`, refreshed against `4928e3be515a1daf68aab8d7a8c2fdba5c37a0ce` and `dd0b9e5`). That revision is behind current `main`, and the quoted commit hashes are not ancestors of it; later changes may have altered the sources, procedures and host this file describes. Re-measure before relying on it. The evidence below is preserved unchanged. The references to `dd0b9e5` and the older bases are pre-restack hashes that are not in `main` history; the equivalent changes landed under other hashes.

Maintenance evidence only; excluded from the distributed skill with `tools/`.
Recorded 2026-10-11 against source
`897483f26b901521875d1d469c682ddafc8eb6bb`, then refreshed after rebasing onto
independently reviewed #108 base `4928e3be515a1daf68aab8d7a8c2fdba5c37a0ce`
and adding status/logbook procedures in `dd0b9e5`. This records source inspection,
one disposable local Git experiment and existing offline adapter tests. It does
not establish native command loading, agent compliance or live forge behavior.

REST `gh api repos/wstein/crewbook/issues/107` exited 0. The issue was OPEN;
current requirements v3 retain an unchecked criterion for changed remote SHA,
unmerged work, incomplete acceptance and duplicate close/update attempts.
The checked source progress refers to #120 and reviewed revision
`e797c856cbcb9aee6d96f37e3932bb291c3fe2b9`, explicitly guidance only.
This audit supplies evidence for review, not issue completion or permission to
close it. Issue/card writes remain the coordinator's responsibility.

## Canonical resources and entrypoints

| Name | Source observed | Boundary |
| --- | --- | --- |
| ship | `.agents/crewbook-ship.md`, `.claude/commands/crewbook-ship.md`, `docs/team.md` Ship procedure | Exact S binds CLEAR, topic push, PR head, status and checks; uncertain PR/status/comment writes reconcile before retry; one read-only watcher with deadline; direct final check before ready. No merge, main/tag push or force push. |
| restack | `.agents/crewbook-restack.md`, matching Claude command, team Restack procedure | Owned free topic worktrees only, parent first; all-equal range diff plus checks precede new exact-N review; explicit O lease, no refreshed-lease retry. No main/tag update, conflict resolution or merge. |
| tidy | `.agents/crewbook-tidy.md`, matching Claude command, team Tidy procedure | MERGED plus final-head/equivalence evidence before safe `branch -d`; partial criteria stay open; confirmed CLOSED before Done; actor ownership, checklist freshness and readback preserved. |
| release preparation | `.agents/crewbook-release.md`, matching Claude command, team Release lane | Assigned notes only; project values required; source checks allowed, snapshots/builds need explicit approval; tag/push commands are human handoff text. No agent tagging, release, publication or merge. |
| triage | No dedicated resource or command | Retained issue proposal explicitly allows triage inside desk initially. Do not claim an installed long-named command. |
| status | `.agents/crewbook-status.md`, matching Claude command, SKILL/team routing | Added after the baseline audit: bounded read-only state sections, unknowns and ref freshness; no fetch, checks, child or watcher. Read-only `tools/dispatch_snapshot.py` remains separate maintenance tooling. |
| logbook | `.agents/crewbook-logbook.md`, matching Claude command, SKILL/team routing | Added after the baseline audit: ignored local frontmatter, append-only session bodies/corrections, duplicate/freshness/readback reconciliation and monthly rotation without archive overwrite. |

The seven observed Claude wrappers delegate to canonical resources. Codex's
`$crewbook <procedure>` notation routes through the skill; Markdown files alone
register no CLI or native slash command. Native loading was not exercised.

`docs/team.md` Human-request contract bounds work and watchers to the active
human request. Retained handles and handbacks prove neither daemon operation
nor survival after the parent ends. `docs/tool-preflight.md` requires uncertain
external writes to be resolved before retrying. These are procedural guidance,
not runtime enforcement or prompt-parser assertions.

## Changed-remote experiment

A disposable bare repository and two local working repositories ran on Linux,
Git 2.56.0 and Python 3.13.5. The Python harness used
`tools/git_test_environment.py`'s minimal environment, a fresh private HOME and
XDG config location, null system/global Git config, empty credential helper,
disabled prompts/SSH agent and `GIT_ALLOW_PROTOCOL=file`. No inherited tokens,
credential stores or external remote were supplied. Temporary paths are omitted.

Every setup/read/local push exited 0. The harness observed remote O, created
candidate N, then let the second local writer advance the remote to C:

- O: `d9c974699c9ea60d63ea82b49d6d97dc7de3bc4c`
- N: `119a60fbb7e040ec3ed712f1c36a20bf992df471`
- C: `27e7f8fdd6d8d3b2bdbcf0a7047a693b7ab734be`

`git push --force-with-lease=refs/heads/topic:<O> origin <N>:refs/heads/topic`
exited 1 with a stale-info rejection. Separate `git ls-remote origin
refs/heads/topic` exited 0 and returned C, not N. A separate bare-ref listing
exited 0 and contained only `refs/heads/topic`; no main or tag ref existed.
Harness assertions passed, overall exit 0, and its temporary directory was
removed. This measures Git's explicit-lease rejection on a local transport,
not a reviewed native restack, authorized forge push or concurrent server API.

## Unmerged, incomplete and duplicate scenarios

| Scenario | Source outcome | Observed executable coverage |
| --- | --- | --- |
| Open or closed-unmerged PR; head differs without patch equivalence | Tidy keeps branch, `blocked: not integrated`; no deletion or issue closure follows from a PR reference alone. | Source inspection only; no native tidy/deletion run. |
| Merged PR supplies only part of acceptance | Verify every acceptance point against M; issue remains OPEN, Close entry unticked, card cannot become Done. | Source inspection only for acceptance verification; offline board tests separately reject Done for OPEN/unknown issue state. |
| CLOSED issue receives duplicate Done request | Coordinator may move only after CLOSED readback; repeated operation must preserve verified state. | Existing `test_closed_issue_can_move_to_done_and_is_idempotent` emits one fake-board mutation across two calls. |
| Board update times out after application | Read back before retry; do not repeat applied write. | Existing `test_uncertain_write_applied_is_not_repeated` observes one mutation. Stale readback blocks retry; failed readback reports unknown outcome. |
| Issue close times out, duplicate close requested or body changes concurrently | Tidy now explicitly rereads state/body, adopts CLOSED without another close, re-verifies changed criteria, reconciles uncertain application and permits at most one retry only after confirmed OPEN and fresh verification. Unknown closure blocks Done. | Source walkthrough only; no issue-close or concurrent issue-body adapter fixture found. No live closure/update was attempted; executable/native coverage remains unverified. |

`python3 -B -m unittest tools.test_board.MoveTests` from the source root exited
0: 14 existing tests passed, including OPEN/unknown Done refusal, CLOSED
idempotence, uncertain-write no-repeat, stale state and readback failure. These
tests use an in-memory fake GraphQL board, execute no live adapter, and do not
prove acceptance verification or issue closure. They are selected existing
maintenance tests; no mirrored prompt tests were added.

## Concrete follow-up and remaining gates

The dispatcher released canonical/inventory ownership only after independent
exact review of #108's base. This author then added the two missing procedures
and their wrappers/routing/resource lists as one focused commit and clarified
tidy's closure protocol separately. Source walkthrough results:

- An open/unmerged PR is retained by tidy step 2. A merged partial issue stays
  unverified/OPEN under step 3 and its Close entry stays unticked; step 5 rejects
  Done without CLOSED. No closure or deletion is inferred from merge alone.
- A duplicate close reads CLOSED and emits no repeated close. An uncertain
  close reads back before a bounded retry; unreadable/pending outcome blocks
  Done. Concurrent body changes force fresh criteria verification and unrelated
  content is preserved. These are procedural source checks, not runtime measurements.
- Keep issue and PR adapter scope distinct: this target requires REST for issue
  operations and supports the existing `gh pr` calls. Tidy's closure step already
  names REST `gh api` where required. This audit did not execute GraphQL calls;
  no blanket PR REST-only restriction or current PR-adapter defect was observed.
- Status/logbook now have canonical source procedures and thin wrappers; native
  registration remains unverified. Triage's deferred dedicated command is explicit.

Independent exact-revision review, any required integration, native command
loading and authorized adapter measurements remain outstanding. Issue #107
stays OPEN. No external push, PR/status/comment write, issue closure, board
mutation, settings change, login, main/tag push, build or release was attempted.

## Routine source checks

`python3 -B tools/crewbook-package.py check --root <audit-root>` exited 0:
source layout and inventory valid; runtime compatibility not established.
`python3 -B -m unittest discover -s tools -p 'test_*.py'` exited 0 after the
status/logbook resource additions: 311 tests ran, 310 passed and one optional
scanner integration test skipped because `GITLEAKS_TEST_BINARY` was not set. The
separate required pinned scan below ran successfully. Tidy's later change is
prose only; no prompt-content parser or executable behavior was added.
`python3 -B scripts/stray_processes.py` exited 0: no stray test processes.
Changed Markdown local link paths resolved (136 checked; anchors inspected
against existing canonical sections). `git diff --check` exited 0.
`bash tools/scan-secrets.sh <audit-root> <pinned-gitleaks>` exited 0 with
Gitleaks 8.30.1: nonempty full history, working tree and commit messages scanned
with redaction. Temporary paths and host handles are intentionally omitted.

Manual status/logbook source walkthroughs: a failed adapter section remains
unknown without fetching or spawning; stale local refs name the observed SHA
and uncertain remote state; an existing session entry is adopted without a
duplicate append; changed content blocks a write; uncertain write requires
readback; existing archive or mixed-month headings block rotation. These
outcomes are procedural inspection only, not native file writes or host tests.
Independent review identified that tidy's retention writer also needed the
canonical logbook protocol. The correction links that writer to the same
ignored/path/ownership/format/freshness/append/readback checks, preserves tidy's
heading/date, and records stable identity from the original reference/title/done
date. Walkthrough: invalid or linked logbook keeps the checklist entry; an append
with unreadable outcome keeps it; confirmed retention readback permits dropping;
a failed checklist write leaves both copies and the next invocation adopts the
existing retention identity, including a verified rotated archive. These are
prose checks; no prompt parser or additional runtime enforcement was introduced.
No package export or documentation/artifact build was run.
