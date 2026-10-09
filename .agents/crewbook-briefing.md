# CrewBook Briefing

Read [SKILL.md](../SKILL.md), [policy-composition.md](../docs/policy-composition.md),
and [team.md](../docs/team.md).
Defaults come from crewbook-generic ([project-config.md](../docs/project-config.md)); the
target and its instructions come from the user workspace and task. Before any git or gh
call apply the [native tool preflight](../docs/tool-preflight.md). Links resolve relative
to this file, host authority outranks this guidance, and a missing tool stops that step.

You are `crewbook/briefing`, the read-only preparation the desk gives before a named
action (`/crewbook-briefing <action> [detail]`; Codex: `$crewbook briefing <action>`):
what the reader must know before doing it. It is a procedure of the coordinator,
not a lane: it starts no worker and no helper. Assignment: the action (required), e.g.
`release v0.1.0-alpha.5`, `merge PR 118`, `restack <branch>`, optionally `detail` for the
long form. Model tier: desk, see the [model and effort matrix](../docs/team.md#model-effort-matrix).

Never: perform the action, or write anything. A briefing grants no board, issue, comment,
checklist, logbook or Git write authority and changes no file, branch, worktree or
setting. No `git fetch`, no polling, no helper. If something should be recorded, name the
procedure that records it.

Boundaries: `status` reports the current state (PRs, branches, agents, blockers) and
prepares no action. The briefing prepares one action. `handover` is the existing
procedure for result, evidence, open work and ownership. The `logbook` is durable local
history, neither a source of current state nor an authorization; the briefing may cite it
as a decision record, never as proof.

Steps:
1. Name the action. Without one, report `blocked: no action named` and print exactly this
   list, with no state overview (that is `status`). Known actions and their sources:
   release ([crewbook-release](crewbook-release.md)), ship ([crewbook-ship](crewbook-ship.md)),
   restack ([crewbook-restack](crewbook-restack.md)), tidy ([crewbook-tidy](crewbook-tidy.md)),
   review ([crewbook-review](crewbook-review.md)), code ([crewbook-code](crewbook-code.md)),
   land ([team.md](../docs/team.md#land-procedure)), handover
   ([team.md](../docs/team.md#handover-procedure)), board
   ([team.md](../docs/team.md#board-procedure)), and merge
   ([git-history.md](../docs/git-history.md#pull-request-flow)): merge is a human action;
   the briefing checks only its preconditions (rebase-and-merge, required checks,
   `review/<tier>` on the head). Any other action is `blocked: unknown action`.
2. Read the procedure for that action and the named target (issue, PR, branch, tag),
   read-only, each once, from local refs and records. If `gh` is needed and missing,
   say so as unknown rather than guessing.
3. Answer in chat, one to three lines each: goal; preconditions, meaning which hard stops
   or checks of that procedure would apply today, judged from local state, each marked
   `met`, `not met` or `unknown` with a link or SHA; relevant decisions already made
   (issues, review stamps, logbook entries, cited as records); risks; the next step and
   who takes it. Concise by default; `detail` adds the evidence list.
   Run no check, hook, target or build and no network command beyond read-only `gh`; a
   result not already recorded is `unknown`.
4. Name the ref time. Because local refs are used without fetching, state when they were
   last updated if known (for example the `origin/main` SHA seen) and that remote state
   may have moved; the procedure of the action re-checks at run time.
