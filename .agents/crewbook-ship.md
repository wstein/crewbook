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
[human-request contract](../docs/team.md#human-request-contract)). It is a procedure of the
coordinator, not a lane: it starts no issue worker, and the one background watcher it
starts is the only child. Assignment: one branch, its issue and the CLEAR evidence.

Never: merge, release, deploy, push `main` or a tag, force-push, change rulesets or settings, or push
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
1. Preconditions, each checked and recorded. Apply the author's
   [pre-push preparation](../docs/git-history.md#auto-push-trial) before binding
   checks and CLEAR to `S`. Resolve and fetch the actual default branch from the
   target's own remote as separate checked calls. The worktree is clean and on
   the branch, `git rev-parse HEAD` equals `S`, and the fresh default tip is an
   ancestor of `S`. For a stack, also require `S` to descend from the updated
   parent `base`; a stale parent returns to the author for dependency-preserving
   restack. A worktree held by another author or dirty is `blocked: worktree
   occupied`, untouched. Ship never rebases: a stale base returns to the author
   for preparation, checks and exact-SHA re-review.
   Immediately before step 2, reobserve the default name/tip and remote topic
   head against the recorded observations. A changed default is `blocked: needs
   rebase`; a changed topic is `blocked: remote moved`. Preserve both heads;
   never proceed using stale clearance or overwrite concurrent work.
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
5. Post the evidence comment: `S`, tier, each independent reviewer's identity and
   scope, executed review round count, conclusion/findings, the checks actually run
   with exit codes, and any accepted Lows with acceptance evidence and owner.
   Distinguish the configured model/effort from runtime identity when the host
   does not expose the latter; never invent runtime attestation. Missing runtime
   identity must not suppress the executed review's conclusion or its public
   status/comment. This does not relax the actual-model grammar or gate for
   [registry/review notes](../docs/project-config.md#review-note), grant a configured
   model tier eligibility, or replace the project's required tier and explicit
   trusted host mapping. Report any unresolved eligibility gap as a blocker.
   Reconcile an uncertain write by listing the comments before retrying; never
   post it twice.
6. Start one background watcher (read-only, reports once, no foreground polling) on the
   configured helper model. Give it `S`, the PR, the required checks (from
   `gh api repos/<o>/<r>/rules/branches/<base>`, `required_status_checks`) and a deadline
   (default 30 minutes; a project profile may override it). It returns per check: name, conclusion,
   job URL and the first failing line. It never judges, reruns or comments.
7. Stamping and watching are separate: step 4 completes before the watcher result is
   awaited. On its report, perform the [Review → Ready preflight](#review-ready-preflight)
   directly; the watcher's word cannot establish readiness.
8. Before final readiness, apply [merge-method readiness](../docs/git-history.md#merge-method-readiness):
   resolve the configured method from trusted inputs and read the actual PR REST
   observation for `S` and the current expected base. A rebase-only target needs
   `rebaseable == true`; clean mergeability and green CI are insufficient. Record
   the linear-history/ownership proof when required. Unknown or stale evidence
   leaves final readiness pending; false eligibility returns to the same author
   for scoped correction and exact-SHA re-review. The authorized draft PR may
   already be open. Complete the preflight before instructing the assigned author
   to mark Ready. The author independently repeats it immediately before
   `gh pr ready <pr>` (or the assigned ship coordinator does when authorized to
   perform that operation); read back `isDraft == false` and `headRefOid == S`.
9. Record the run per [run records](../docs/team.md#run-records), then report to the human: PR URL, `S`, tier, checks with conclusions, and that merging by
   rebase is the human's action.

<a id="review-ready-preflight"></a>
## Review → Ready preflight

Before the desk instructs Ready, and independently before the assigned author
marks Ready, read the actual GitHub state for the exact pushed/reviewed `S`:

- Read the PR head and remote topic head; both must equal `S`, with independent
  CLEAR evidence for `S` satisfying the target's review tier and scope.
- Read the commit statuses on `S`. Require the effective `review/<tier>` status
  to be `success`, created by the target-required account. A same-named status
  from another account or on another SHA does not count.
- List the PR comments and read back the exact evidence comment posted in step 5
  for `S`, retaining its URL/id. Verify its tier, reviewers/scopes, executed round
  count, conclusion/findings and accepted Lows with acceptance evidence/owner,
  and executed checks with exit codes against the review handbacks. An internal
  handback, PR body or git note cannot replace the visible status and comment.
- Read required checks directly with
  `gh pr view <pr> --json headRefOid,statusCheckRollup`: each required check must
  be present and successful on `S`. Read the PR REST head/base and current target
  base per [merge-method readiness](../docs/git-history.md#merge-method-readiness),
  including `rebaseable == true` for a rebase-only target and required local
  history/ownership proof. Preserve any other named blocker.
- Finally resample the PR head, remote topic head and target base. A changed
  head blocks Ready; a changed base requires refreshed checks/eligibility under
  target policy before repeating this preflight. Do not act on stale observations.

Missing or mismatched public review evidence is `blocked: review evidence missing`;
keep the PR Draft with that named blocker. Return missing writes to the desk,
the status/comment owner; author and dispatcher read back rather than duplicating
those writes. Reconcile uncertain writes under steps 4–5 before retrying.
Ready remains the human-merge handoff, never permission for an agent to merge.

Blocked outcomes (when a PR exists it stays draft with the blocker named in its body; several
blocked outcomes happen before any PR exists, and then the report alone carries the blocker. No retry
loop, no workaround; report the blocker, `S`, observed state and the next human or author action):
- changed HEAD (local, remote or PR head not `S`): `blocked: head changed`.
- missing checks (a required check absent or not on `S` at the deadline): `blocked: checks missing`;
  a failed check: `blocked: check failed` with name, URL and first failing line.
- duplicate invocation: `blocked: duplicate invocation`, per step 3.
- gate timeout (watcher deadline reached, or gate re-run retries exhausted): `blocked: gate timeout`;
  the PR stays draft (with the evidence comment if step 5 ran). Not a failure of the PR; the desk may
  re-invoke once the gate is available, which re-verifies `S` from step 1.
- rebase conflicts, behind the fresh default or a stacked branch without `base`: `blocked: needs rebase` /
  `blocked: stacked branch`; ship never rebases.
- occupied worktree: `blocked: worktree occupied`, per step 1.
- remote topic changed before push: `blocked: remote moved`; preserve both heads.
- push rejected (non-fast-forward): `blocked: remote diverged`; never force.

Blocker in the PR body: to name a blocker in an existing PR body, first read the current
body (`gh pr view <pr> --json body`) and the PR comments, edit the body once with the
blocker added or replaced, and never post the same blocker twice (reconcile an uncertain
write by reading the body again before any retry). Clear the blocker line when the blocker
is resolved.

Apply the [precise reporting contract](../docs/team.md#precise-issues-handovers-and-review-reports).
Card and issue writes stay with the designated coordinator.
Workflow and context boundaries: packaged team manual. Claude tier: Sonnet (the desk's own);
the watcher uses the configured helper mapping; Codex per README mapping.
