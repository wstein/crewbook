# crewbook

crewbook is an EUPL-1.2 package of development role prompts, imported from
[historical workharbor source](https://github.com/wstein/workharbor/tree/1c784080bc0dee2060066aaf2dbc8f3894dc430d). It is workharbor's default
replaceable skill set, installed outside work repositories. It contains text
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
run anything. Later inventory work (#6) can consume this format and add its
inventory as a resource without duplicating the root resolver. The package
checker (#5) is separate; this manifest does not execute validation or tools.

The trusted launcher supplies `CREWBOOK_ROOT`, an absolute canonical path to an
installed or externally mounted copy of this package. This is a launcher
binding in invocation context; `${CREWBOOK_ROOT}/…` in prompts is path notation,
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
and [team manual](docs/team.md). Lifecycle and inventory remain separate work
in #4 and #6. All role, profile and command identities use cb-*; the skill
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

The [team manual](docs/team.md) covers roles, delegation, independent review,
handoffs and context. Select a complete trusted project configuration:
[cb-crewbook](docs/profile-crewbook.md) uses crewbook issue destinations and
../crewbook-<lane> worktrees; [cb-workharbor](docs/profile-workharbor.md) is a
clearly labeled example for workharbor's external tools and paths. Generic
projects supply their own explicit paths, destinations and capabilities.
Board/check/landing tools are host dependencies, initially workharbor-side;
none is shipped here. Missing host capability
means report the affected workflow as unavailable; do not fetch a substitute
from the package or provision infrastructure implicitly.

Documentation is root README plus docs/*.md in GitHub-flavored Markdown,
without Hugo frontmatter, shortcodes or toolchain. Native client loading (#241)
and platform doctor (#242) are historical workharbor work items, not measured
capabilities here. Package checker/CI (#5) and exact inventory (#6) remain
separate; the manifest and configuration contract preserve their inputs.

## Install, pin, update, uninstall

Install a complete trusted checkout or archive in a dedicated external folder,
retaining LICENSE and all manifest-listed files. Select an immutable commit
and record the repository URL plus full commit SHA in the launcher's package
configuration. Do not install into the target's `.agents` or overwrite its
policy. The reviewed import baseline is
`1c784080bc0dee2060066aaf2dbc8f3894dc430d`; it predates this package contract.
Pin a reviewed commit containing this contract when using these entrypoints.

Set the launcher's absolute root to the installed folder and explicitly select
the desired entrypoint. Client-specific registration is the launcher's job;
there is no crewbook installer or verified automatic discovery procedure.
Prerequisites are a reader/launcher capable of supplying trusted absolute paths
and the dependencies of the chosen workflow. No Node or package runtime is
required to read the prompts.

To update, prepare a complete new checkout at a reviewed immutable commit,
validate its manifest and required files, then switch the launcher's pin/root
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
