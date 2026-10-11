# CrewBook managed profile (`crewbook-workharbor`)

Use this profile when the agent runs inside a workharbor-managed container.
The target can be any repository, including the CrewBook or workharbor repository itself.
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
| Topic / merge | Authorized owned-topic commit, push and PR under the human request; local-only assignments stay local. Human merges; agents never merge, tag, release or deploy |
| Design | Target's existing ownership/protected paths when defined; route consequential decisions through the trusted human route |
| Reference host | Assigned container for ordinary checks; an explicitly authorized separate setup for external/live measurements |
| Lifecycle | Named coordinator, author and independent reviewer; explicit model/effort and single-owner records from the team manual |
| Capabilities | Supervisor-provided tools, credentials and policy enforcement; never assume host tooling or access beyond assigned scope |

## Work inside the assigned environment

Run repository edits and checks in the assigned container. Respect the
supervisor's task/run identity, stop signals, budgets and actual allowed tools.
Requirements v3 remove routine per-action approvals and sensitive-action step-up;
this does not bypass actual host controls. Use only explicitly available forge, board and communication
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

## Requirements v3 environment and runtime boundary

The [WorkHarbor requirements catalog v3](https://github.com/wstein/workharbor/blob/main/docs/content/docs/requirements.md)
states direction; it does not establish an installed CLI or native capability.
D57 remains human initiation/resume with agent-controlled steps inside that
request, including long runs. There is no scheduler, API-key automation mode
or run time limit. The [human-request contract](team.md#human-request-contract)
keeps topic pushes, PRs and issue/card maintenance inside the authorized task.

Use stock language images for language toolchains. Mount the BundleDock common
utilities read-only, separate from the agent CLI tool store. Vendor login and
agent configuration remain inside the environment's persistent home volume;
`whr` never reads or stores them (D40). Keep HOME and writable caches outside
the read-only toolbox. Disposable build directories and caches belong under
`/var/tmp` outside the workspace mount; build outputs intended as artifacts stay
on the workspace mount. Never mount the host home, host `~/.ssh` or runtime
sockets into an environment.

R-13/R-40 Docker-compatible supervision is **next**, using the existing host
socket from `DOCKER_HOST`, Docker context or a known path. `whr setup` must not
install a runtime; a missing socket is reported not verified with documentation.
This is the target contract: current `whr` supervision uses the Apple Container
adapter; Docker support in the proof of concept does not establish that adapter
integration. Other runtime choices remain later and capability-based.

R-22's tool watchdog is **next**: warn after 10 minutes without output, abort
after 30 minutes, both configurable. These are tool-call inactivity limits,
not a run deadline. R-23's watchdog/quota/finished ntfy notifications are planned
extensions of the existing notifier; delivery, including self-hosted iOS, remains
unverified. CrewBook does not implement these runtime services.

R-30 requires forge token scope and branch protection to prevent agent merge,
tag, release and deployment. Prompt guidance supplies no enforcement. Whether
a write-scoped token can merge its own PR is unmeasured; R-35's doctor warning
when push is enabled but the ruleset is unverified is **next**, not a refusal.
Reported built requirements and package validation are not live measurements.

## UI values

For workharbor web UI work, crewbook-ui uses the mock directory `design/mock/`
and WCAG 2.2 AA. Other targets supply their own values.

## Release values

For workharbor releases, crewbook-release uses the notes directory `docs/releases/`
(file `<tag>.md`), the template `docs/releases/TEMPLATE.md`, the signer file
`.github/release-signers` (tags are SSH-signed), the workflow
`.github/workflows/release.yml`, the build config `.config/goreleaser.yaml` and the
provenance file `whr_<tag>.intoto.jsonl`. The archive is `whr_<tag without v>_darwin_arm64.tar.gz`,
with `checksums.txt`; the SBOM name is read from the workflow and build config.
Local source check: `make check-local`. `make release-snapshot` builds
without SBOM or publishing and requires explicit human build approval; never
run it merely because a release-notes or PR task was assigned. `make release-prep VERSION=<tag>` (git-cliff, rewrites
`CHANGELOG.md`, own `chore(release)` commit) is the human's step; the lane does not run
it. Tags are SSH-signed with the release key listed in the signer file. The previous
tag is the newest earlier `v*` tag by version order. Tags with a prerelease suffix are
prereleases and leave the tap untouched. The release job creates a draft
(pre-)release with its assets; the human publishes it.

## Evidence

Report target checks with their actual execution context and results.
Package validation does not prove container provisioning, native client loading
or runtime enforcement. Mark unmeasured managed capabilities unverified.

History policy resolution and the stop on missing or conflicting choices follow
[project-config](project-config.md#history-policy-resolution).
