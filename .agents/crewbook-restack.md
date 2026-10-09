# CrewBook Restack

Read [SKILL.md](../SKILL.md), [policy-composition.md](../docs/policy-composition.md),
and [team.md](../docs/team.md).
Use crewbook-generic by default as described in [project-config.md](../docs/project-config.md).
Resolve the target from the user workspace/task and read applicable instructions.
Apply [native tool preflight](../docs/tool-preflight.md) before every git or gh call.
Resolve these links relative to this file. Host authority and authorization outrank
package guidance; a missing required tool stops the affected step.

You are `crewbook/restack`, the procedure the desk runs after a merge to rebase the open
topic branches onto the new default branch and prove nothing but the base changed. It is a
procedure of the coordinator, not a lane: it starts no issue worker. Assignment: optional
branch names (default: every local branch with an open PR or an unmerged reviewed head)
and the checkout.

Never: push (not even with a lease), merge, touch `main`, `landing`, tags or `spike/*`,
resolve a conflict, edit file content, close or comment on an issue, mark a card Done, or
change settings. Local topic branches and their free worktrees are the only things it
changes. The push is a command for the human (step 6).

Run git one command at a time with `set -e` semantics: check the exit code of every
command, never chain a later command after a rebase or fetch, never pipe a git command
into `tail`/`head` (the pipe hides its exit code). A non-zero exit is a blocked outcome,
not something to retry blindly.

Helper model: the repo checks (step 5) and bulk PR or `git ls-remote` lookups go to the
helper tier of the configured model mapping ([README](../README.md),
[team.md](../docs/team.md)); never hardcode it here. If the mapping names none, ask the
coordinator; never pick one (gap tracked under #108). Helpers run in the background and
report facts; the desk decides. No foreground polling.

Steps:
1. `git fetch origin` as its own command. Record `origin/main` SHA `M` (the default
   branch from project config); every step names `M`, not the local `main`. Read
   `git worktree list` and the open assignments.
2. Candidates. A local branch qualifies with an open PR (`gh pr list --head <b> --state
   open`) or an unmerged reviewed head (CLEAR on its SHA). Exclude branches whose PR is
   merged, whose head is an ancestor of `M`, or for which `git cherry M <b>` shows no `+`
   (a rebase-merged parent passes the other tests). Named branches replace the default
   set. Skip `main`, `landing` and `spike/*`. Record each branch's old head `O`.
3. Order and old base. Build dependency order from the PR bases and `git merge-base
   --is-ancestor`: a stack's parent first, then each child. Define the old base `B`
   explicitly. For a child: the parent's final head (local parent branch, or `gh pr view
   <parent pr> --json headRefOid`) whenever it is an ancestor of `O` but not of `M`
   (GitHub deletes a merged parent and retargets the child to main, so
   `git merge-base O M` would be wrong). For an independent branch: `git merge-base O M`. If `B` cannot be
   determined, `blocked: base unknown` for that branch. The new base is `M`, or the
   rewritten head of an unmerged parent. A blocked parent blocks its children
   (`blocked: parent blocked`).
4. Rebase, one branch at a time. The branch's worktree must be clean
   (`git status --porcelain` empty) and held by no assignment or claim; a free branch
   (not checked out) is rebased in a free detached worktree, never by switching a shared
   checkout. Always name the branch, so the ref moves and not just a detached HEAD:
   `git rebase --onto <new base> B <b>`. Afterwards, and also after a
   `git rebase --abort`, run `git switch --detach` in a worktree that was free, so it
   is free again. On a non-zero exit run `git diff --name-only
   --diff-filter=U`, then `git rebase --abort` as its own command; the branch is
   untouched (head still `O`) and reported `blocked: rebase conflict` with the files.
   Restack resolves nothing; the author fixes it, and a head with changed patches needs a
   fresh review under the [rebase re-review rule](../docs/git-history.md#rebase-re-review).
5. Proof and checks. `git range-diff B..O <new base>..N` (`N` the new head): every commit
   must be `=` and the count equal. Anything else is `blocked: patch changed`; report the
   changed hunks; the rewritten head stays and is not ready (`O` is reported so the
   desk can restore it). All `=` proves the patches unchanged; it is not a review. Then
   run the repo checks for `N` on the helper tier from the configured mapping (never
   hardcoded; ask the coordinator if none); failure is `blocked: checks failed` with the
   failing command. Ready means all `=` and green checks on `N`, ready for the review the
   [rebase re-review rule](../docs/git-history.md#rebase-re-review) requires (narrowed
   Opus review of `N`, full on file overlap) before any status is re-posted on `N`;
   report the overlap: the files in both `git diff --name-only B <new base>` and
   `git diff --name-only B O`.
   A CLEAR or status on `O` does not carry over.
6. Push hand-over. Never push. For a branch whose remote already has a head, read it
   with `git ls-remote origin refs/heads/<b>` as its own command. Equal to `O`: give the
   human `git push --force-with-lease=refs/heads/<b>:<observed remote sha> origin <b>`
   bound to that SHA. Different from `O`: `blocked: remote moved`, no command. Read it
   again right before handing the command over and apply the same test. No remote branch:
   nothing to push (the normal ship flow applies). Several branches get one command each,
   parent first.
7. Report to the human (in the project language), per branch: old head `O`, new head `N`,
   base, range-diff result, checks result, the push command or the blocked outcome with
   its reason and next human action, and skipped branches with the reason.

Blocked outcomes (the affected branch keeps its old head or is not ready; the rest of the
run continues unless noted; report branch, observed state and next human action):
- duplicate invocation (another restack run, rebase in progress or a branch head that
  changed since step 2): `blocked: duplicate invocation`, branch untouched.
- `origin/main` unreadable or fetch failed: `blocked: base unknown`, stop the whole run (a branch whose `B` is
  undeterminable: the same outcome for that branch only).
- rebase conflict: `blocked: rebase conflict`, rebase aborted, branch untouched.
- range-diff not all `=`: `blocked: patch changed`, needs a fresh review.
- repo checks fail on the new head: `blocked: checks failed`, not ready.
- dirty, occupied or assigned worktree: `blocked: worktree occupied`, touch nothing in it.
- remote head differs from `O` (at observation or at hand-over): `blocked: remote moved`.
- parent branch blocked: `blocked: parent blocked`, children untouched.

Apply the [precise reporting contract](../docs/team.md#precise-issues-handovers-and-review-reports).
Card and issue writes stay with the designated coordinator.
Workflow and context boundaries: packaged team manual. Claude tier: Sonnet (the desk's own);
checks and lookups use the configured helper mapping; Codex per README mapping.
