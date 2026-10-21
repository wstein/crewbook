---
name: restack-after-merge
description: Restack child branches or stacked pull requests after the owner rebase-merges their parent, with range-diff evidence, semantic-break checks, a lease push and an owner resync command.
---

# Restack after merge

Use this after a pull request was merged by rebase-merge. The merge rewrote the
parent's commits to new SHAs, so each child still carries the parent's commits
under their old SHAs and shows `CONFLICTING`. The procedure moves only the
child's own commits onto the new base and proves nothing else changed.

Follow the [restack procedure](../../crewbook-restack.md) for the desk's
blocked outcomes, and the target's pull request, history and delegation rules
([git-history.md](../../../docs/git-history.md),
[team.md](../../../docs/team.md)) for who may push and which review tier applies.
Host authority and the user's scope outrank this checklist. Never merge, tag,
release, publish, build or change settings or git identity.

## 1. Verify the inputs

Name both SHAs in every command; never rely on a branch name or `origin/main`.

- [ ] Fetch first: `git fetch --prune origin`. Record the new base `M` (full SHA of
      the fetched default branch).
- [ ] Per child, read the pushed head and base:
      `gh pr view <n> --json headRefOid,headRefName,baseRefName`. The head is `O`.
- [ ] Old parent head `P`: the parent's last pushed head (from its PR or the
      child's own history), an ancestor of `O`, not of `M`.
- [ ] Work in your own worktree, never in the owner's checkout. Use
      `git worktree add` on the child branch; the worktree must be clean.
- [ ] The local branch pointer must equal the SHA that was reviewed or pushed.
      A detached `HEAD` can differ from the branch name, so always rebase the
      named branch (the ref must move, not only a detached `HEAD`), compare
      `git rev-parse <branch>` with `O` before and `N` after, and push the
      exact reviewed SHA by full hash.
- [ ] Stop on commits you did not author, an occupied worktree or a moved remote.

## 2. Rebase

```sh
git -c rebase.updateRefs=false -c rerere.enabled=false rebase --onto <M or new parent> <P> <branch>
```

- [ ] Commits already on the base drop out. Confirm with `git cherry <M> <P>`:
      every line must start with `-`. If a patch id differs (for example after
      a conflict at merge time), prove tree equivalence instead:
      `git diff <M> <P> -- <paths the parent touched>` is empty.
- [ ] Go bottom-up through a stack. The first child rebases onto `M`; the next
      child rebases onto the rewritten head of the one below it, with that
      one's old head as `<old parent>`.
- [ ] Branched stacks: each branch rebases onto its own parent's new head.
      Finish a parent before its children; a blocked parent blocks them.
- [ ] A conflict is outside the desk restack, which resolves nothing: run
      `git rebase --abort`, leave the branch at `O` and report
      `blocked: rebase conflict` with the files (see
      [crewbook-restack](../../crewbook-restack.md)). Only when the author-tier
      agent restacks its own branch is resolution a middle-tier authoring task:
      keep both sides of a shared ledger or index file, validate the result
      (parse it, compare id sets before and after for lost or duplicated
      entries), note it for step 3, and expect the stronger-tier review of
      step 5. Stop on a conflict in files you do not own.

## 3. Evidence

```sh
git range-diff <P>..<O> <M or new parent>..<N>
```

`N` is the new head. Own commits must show `=` with equal counts.

- [ ] Explain every `!`. The usual cause is a conflict in a shared ledger, index
      or generated-list file resolved by keeping both sides. For such a file,
      validate it (parse or run its own check) and compare the id sets before
      and after: no lost entry, no duplicate.
- [ ] A commit shown as `<` or `>` is lost or added: stop and investigate.
- [ ] State the range-diff result in the report, per branch.

## 4. Semantic breaks

A clean rebase and all `=` do not prove the code still works. The parent may have
changed a signature, contract, schema or shared file the child relies on.

- [ ] Run vet or compile for every platform the project targets, and the tests the
      change affects, on `N` before any push.
- [ ] An adaptation is authoring work by the author-tier agent on its own branch,
      never part of the desk restack, and gets the stronger-tier review of
      step 5. Fix it inside the commit that needs it:
      `git commit --fixup=<commit>`, then
      `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <base>`.
      Rerun the range-diff and say that an adaptation exists and why.
- [ ] Do not add an unrelated commit just to make the build pass.

## 5. Review before the push

Apply the target's pull request and delegation rules and the
[rebase re-review rule](../../../docs/git-history.md#rebase-re-review); they
set the tiers and win over this table, which only gives the shape:

| Rewritten head | Before the push |
| --- | --- |
| Docs or specification only (no code, tests, scripts, generated files) | Green local checks and, for a pure rebase, range-diff equality; no review. The review of the exact head still belongs to Ready. |
| Code, conflict-free pure rebase with equal range-diff | The narrowed exact-SHA review the rule names: range-diff equality plus tests at `N`, one mutation probe per PR, author identity. |
| Code, conflict resolved (for example in CI configuration), file overlap, or a semantic adaptation | The full review the rule names, on the exact new SHA, by the strongest tier. |

The old review never carries over to `N`.

## 6. Push

- [ ] Author check, owner only:
      `git log --format='%an <%ae> | %cn <%ce>' <M or new parent>..<N>`
      and `git config --show-origin --get-regexp '^user\.'`. Never write identity
      into any git config; repair a leak as the target's rules describe.
- [ ] Observe the remote head and require it to equal `O`:
      `git ls-remote origin refs/heads/<ref>`.
- [ ] Push with the observed full old SHA as lease and the full new SHA:

```sh
git push --force-with-lease=<ref>:<O> origin <N>:refs/heads/<ref>
```

- [ ] Never plain `--force`. Never push the default branch or a tag. Never retry
      with a newer expected head: a lease refusal means the remote moved; keep
      both heads and report.
- [ ] A fast-forward fix on top of an already-pushed head needs no lease.
- [ ] Read back the remote tip and confirm it equals `N`.

## 7. CI and the pull request

- [ ] Expect a fresh run on `N`. Wait with the project's read-only CI watcher, not
      a custom loop.
- [ ] A re-run of an old run after the base moved can fail a merge-shape check
      because a re-run reuses the old event. Trigger a fresh run instead.
- [ ] GitHub native stacks rebase and retarget children themselves after a merge.
      Verify with `git range-diff` before trusting the result.
- [ ] A closed duplicate is not restacked. Close it with the evidence:
      `git cherry <M> <branch>` shows only `-` lines.
- [ ] Update the pull request description and base if they changed. Flip Draft or
      Ready per the target's rule: Ready only with a CLEAR review of the exact
      head, green required checks and no named blocker.

## 8. Report

Per branch: old SHA `O`, new SHA `N`, base `M`, range-diff result, checks, review
tier used and the push command. Add the owner-side resync, because the owner may
have the branch checked out:

```sh
git fetch --prune
# the owner has local commits on the branch:
git rebase --onto origin/<branch> <old pushed SHA> <branch>
# the owner has none (destructive for local-only work and uncommitted changes):
git switch <branch> && git reset --hard origin/<branch>
```

If nothing was rewritten, say that no owner-side action is needed.

## Delegation

Name the model on every subagent call; tiers follow the configured mapping in
[README.md](../../../README.md) and [team.md](../../../docs/team.md).

- Mechanical rebase and evidence collection: middle-tier author.
- The check of step 5: an independent reviewer, not the author.
- CI log triage and polling: cheapest helper.
- Parallel authors each use their own worktree.
