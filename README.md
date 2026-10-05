# crewbook

crewbook is an EUPL-1.2 package of development role prompts, imported from
[historical workharbor source](https://github.com/wstein/workharbor/tree/c6bbb7bcd903ea3027285baa9237f4ad179a9bb7). It is intended to be workharbor's default
replaceable skill set, installed outside work repositories; native Codex skill discovery uses the installed skill directory. Workharbor
runtime integration still awaits a supported production binding. Its distribution contains text
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
and `status`, and optional explicit `paths` for external file references.
They are descriptions, not install commands or authorization to run anything.
Relative links and paths beneath `${CREWBOOK_ROOT}` resolve inside the package;
an external file link must use `host:<path>` with an exact declared host path.
The maintained Go checker validates content, profiles, references and the
complete inventory without executing instructions.
[PROVENANCE.md](PROVENANCE.md) records the original import
and post-import transformations; the [distribution contract](docs/distribution.md)
separates current content integrity from pending runtime compatibility.

The native skill host supplies its installed directory, or a trusted launcher supplies `CREWBOOK_ROOT`, an absolute canonical path to an
installed or externally mounted copy of this package. This is a host-provided
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

Native skill use starts with the host instructions and user workspace, as
described in [SKILL.md](SKILL.md). Before applying specialized roles, read the
[policy composition contract](docs/policy-composition.md). Use trusted target
context and the configuration needed by that operation separately from
`CREWBOOK_ROOT`. Missing required inputs stop only the affected workflow. Routine native skill use follows existing host/project instructions even when
no `AGENTS.md` exists; specialized operations require their applicable inputs.

Package guidance cannot relax system/platform controls or human approval
boundaries. crewbook supplies no permission settings, hooks or tool enforcement;
native tool limits are not enforced by Makefiles. The contract documents trusted
writers and focused missing-policy/conflicting-skill review cases. Workharbor's
current Hard rules remain in its own project policy, not in this package.

## Entrypoints and support

- **Skill:** discover the installed `SKILL.md`; its host-provided directory
  supplies `CREWBOOK_ROOT`. A launcher may also load it by absolute path. Its routing table selects a role without loading all
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
  equivalence. Native Codex discovery is enabled by `agents/openai.yaml`; child model
  propagation still depends on the host.
- **workharbor:** mounted provisioning, root propagation and enforcement are
  **conceptual/unverified**, tracked in historical workharbor integration issue #283. This package supplies
  no enforcement, tool permissions or workharbor runtime adapter.

Public issue/review profiles and direct role commands execute as leaves, never
re-delegating their assignment. Only cb-dispatch or an explicitly designated
session coordinator starts those workers; cb-desk routes unless designated in
its place. The manual defines single ownership and a counted lifecycle example.

The [team manual](docs/team.md) covers roles, delegation, independent review,
handoffs and context. For configured team workflows, select applicable trusted project configuration:
[cb-generic](docs/profile-generic.md) is the default for any repository in
the current native session, without a workharbor container or board;
[cb-workharbor](docs/profile-workharbor.md) applies to any repository inside
a workharbor-managed container. Both profiles use the target repository's
instructions, destinations and checks; neither selects a specific repository.
Board and landing capabilities belong to the target project or supervisor;
none is shipped here. Missing host capability
means report the affected workflow as unavailable; do not fetch a substitute
from the package or provision infrastructure implicitly.

Documentation is root README plus docs/*.md in GitHub-flavored Markdown,
without Hugo frontmatter, shortcodes or toolchain. Native client loading (#241)
and platform doctor (#242) are historical workharbor work items, not measured
capabilities here. Source checks and CI do not establish native runtime support.

## Go maintenance

Maintainers use Go 1.27 or newer on Linux or macOS. The standard library handles
package maintenance; Goldmark parses GFM for content validation. Maintenance
code and module dependencies are excluded from the distributed text artifact.
From the source checkout, use a canonical absolute source path:

```sh
go run ./cmd/crewbook-package check --root /absolute/path/crewbook
go run ./cmd/crewbook-package inventory --root /absolute/path/crewbook
go run ./cmd/crewbook-package update --root /absolute/path/crewbook
go run ./cmd/crewbook-package export --root /absolute/path/crewbook --dest /absolute/path/new-text-package
go test ./...
go test -race ./...
go vet ./...
go build -trimpath -buildvcs=false -o /tmp/crewbook-package ./cmd/crewbook-package
```

Use a fixed Go patch version and `CGO_ENABLED=0` for reproducible optional
binary builds. No binary is needed by agents. `check` verifies source inventory,
required resources, supported scalar frontmatter, role/model mappings, prompt
links, bundled references, helper tool restrictions and GFM links/anchors.
Hugo shortcodes and undeclared host links fail. Maintenance-only `tools/README.md`
documents the supported syntax and focused nonzero-exit fixtures.

CI runs this same entrypoint, Go tests including race checks, vet and formatting
on ordinary pull requests, plus pinned redacted Gitleaks history/tree/message
scans. CodeQL builds and analyzes the actual Go maintenance packages. External
HTTP(S) link checks run only weekly or on manual request, with bounded retries
and timeouts; upstream outages do not gate ordinary package validation.
Dependabot proposes weekly Action and Go-module updates for human review.
Every Action has an official-upstream full commit pin and version comment;
checkout does not persist credentials. Routine jobs receive contents read;
only CodeQL receives security-events write. There is no agent execution,
board access, automatic merge, release or deployment. Native GitHub secret
scanning and push protection are separate enabled repository settings.
Maintenance-only `tools/CI.md` and `tools/SECURITY.md` record reproduction and
pin evidence. Hosted execution remains **unverified** until actual publication
and a GitHub run; passing local checks does not claim hosted success.

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

## Install, update, uninstall

For Codex, place the package in `~/.codex/skills/cb-crewbook` (or the corresponding
`$CODEX_HOME/skills` directory). For a local source checkout, use an absolute
symlink; keep it outside the target repository's instruction directories:

```sh
mkdir -p ~/.codex/skills
ln -s /absolute/path/crewbook ~/.codex/skills/cb-crewbook
```

If that destination already exists, inspect it before replacing anything.
Restart Codex or open a new session to refresh discovery. `agents/openai.yaml`
enables implicit invocation: ordinary repository requests can select Crewbook
automatically. `$cb-crewbook` remains available for explicit selection. The host's
loaded skill path supplies `CREWBOOK_ROOT`; no launcher or environment variable
is necessary. Routine coding, review, docs and verification use existing project
instructions without full team setup. Specialized roles load only on demand.

A symlink follows local edits; use a reviewed text export in the skill directory
when you need a fixed copy. Run the package check before export and preserve all
declared resources, licence and provenance. Both source and exported packages
include the Codex discovery metadata. This installation does not register Claude
commands or establish workharbor runtime compatibility. Workharbor's production
pin/adapter checks remain a separate integration contract.

To update a linked checkout, review and validate its changes. For a fixed copy,
validate a new export before switching registration for new sessions. Keep old
copies while active sessions use them. To uninstall a linked skill, remove only
the `cb-crewbook` symlink; retain the source checkout and target project policy.

## Licence and provenance

[LICENSE](LICENSE) retains EUPL-1.2, including its existing notices. The imported
prompts and manual originate in wstein/workharbor; crewbook's import is recorded
at the baseline SHA above. Keep the licence, provenance and existing attribution
when redistributing or updating; do not relabel imported material as newly
authored. New package documentation is distributed under the same licence.
