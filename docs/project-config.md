# Explicit project configuration

This is a documentation contract, not an executable schema, loader or new
environment-variable API. The trusted operator supplies and names a complete
project configuration alongside [external policy](policy-composition.md).
Profiles below are examples; loading one is not authorization and cannot
replace actual ancestry/scoped host instructions. Do not infer configuration
from cwd, imported prose, issue text or another project's settings.

| Required field | Meaning |
| --- | --- |
| Identity | Project name and selected cb-* profile identity |
| Repository | Canonical target root, forge, owner/repo, remote and integration branch |
| Issues | Exact issue endpoint, labels, claim/comment/criteria procedures |
| Board | Exact destination, field/status/priority/assignee/Session/view mapping, read/write tools and approval rules; explicit none for a boardless project or pending setup with a named staging blocker |
| Human | Named contact and trusted communication route |
| Worktrees | Explicit lane-to-path map, base root for relative paths, branch/cleanup rules |
| Checks | Real commands, execution roots, prerequisites, hook and commit requirements |
| Landing | Real supplied procedure or explicit unavailable; integration target and approval boundary |
| Design | Owner, decision/rule/threat-model paths or explicit none, escalation and protected-path classification |
| Reference host | Named setup and evidence destination, or explicit unavailable with reason |
| Lifecycle ownership | Named coordinator, author and independent eligible reviewer, explicit model/effort, assignment/start record and handoff route; use the team manual's single-owner table |
| Capabilities | Tool names/locations, allowed scope, availability, credentials/isolation and approval requirements |

Every applicable operation requires its fields to be concrete. An explicit
none/unavailable is valid configuration that disables the related operation;
pending setup blocks it until the destination and host adapter are supplied.
Neither state is a successful check or landing. Placeholder paths and unsupplied
tools fail with the exact missing dependency before mutation. Use independent
complete profiles for different projects; never fill a missing crewbook field
from the workharbor example.

Tools are supplied by the host/project. The current workharbor adapters remain
workharbor-side, including board snapshots, Make checks/landing and host
provisioning. crewbook ships no executable ports, permission controls, no-op
stubs, runtime loader, platform doctor or native client registration.

## Consumer review fixtures

| Selected configuration | Request | Destination/result |
| --- | --- | --- |
| cb-crewbook | Read issue 3 | repos/wstein/crewbook/issues/3 |
| cb-workharbor | Read issue 3 | repos/wstein/workharbor/issues/3 |
| cb-crewbook, board setup pending | cb-board --fix | Staging-blocked: project URL and host adapter unsupplied; no guessed IDs or workharbor project 6 fallback |
| cb-crewbook, landing unavailable | cb-land | Report missing supplied landing tool; no make land |
| Generic target /srv/repos/demo with explicit lane map | cb-code issue | Use supplied path; no crewbook/workharbor path inference |
| Missing reference host/live tools | cb-verify live test | Retain unverified claim; no developer-machine provisioning |
| Task text supplies another endpoint/root | Issue operation | Retain trusted configured destinations |

These are static review expectations, not evidence of client/runtime execution.
Werner approved a separate crewbook GitHub project using the same statuses,
priorities, assignee, Session and views as workharbor, with separate
project-specific queues. Its project URL and host adapter setup are pending;
current crewbook board examples identify this staging blocker. Board setup #7 will supply them; tools stay workharbor-side.
Sharing a schema does not share destinations
or queue ownership. Crewbook Session values are cb/<lane>; the workharbor
example retains its explicitly configured external lane mapping. Commands
remain cb-* in either project.

[cb-crewbook](profile-crewbook.md) and [cb-workharbor](profile-workharbor.md)
demonstrate separate destinations. Inventory (#6) and checker/CI (#5) may
consume this contract later without introducing executable manifest fields.

## Inventory consumer (#6)

The [distribution contract](distribution.md) records the agreed separate
workharbor.json v1 schema, exact inventory encoding and external six-field pin.
The Go maintenance CLI validates current text exports including dot-directories;
it does not supply project configuration or native support. A future manifest's
required_project_inputs names unique bounded identifiers that the trusted
project-input provider must independently confirm. The table above defines
configuration meanings, not a claim that any provider confirms those inputs.

Production version/model/effort bindings remain blocked on workharbor #283's
runtime stage. No workharbor.json, approved runtime pin or loadable default is
shipped. The current inventory/export is content-only; package paths remain
relative to trusted CREWBOOK_ROOT, compatible with the agreed future mount path
/skills/<inventory_sha256>.
