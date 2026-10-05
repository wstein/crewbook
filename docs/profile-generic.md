# cb-generic: ordinary repository workflow

Use this default profile in any repository through the current native agent
session. No workharbor installation, supervisor, container, reference host,
board adapter or launcher is required. Follow relative links from the loaded skill files; the user workspace and
task supply the target repository.

## Resolve only what the task needs

Read applicable ancestry and scoped AGENTS.md files when present. If none
exist, follow host instructions, the user request and this generic workflow.
Missing project-specific policy alone does not block local work or dispatch.
Use existing repository documentation and tools to determine checks. Inspect
Git remotes to identify an issue destination when needed; verify the destination
before an external write. Ask only when context cannot resolve a material ambiguity.
Never borrow workharbor endpoints, credentials, hooks or lane paths.

| Field | Generic default |
| --- | --- |
| Identity | Target repository; cb-generic |
| Repository | Canonical root from workspace/task; inspect existing remote and branch conventions when Git operations are needed |
| Issues | User task or supplied issue; use existing authorized forge CLI/API when available; no issue required for local work |
| Board | None unless the user or applicable policy selects a board; do not require board setup to dispatch local tasks |
| Human | User in the current session |
| Worktrees | Current checkout for one authorized editor; use an explicitly assigned isolated checkout for concurrent editing; no persistent lane directory required |
| Checks | Existing repository commands appropriate to the change; report unavailable checks and their limits |
| Landing | Local diff and handoff by default; no automatic commit, merge, push or publication; use project procedures only when authorized |
| Design | Existing owner/protected paths if defined; otherwise coordinator routes consequential decisions to the user and avoids overlapping ownership |
| Reference host | None needed for local work; external measurements require an explicitly authorized setup |
| Lifecycle | Invoking dispatch session is coordinator; named author/reviewer assignments with explicit model/effort follow the team manual |
| Capabilities | Tools available in the current session; require authentication and permission only for operations that use them |

## Dispatch without a supervisor

A request to start dispatch designates the current session as coordinator.
Invoking cb-desk instead automatically starts/reuses one persistent dispatch
subagent; desk is the human contact and that subagent is the coordinator.
Check current assignments and issue claims using available session/forge evidence;
do not require a separate desk session. Use the invoking session for human
communication. Route user tasks directly when no issue queue is configured.
For an issue queue, use confirmed issue priorities and ownership; a missing
optional board does not block work. Do not treat an unknown required board
status or claim as permission to take already-owned work.

Record each assignment in the current session before starting one fresh author
context with the selected skill resources, target, applicable instructions, scope,
checks and explicit model/effort. At most two code workers and one editor per
checkout may run. With one checkout, run editors sequentially. No external
claim/comment or card write is needed for a local task. Require an independent
review for publication and report the exact reviewed revision; a local diff
handoff may remain uncommitted and unlanded. Preserve host approval boundaries.

When a requested operation lacks a required capability, report that operation
and continue independent authorized work. Do not turn missing workharbor
infrastructure into a blocker for generic repository development.
