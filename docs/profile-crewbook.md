# cb-crewbook project profile

This profile describes crewbook's own development, not a new local contribution
policy. The trusted operator supplies actual applicable policy and canonical
target root. Workharbor's local policies are not imported authority here.

| Field | Value / prerequisite |
| --- | --- |
| Identity | crewbook; cb-crewbook |
| Repository | GitHub wstein/crewbook; operator-supplied canonical root and remote; main integration branch |
| Issues | REST repos/wstein/crewbook/issues/<n>; labels documentation and area:docs for this docs scope; claim, finished-commit and completion comments; criteria updated with evidence |
| Board | Verified existing owner wstein, project 10, ID PVT_kwHNjWrOAZaiCg, https://github.com/users/wstein/projects/10; reviewed host adapter and live mapping below; UI checks remain pending under #7 |
| Human | Werner, through the trusted invoking session/cb-desk |
| Worktrees | Relative to repository root: cb-platform ../crewbook-platform, cb-runtime ../crewbook-runtime, cb-docs ../crewbook-docs, cb-verify ../crewbook-verify, cb-review ../crewbook-review, cb-design ../crewbook-design, cb-desk ../crewbook-desk, cb-dispatch ../crewbook-dispatch; operator can explicitly override an assigned path |
| Checks | Go 1.27+: go run ./cmd/crewbook-package check --root <canonical-source-root>, go test ./..., go vet ./...; source content, GFM references, layout and inventory checks; CI wiring supplied, hosted execution unverified; no shipped make check/check-ci or hooks |
| Landing | unavailable until a real procedure is supplied; local topic commit and handoff permitted only under task authorization; no make land fallback |
| Design | cb-design owns package/config decisions; README, crewbook.json, docs/project-config.md and docs/policy-composition.md are references, not automatically governing policy; protected paths and decision ownership must be supplied by trusted policy |
| Reference host | unavailable for native client loading/mount measurements; local text/path checks only, report setup; record check evidence in issue; live testing requires explicit setup/evidence configuration |
| Capabilities | Trusted package/file reader; isolated Git for local work; authorized gh REST for this repository only; Go maintenance checks in source checkout; reviewed board adapter remains host-side and requires explicit invocation prerequisites below; landing adapter unavailable until supplied; no runtime loader or platform doctor shipped |

For dispatch coordination, crewbook's board Session mapping is cb/<lane>:
cb/platform, cb/runtime, cb/docs, cb/verify, cb/review, cb/design, cb/desk and
cb/dispatch. These field values are independent of cb-* role/command names.
Live readback recorded in [issue 7](https://github.com/wstein/crewbook/issues/7)
confirms Status values Todo, In progress, Blocked, In review, Ready to push and
Done; Priority values P1, P2 and P3; the cb/<lane> Session values above with
the existing Werner option preserved. Agents cannot select Werner. Queues
remain scoped to wstein/crewbook and project 10; the team manual retains
status/ownership boundaries.

The operator supplies a trusted absolute path to workharbor's
scripts/board-snapshot.sh. The reviewed host commit is
a732e0668a35473cdca6f553d9d6162d8e1f8084; script SHA-256 is
b4ffc53fd2d32f9c4a0e6906c39fc706c428bba1a84d2d75d8d4f428d8fe43e4.
Each authorized invocation uses this explicit host adapter mapping:

```sh
WHR_BOARD_REPOSITORY=wstein/crewbook \
WHR_BOARD_OWNER=wstein \
WHR_BOARD_PROJECT_NUMBER=10 \
WHR_BOARD_PROJECT_ID=PVT_kwHNjWrOAZaiCg \
WHR_BOARD_LANE_PREFIX=cb \
bash "${TRUSTED_HOST_BOARD_SCRIPT}" <authorized-operation-and-arguments>
```

TRUSTED_HOST_BOARD_SCRIPT is an operator-supplied path, not a package loader
input or a new crewbook configuration API. Before any mutation, require the
trusted host script to be available, authorized authentication for this exact
destination and permission for the requested operation; report a missing
prerequisite and stop. Do not copy the script into crewbook, resolve it from
CREWBOOK_ROOT, discover it globally, run it automatically or fall back to
workharbor project 6. This contract grants no board write permission or
automatic native client loading.

Live setup and readback verified five repository/status-scoped views: Dispatch
queue, Active work, Review queue, Blocked work, and Release and milestones.
Their ordered fields are Title, Status, Priority, Assignees, Session and
Milestone. Existing Roadmap and Board views were preserved; project 6 was
untouched. UI Priority ascending sorting, milestone grouping and workflow-rule
trigger/action behavior remain unverified. In project 10, open Dispatch queue,
choose Sort, select Priority ascending (P1, P2, P3) and save. Open Release and
milestones, choose Group, select Milestone and save. Reload both views to verify
the saved settings. Open the project menu's Workflows, inspect Item closed and
verify that only issue closure sets Status to Done. Disable any workflow that
sets Ready to push, sets Done on merge or another trigger, or closes an issue
when Status changes. Save, reload and record the settings in issue 7. Inspect
each enabled workflow's trigger and action; test a real closure only with human
authorization to close that issue. These are pending operator steps from the
host manual, not actions performed by this docs slice.
Metadata identity/enabled state cannot establish rule behavior, and the adapter
cannot mutate workflow rules. These remaining UI tasks keep issue 7 Blocked
after this docs slice; do not mark the whole issue Ready to push or Done.

The four verified milestone assignments are grouping, not serial gates:

| Milestone | Issues |
| --- | --- |
| 1: Portable foundation | 1–8 |
| 2: Codex | 9 |
| 3: Reliable workflows | 11–16 |
| 4: AGY | 10 |

Complete Codex issue 9, then start milestone 3 immediately before AGY.
Optional issue 7 view setup is not a prerequisite for Codex.

All role identities and Claude commands are cb-*. ../crewbook-<lane> is the
default layout for this project; a generic consumer explicitly maps its own
paths. cb-helper has no separate worktree. A second editing worktree requires
a separately supplied approval/map.

Lifecycle ownership follows the team manual: one explicitly designated
coordinator owns claims/cards and starts, an assigned author leaf owns local
checks/commits and any supplied landing, and an independent eligible reviewer
leaf owns the exact-SHA review record. The trusted invocation names these
owners and model/effort; this example supplies no implicit coordinator.
Missing tools remain unavailable, never silently borrowed from workharbor.
