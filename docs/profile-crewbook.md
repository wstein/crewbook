# cb-crewbook project profile

This profile describes crewbook's own development, not a new local contribution
policy. The trusted operator supplies actual applicable policy and canonical
target root. Workharbor's local policies are not imported authority here.

| Field | Value / prerequisite |
| --- | --- |
| Identity | crewbook; cb-crewbook |
| Repository | GitHub wstein/crewbook; operator-supplied canonical root and remote; main integration branch |
| Issues | REST repos/wstein/crewbook/issues/<n>; labels documentation and area:docs for this docs scope; claim, finished-commit and completion comments; criteria updated with evidence |
| Board | pending setup: Werner approved a separate crewbook GitHub project with shared statuses, priorities, assignee, Session and views; project URL and host adapter are not created/supplied yet; staging blocker, no guessed IDs or workharbor project 6 fallback |
| Human | Werner, through the trusted invoking session/cb-desk |
| Worktrees | Relative to repository root: cb-platform ../crewbook-platform, cb-runtime ../crewbook-runtime, cb-docs ../crewbook-docs, cb-verify ../crewbook-verify, cb-review ../crewbook-review, cb-design ../crewbook-design, cb-desk ../crewbook-desk, cb-dispatch ../crewbook-dispatch; operator can explicitly override an assigned path |
| Checks | Trusted supplied quick_validate.py for SKILL plus manifest/reference/frontmatter/config review; exact command/interpreter path must be supplied; no shipped make check/check-ci or hooks |
| Landing | unavailable until a real procedure is supplied; local topic commit and handoff permitted only under task authorization; no make land fallback |
| Design | cb-design owns package/config decisions; README, crewbook.json, docs/project-config.md and docs/policy-composition.md are references, not automatically governing policy; protected paths and decision ownership must be supplied by trusted policy |
| Reference host | unavailable for native client loading/mount measurements; local text/path checks only, report setup; record check evidence in issue; live testing requires explicit setup/evidence configuration |
| Capabilities | Trusted package/file reader; isolated Git for local work; authorized gh REST for this repository only; quick validator external; board adapter pending host setup in workharbor; landing adapter unavailable until supplied; no runtime loader or platform doctor shipped |

For dispatch coordination, crewbook's board Session mapping is cb/<lane>:
cb/platform, cb/runtime, cb/docs, cb/verify, cb/review, cb/design, cb/desk and
cb/dispatch. These field values are independent of cb-* role/command names.
The shared schema uses the team manual's status/ownership boundaries, with
shared priorities, assignee and views; queues
must be scoped to crewbook's configured repository and project destination.
Until that destination, field mapping and adapter are supplied, board operations
are staging-blocked. A queued crewbook board setup item is forthcoming; its
number must be supplied, never guessed. Host tooling stays in workharbor.
This choice authorizes no board script port or live board write.

All role identities and Claude commands are cb-*. ../crewbook-<lane> is the
default layout for this project; a generic consumer explicitly maps its own
paths. cb-helper has no separate worktree. A second editing worktree requires
a separately supplied approval/map.

For this issue's authorized local commit: one finished Conventional Commit,
Refs: #3 and Assisted-by: codex:gpt-6.1-sol, no human sign-off or closing
trailer. This is a task-specific instruction, not a policy for future tasks.
Missing tools remain unavailable, never silently borrowed from workharbor.
