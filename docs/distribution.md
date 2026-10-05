# Distribution and workharbor consumer contract

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
[PROVENANCE.md](../PROVENANCE.md) records the original import
and post-import transformations; the [distribution contract](distribution.md)
separates current content integrity from pending runtime compatibility.

Follow relative links from the loaded skill or role file. Package metadata
paths resolve relative to `crewbook.json`. No root environment variable,
launcher binding or placeholder expansion is required. Use the loaded skill's
resources rather than similarly named files in the target repository.

Target `AGENTS.md`, repository configuration, worktrees, issues, design files
and host scripts remain target resources. The `.agents/` and `.claude/` paths
listed here are package resources. A target's unrelated `.agents` must never
substitute for packaged prompts. Portable roles use the explicit [project configuration](project-config.md)
and [team manual](team.md). The [execution contract](team.md#coordinator-and-leaf-execution-contract)
separates designated coordinators from directly executing leaves. All role,
profile and command identities use cb-*; the skill
entrypoint is `crewbook`, invoked as `$crewbook`. The package and skill identifiers remain `crewbook`; the reader-facing name is “Crew Book”.

## Current content artifact

The original import is recorded in [PROVENANCE.md](../PROVENANCE.md), including
its exact selected paths and separate source-removal boundary. The current
distribution is a different artifact: `tools/package-policy.json` in the
reviewed source checkout explicitly enumerates its text files. `crewbook.json`
declares the same resources and entrypoints. `tools/package.sha256` records
their current byte digests, not the original import digests.

These maintenance files and all Python maintenance source/tests, `.github/` and `.git/`
are excluded from the distribution. The export contains LICENSE, provenance,
README, SKILL, Codex discovery metadata, layout metadata, docs and every declared `.agents/` and `.claude/`
resource. It contains no agent executable tools, runtime plugins, permission
settings, hooks or maintenance inventory. A source checkout can be linked as a native Codex skill; a pinned distribution
uses the exported text artifact. No automatic upstream synchronization or source deletion follows
from either inventory.

The maintenance CLI validates source content and emits a deterministic export
from its validated snapshot. Export files use mode `0400`; directories use
`0700`. Existing destinations are refused. Revalidation uses the separately
maintained `tools/export-policy.json`: it has the identical distributed set
and **no maintenance exclusions**, so extra `.git/`, tools or CI files in a
staged export cannot be ignored. Supply this policy and the saved inventory
from the trusted source checkout, outside the export:

```sh
python3 /absolute/source/crewbook/tools/crewbook-package.py check --root /absolute/source/crewbook
python3 /absolute/source/crewbook/tools/crewbook-package.py export --root /absolute/source/crewbook --dest /absolute/staged/crewbook-text
python3 /absolute/source/crewbook/tools/crewbook-package.py check --root /absolute/staged/crewbook-text --policy /absolute/source/crewbook/tools/export-policy.json --inventory /absolute/source/crewbook/tools/package.sha256
```

Roots must be canonical absolute paths; no cwd or target-repository fallback
exists. The source policy's maintenance exclusions are for source checks only.
The export can be relocated to another external root and rechecked with the
same trusted export policy/inventory. Missing, extra or tampered text refuses
the check. A passing content check establishes integrity/layout, not native
client registration, loading, permissions or compatibility.

## Deterministic inventory and updates

Every distributed file, including dot-directory resources, is hashed except
`workharbor.json` itself when that future manifest exists. Sort relative POSIX
paths by ascending ASCII bytes. The inventory bytes are UTF-8 records:

```text
<64 lowercase hexadecimal SHA-256><two spaces><relative POSIX path><LF>
```

The final record also ends in LF. SHA-256 of all concatenated records is
`inventory_sha256`; hash file bytes exactly, without newline normalization.
The runtime manifest is hashed separately as `manifest_sha256`. No file embeds
its own digest, and package-reported hashes do not establish operator trust.

For a reviewed package edit, change the required resources in `crewbook.json`
and both source/export policies if the file set changes. Keep their distributed
sets identical; `tools/export-policy.json` must retain `maintenance: []`.
Then run:

```sh
python3 /absolute/source/crewbook/tools/crewbook-package.py update --root /absolute/source/crewbook
python3 /absolute/source/crewbook/tools/crewbook-package.py check --root /absolute/source/crewbook
python3 /absolute/source/crewbook/tools/crewbook-package.py inventory --root /absolute/source/crewbook
```

`update` accepts deliberately reviewed new bytes; it is not a tamper check.
Commit the changed content, declarations and generated `tools/package.sha256`
together. Repeating update on unchanged content produces identical bytes.
The original extraction evidence is not regenerated. The layout checker/CI
must perform this same coordinated update when it changes packaged resources;
adding maintenance-only CI or Python source changes no distributed bytes.

## Agreed producer metadata for workharbor #283

The following v1 encoding is agreed structurally with the platform author.
It describes the future runtime manifest; this content-only artifact currently
ships **no `workharbor.json`**. Unknown or duplicate JSON keys are invalid,
including nested objects. JSON and resources must be UTF-8.

| Manifest field | Required type and constraint |
| --- | --- |
| `contract_version` | Integer exactly `1`. |
| `identity` | String matching `[a-z][a-z0-9_-]{0,63}`; crewbook identifies itself as `crewbook`. |
| `entrypoint` | Relative path to one inventoried public text file; crewbook's entrypoint is `SKILL.md`. |
| `required_project_inputs` | Array of at most 32 unique strings, each using the identity syntax; confirmed separately by the trusted project-input provider. |
| `adapters` | Array of 1–32 objects, each with required string `name`, `version`, `model`, `effort`; names use the identity syntax and are unique. |
| `files` | Array of required `{path, sha256}` string pairs, complete and sorted as above, excluding `workharbor.json`. |

Adapter version/model strings are nonempty and at most 128 UTF-8 bytes; effort
is nonempty and at most 32 bytes. They contain no CR, LF or NUL. `version` is
the exact opaque native CLI version string, not the integer adapter protocol,
a version range, wildcard or an invented value. The provider must validate
and apply the exact name/version/model/effort tuple; matching declared strings
alone does not measure support. Missing inherited/default model or effort is
not substituted for a required binding. An empty adapter array is invalid.

Paths are at most 240 ASCII bytes, using only letters, digits, `.`, `_`, `-`
and `/`. Refuse absolute paths, empty/`.`/`..` components, backslashes, trailing
dots, `.git` components, controls, non-ASCII and case collisions across files
or directories. Refuse symbolic/hard links, executables, special files,
unexpected empty directories, unsafe ownership/permissions and binary content.
Limits are 256 KiB manifest, 1,024 inventoried files, 1 MiB per file, 16 MiB
total and 16,384 filesystem entries.

The trusted external operator lock has exactly six required fields:

| Pin field | Required type and constraint |
| --- | --- |
| `contract_version` | Integer exactly `1`. |
| `identity` | Package identity string, with the manifest's identity syntax. |
| `source` | Nonempty repository identity string, at most 2,048 UTF-8 bytes; no CR, LF or NUL; never a fetch command or embedded credential. |
| `commit` | Full 40-character lowercase hexadecimal reviewed source commit. |
| `manifest_sha256` | 64 lowercase hexadecimal characters, hashing the manifest bytes. |
| `inventory_sha256` | 64 lowercase hexadecimal characters, hashing the inventory records. |

Keep the operator lock and provider assertions outside the package, under
independent operator control. Do not accept a package-owned pin as trusted.
The supervisor stores content by inventory digest and mounts it read-only at
`/skills/<inventory_sha256>`; agents follow the loaded skill's relative links. Store/mount/loading enforcement is workharbor-side, not a
capability delivered by this package or its maintenance CLI.

## Runtime gate, installation and rollback

**Blocked:** production `claude-code` has no approved measured native
version/model/effort tuple. The current adapter has optional model selection,
but no validated effort/version binding. Runtime stage 2 of
[workharbor #283](https://github.com/wstein/workharbor/issues/283) owns that
measurement, supported binding validation/application and live loading.
Declared target model mappings and test-only bindings are not production
compatibility evidence. No loadable default, native compatibility or installed
runtime pin is claimed here. `runtime-check` and `lock` fail explicitly because
the manifest is missing, even when source checks and export pass.

After the supported tuple and required project inputs are independently
validated, a reviewed package change can add the manifest and regenerate the
content inventory. Only **after all package changes are committed**, obtain
the actual full commit from isolated Git and generate a candidate installation
lock. The CLI does not run Git or verify the supplied commit against history:
the operator must use an unchanged reviewed checkout/export from that commit,
not guess a self-referential future commit hash.

```sh
env -u SSH_AUTH_SOCK -u SSH_AGENT_PID \
  GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_GLOBAL=/dev/null \
  GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c core.fsmonitor=false rev-parse HEAD
python3 /absolute/source/crewbook/tools/crewbook-package.py lock --root /absolute/source/crewbook --source https://github.com/wstein/crewbook --commit ACTUAL_FULL_COMMIT --provider /external/reviewed-provider.json > /external/candidate-pin.json
python3 /absolute/source/crewbook/tools/crewbook-package.py runtime-check --root /absolute/staged/crewbook-text --policy /absolute/source/crewbook/tools/export-policy.json --inventory /absolute/source/crewbook/tools/package.sha256 --pin /external/reviewed-pin.json --provider /external/reviewed-provider.json
```

These future commands require an admissible manifest and trusted external
inputs; they cannot install today's content-only artifact. Provider JSON has
`bindings` (exact four-string objects) and `project_inputs` (confirmed input
identifiers). It asserts independently established support, not measurements
generated by the package. Review a candidate pin before promoting it to the
operator configuration.

Prepare and revalidate each new immutable export before changing registrations
or selecting a new runtime pin. Never follow a mutable branch silently. Keep
existing sessions on their recorded revision; retain that export and pin for
resume or rollback. Rollback selects the earlier reviewed pin for new sessions;
it does not rewrite running sessions. To uninstall, remove the registration/root
selection, wait for its sessions to finish, then remove only that dedicated
package copy. Leave project policy, repositories and host tools intact.

## Source maintenance and CI


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
in the same commit. [tools/README.md](../tools/README.md) describes command flags,
filesystem safeguards and tests; [docs/distribution.md](distribution.md)
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
