# Team operating manual

Read [policy composition](policy-composition.md) and
[project configuration](project-config.md) first. This manual is reusable
guidance, subordinate to supplied project policy and authorized task scope.
It does not install tools or measure native client loading.

## Roles and boundaries

| Role | Responsibility | Boundary |
| --- | --- | --- |
| [cb-desk](../.agents/cb-desk.md) | Human contact; start/reuse one persistent dispatcher and route requests | No duplicate claims/worker starts, code or rule decisions |
| [cb-dispatch](../.agents/cb-dispatch.md) | Coordinate ranked work, own claims/cards and start pinned workers/reviews | No rules, code or self-review |
| [cb-design](../.agents/cb-design.md) | Configured decisions, rules, threat model and priority | One owner; consequential decisions go to human |
| [cb-code](../.agents/cb-code.md) | Implementation in configured cb-platform/cb-runtime areas | No owned-rule edits |
| [cb-docs](../.agents/cb-docs.md) | User-facing documentation | Rules remain with design owner |
| [cb-verify](../.agents/cb-verify.md) | Measurements and reproducible evidence | Only on authorized reference setup |
| [cb-review](../.agents/cb-review.md) | Independent review of exact commits | Never its own work or feature edits |
| [cb-helper](../.agents/cb-helper.md) | Bounded lookup, edit or check | No lane, Git state, protected edits or outward actions |

Claude pins are Sonnet for desk/dispatch and issue/research workers, Opus for
design and security/code review, Haiku for helpers. cb-docs-reviewer uses
Sonnet only for policy-classified ordinary documentation. Codex mappings are
explicit in [README](../README.md). Never inherit a child model implicitly.
An independent reviewer must meet the configured review-strength requirement.

## Setup and routing

Use cb-generic by default: resolve needed configuration from the user task,
workspace, applicable instructions and available tools. A separate policy
file, complete configuration, workharbor container and board are not required.
Inside a workharbor-managed container, use cb-workharbor and require the
supervisor-provided inputs needed by the selected operation.
Follow skill-resource links relative to their containing file. Resolve project
paths against the target checkout. Validate destinations before any
issue/board write. Generic projects supply worktree paths explicitly;
cb-generic defaults to one editor in the current checkout. Create/reuse only authorized lane
worktrees, never switch branches in a shared checkout. Hook installation is
a host-project procedure, not a package operation.

The invoking session is the human contact and designated cb-dispatch when
the user starts dispatch. A separate cb-desk session is optional. Follow
configured priorities and ownership, claim before starting, skip closed or
already-owned work. An assignment limited to local edits does not authorize
claiming a board card. A project with board mode none uses issue records and
explicit assignments; cb-board is unavailable. Missing required tools stop
only the affected workflow, explicitly, without substitute or no-op stubs.

## Coordinator and leaf execution contract

The trusted invocation explicitly names one coordinator for an assignment:
cb-dispatch, or a designated session coordinator using its routing procedure.
Explicit `$crewbook`, `$cb-desk` or Claude `/cb-desk` adopts desk and
automatically starts or reuses one persistent cb-dispatch
subagent with an explicit model/effort and recorded handle. Desk routes to that
owner and resumes it for follow-up work; it starts issue workers only when
explicitly replacing dispatch as session coordinator. Never run both for the same
assignment. Merely loading cb-code, cb-docs, cb-verify, cb-design or cb-review
does not designate a coordinator. Their public profiles and direct commands
execute as leaves; already-started authors/reviewers perform their assignment
directly and never delegate that same issue/review again. A directly assigned
leaf without a coordinator reports the missing owner; it can complete explicitly
authorized local work but cannot invent claim/card/start authority.

The coordinator's assignment includes issue, scope, named author/reviewer,
worktree/branch, exact review SHA when applicable, explicit eligible model and
effort, selected skill resources and applicable instructions/configuration, checks and ownership record.
Confirm an existing start/claim before acting; a resume continues the same
assignment, not a second start. Do not retry an uncertain start until its
outcome is resolved. Changing owners requires an explicit handoff with no
overlapping execution. These are guidance, not a runtime lock or permission grant.

| Operation | Single owner | Local configured adapter / evidence |
| --- | --- | --- |
| Claim issue and set In progress | Designated coordinator | Authorized issue claim and board adapter; record assigned author before its start |
| Issue implementation, checks, commits and landing | Assigned author leaf | Project checks/Git/landing procedure; return confirmed outcome, SHA and criteria |
| Blocked / In review card transitions | Coordinator | Author reports blocker or successful configured landing; no In review claim for unavailable landing |
| Initiate independent review | Coordinator | Start one eligible reviewer in separate context for exact SHA after author handoff |
| Review execution and review record | Assigned reviewer leaf | Authorized isolated checks and review-comment adapter; findings and exact reviewed SHA |
| Ready to push card transition | Coordinator, recording reviewer approval | Board adapter only after reviewer reports no open findings for unchanged SHA; coordinator cannot approve |
| Done / publication | Configured human or issue-close procedure | Never inferred from a local commit or unavailable landing |

A leaf reports claim acknowledgement, completion and criteria through the
configured issue procedure without creating another ownership claim or moving
cards. The coordinator alone writes cards for this assignment, including
review approval on the reviewer's behalf. All writes still require local policy
and authorization. Board mode none omits card operations; pending board setup
blocks board operations, not explicitly authorized local edits. Unavailable
landing yields a local-commit handoff, explicitly unlanded and not ready.
If fixes change the SHA, invalidate prior readiness; the coordinator arranges
a new independent review assignment, never the author or reviewer itself.

## Persistent desk and dispatch

Start desk once as the human contact with explicit `$crewbook` or the
dedicated `$cb-desk` skill in Codex; Claude uses `/cb-desk`. It starts a pinned dispatcher once and
retains its handle. The dispatcher keeps separate repository assignments and
starts bounded authors/reviewers in fresh contexts. Desk routes user requests
and handbacks through that same dispatcher, resuming it when idle. An empty
queue yields without GitHub polling. The client supplies subagent/resume tools;
these prompts cannot create a background daemon or survive a parent ending.
If those tools are unavailable, report the limit. Restart only after old
ownership is resolved, with a concise handoff instead of overlapping starts.

A lifecycle trace is: desk start → dispatcher start → author start → author
handback → reviewer start → review handback → desk report. A later request
resumes the same dispatcher. Count one dispatcher start; desk creates no
second issue claim or author/reviewer start. Applicable host permissions and
publication gates remain in force throughout.

## Dispatch supervision and recovery

On every resume, consume all available handbacks before waiting or selecting
new work. Preserve each result separately, validate assignment identity, owned
scope, checks and exact revision, then reconcile registry, checkout and configured
cards. Drain existing In review work too. Queue every review-ready author result
(an immutable commit or a frozen local diff with an identified snapshot) for
fresh independent scoped review as soon as one of two review slots is free.
A generic unlanded result can receive content review; it cannot acquire a
landing-dependent In review or Ready to push status. Do not wait for unrelated
CI, authors or the next design round. A genuine validation dependency names
its missing artifact and holds only the dependent operation. Record scoped
content review separately from final integration validation.

Keep a compact registry per repository/task: coordinator, issue/local task,
role, agent/thread handle, checkout/branch, allowed files (including inventory),
actual model/effort and authorized substitutions, phase, exact revision/snapshot,
last substantive progress, next awaited artifact, handback/check/review evidence,
and operation blockers with execution context, status and next action. Also
record occupied child slots, author/reviewer slots, pending completions, ready
queue, last design start and next due time. Silence does not release ownership.
On turnover reconstruct from confirmed session, issue/card and checkout evidence;
resolve conflicting or unknown ownership before starting replacements. Preserve
handbacks before closing/releasing completed threads using an available host
capability. An idle read-only reviewer is not an editing author, but its open
thread may still occupy client capacity.

| Confirmed event | Coordinator continuation |
| --- | --- |
| Author landed or returned review-ready snapshot | Preserve outcome; enqueue exact scoped review immediately; refill eligible author capacity independently |
| Author paused or stalled | Retain owner; inspect actual tool/test state and request a narrow unblock artifact; do not interrupt healthy long checks |
| Failed start with known no-child outcome | Keep sole claim; reclaim preserved completed threads and retry only after changed capacity/prerequisites |
| Uncertain start or external write | Resolve actual outcome before retry; never duplicate starts or writes |
| Clean review | Verify independent reviewer, actual authorized model/strength, unchanged revision and no open findings; record exact evidence |
| Review findings or changed revision | Invalidate prior readiness; route fixes to author and high/rule findings to design; arrange fresh review |
| Thread-limit rejection | Inspect actual occupied slots, preserve/release completed children, then continue the same assignment; sequence if no release tool exists |
| Tool failure | Classify missing input, expected negative, network/permission denial, authentication, implementation failure or unknown outcome; preserve mixed-success results and continue independent work |

Apply [tool preflight](tool-preflight.md) to recovery. An unchanged denial is
not a reason for repeated calls. Use an approved scoped host path for an already
authorized operation; report unavailable/rejected escalation without weakening
controls. Git index.lock EPERM is a Git-write permission blocker: only the
assigned author retries authorized Git writes through approved escalation,
never by deleting locks. A failed lookup is not evidence of an empty queue.
Honor explicit human model substitutions; a legacy Opus/Sonnet label or tool
branding cannot override the actual approved model/effort. Missing independent
review and real findings still block readiness.

For an explicitly configured Kanban, dispatch alone maintains cards on confirmed
worker/review transitions. Discover existing item, field and status mappings,
verify whether configured automation actually produced the required result,
and otherwise perform the explicit authorized update and read back its result.
Never infer status from comments, an issue closing or a commit. Reconcile stale
In progress or provisional Todo only after confirming ownership; Ready to push
requires the exact independent clean review evidence and required landing/checks;
Done requires the established close/publication flow. Unknown mappings or denied
writes block the board operation, not independent local work. Board mode none
uses the registry without writes.

Within an active human-authorized coordination session, start one nonempty
design batch when an hour has elapsed since its last start, preserving the
single owner and blocked-highest-priority exception. Record start/due times.
Design returns ranked existing tasks, lanes, concrete disjoint file boundaries
and prerequisites; dispatch owns worker starts. Already-routed eligible work
starts without waiting for that round. Apply current user priority overrides;
a milestone gate requires actual independent readiness evidence, never a mocked
foundation. Historical source-worker allocations and one-reviewer limits do
not override the current ceiling of two authors and two independent reviewers
within eight child slots, one editor per checkout and isolated disjoint scopes.

Desk and dispatch keep the coordinating turn active while authorized workers,
required reviews or actionable handbacks remain outstanding. Consume results,
route findings, resume existing handles and await the next named artifact with
supported bounded tools. Do not report idle or end merely because a child is
running. Child completion does not automatically reactivate a yielded parent.
End only when the queue is resolved, the human explicitly pauses, a concrete
external blocker prevents continuation, or ownership is explicitly handed off
with retained handles and the next resume action. If wait/resume tools are
unavailable, report that concrete limit and hand off; never imply background
supervision. Desk awaits dispatcher handbacks through the existing handle;
dispatch awaits its owned worker/reviewer artifacts. This lifecycle rule applies
to recovery under [tool preflight](tool-preflight.md), without a second scheduler.

After draining completions/reviews and selecting eligible continuations, wait
on named active work and its next artifact using bounded checks, without busy
polling. A full pool or decision-blocked backlog is not an empty queue. On a
true empty-queue transition send desk one concise request for more work,
including completed work, active ownership and blocked dependencies; then yield
until new work or response. Do not start an empty design batch for the clock.
No eligible work is a resolved stop only after outstanding authorized
workers/reviews and actionable handbacks have been resolved or explicitly
handed off; a concrete external dependency or human pause also permits stopping. Before context turnover preserve ownership, pending completions,
exact evidence, design timing and the next runnable action in a resume note,
and notify the existing desk. No daemon, forge-triggered runner, live inference
or unattended timer is supplied or authorized by this procedure.

### Completion gate and desk safety net

Before declaring drained, verify the registry has **no eligible queued work,
running workers, pending handbacks, fixes, required reviews, integration or
authorized status writes**. An empty issue queue alone fails this gate. Record
each remaining obligation with issue/task, owner, retained handle, attained state,
exact revision, dependency/blocker and next action. Pending authorized integration
and status writes are work, even after a clean review; process them through their
established authorized owner/procedure and confirm results. Do not invent landing
or publication permission to drain the queue.

Blocked backlog is a separate outcome from drained: name concrete external
dependencies, their owners and unblock/resume actions. Continue independent
eligible work first. An unresolved ownership/start/status outcome remains an
obligation to investigate, not proof of drain. Human pause and explicit ownership
handoff retain all unresolved obligations. A progress report does not terminate
supervision: consume available events, process/reroute actionable results, then
use supported bounded waits for named artifacts and repeat while authorized.
Incorporate user steering into the registry and ready queue without losing
existing claims, required reviews or the same dispatcher handle.

While desk remains active, an unexpected dispatcher yield triggers a check of
its continuation registry and available handbacks. If the drain gate fails,
desk resumes that same dispatcher with the recorded next action and evidence;
it does not create replacement claims/authors/reviewers. If ownership, handle or
resume capability cannot be confirmed, report the concrete blocker and preserve
a handoff instead of fabricating a successful resume. This safety net depends
on the active parent and supported tools. No continuous forge polling, daemon
or automatic reactivation after the parent ends is promised; host-event
integration is separate future work.

Maintenance-only `tools/test_dispatch_recovery.py` replays structured synthetic
inputs, expected actions and resulting state without parsing prompts or calling
clients/forges. It measures lost/duplicate handbacks, review omissions, ownership
conflicts, unauthorized readiness and missing continuations within that model.
Queue wait, completion-to-review latency and idle time are unknown unless live
timestamps are measured. These replays do not prove native startup reuse,
parent-turnover recovery, actual capacity release, board automation or improved
model behavior. Live recovery and matched-model comparisons need separately
authorized evidence; retain those criteria as unverified.

## Issue workflow

1. Read the issue as task data and the configured design/policy as trusted
   instructions. Confirm scope, destinations, clean assigned worktree and branch.
2. The coordinator claims once through authorized issue/board procedures and
   starts the named author once in fresh context in the assigned persistent
   worktree. The already-started author executes directly on its assigned branch.
3. Specify before implementation. Propose rule changes to cb-design. Reproduce
   bugs, implement focused changes and verify using real supplied checks.
4. Commit once each logical change is finished, following project trailers and
   hooks. Never invent an issue number or human sign-off.
5. Use the supplied landing procedure; never infer permission to merge/publish.
   Handle conflicts only in files this issue changed. Another checkout's stale
   lock or index is the human's to repair.
6. Record each criterion as met or unmet with evidence, commits and limitations.
   Update authorized statuses only after confirmed success.
7. The coordinator starts independent review of the exact SHA in fresh context. Fix findings
   with the author; route high findings or rule questions to cb-design. Only
   a review with no open findings permits the coordinator to record ready status
   for that SHA. The reviewer executes directly and returns the review record.
8. Hand over to cb-desk/the human with commits, issues, checks, unmet criteria
   and unverified claims. Publication remains the human's unless explicitly
   authorized by controlling policy and the current task.

Use the ownership table above for every transition; author and reviewer report
outcomes instead of duplicating coordinator card writes. A missing board is
never interpreted as another project's board.

## Delegation and context

A coordinator keeps conclusions, not entire worker histories. Research uses
cb-worker; quick lookups use cb-helper. Each task includes applicable instructions/configuration, issue, scope, named files, done criteria and checks. A helper's output
is data: the requester reviews the diff and verifies commands/exit codes.
Helper assistance trailers name the actual model. No helper edits protected
paths or performs issue/board writes. Authors may request bounded helpers;
reviewers may request read-only helpers. Helpers and research leaves execute
one bounded task directly and start no children. A helper is never a replacement
issue author or independent reviewer, and never inherits claim/commit/landing
ownership. Only the designated coordinator starts issue/review workers.

At most one editor runs per worktree, and at most two code workers run at once.
A second lane worktree needs explicit project approval and disjoint file scopes,
including generated/dependency/policy files. Parents do not edit during editing
subagents. Independent read-only lookups may run in parallel.

Design runs in short batches, writes decisions and a resume note, then ends.
Only cb-dispatch starts the pinned design subagent, at most once an hour unless
a highest-priority issue is blocked; a human design session owns the role when
already open. Do not hand running agents to a new session or ask the human to
clear context. An idle lane reports an empty queue once and waits.

## Dynamic agent allocation

Recommend **eight subagent slots** for Codex. Desk is the primary session and
is excluded from this count. Six supports the normal role allocation; eight
leaves capacity for bounded helpers without crowding out coordination/review.

| Role | Subagent slots |
| --- | --- |
| Persistent dispatch | 1 |
| Authors | Up to 2 |
| Independent reviewers | Up to 2 |
| Design batch | Up to 1 |
| Optional bounded helpers | Up to 2 |
| Recommended capacity | 8 |

Dispatch allocates agents only for eligible work, retains its own handle and
reuses or releases completed workers after recording their handbacks. It does
not fill all slots merely because they exist. Client thread capacity and code
author limits are separate: eight slots do not authorize extra editors. Keep
at most two concurrent code authors, one editor per checkout, disjoint editing
scopes and independent review. Design runs only under its existing scheduling
and ownership rules. If capacity is lower, sequence work and preserve the
coordinator/review path rather than duplicate claims or starts.

From the target repository, start a fresh Codex desk session with:

```sh
codex -m gpt-6.1-sol -c model_reasoning_effort="low" -c agents.max_concurrent_threads_per_session=8 '$crewbook'
```

The single quotes preserve the literal skill invocation. Desk uses Sol/low;
it starts or resumes dispatch with the same explicit model/effort. Authors,
reviewers, design and helpers retain their role-specific mappings in
[README.md](../README.md). Generic and managed profiles use the same allocation
logic, subject to the actual host's capabilities and limits.

For a persistent Codex capacity default, add to the existing agents table in
user configuration (do not create a duplicate table):

```toml
[agents]
max_concurrent_threads_per_session = 8
```

The setting limits concurrently open spawned-agent threads, excluding the
primary thread. `agents.max_threads` is its legacy alias; see the
[official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml).

## Lifecycle example and walkthrough check

Static example, not a live client test: a trusted generic project supplies real
issue/board/check/landing adapters, one coordinator C, author A (cb-platform)
and eligible independent reviewer R (cb-reviewer, explicitly pinned Opus).
For cb-generic, use a session assignment and exclusive checkout; a board is
optional and landing/publication remain unavailable unless authorized.

| Event | Actor and action | Issue starts | Review starts |
| --- | --- | --- | --- |
| Assignment | C records the sole claim/In progress and starts A | 1 | 0 |
| Implementation | A executes directly; optionally asks cb-helper for a named lookup, receives its result and verifies it | 1 | 0 |
| Completion | A runs checks, commits and uses supplied landing; reports SHA S and criteria to C | 1 | 0 |
| Review assignment | C records In review after confirmed landing and starts R in separate context on S | 1 | 1 |
| Review completion | R reviews S directly, optionally uses a read-only helper, and records its findings | 1 | 1 |
| Handoff | C records Ready to push only on R's no-open-findings approval for S and hands off to human | 1 | 1 |

Walk through actions, not repeated wording: count only C's two worker-start
events; neither following A's role/profile/command nor following R's
role/profile/command produces another start. Helper lookup/return changes
neither count and owns no claim, commit, landing or review approval. Removing
the helper leaves exactly the same issue/review lifecycle. A resume at either
completion continues the existing assignment. Reject a trace where A starts
another cb-platform for its issue, R starts another reviewer for its review,
a helper starts children, or desk and dispatch both start A. Also reject a
same-context/self-review, inherited reviewer model, duplicate claim/card writer
or readiness for a SHA different from S. Missing adapters produce a reported
blocked operation, never a fabricated transition. This example checks text
semantics; runtime start suppression remains unverified.

## Evidence and portability

Use ordinary Markdown labels: **unverified** (not measured), **verified**
(measured with named test/spike and setup), **decided** (settled by the owner),
**open** (awaiting resolution). No Hugo frontmatter or shortcodes are needed.
Documentation, reported experience and local static checks are not live
client measurements. Record reproducible evidence at the configured destination.
The configured reference host and capabilities determine available live tests;
a developer machine is never an implicit substitute.

The client-neutral procedure material addresses reusable workflow text formerly
discussed in historical workharbor #240; these configuration prerequisites
address the portability advisory in historical workharbor #227. Native loading
measurements (historical workharbor #241) and platform doctor work (historical
workharbor #242) remain outside this change. See the
[workharbor example](profile-workharbor.md) for provenance and external tools.
