# Crew Book managed profile (`crewbook-workharbor`)

Use this profile when the agent runs inside a workharbor-managed container.
The target can be any repository, including the Crew Book or workharbor repository itself.
The profile selects execution context, never repository identity or endpoints.
For an ordinary native session, use [crewbook-generic](profile-generic.md).

## Trusted managed context

The supervisor/host supplies the target checkout, assignment, applicable
instructions and available capabilities. Follow relative links from the installed or mounted skill files independently
of the target checkout. Read ancestry and scoped
AGENTS.md files when present; when absent, follow host instructions and the
user task. Do not require a repository-specific profile or governing file.

| Field | Managed behavior |
| --- | --- |
| Identity | Assigned target repository; crewbook-workharbor execution profile |
| Repository | Supervisor-assigned canonical checkout, remote and branch; never assume wstein/workharbor or main |
| Issues | Assigned issue/task and confirmed target forge endpoint; use supplied authorized capability |
| Board | None unless explicitly configured for the target; use only its supplied mapping and approved adapter |
| Human | User through the supervisor's trusted communication route or current invoking session |
| Worktrees | Assigned managed checkout; do not create host lane paths or switch another checkout's branch |
| Checks | Target repository's existing commands inside the assigned environment; no default make check, hooks or workharbor build targets |
| Landing | Supplied target procedure and authorization; otherwise local diff/handoff without merge, push or publication |
| Design | Target's existing ownership/protected paths when defined; route consequential decisions through the trusted human route |
| Reference host | Assigned container for ordinary checks; an explicitly authorized separate setup for external/live measurements |
| Lifecycle | Named coordinator, author and independent reviewer; explicit model/effort and single-owner records from the team manual |
| Capabilities | Supervisor-provided tools, credentials and policy enforcement; never assume host tooling or access beyond assigned scope |

## Work inside the assigned environment

Run repository edits and checks in the assigned container. Respect the
supervisor's task/run identity, stop signals, budgets, allowed tools and
approval gates. Use only explicitly available forge, board and communication
capabilities. The package supplies workflow guidance, not a container launcher,
credential store, runtime adapter or permission override.
Reuse established operation authorization within its scope, subject to actual
supervisor/host controls. Keep local commits, target integration and publication
separate; follow the target's exact review/integration order. Authorization for
local integration alone never authorizes a push or publication.

A board is optional. For a local task without a board, the coordinator records
a session/supervisor assignment before starting the author. A configured
board/status mapping with an authorized writer, or a required external claim
procedure, selects [split mode](team.md#coordinator-modes); a
supervisor-supplied registry path overrides the default
[registry location](project-config.md#coordinator-mode-and-registry). Do not bypass an
explicitly configured issue claim or status gate. Confirm ownership before
starting or resuming; never duplicate a supervisor-started worker.

When an adapter or managed capability required by an operation is unavailable,
report that operation and continue independent authorized work inside the
assigned environment. Do not provision containers, access host credentials,
copy host tools or run a host fallback implicitly. If the agent is outside a
managed container, use crewbook-generic; do not claim managed execution from a
repository name or the presence of workharbor files.

## Evidence

Report target checks with their actual execution context and results.
Package validation does not prove container provisioning, native client loading
or runtime enforcement. Mark unmeasured managed capabilities unverified.

History policy resolution and the stop on missing or conflicting choices follow
[project-config](project-config.md#history-policy-resolution).
