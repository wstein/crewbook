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
Relative links resolve from the file containing each link;
an external file link must use `host:<path>` with an exact declared host path.
The Python checker validates layout, filesystem safety and the complete
inventory without interpreting instructions.
[PROVENANCE.md](PROVENANCE.md) records the original import
and post-import transformations; the [distribution contract](docs/distribution.md)
separates current content integrity from pending runtime compatibility.

Follow relative links from the loaded skill or role file. Package metadata
paths resolve relative to `crewbook.json`. No root environment variable,
launcher binding or placeholder expansion is required. Use the loaded skill's
resources rather than similarly named files in the target repository.

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
context and only the configuration needed by that operation. Missing required inputs stop only the affected workflow. Routine native skill use follows existing host/project instructions even when
no `AGENTS.md` exists; specialized operations require their applicable inputs.

Package guidance cannot relax system/platform controls or human approval
boundaries. crewbook supplies no permission settings, hooks or tool enforcement;
native tool limits are not enforced by Makefiles. The contract documents trusted
writers and focused missing-policy/conflicting-skill review cases. Workharbor's
current Hard rules remain in its own project policy, not in this package.

## Entrypoints and support

- **Skill:** discover the installed `SKILL.md`; follow links relative to that file. It may also be loaded by absolute path. Its routing table selects a role without loading all
  prompts. Manual text loading and local path resolution can be checked without
  a live agent runtime.
- **Claude Code:** profiles are `.claude/agents/cb-*.md`; commands are
  `.claude/commands/cb-*.md` (including `/cb-code platform`, `/cb-desk`,
  `/cb-review`, `/cb-delegate`, `/cb-board`, `/cb-land` and `/cb-handover`). A
  client must register/load these files from the installed skill directory; merely setting an environment variable does not register slash
  commands or profiles. Automatic discovery from an external mount is
  **unverified**. Existing `model: sonnet`, `opus` and `haiku` pins remain
  Claude profile values.
- **Codex:** select `SKILL.md` or load a selected role by absolute path from the installed skill. `.claude` files are reference data, not Codex registration.
  Model selection is a separate launcher setting, not a rewrite of Claude YAML:

  | Claude role tier | Codex model | Reasoning effort |
  | --- | --- | --- |
  | Sonnet | `gpt-6.1-sol` | low |
  | Opus | `gpt-6.1-sol` | medium |
  | Haiku | `gpt-6-luna` | medium |

  These are requested mappings, not measured claims about availability or
  equivalence. Native Codex discovery is enabled by `agents/openai.yaml`; child model
  propagation still depends on the host.
- **workharbor:** mounted provisioning and enforcement are
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

## Python maintenance

Use Python 3.9 or newer on macOS or Linux. The maintenance CLI uses only the
standard library; no pip packages, virtual environment, Go toolchain or
Markdown parser is needed. On a Mac with Apple's command line tools,
`/usr/bin/python3` is sufficient. Python availability depends on the macOS
installation; a machine without Python still needs an interpreter.

From the source checkout, use a canonical absolute root:

```sh
python3 tools/crewbook-package.py check --root /absolute/path/crewbook
python3 tools/crewbook-package.py inventory --root /absolute/path/crewbook
python3 tools/crewbook-package.py update --root /absolute/path/crewbook
python3 tools/crewbook-package.py export --root /absolute/path/crewbook --dest /absolute/path/new-text-package
python3 -B -m unittest discover -s tools -p 'test_*.py'
```

`check` validates package layout, file safety and saved inventory digests.
It does not parse Markdown, validate prompt prose, enforce role/model mappings
or resolve links. Instruction text is data and is never executed. `update`
accepts reviewed content changes and writes the inventory; it is not a tamper
check. Export uses validated snapshot bytes and requires a new destination.
Source/export policies enumerate the same distributed files, including dot
directories. Maintenance code, tests, CI and the inventory are not exported.

Inventory records are sorted ASCII
`<lowercase SHA-256><two spaces><relative POSIX path><LF>`, including the final
LF. `workharbor.json`, when present, is hashed separately and excluded from
these records. Keep changed resources, declarations and regenerated inventory
in the same commit. [tools/README.md](tools/README.md) describes command flags,
filesystem safeguards and tests; [docs/distribution.md](docs/distribution.md)
describes relocation and the runtime contract.

`runtime-check --root … --pin /external/pin.json --provider /external/provider.json`
requires the v1 `workharbor.json` and an independently reviewed six-field pin.
`lock --root … --source … --commit <40-hex> --provider /external/provider.json`
prints a candidate pin after the same checks. Provider assertions describe
exact version/model/effort bindings and confirmed project inputs. These offline
checks do not measure native client loading or runtime enforcement. No approved
production tuple or manifest is currently shipped; both commands fail clearly
on the missing manifest.

CI runs the Python tests and package check on Linux and macOS, plus isolated
secret-scanner fixtures. CodeQL analyzes Python maintenance source. External
HTTP(S) links are checked only on a schedule or manual request. Actions retain
immutable pins and least-privilege permissions. Hosted results remain
unverified until publication and an actual GitHub run.

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
loaded skill uses relative links; no launcher or environment variable is
necessary. Routine coding, review, docs and verification use existing project
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
