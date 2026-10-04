# Maintenance boundary for #5 and #6

The stable entrypoint is `go run ./cmd/crewbook-package <command> --root <absolute-root>`.
Commands are `check`, `inventory`, `update`, `export`, `runtime-check` and `lock`.
All errors exit nonzero. Inventory and candidate lock data use stdout; human
diagnostics use stderr. Optional flags are documented by each command's `-h`.
No command runs prompts, Git, a native client, board tools or hooks.

`internal/packagefmt` is the standard-library package API:

- `LoadPolicy` and `Scan` validate the explicit source/distribution boundary.
- `Snapshot` retains validated bytes; export never reopens source files.
- `Encode([]File)` produces the canonical v1 hash lines.
- `Check` compares those lines and revalidates the snapshot's bytes.
- `CheckLayout` checks crewbook v1 metadata and its complete required resources.
- `CheckContent` checks scalar frontmatter, role/profile identifiers, Claude
  models and the separately documented Codex mapping, prompt links, helper
  tools, package-root references, GFM links/heading anchors and Hugo leftovers.
- `RuntimeCheck` validates the unchanged `Manifest`, six-field `Pin`, exact
  supported `Binding` tuples and independently confirmed project inputs.
- `Export` writes only validated text resources into a new directory.
- `ReadRegular` provides bounded, nonblocking, no-follow reads with opened
  identity checks. `Decode` refuses duplicate/unknown JSON fields.

Limits match the committed workharbor v1 consumer contract: 256 KiB manifest,
1,024 files, 1 MiB per file, 16 MiB total, 16,384 filesystem entries, 240-byte
ASCII paths, 1–64-character lowercase identifiers. Supported maintenance hosts
are Linux and macOS; filesystem checks use their Unix metadata.

`check` combines content, layout and deterministic inventory validation, with
exit 1 on failure. `update` intentionally checks layout only so invalid-content
fixtures can get a correct inventory and prove that content validation fails.
`export` preserves the existing byte/layout contract; run `check` before export.
Frontmatter supports only unique, single-line scalar fields: skill name and
description; profile name, description, model and optional tools; command
description and optional argument-hint. Double-quoted values use JSON string
syntax; other YAML constructs fail explicitly. Keys are unique even when a
previous decoded value is empty.
Goldmark v1.7.13 is the sole maintenance dependency: a real GFM parser handles
tables, reference links, images and fenced/inline code without a duplicate
ad-hoc Markdown parser. It is excluded from the distributed artifact.

All relative Markdown links and `${CREWBOOK_ROOT}/...` references are bundled
resources. Missing ones fail even if a host dependency has the same path.
An intentional external file link uses `host:<path>` and must appear in one
`crewbook.json` host dependency's explicit `paths` list; declarations require
name, scope and status and cannot overlap bundled resources. Descriptive
host capabilities remain external inputs, not locally executable resources.
Static source checks establish neither runtime permissions nor native loading.
Focused tests mutate actual source bytes and exercise failure diagnostics;
CLI subprocess fixtures assert exit 1 with a matching, freshly generated
inventory. Instruction samples are read as data and are never executed.

Local checks (Go 1.27, Linux/macOS):

```sh
go test ./...
go test -race ./...
go vet ./...
test -z "$(gofmt -l cmd internal)"
go run ./cmd/crewbook-package check --root "$(pwd -P)"
```

#6 documents provenance and the agreed consumer contract in
[PROVENANCE.md](../PROVENANCE.md) and [docs/distribution.md](../docs/distribution.md),
using this Go implementation rather than a second validator. Source checks use
`tools/package-policy.json`; staged exports use `tools/export-policy.json`,
whose distributed set is identical but whose maintenance exclusions are empty.
Supply the latter and `tools/package.sha256` from outside the staged export
for exact missing/extra/tampered checks. Keep both policies, resource declarations,
changed content and generated inventory in the same commit. Use only `update`'s
default inventory destination or a custom path under source `tools/` or outside
the source root. Output parents must already exist and be canonical without
symlink aliases. A new destination is allowed; an existing destination must be
a regular, unlinked canonical inventory file. Distributed files, the runtime
manifest and the selected policy are protected even through case/identity
aliases. Other existing metadata and tool files cannot be overwritten.
The output path never changes the declared distribution exclusions.
The inventory itself remains
maintenance metadata outside the exported package to avoid self-hashing.
The original extraction evidence is unchanged; the abandoned Python maintenance
draft was archived outside the source checkout and never validated or executed.

Provider JSON and operator pins are external trusted inputs, not distributed
self-attestations. The current source has no production `workharbor.json`.
The synthetic binding in tests is fixture data only. Native-client measurement,
live loading and independent package review remain required. Passing source
or export checks must not be reported as a loadable production default.
