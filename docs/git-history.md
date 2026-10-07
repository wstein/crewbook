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

After a rebase the old stamp does not carry over silently. A rebase that is
conflict-free, shows identical commits in `git range-diff` (all `=`) and touches
no file the rebase base change touched needs, unless the [landing pointer rule](#landing-pointer) applies, one narrowed Opus review of the new
exact SHA (range-diff equality plus tests at the new SHA). A rebase with
conflicts or file overlap needs a full review. The CLEARs the
[pre-land gate](team.md#pre-land-gate) requires still apply to the new SHA.

<a id="landing-pointer"></a>
### Landing pointer branch

`landing` is a pointer branch to the newest reviewed stack tip. Nobody commits on it, and it neither replaces nor copies the original branches (unlike [`integration/batch-<n>`](team.md#batch-integration)). After every CLEAR the desk moves it fast-forward-only to that tip (merged mode: the desk; split mode: the dispatcher routes, the desk moves the ref). The next branch is rebased onto `landing` before its landing review, and dependent new work bases on `landing`. Such a rebase follows the [rebase re-review rule](#rebase-re-review) with a Sonnet landing review of the rewritten SHA (range-diff against the original plus tests); originals and conflict or overlap rebases keep the required-tier review. The human lands the target by fast-forward to the full tip SHA of `landing` (`git merge --ff-only <full sha>`). Landing tooling must enforce the stack order (oldest CLEAR first, never a tip that skips earlier stack commits). This Sonnet review is valid only when every original already has its required-tier CLEAR at its own SHA (Opus for rule and security paths); it checks only range-diff equality and tests, and the desk checks every original SHA has its required-tier CLEAR note before it counts the Sonnet CLEAR. The pre-land gate's tier check needs no code exception, but the project's tier rule must accept `sonnet` for this review, otherwise the gate fails closed.

<a id="commit-hygiene"></a>
### Commit hygiene

One concern per commit (one behaviour, fix or docs change); a change that needs a test carries it. The subject is a Conventional Commit, `type(scope): imperative summary`, at most 72 characters; the body says why, then `Refs: #n` and the agent co-author trailer. Individual commits need not build or pass tests on their own; the landing tip must. The full test suite never runs per commit: one full run happens once on the stack tip before review, and its result is tied to the exact reviewed SHA (no re-run while the SHA is unchanged; see the [pre-land gate](team.md#pre-land-gate)). Fold fixes of an earlier commit of the branch into it before review, and after a review round fold each fix into the commit it fixes; the rewritten SHA needs a fresh review of the exact new SHA (narrowed only per the [rebase re-review rule](#rebase-re-review)). The final history has no fixup or "address review" commits; review rounds live in notes. Exception: the [batch integration](team.md#batch-integration) fix round keeps its fix commits separate for the narrowed re-review. A branch with several concerns is several commits in review order, small first. The reviewer reports a violating commit as a Medium finding (NOT CLEAR) unless the human waived it. Before dispatching a review the desk reads `git log --oneline <target>..<branch>` (for example `main`) for subject and scope.

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

Crew Book's source repository currently requires linear, fast-forward-only
integration under its source-only AGENTS.md; the human owns push. This example
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
