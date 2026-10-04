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
- `RuntimeCheck` validates the unchanged `Manifest`, six-field `Pin`, exact
  supported `Binding` tuples and independently confirmed project inputs.
- `Export` writes only validated text resources into a new directory.
- `ReadRegular` provides bounded, nonblocking, no-follow reads with opened
  identity checks. `Decode` refuses duplicate/unknown JSON fields.

Limits match the committed workharbor v1 consumer contract: 256 KiB manifest,
1,024 files, 1 MiB per file, 16 MiB total, 16,384 filesystem entries, 240-byte
ASCII paths, 1–64-character lowercase identifiers. Supported maintenance hosts
are Linux and macOS; filesystem checks use their Unix metadata.

#5 extends this Go implementation with full profile/frontmatter, references,
resource and helper-permission checks and the approved six-part CI baseline
(including Go CodeQL). CI can call `check`, `go test ./...`, `go vet ./...`
and verify `gofmt -l cmd internal` is empty; it must not run agent instructions.
No CI baseline or native-settings change is implemented in #8.

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
