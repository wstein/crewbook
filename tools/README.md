# Package maintenance

The entrypoint is `python3 tools/crewbook-package.py <command> --root <absolute-root>`.
It supports `check`, `inventory`, `update`, `export`, `runtime-check` and `lock`.
Use Python 3.9+ on macOS or Linux; all imports are standard-library modules.
No dependency installation, Go compiler, prompt parser or runtime is required.
`--help` lists flags. Errors exit 1; inventory and candidate pins use stdout,
and human diagnostics use stderr. The CLI never runs Git, prompts, clients,
board tools or hooks.

## Validation boundary

`packagefmt.py` validates strict UTF-8 JSON with duplicate/unknown field
rejection, declared layout/resources, filesystem boundaries, canonical hash
records and the existing runtime manifest/pin/provider contract. It does not
parse Markdown, enforce prompt wording, check heading anchors or hardcode
role/model mappings. Repository authors own those text choices.

Limits remain 256 KiB manifest, 1,024 inventoried files, 1 MiB per file,
16 MiB total, 16,384 filesystem entries, 240-byte ASCII paths and bounded
lowercase identifiers. Files must be singly linked regular text, owned by the
current user, without executable, group/world-write or special permission bits.
Directories must be owned by the user without group/world-write or special
bits. Reads are bounded and nonblocking, with no-follow opens, fd-relative
traversal and identity/metadata checks before and after reading. Parents remain
pinned by open descriptors during scan and writes. This is a maintenance
integrity check, not a sandbox for concurrently hostile processes.

`check` compares the saved inventory and checks layout. `update` checks layout
and accepts reviewed bytes. `export` checks saved digests/layout and writes only
snapshot bytes into a new directory (0400 files, 0700 directories). Existing
and concurrently created destinations are refused. Source policies enumerate
maintenance exclusions; export policy has the same distributed set with none.
Use external policy/inventory paths to revalidate a relocated export exactly.

An inventory output inside source must already be excluded under `tools/`.
Existing outputs must be canonical singly linked inventory files. Distributed
resources, the runtime manifest and the selected policy cannot be overwritten,
including case, symlink-parent and inode aliases. New output parents must exist
and be canonical. Writes use a private temporary file and atomic replacement.

## Checks

```sh
python3 -B -m unittest discover -s tools -p 'test_*.py'
python3 -B tools/crewbook-package.py check --root "$(pwd -P)"
```

On the development Mac these commands are also run with `/usr/bin/python3`
(3.9.6). Tests cover deterministic hashes, exact exports and relocation,
unsafe paths/files, metadata changes, output collisions, size/count limits,
JSON/layout errors, runtime pins/bindings and subprocess exit behavior.
Synthetic scanner fixtures are optional and require the separately installed
pinned binary; see [SECURITY.md](SECURITY.md). They run isolated Git without
host credential helpers. Tests never execute instruction fixtures.

The unittest command runs every `tools/test_*.py` file: `test_package.py`
(package, export and hash checks), `test_evaluation.py` and
`test_evaluation_fixtures.py` (evaluation harness and fixtures),
`test_source_linear_history.py` (source main guard), `test_confirm.py`
(confirmation record v1 codec against shared fixtures), `test_preflight.py`,
`test_scanner.py`, `test_dispatch_recovery.py`, `test_dispatch_snapshot.py`
and `test_usage_report.py` (synthetic-fixture and redaction tests for the
distributed `scripts/usage_report.py`).

The exported skill contains no maintenance code or dependencies. Source/layout
checks and provider assertions do not establish native loading, permission
enforcement or a loadable production default.

Credential-free [preflight scenarios](../docs/tool-preflight.md) run with the
same unittest command. They test observable offline outcomes, not live agent
compliance or permission enforcement.

Credential-free dispatch recovery replays in `test_dispatch_recovery.py` preserve
structured events and assert exact review continuations, model substitutions,
confirmed host capacity separately from retained completed handles, same-item
author/review corrections, unrelated review freshness, unchanged-capacity retry
suppression, uncertain starts, stale ownership, mixed tool results and
once-per-transition empty requests. Explicit required/authorized landing replays
retain the obligation after clean exact review without a seeded integration queue,
route the same author once, await validated owner/revision/ref/success evidence,
reject stale or uncertain results, and preserve content-review-only completion.
Coordinator-mode replays cover mode selection (a configured or unavailable
gate selects split, none selects merged, user override both ways), merged
lifecycle counts with zero dispatcher starts, keyed registry round trips with
stale-handle ownership resolution, and a merged desk without a wait tool handing
off; the desk dispatcher-resume safety net is split-only in the model. Split
sole-writer replays check that desk writes the header and its own start record
(and may update that record's outcome) while the dispatcher alone writes
everything else, and that a header `session` from another session, or no `session`
line, makes a second desk read-only even after human confirmation of
concurrency, and that only a human-confirmed takeover lets a successor rewrite
the header.
These synthetic cases do not establish native landing or parent supervision.
They are a maintenance reference model,
not runtime enforcement or tests that an agent follows prompt text. Timing and
native-client recovery remain unverified.

## Dispatch snapshot

`dispatch_snapshot.py` (source-only maintenance, not exported, not in the export
policy) prints one compact deterministic block: own board cards per column,
local branches ahead of main with full SHA, whether `refs/notes/review` (the
only notes ref read) has a note per SHA, worktrees (path, branch or `bare`,
short HEAD and explicit `owner=unknown`), latest CI run per workflow and a registry summary (header
mode/coordinator/target, phase counts and one `name owner=... phase=...` line
per assignment, owner only from the registry `owner` key). Each section is
capped at 12 lines; any excess ends with a `... N more` line, so the maximum is
the six section headers plus 6 x 12 lines plus the optional stamp (79 lines).
Truncation counts include every omitted row; unavailable statuses remain visible.
The registry grammar supplies no exact worktree path/branch association, so
worktree ownership cannot be inferred from its assignment names or evidence.
The registry is parsed with the strict grammar of
[project-config.md](../docs/project-config.md#coordinator-mode-and-registry);
a damaged or foreign file (including a header without `session`) prints
`unavailable: damaged or foreign` and nothing else from it. The reader has no
session marker, so a valid registry from any session is summarised. It is
read-only (Git plumbing only, no writes, no network, no GraphQL) and prints no
file contents, note bodies or prompt text; unsafe tokens print as `?`. Each
section degrades alone to `unavailable: <reason>`.

```sh
python3 -B tools/dispatch_snapshot.py --root "$(pwd -P)" [--main main] \
  [--board board.json|-] [--ci ci.json|-] [--registry PATH] [--stamp LABEL]
```

This repository has no `scripts/board-snapshot.sh`; the caller supplies board
and CI data as JSON (shapes in the script docstring; `-` reads stdin for at
most one input; a card counts only with `"own": true`), otherwise those sections read `unavailable`. The only
time line is the optional caller-labelled `--stamp`. Shipping it is the human's
decision.

## Optional source main guard

Crew Book's own source `AGENTS.md` selects linear, fast-forward-only integration.
The optional `source_linear_history.py` and `git-hooks/reference-transaction`
enforce that source maintenance choice at Git's prepared reference transaction:
main updates must descend from its current direct commit and introduce no merge
commits. Existing historical merges remain unchanged; main creation, deletion,
symbolic/noncommit main and failed lookups are refused. Replacement objects
cannot hide physical merges; shallow history and legacy grafts are refused.
Unspecified old values
are resolved from the locked current ref. Other refs are unconstrained, but a
rejected main update aborts the whole prepared transaction.

This is **source-only**, excluded with all `tools/` from exported artifacts.
It supplies no policy, required hook, launcher or enforcement to consuming
repositories. Each target selects its history policy in its own `AGENTS.md`.

After independent exact-commit review and explicit operator authorization,
run the reviewed source installer, naming the full reviewed commit SHA:

```sh
python3 -I -B tools/source_linear_history.py install --root /absolute/source/repository \
  --reviewed-sha FULL_REVIEWED_COMMIT_SHA --confirm-effective-hook-routing
python3 -I -B tools/source_linear_history.py verify --root /absolute/source/repository \
  --reviewed-sha FULL_REVIEWED_COMMIT_SHA
```

The confirmation asserts that the operator checked effective hook routing;
it does not grant review or integration authorization. Installer Git operations
use null system/global configuration, no credential helper, prompts or SSH agent.
They never inspect human global/system configuration or credential stores.
Consequently system/global/command hook overrides remain unknown to the tool;
the operator must confirm they do not supersede the repository-local routing.

The operator must invoke reviewed bytes from a trusted source; Python isolated
mode excludes sibling/PYTHONPATH/user-site imports. Self-verification detects
accidental mismatch, not a malicious already-running installer.

Installation requires matching installer bytes from the reviewed commit, pins
both installed files to that commit, and reports SHA-256 digests. It places
a private version directory in the common Git directory, surviving linked
worktrees and older checkouts. Hook validation binds every Git read explicitly
to that installed common directory, ignoring invocation cwd and inherited
repository selection. It validates the installed layout and pinned bytes; running
the uninstalled source script as a hook is refused. Existing local hooksPath, worktree-specific
configuration and non-sample default hooks cause refusal; no existing hook or
unrelated configuration is replaced. Exact existing installations can be
verified and reused. Installed files are read-only; path links, unsafe directory
permissions, altered bytes and unexpected files are refused. This checks ordinary
maintenance integrity, not concurrent hostile filesystem writers.

Git and Python must be available for hook invocation; absence fails the update
when Git invokes the installed hook. Native isolated tests measured this boundary
with Apple Git 2.54.0 and stock Python 3.9.6; other Git versions/platforms remain
unverified. `verify` checks local routing and bytes, not actual hook execution.
Configuration overrides, deleting hooks and direct filesystem ref writes can
bypass local hooks; this is not a tamperproof boundary or forge policy. Installing
or verifying a guard never authorizes main integration, push or publication.
