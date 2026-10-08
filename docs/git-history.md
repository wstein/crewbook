# Target Git history policy

This is instruction-layer guidance under [policy composition](policy-composition.md),
not Git enforcement. Resolve the target's integration branch, history policy,
checks, review order and operation authorization from applicable project
instructions and explicit user/session decisions before integration. Record the
sources and their scope in the assignment/handoff. Repository identity, existing
history and crewbook-generic/crewbook-workharbor execution profile do not select a policy.
Git configuration describes mechanics; it does not grant integration authority.

Apply the host's instruction hierarchy to a user override or conflicting inputs.
An explicit authorized choice may replace a compatible workflow default, but
cannot relax controlling host instructions or permissions. If the material
choice remains missing, ambiguous or conflicting, ask through the configured
human route before integration. Continue independent authorized edits/checks;
do not silently choose merges or rewrite history. No separate policy file is
required when trusted instructions and session decisions supply the inputs.

## Linear, fast-forward-only target

Do not create merge commits, integrate non-fast-forward, cherry-pick into the
integration branch or rewrite its existing history. Return the checked immutable
candidate to the coordinator for independent exact-SHA review before integration.
The assigned author fast-forwards only the approved unchanged revision through
the authorized target procedure. Confirm the resulting target SHA and checks.

If the candidate diverges from the current integration branch, the author
rebases only their own commits onto its current tip. Stop on conflicts outside
the assigned changed files or commits outside author ownership. Rerun relevant
checks and return the rewritten SHA for independent review through the
coordinator before fast-forward integration. A rewritten SHA never inherits
prior approval and readiness silently; see the
[rebase re-review rule](#rebase-re-review). If the target moves again, repeat
the required checks/review for any further changed candidate; never reuse old
clearance.

<a id="rebase-re-review"></a>
### Rebase re-review rule

After a rebase the old review does not carry over silently. A rebase that is
conflict-free, shows identical commits in `git range-diff` (all `=`) and touches
no file the rebase base change touched needs, unless the [landing pointer rule](#landing-pointer) applies, one narrowed Opus review of the new
exact SHA (range-diff equality plus tests at the new SHA). A rebase with
conflicts or file overlap needs a full review. In the [pull request flow](#pull-request-flow)
a commit status sits on one head SHA and is lost when the head changes, so the
desk re-posts it on the new head only together with a range-diff proof that all
patches are unchanged; a changed patch needs a new review. The CLEARs the
[pre-land gate](team.md#pre-land-gate) requires still apply to the new SHA.

<a id="pull-request-flow"></a>
### Pull request flow

Design source: workharbor `docs/content/docs/design/pr-flow-landing.md` (workharbor #407, #414). Unverified here: the workharbor files were read, not run against this repository, and the issue references #407, #414 and #421 were not checked.

- One pull request per branch, merged by rebase and merge only, so the atomic conventional commits survive. The human merging is the consent; agents never merge. The PR body carries `Closes #N`; commits carry `Refs:` only.
- The dispatcher (PR author) opens a draft PR and marks it ready after the review is CLEAR (the design says the human marks it ready, the manual says the dispatcher; workharbor #429 corrects it: the PR author/dispatcher marks ready). The desk posts the commit status `review/sonnet` or `review/opus` on the PR head plus an evidence comment naming the head SHA and the tier. The status creator must be the human account.
- A `gate` check derives the path class from the changed files with the base branch's path script (ordinary or carve-out) and requires `review/opus` for carve-out paths. CrewBook has no `gate` workflow yet; its `main` ruleset requires a PR, rebase merge and the checks `package (ubuntu-latest)`, `package (macos-15)` and `secrets`.
- PR size budget: at most 10 commits and about 500 changed lines per PR and review; the fast lane (documentation that policy classifies as Sonnet-eligible, see [crewbook-review](../.agents/crewbook-review.md); proposal, Werner to confirm) stays at 3 commits. Split larger work into a stack. The budget applies per PR, also to every PR of a stack; the batch PR of [batch integration](team.md#batch-integration) is exempt from the size budget; each original branch keeps its own budget (proposal, Werner to confirm).
- Auto-delete after merge covers finished work branches only (`fix/`, `feat/`, `docs/`, `chore/`, `ci/`, `refactor/`, `test/`); `spike/*` is never deleted automatically, which holds only while spike PRs are not merged by the human (GitHub deletes the head of any merged PR). This is the authorization the [dispatch rule](../.agents/crewbook-dispatch.md) on branch cleanup asks for, only for branches merged through a PR (proposal, Werner to confirm). GitHub deletes the remote head branch (enabled); local cleanup uses `git branch -d`, and `-D` only with `git cherry` or patch-id proof.
- Large work and related work form a stack of PRs (`gh stack`, workharbor #421, unverified). The desk decides automatically at dispatch time which issues form a stack (thematic relation or dependency, no explicit hint needed) and records the stack order in the dispatch note; independent topics stay single PRs. Agents never run `gh stack merge`; the human merges with rebase. The desk posts `review/<tier>` on every PR head in the stack after a range-diff proof. Mechanics: `gh stack init`/`add` build the stack, `gh stack submit --auto` opens the PRs as drafts, `gh stack sync`/`rebase` keep it current (unverified). The atomic stack merge enforces required statuses per PR. After a merge below a PR the head moves and its statuses are gone: re-post them with a range-diff proof (see the [rebase re-review rule](#rebase-re-review)).

<a id="auto-push-trial"></a>
### Auto-push trial

Trial (#83), revisit after a few PRs. After the required CLEAR on the exact head SHA (and after any rebase the range-diff proof), during the trial the desk takes over push, PR open and ready from the author/dispatcher in merged mode: it may push that topic branch (never force), open the PR as a draft with `Closes #N`, post `review/<tier>` plus the evidence comment, hand check watching to a background Haiku helper and mark the PR ready when the checks are green. Carve-out paths still need `review/opus`; the human merges (rebase). Never: merge, push `main` or tags, force-push, change rulesets or repository settings, or push a branch without the required CLEAR.

<a id="landing-pointer"></a>
### Landing pointer branch (retiring)

Until the migration finishes (exit: the first crewbook PR merged by rebase), the old flow stays valid where crewbook still depends on it: `landing` is a pointer branch to the newest reviewed stack tip, nobody commits on it, the desk moves it fast-forward-only after every CLEAR, the next branch is rebased onto it, and the human lands the full tip SHA. Landing must go through a pull request: the live ruleset requires a PR with no bypass, so a direct `git merge --ff-only` push is refused. The old direct-push fallback is unverified and removed. Review and tier rules are those of the [rebase re-review rule](#rebase-re-review) and the [pre-land gate](team.md#pre-land-gate). The Sonnet landing review of a rebased original (range-diff against the original plus tests) is valid only when every original already has its required-tier CLEAR at its own SHA (Opus for rule and security paths); the desk checks that before it counts the Sonnet CLEAR, and landing tooling must enforce the stack order (oldest CLEAR first, never a tip that skips earlier stack commits). Originals and conflict or overlap rebases keep the required-tier review. New work in the PR flow does not use the pointer; the pointer, `TO_LAND.md` and `refs/notes/review` are retired together with workharbor `make land` (#414).

<a id="commit-hygiene"></a>
### Commit hygiene

One concern per commit (one behaviour, fix or docs change); a change that needs a test carries it. The subject is a Conventional Commit, `type(scope): imperative summary`, at most 72 characters; the body says why, then `Refs: #n` and the agent co-author trailer. Individual commits need not build or pass tests on their own; the PR head must. The full test suite never runs per commit: one full run happens once on the stack tip before review, and its result is tied to the exact reviewed SHA (no re-run while the SHA is unchanged; see the [pre-land gate](team.md#pre-land-gate)). Fold fixes of an earlier commit of the branch into it before review, and after a review round fold each fix into the commit it fixes; the rewritten SHA needs a fresh review of the exact new SHA (narrowed only per the [rebase re-review rule](#rebase-re-review)). The final history has no fixup or "address review" commits; review rounds live in the PR evidence comments (the review note in the old flow). Exception: the [batch integration](team.md#batch-integration) fix round keeps its fix commits separate for the narrowed re-review. A branch with several concerns is several commits in review order, small first. The reviewer reports a violating commit as a Medium finding (NOT CLEAR) unless the human waived it. Before dispatching a review the desk reads `git log --oneline <target>..<branch>` (for example `main`) for subject and scope.

## Non-linear target with authorized merges

Merge only when the applicable target policy permits it and the user/session
scope authorizes that integration operation. Follow the target's real procedure
and review order, including any topic review required before preparing a merge.
The assigned author prepares the final integration candidate in an authorized
isolated checkout; do not update a protected/shared target merely to create a
reviewable candidate. Resolve conflicts only within assigned changed files;
stop and report outside-scope conflicts instead of expanding ownership.

Run required checks on the final integration/conflict-resolution result and
return its immutable SHA, parent SHAs, target base, resolved files and evidence
to the coordinator for independent review. Review of the topic SHA alone does
not clear the merge result, even when Git merged without conflicts. The
reviewer inspects the combined result and resolutions, not only the topic diff.
The author installs only that approved unchanged result using the authorized
procedure. If the target moves or any resolution/result changes, previous
clearance does not cover it: prepare, check and independently review the new
final result before completing integration. If the host procedure cannot expose
an immutable final result for the required review/checks, report the missing
capability and leave integration pending; do not claim a reviewed landing.

## Ownership and evidence

The author alone owns edits, checks, commits and authorized integration; the
coordinator obtains independent review and records readiness for the exact
result. Reviewers do not integrate or resolve author conflicts. Preserve user
work, hooks, permissions and [team ownership](team.md#local-integration-and-publication).
Never clear locks, bypass controls or invent landing tools. Record candidate,
reviewed and resulting target SHAs, policy sources, checks, reviewer evidence,
conflict scope and any pending operation. Local integration never implies push,
tag, release or publication authorization; retain the configured human owner.

CrewBook's source repository currently requires linear, fast-forward-only
integration under its source-only AGENTS.md; the human owns push (except the [auto-push trial](#auto-push-trial)). This example
supplies no policy or authority to another target.

## Static decision walkthroughs

These are prose review scenarios with expected actions, not executed Git
fixtures, measured native behavior or runtime enforcement tests. In each case
A is the assigned author, C the coordinator and R an independent reviewer.

| Supplied context / trigger | Expected action and evidence |
| --- | --- |
| Generic target selects linear history; checked candidate S descends from target B | A returns S/checks; C obtains R's clean exact-S review; A performs authorized fast-forward and records target S. Human retains publication. |
| Managed target selects linear history; reviewed S diverges after target moves to B2 | A rebases only owned commits onto B2, reruns checks, returns S2; C invalidates S approval/readiness and obtains R review of S2 before A fast-forwards. Profile changes none of these requirements. |
| Linear rebase conflicts in an unassigned file or requires rewriting another author's commits | A stops that operation and reports paths/ownership to C; no expanded edit or target update. Prior review cannot clear a changed candidate. |
| Target policy permits merges and session authorizes local merge integration; topic S was reviewed | A prepares final merge M with recorded parents/base, runs final-result checks; C obtains R review of M including combined behavior. Only then does A install unchanged M. Topic review alone is insufficient. |
| Authorized merge produces conflicts in assigned files | A resolves them in the isolated candidate, records files and final M/checks; R reviews resolutions and full integration result through C. Any changed resolution produces a new SHA and requires new checks/review. Outside-scope conflicts stop A. |
| Target moves after final merge M was reviewed | A does not install stale M over the new target; follows the authorized retry procedure, prepares/checks M2 and returns it for independent exact-result review before completion. |
| No history policy is supplied, or project instructions conflict with session configuration | A/C identify the missing choice or conflicting sources and resolve it with the human before integration; authorized local edits/checks may continue. Existing merge commits, repository name and execution profile select neither policy. |
| User explicitly selects merges over a package/default preference; target permits that choice | Record the decision and scope, then use the authorized non-linear procedure. If controlling host instructions prohibit merges, omit conflicting package guidance and report the conflict; user text cannot weaken actual host controls. |
| User authorizes only edits, or author/reviewer/Git/landing capability is unavailable | Return the available checked local result and name the missing authority/capability. No target mutation, invented review or publication; C records integration pending rather than ready. |
| Host merge tool cannot provide the immutable final result for required pre-integration review | A reports the capability gap and hands off topic evidence separately; C cannot label the integration result checked/reviewed. Continue only independent authorized work. |
