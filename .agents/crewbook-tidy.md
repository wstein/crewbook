# CrewBook Tidy

Read [SKILL.md](../SKILL.md), [policy-composition.md](../docs/policy-composition.md),
and [team.md](../docs/team.md).
Use crewbook-generic by default as described in [project-config.md](../docs/project-config.md).
Resolve the target from the user workspace/task and read applicable instructions.
Apply [native tool preflight](../docs/tool-preflight.md) before tool calls.
Resolve these links relative to this file. Host authority and authorization outrank package
guidance; a missing required tool stops the affected step.

You are `crewbook/tidy`, the procedure the desk runs after a merge to remove what is
integrated, maintain verified issue closure and clean `.work/CHECKLIST.md`. It is a
procedure of the coordinator, not a lane: it starts no issue worker. Assignment: optional PR
numbers (default: all local topic branches) and the checkout.

Never: merge, tag, release, deploy, push, force-push, delete anything without
the evidence below, or change settings. Local branches, worktrees,
`.work/CHECKLIST.md` and authorized coordinator issue/card writes are its scope.
Follow the [human-request contract](../docs/team.md#human-request-contract).
Delete with `git branch -d` only; never `-D`, `git worktree remove --force` or `git clean`.

Helper model: bulk reference checks (many PR, issue, commit or tag lookups) go to the
helper tier of the configured model mapping ([README](../README.md),
[team.md](../docs/team.md)); never hardcode it here. If the mapping names none, ask the
coordinator; never pick one (gap tracked under #108). Helpers are read-only and report
facts per reference; the desk decides and acts.

Steps:
1. `git fetch --prune origin` as its own command (the prune only removes stale remote-tracking
   refs of branches deleted on the remote, for example after a merge; it never deletes local
   branches or commits, so the `git branch -d` only rule and "`spike/*` is never deleted" are
   unchanged, and a pruned `origin/spike/*` ref is no reason to delete the local branch). Read `git worktree list`, the registry/claim
   records and the open assignments. Record `origin/main` SHA `M`; every check below
   names `M`, not the local `main`.
2. Branches and worktrees. For each local topic branch (never `main`, `landing`, the
   current branch of an occupied worktree) collect: its PR (`gh pr list --head <b>
   --state all`), the PR state and final head (`gh pr view <n> --json
   state,headRefOid,mergedAt`). With no argument scan all local topic branches; with PR
   numbers limit steps 2-3 to those PRs' branches and issues. Integration evidence is both: the PR is `MERGED`
   and either the branch head equals the PR's final `headRefOid` or the branch tree is
   patch-equivalent to `M` (`git cherry origin/main <b>` shows no `+` lines). Only then:
   if the branch is checked out in a worktree, that worktree must be clean
   (`git status --porcelain` empty) and named by no assignment or claim; detach it at
   `origin/main` first (free means detach, not remove). Then `git branch -d <b>`; its
   refusal is a veto, never forced (see `kept: integrated, -d refused` below).
   Keep and report everything else: no PR, open or closed-unmerged PR, head differs
   without patch equivalence, dirty or occupied worktree, active assignment, every
   `spike/*`, any uncertain read.
3. Close list. For each issue whose work is claimed done (merged PR `Closes`/`Refs`,
   checklist `Close` entries, issues named by deleted branches), verify against `M`:
   the closing commit or PR is an ancestor of `M` (`git merge-base --is-ancestor`) and
   every acceptance point the issue lists is met on `M`. List only verified ones with
   the proof (PR, SHA); put partial or unclear ones under "not verified" with the gap.
   Immediately before a close, re-read the issue state and body through the
   target's configured authorized issue adapter. If the body changed since
   acceptance verification, reconcile it and verify the current criteria again;
   preserve unrelated content, never replace the body as part of closing.
   Already CLOSED means no repeated close; record that readback separately from
   completion evidence. Within authorized scope the coordinator closes only
   verified issues still OPEN, then reads back CLOSED through the same adapter.
   An uncertain close (timeout, failed response or unknown application) is
   reconciled by reading state before any retry. Confirmed CLOSED means no retry;
   confirmed OPEN allows at most one retry after fresh criteria/body and scope
   verification. Unreadable state, another uncertain result or exhausted retry
   means `blocked: closure outcome pending`; do not repeat the close or mark Done.
   Use REST `gh api` where target policy requires
   REST-only forge access; use `gh issue close` only when the target permits it.
   Missing authority or capability yields a verified close list for the human.
   A partial merged PR leaves the issue open; never close from merge alone.
4. Checklist `.work/CHECKLIST.md` (format: [#107](https://github.com/wstein/crewbook/issues/107)).
   Read the frontmatter first: `type: checklist`, `schema`, `updated`, `owner`. Schema 2
   is current; schema 1 (no emoji, `who:` in the parenthetical) is still accepted: process
   it as below with `who: human` read as 🧑 and `who: desk` as 🤖 (a missing `who:` counts as no emoji), change no format and
   report once that the file should be migrated to schema 2; never fail on it.
   Schema 2 entry: `- [ ] <emoji> **Title** [#N](url): sentence (prio: P2, kind: do,
   waits: #28, added: 2026-10-09)`.
   - Actor: the emoji after the checkbox is mandatory on every entry, `Done` included:
     🧑 human, 🤖 desk/LLM. An entry without one is reported (`defect: no emoji`), never
     guessed and never fixed by tidy. Tidy acts only on 🤖 entries (tick, move, drop). 🧑
     entries are never changed; report their state (for example a ticked human entry, or
     a reference already done) and respect the human's ticks and their position.
   - Attributes in the trailing parenthetical: `prio` (P1-P3), `kind` (do, decide, wait,
     review), `waits`, `added`, `done`. Unknown attributes are kept as they are. A missing
     `added:` is reported.
   - Tick (🤖 entries): for each open entry read its reference (PR, issue, commit or tag)
     against `M` and GitHub. Done means the PR is merged or the issue is closed or the
     commit/tag is reachable from `M`. A done entry becomes `- [x]` and moves to `Done`
     keeping its emoji. Dates sit in the parenthetical as `added: 2026-10-09`; in Done
     `added: 2026-10-09, done: 2026-10-10` with `done:` set to today (same date format).
   - Retention: for `Done` 🤖 entries with `done:` more than 7 days ago, first
     append one line (`- <date> <title> <ref>`) to an existing `.work/LOGBOOK.md`
     under its own heading `## <date> tidy` (never inside a session entry).
     Apply the canonical [logbook writer protocol](crewbook-logbook.md), including
     ignored/owned/non-linked regular-file and format checks, freshness, stable
     retention identity, uncertain-append reconciliation and exact readback.
     The line keeps exactly this format; the stable retention identity adds no field.
     It is the entry's reference plus title, matched against the lines under `## <date> tidy`
     headings in the current logbook and verified monthly archives. A tidy-only append in
     a new month follows the logbook's first-append rotation rule before appending.
     Drop the checklist entry only after that retention record is confirmed by
     readback; an already-recorded identity is adopted without another append.
     Without a logbook or with any blocked/uncertain append or readback, keep the
     entry and report the gap. A later checklist-write failure retains both copies;
     the same retention identity prevents a duplicate on the next run.
     🧑 `Done` entries are never dropped: report those with `done:` more than 7 days ago as
     `retention due` (the human removes them).
   - Order: sections `Now`, `Decide`, `Later`, `Close`, `Settings`, `Done`, in this order.
     `Now` holds only 🧑 entries; a 🤖 entry found there (or a schema-1 `who: desk`
     one) moves to `Later` and is listed in the report. Desk tasks live in `Later`. `Close`
     entries confirmed CLOSED in step 3 are ticked and moved if 🤖; a verified 🧑 entry stays
     unchanged and is reported as closable with its close command. Unverified ones stay unticked in place and are listed under
     "not verified". Never replace `Close` by the verified list.
     Keep each entry's title, link, sentence, emoji (or `who`) and indented command block
     unchanged; commands carry no `#` lines.
   - Report, never delete: entries without a reference, without a creation date, or whose
     reference cannot be read.
   - Record `updated` (or a content hash) when reading; re-read it just before the write.
     Set `updated` to the current local time with offset. Write the file once, after all
     reads, keeping a copy of the previous content until the write is read back; on a
     mismatch restore the copy (`blocked: checklist write`).
5. Board. Only through the configured authorized writer (project config), only for cards
   whose merge or review state step 2/3 verified. Move to `Done` only after
   reading back the issue as CLOSED; OPEN or unknown state blocks Done. Without a
   configured writer or with board mode none, skip and say so.
6. Stray processes (report only). Run `python3 -B ../scripts/stray_processes.py` (path relative to this file; read-only `ps`;
   without the script: `ps -axo pid=,ppid=,etime=,pcpu=,command=`). It lists processes whose command
   line names a temp test directory (a path under `/tmp`, `/var/tmp`, `/var/folders` or `$TMPDIR` with
   `/Test<Name>` or `pytest-of-<user>`) and that are orphaned (ppid 1) or older than 10 minutes
   at more than 80% CPU. Per process one block: pid, age, CPU, ppid, temp directory, test name
   if derivable, its child pids, one plain-English "why this looks stray" line and the copy-paste `kill <pid>`
   (and `kill -KILL <pid>` fallback) for the human; then "nothing was killed". None found: one
   line `no stray test processes`. The launcher of a full test run (see team.md, Haiku helpers) also runs it once after it. Tidy never kills anything. False positive: a legitimate long `make check-ci` or
   `go test -race` still running; check elapsed time and parent before reporting, a process
   with a live parent shell younger than the longest expected run is not stray.
7. Report to the human (in the project language): deleted branches (`git branch -d` exit
   codes), freed worktrees, kept items with the reason each, the close list with commands,
   the checklist diff in counts (ticked, moved, dropped, reordered, reported), board
   writes, the stray-process blocks (or `no stray test processes`), and every blocked outcome.

Blocked outcomes (nothing is deleted or rewritten for the affected item; the rest of the
run continues unless noted; report item, observed state and next human action):
- duplicate invocation (the checklist `updated` value or content hash differs from the one
  recorded when it was read, checked just before the write): `blocked: duplicate
  invocation`, checklist untouched, the rest reported. Branch steps are idempotent.
- uncertain evidence (PR not merged, head mismatch without patch equivalence, merge state
  unreadable): `blocked: not integrated`, branch kept.
- integrated but `git branch -d` refuses (rewritten SHAs after a rebase-merge):
  `kept: integrated, -d refused`, branch kept; report PR, `headRefOid` and cherry
  evidence plus the exact `git branch -D <b>` command for the human. Tidy never runs `-D`.
- checklist write read-back differs: restore the backup copy, `blocked: checklist write`.
- dirty or occupied worktree (uncommitted changes, held by another author, active
  assignment): `blocked: worktree occupied`, touch nothing in it.
- unreadable reference (PR, issue, commit or tag not found or the call failed): the entry
  keeps its place, unticked, marked in the report as `blocked: reference unreadable`;
  an uncertain read is retried once as its own command, never guessed.
- uncertain issue close without confirmed CLOSED readback: `blocked: closure outcome
  pending`; retain the issue/adapter evidence and next read, never repeat blindly or mark Done.
- checklist without valid frontmatter or with a `schema` other than 1 or 2: `blocked: checklist
  format`, checklist untouched; steps 2, 3, 5, 6 and 7 still run.
- `origin/main` unreadable or fetch failed: `blocked: main unknown`, stop the whole run.

Apply the [precise reporting contract](../docs/team.md#precise-issues-handovers-and-review-reports).
Card and issue writes stay with the designated coordinator.
Workflow and context boundaries: packaged team manual. Claude tier: Sonnet (the desk's own);
bulk reference checks use the configured helper mapping; Codex per README mapping.
