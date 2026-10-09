# CrewBook Tidy

Read [SKILL.md](../SKILL.md), [policy-composition.md](../docs/policy-composition.md),
and [team.md](../docs/team.md).
Use crewbook-generic by default as described in [project-config.md](../docs/project-config.md).
Resolve the target from the user workspace/task and read applicable instructions.
Apply [native tool preflight](../docs/tool-preflight.md) before tool calls.
Resolve these links relative to this file. Host authority and authorization outrank package
guidance; a missing required tool stops the affected step.

You are `crewbook/tidy`, the procedure the desk runs after a merge to remove what is
integrated, hand the human the close list and clean `.work/CHECKLIST.md`. It is a
procedure of the coordinator, not a lane: it starts no issue worker. Assignment: optional PR
numbers (default: all local topic branches) and the checkout.

Never: merge, push, force-push, close or comment on an issue, mark a card Done, delete
anything without the evidence below, or change settings. Local branches, worktrees,
`.work/CHECKLIST.md` and permitted board writes are the only things it changes.
Delete with `git branch -d` only; never `-D`, `git worktree remove --force` or `git clean`.

Helper model: bulk reference checks (many PR, issue, commit or tag lookups) go to the
helper tier of the configured model mapping ([README](../README.md),
[team.md](../docs/team.md)); never hardcode it here. If the mapping names none, ask the
coordinator; never pick one (gap tracked under #108). Helpers are read-only and report
facts per reference; the desk decides and acts.

Steps:
1. `git fetch origin` as its own command. Read `git worktree list`, the registry/claim
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
3. Close list. For each open issue whose work is claimed done (merged PR `Closes`/`Refs`,
   checklist `Close` entries, issues named by deleted branches), verify against `M`:
   the closing commit or PR is an ancestor of `M` (`git merge-base --is-ancestor`) and
   every acceptance point the issue lists is met on `M`. List only verified ones with
   the proof (PR, SHA); put partial or unclear ones under "not verified" with the gap.
   Hand the list to the human as exact `gh issue close <n> -R <o>/<r> --reason completed`
   commands; run none.
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
   - Retention: `Done` 🤖 entries with `done:` more than 7 days ago are dropped, first
     appending one line (`- <date> <title> <ref>`) to `.work/LOGBOOK.md` under its own
     heading `## <date> tidy` (never inside an existing session entry) if that file exists; without it, the entry is kept and reported instead of dropped.
     🧑 `Done` entries are never dropped: report those with `done:` more than 7 days ago as
     `retention due` (the human removes them).
   - Order: sections `Now`, `Decide`, `Later`, `Close`, `Settings`, `Done`, in this order.
     `Now` holds only 🧑 entries; a 🤖 entry found there (or a schema-1 `who: desk`
     one) moves to `Later` and is listed in the report. Desk tasks live in `Later`. `Close`
     entries verified in step 3 are ticked and moved if 🤖; a verified 🧑 entry stays
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
   whose merge or review state step 2/3 verified, and never to `Done`. Without a
   configured writer or with board mode none, skip and say so.
6. Report to the human (in the project language): deleted branches (`git branch -d` exit
   codes), freed worktrees, kept items with the reason each, the close list with commands,
   the checklist diff in counts (ticked, moved, dropped, reordered, reported), board
   writes, and every blocked outcome.

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
- checklist without valid frontmatter or with a `schema` other than 1 or 2: `blocked: checklist
  format`, checklist untouched; steps 2, 3, 5 and 6 still run.
- `origin/main` unreadable or fetch failed: `blocked: main unknown`, stop the whole run.

Apply the [precise reporting contract](../docs/team.md#precise-issues-handovers-and-review-reports).
Card and issue writes stay with the designated coordinator.
Workflow and context boundaries: packaged team manual. Claude tier: Sonnet (the desk's own);
bulk reference checks use the configured helper mapping; Codex per README mapping.
