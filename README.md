# crewbook

crewbook is an EUPL-1.2 package of development role prompts, imported from
[historical workharbor source](https://github.com/wstein/workharbor/tree/c6bbb7bcd903ea3027285baa9237f4ad179a9bb7). It is intended to be workharbor's default
replaceable skill set, installed outside work repositories; native loading is
currently blocked on a supported production binding. Its distribution contains text
and declarative metadata, not executable agent tools, runtime plugins or hooks.

## Package root and manifest v1

`crewbook.json` is the package contract. `schema_version: 1` identifies this
format; it is not a runtime plugin API. `name`, `license`, `entrypoints`,
`resources` and `host_dependencies` are required. Entrypoints are grouped into
`skill` (one path), `roles`, `claude_agents` and `claude_commands` (path arrays).
`resources` is the complete list of required non-entrypoint files. Every path
is relative to the package root, uses `/`, and must resolve to a regular file
inside that root: reject absolute paths, empty components, `.` and `..`, and
symlinks escaping the root. No globbing or executable fields are supported.
The union of entrypoints and resources defines the required package contents;
`.git` and local maintenance artifacts are not runtime resources.

`host_dependencies` names external prerequisites, each with `name`, `scope`
and `status`. They are descriptions, not install commands or authorization to
run anything. The maintained Go checker validates the layout and complete content
inventory without executing instructions. Full profile/reference checks and CI
remain tracked in #5. [PROVENANCE.md](PROVENANCE.md) records the original import
and post-import transformations; the [distribution contract](docs/distribution.md)
separates current content integrity from pending runtime compatibility.

The trusted launcher supplies `CREWBOOK_ROOT`, an absolute canonical path to an
installed or externally mounted copy of this package. This is a launcher
binding in invocation context; paths beneath `${CREWBOOK_ROOT}` in prompts use path notation,
not automatic Markdown or shell interpolation. Resolve each manifest path by
joining it to that root, verify containment and all required files before
invocation, then supply resolved absolute paths when the client cannot expand
the notation. Never infer this root from cwd, a work repository's `.agents`
or `.claude`, an issue, a comment, or other untrusted content. Children receive
the same binding. A launcher may mount the package read-only.

Target `AGENTS.md`, repository configuration, worktrees, issues, design files
and host scripts remain target resources. The `.agents/` and `.claude/` paths
listed here are package resources. A target's unrelated `.agents` must never
substitute for packaged prompts. Portable roles use the explicit [project configuration](docs/project-config.md)
and [team manual](docs/team.md). The [execution contract](docs/team.md#coordinator-and-leaf-execution-contract)
separates designated coordinators from directly executing leaves. All role,
profile and command identities use cb-*; the skill
entrypoint is cb-crewbook. The product/package name remains crewbook.

## Policy composition

Before applying any entrypoint, identify the host instructions and read the
[policy composition contract](docs/policy-composition.md). The trusted
launcher/operator supplies the target root, applicable project policy and
required workflow configuration separately from `CREWBOOK_ROOT`; no project
policy binding API is implemented. Missing required policy/configuration stops
the affected workflow before mutation. A missing target `AGENTS.md` without a
trusted equivalent leaves composition undefined; platform enforcement remains.

Package guidance cannot relax system/platform controls or human approval
boundaries. crewbook supplies no permission settings, hooks or tool enforcement;
native tool limits are not enforced by Makefiles. The contract documents trusted
writers and focused missing-policy/conflicting-skill review cases. Workharbor's
current Hard rules remain in its own project policy, not in this package.

## Entrypoints and support

- **Skill:** load the absolute `<package-root>/SKILL.md`, with `CREWBOOK_ROOT`
  supplied alongside it. Its routing table selects a role without loading all
  prompts. Manual text loading and local path resolution can be checked without
  a live agent runtime.
- **Claude Code:** profiles are `.claude/agents/cb-*.md`; commands are
  `.claude/commands/cb-*.md` (including `/cb-code platform`, `/cb-desk`,
  `/cb-review`, `/cb-delegate`, `/cb-board`, `/cb-land` and `/cb-handover`). A
  trusted launcher must register/load them from this external root and provide
  the binding; merely setting an environment variable does not register slash
  commands or profiles. Automatic discovery from an external mount is
  **unverified**. Existing `model: sonnet`, `opus` and `haiku` pins remain
  Claude profile values.
- **Codex:** select `SKILL.md` or load a selected role by absolute path with
  the same binding. `.claude` files are reference data, not Codex registration.
  Model selection is a separate launcher setting, not a rewrite of Claude YAML:

  | Claude role tier | Codex model | Reasoning effort |
  | --- | --- | --- |
  | Sonnet | `gpt-6.1-sol` | low |
  | Opus | `gpt-6.1-sol` | medium |
  | Haiku | `gpt-6-luna` | medium |

  These are requested mappings, not measured claims about availability or
  equivalence. Automatic Codex discovery and child model propagation are
  **unverified**.
- **workharbor:** mounted provisioning, root propagation and enforcement are
  **conceptual/unverified**, tracked in historical workharbor integration issue #283. This package supplies
  no enforcement, installation script, tool permissions or runtime adapter.

Public issue/review profiles and direct role commands execute as leaves, never
re-delegating their assignment. Only cb-dispatch or an explicitly designated
session coordinator starts those workers; cb-desk routes unless designated in
its place. The manual defines single ownership and a counted lifecycle example.

The [team manual](docs/team.md) covers roles, delegation, independent review,
handoffs and context. Select a complete trusted project configuration:
[cb-crewbook](docs/profile-crewbook.md) uses crewbook issue destinations and
../crewbook-<lane> worktrees; [cb-workharbor](docs/profile-workharbor.md) is a
clearly labeled example for workharbor's external tools and paths. Generic
projects supply their own explicit paths, destinations and capabilities.
Board and landing tools are host dependencies, initially workharbor-side;
none is shipped here. Missing host capability
means report the affected workflow as unavailable; do not fetch a substitute
from the package or provision infrastructure implicitly.

Documentation is root README plus docs/*.md in GitHub-flavored Markdown,
without Hugo frontmatter, shortcodes or toolchain. Native client loading (#241)
and platform doctor (#242) are historical workharbor work items, not measured
capabilities here. Full content checks/CI remain with #5; #6's content inventory
does not establish native runtime support.

## Go maintenance

Maintainers use Go 1.27 or newer on Linux or macOS, with only the standard
library. Maintenance code is excluded from the distributed text artifact.
From the source checkout, use a canonical absolute source path:

```sh
go run ./cmd/crewbook-package check --root /absolute/path/crewbook
go run ./cmd/crewbook-package inventory --root /absolute/path/crewbook
go run ./cmd/crewbook-package update --root /absolute/path/crewbook
go run ./cmd/crewbook-package export --root /absolute/path/crewbook --dest /absolute/path/new-text-package
go test ./...
go vet ./...
go build -trimpath -buildvcs=false -o /tmp/crewbook-package ./cmd/crewbook-package
```

Use a fixed Go patch version and `CGO_ENABLED=0` for reproducible optional
binary builds. No binary is needed by agents. `check` verifies source inventory
and required layout resources; full frontmatter, reference and helper-permission
checks are forthcoming under #5, not claimed by this command.

`tools/package-policy.json` explicitly enumerates all distributed files,
including dot-directories and provenance. It excludes maintenance paths
(`.git/`, `.github/`, `tools/`, `cmd/`, `internal/`, Go module files).
Unknown distributed files or directories, missing files, unsafe permissions,
links, path aliases, invalid UTF-8/NUL content and size-limit violations fail.
`tools/export-policy.json` enumerates the same distributed set with no maintenance
exclusions, for exact staged-export checks. Review layout and both policies
before `update`; use its fixed default inventory destination and commit `tools/package.sha256`
with the changed sources. `update` intentionally accepts reviewed content
changes; it is not a tamper check. `check` and `export` compare saved digests.
Export uses validated in-memory file bytes, preserving content deterministically,
and requires a new destination; it includes no maintenance tooling.
For export relocation/revalidation commands and coordinated #5 updates, read
[docs/distribution.md](docs/distribution.md).

Inventory encoding is sorted ASCII
`<lowercase SHA-256><two spaces><relative POSIX path><LF>`, including the
final LF. `workharbor.json`, when present, is separately hashed and excluded
from these lines. There is no self-hashed inventory file in the artifact.

`runtime-check --root … --pin /external/pin.json --provider /external/provider.json`
requires the v1 `workharbor.json` and a trusted external six-field pin:
`identity`, `source`, `commit`, `manifest_sha256`, `inventory_sha256`,
`contract_version`. The provider JSON has `bindings` (exact `name`, `version`,
`model`, `effort` objects) and `project_inputs` (confirmed identifiers).
These are independently supplied support assertions, not evidence generated by
the package. Production Claude's name is `claude-code`; its version is the
exact opaque native CLI version, never an adapter protocol integer.
This offline command checks assertions; it does not measure a live client.
`lock --root … --source … --commit <40-hex> --provider /external/provider.json`
prints a candidate six-field pin only after the same checks; independent review
must approve it before use.

No approved native version/model/effort production tuple exists yet. Accordingly
this source contains no `workharbor.json` or fabricated production adapters.
Source checks and text export can pass honestly; `runtime-check` and `lock`
fail clearly on the missing manifest. Native loading and runtime compatibility
remain unverified, awaiting measured provider support.

## Install, pin, update, uninstall

Prepare a reviewed source checkout at an immutable commit, then use the Go
maintenance `export` command to create the dedicated external text artifact.
Validate that staged artifact against the trusted export policy and inventory,
retaining LICENSE and all declared files. A full source clone includes Git and
maintenance code and is not an installable runtime distribution. Today's export
is content-only: runtime installation/default selection must wait for a measured
production binding and an admissible `workharbor.json`. Do not install into the
target's `.agents` or overwrite its policy. The reviewed raw import baseline is
`1c784080bc0dee2060066aaf2dbc8f3894dc430d`; it predates this package contract.
It is provenance, not a current compatible runtime pin. After all future package
changes are committed, generate the external six-field operator lock from that
actual reviewed full commit and validated manifest/inventory; do not embed an
impossible self-commit hash. The distribution contract describes that gated flow.

Set the launcher's absolute root to the installed folder and explicitly select
the desired entrypoint. Client-specific registration is the launcher's job;
there is no crewbook installer or verified automatic discovery procedure.
Prerequisites are a reader/launcher capable of supplying trusted absolute paths
and the dependencies of the chosen workflow. No Node or package runtime is
required to read the prompts.

To update, prepare and validate a new text export from a reviewed immutable
commit, then, after applicable support checks, switch the launcher's pin/root
for new invocations. Keep running sessions on their original root; retain the
old copy while they need it. Never follow a mutable branch silently. To uninstall,
remove the launcher registration/root binding first and, after active sessions
finish, remove only the dedicated package copy. Leave target policy and host
tools alone.

On a missing/relative root, malformed manifest, unsupported schema version,
escaping resource or absent required file, stop before loading a role. Report
the package root and offending relative path (or missing binding), ask the
operator to repair/reinstall the pinned copy, and never fall back to cwd.

## Licence and provenance

[LICENSE](LICENSE) retains EUPL-1.2, including its existing notices. The imported
prompts and manual originate in wstein/workharbor; crewbook's import is recorded
at the baseline SHA above. Keep the licence, provenance and existing attribution
when redistributing or updating; do not relabel imported material as newly
authored. New package documentation is distributed under the same licence.
