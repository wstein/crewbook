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

The exported skill contains no maintenance code or dependencies. Source/layout
checks and provider assertions do not establish native loading, permission
enforcement or a loadable production default.
