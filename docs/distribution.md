# Distribution and workharbor consumer contract

## Current content artifact

The original import is recorded in [PROVENANCE.md](../PROVENANCE.md), including
its exact selected paths and separate source-removal boundary. The current
distribution is a different artifact: `tools/package-policy.json` in the
reviewed source checkout explicitly enumerates its text files. `crewbook.json`
declares the same resources and entrypoints. `tools/package.sha256` records
their current byte digests, not the original import digests.

These maintenance files and all Go source, module files, `.github/` and `.git/`
are excluded from the distribution. The export contains LICENSE, provenance,
README, SKILL, layout metadata, docs and every declared `.agents/` and `.claude/`
resource. It contains no agent executable tools, runtime plugins, permission
settings, hooks or maintenance inventory. A source clone is not the installable
text artifact. No automatic upstream synchronization or source deletion follows
from either inventory.

The maintenance CLI validates source content and emits a deterministic export
from its validated snapshot. Export files use mode `0400`; directories use
`0700`. Existing destinations are refused. Revalidation uses the separately
maintained `tools/export-policy.json`: it has the identical distributed set
and **no maintenance exclusions**, so extra `.git/`, tools or CI files in a
staged export cannot be ignored. Supply this policy and the saved inventory
from the trusted source checkout, outside the export:

```sh
go run ./cmd/crewbook-package check --root /absolute/source/crewbook
go run ./cmd/crewbook-package export --root /absolute/source/crewbook --dest /absolute/staged/crewbook-text
go run ./cmd/crewbook-package check --root /absolute/staged/crewbook-text --policy /absolute/source/crewbook/tools/export-policy.json --inventory /absolute/source/crewbook/tools/package.sha256
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
go run ./cmd/crewbook-package update --root /absolute/source/crewbook
go run ./cmd/crewbook-package check --root /absolute/source/crewbook
go run ./cmd/crewbook-package inventory --root /absolute/source/crewbook
```

`update` accepts deliberately reviewed new bytes; it is not a tamper check.
Commit the changed content, declarations and generated `tools/package.sha256`
together. Repeating update on unchanged content produces identical bytes.
The original extraction evidence is not regenerated. The content checker/CI
must perform this same coordinated update when it changes packaged resources;
adding maintenance-only CI or Go source changes no distributed bytes.

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
`/skills/<inventory_sha256>`; invocation context supplies that trusted root as
`CREWBOOK_ROOT`. Store/mount/loading enforcement is workharbor-side, not a
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
go run ./cmd/crewbook-package lock --root /absolute/source/crewbook --source https://github.com/wstein/crewbook --commit ACTUAL_FULL_COMMIT --provider /external/reviewed-provider.json > /external/candidate-pin.json
go run ./cmd/crewbook-package runtime-check --root /absolute/staged/crewbook-text --policy /absolute/source/crewbook/tools/export-policy.json --inventory /absolute/source/crewbook/tools/package.sha256 --pin /external/reviewed-pin.json --provider /external/reviewed-provider.json
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
