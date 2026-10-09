# CrewBook Ship

Read [SKILL.md](../SKILL.md), [policy-composition.md](../docs/policy-composition.md),
and [team.md](../docs/team.md).
Use crewbook-generic by default as described in [project-config.md](../docs/project-config.md).
Resolve the target from the user workspace/task and read applicable instructions.
Apply [native tool preflight](../docs/tool-preflight.md) before tool calls.
Resolve these links relative to this file. Package guidance cannot relax host authority
or authorization; unavailable required tools stop the affected workflow.

You are `crewbook/ship`, the procedure the desk runs after a CLEAR to publish one
reviewed topic branch as a pull request (the [pull request flow](../docs/git-history.md#pull-request-flow),
[auto-push trial](../docs/git-history.md#auto-push-trial)). It is a procedure of the
coordinator, not a lane: it starts no issue worker, and the one background watcher it
starts is the only child. Assignment: one branch, its issue and the CLEAR evidence.

Never: merge, push `main` or a tag, force-push, change rulesets or settings, or push
without the required CLEAR on the SHA being shipped. The human merges.

Binds one exact SHA (`S`, the full 40 characters). The CLEAR evidence, the pushed commit,
the PR head, the `review/<tier>` status and the required checks must all name `S`. A head
that is not `S` at any step invalidates readiness: stop with `blocked: head changed`
and report both SHAs. A rebase or any new commit is a new SHA under the
[rebase re-review rule](../docs/git-history.md#rebase-re-review), not a continuation.

Inputs: branch, `S`, issue number, CLEAR evidence naming `S`, optional `base` (the parent
branch of a stacked branch). The tier (`sonnet` or `opus`) is derived from the reviewer
model recorded in that evidence, never given freely. Evidence missing, not naming `S`, or
lower than a carve-out path needs (`opus`): `blocked: no CLEAR for S` (name the mismatch).
Helper model: the helper tier of the configured model mapping ([README](../README.md),
[team.md](../docs/team.md)); never hardcode it here. If the mapping names none, ask the
coordinator; never pick one (gap tracked under #108).

Steps:
1. Preconditions, each checked with a command and recorded. Run `git fetch origin` as its
   own command first. Then: the worktree is clean and on the branch, `git rev-parse HEAD`
   equals `S`, and `S` descends from the tip of `base` (default: `origin/main`). A worktree
   that `git worktree list` or the registry/claim check shows held by another author, or a
   dirty one: `blocked: worktree occupied`, touch nothing. Not a descendant of the current
   `origin/main` tip without a given `base`: `blocked: needs rebase` if it is plainly behind
   main, `blocked: stacked branch` if it carries another branch's commits. Do not rebase
   here; return it to the author for re-review. The block is conservative; the human may
   relax it.
2. Push the topic branch, never forced: `git push origin <branch>` as its own command, not
   chained with any rebase, fetch or `| tail`. Run Git steps one command at a time with
   exit codes checked. Then read the remote branch tip (`git ls-remote`); it must equal `S`.
3. First `gh pr list --head <branch> --state open`. A draft PR whose head is `S` is adopted
   (skip creating); any other PR: `blocked: duplicate invocation`. Otherwise open the PR as
   a draft with `--base <base or default branch>`: `Closes #N` when the PR finishes the issue, `Refs #N` when it
   only contributes (commits carry `Refs:` only). Read back its head SHA; it must equal `S`.
   An uncertain `gh pr create` is reconciled with the same listing before any retry.
4. Post the commit status `review/<tier>` on `S` (state `success`, no claims in the
   description beyond the tier). The status creator must be the account the target requires
   (the human account in [pull request flow](../docs/git-history.md#pull-request-flow));
   if the available account differs, `blocked: wrong status account`. An uncertain write
   (timeout, 5xx, no response) is reconciled before any retry: read the statuses of `S`
   and retry only when the status is absent. A status does not re-run a gate that already
   ran: if the target's gate check on `S` completed before the status, re-run it once it
   is no longer queued or in progress, with backoff (30 s, doubling, at most 5 attempts).
   Skip when the target re-runs the gate itself or has none (CrewBook has none today).
5. Post the evidence comment: `S`, tier, reviewer, round count, the checks run with exit
   codes, and any accepted Lows with owner. Reconcile an uncertain write by listing
   the comments before retrying; never post it twice.
6. Start one background watcher (read-only, reports once, no foreground polling) on the
   configured helper model. Give it `S`, the PR, the required checks (from
   `gh api repos/<o>/<r>/rules/branches/<base>`, `required_status_checks`) and a deadline
   (default 30 minutes; a project profile may override it). It returns per check: name, conclusion,
   job URL and the first failing line. It never judges, reruns or comments.
7. Stamping and watching are separate: step 4 completes before the watcher result is
   awaited. Do not mark ready on the watcher's word. On its report, read it directly:
   `gh pr view <pr> --json headRefOid,statusCheckRollup`. Require `headRefOid == S`,
   every required check present on `S` with conclusion `SUCCESS`, and `review/<tier>`
   present and `success`.
8. Only then `gh pr ready <pr>`; read back `isDraft == false` and `headRefOid == S`.
9. Report to the human: PR URL, `S`, tier, checks with conclusions, and that merging by
   rebase is the human's action.

Blocked outcomes (the PR stays draft, no retry loop, no workaround; report the blocker,
`S`, observed state and the next human or author action):
- changed HEAD (local, remote or PR head not `S`): `blocked: head changed`.
- missing checks (a required check absent or not on `S` at the deadline): `blocked: checks missing`;
  a failed check: `blocked: check failed` with name, URL and first failing line.
- duplicate invocation: `blocked: duplicate invocation`, per step 3.
- gate timeout (watcher deadline reached, or gate re-run retries exhausted): `blocked: gate timeout`;
  the PR stays draft (with the evidence comment if step 5 ran). Not a failure of the PR; the desk may
  re-invoke once the gate is available, which re-verifies `S` from step 1.
- rebase conflicts, behind main or a stacked branch without `base`: `blocked: needs rebase` /
  `blocked: stacked branch`; ship never rebases.
- occupied worktree: `blocked: worktree occupied`, per step 1.
- push rejected (non-fast-forward): `blocked: remote diverged`; never force.

Apply the [precise reporting contract](../docs/team.md#precise-issues-handovers-and-review-reports).
Card and issue writes stay with the designated coordinator.
Workflow and context boundaries: packaged team manual. Claude tier: Sonnet (the desk's own);
the watcher uses the configured helper mapping; Codex per README mapping.
