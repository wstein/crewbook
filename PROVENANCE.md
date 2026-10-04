# Extraction provenance

crewbook originated in [wstein/workharbor](https://github.com/wstein/workharbor)
at source commit `c6bbb7bcd903ea3027285baa9237f4ad179a9bb7`. The raw import in
[wstein/crewbook](https://github.com/wstein/crewbook/tree/1c784080bc0dee2060066aaf2dbc8f3894dc430d)
is `1c784080bc0dee2060066aaf2dbc8f3894dc430d`: 31 files at the tip and 69
retained commits. These are original extraction revisions, not a current
distribution pin or a claim of runtime compatibility.

## Original selection and history

[original-import.json](docs/provenance/original-import.json) records the exact
31 selected tip paths, their original Git blob SHA-1 IDs and SHA-256 byte
digests, the verification/scan summaries, and the separate removal boundary.
It is immutable historical evidence; updating the current package must not
regenerate it from current prompts. The selection consists of 8 role prompts,
10 Claude profiles, 11 commands, LICENSE and the complete mixed manual.

[extraction-paths.txt](docs/provenance/extraction-paths.txt) is the exact
32-path filtering allowlist, including the historical-only `.agents/worker.md`
that preceded `.agents/code.md`. No path rename or section rewrite was applied
in the raw extraction. The recorded `git filter-repo --version` identifier is
`a40bce548d2c`. In a fresh isolated clone of the source at the full source
revision, the extraction command was:

```sh
env -u SSH_AUTH_SOCK -u SSH_AGENT_PID \
  GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_GLOBAL=/dev/null \
  GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c core.fsmonitor=false \
  filter-repo --paths-from-file extraction-paths.txt
```

The argument denotes the supplied allowlist, not a private local path.
Do not run this command against workharbor itself or synchronize upstream
automatically. Filtering was performed on a disposable copy, without changing
the source repository or its history.

[commit-map.txt](docs/provenance/commit-map.txt) preserves all 69 nonzero
old-to-new commit mappings plus the source tip's all-zero mapping. The original
filter map also contained 1,119 other discarded source commits mapping to the
all-zero ID; those unrelated rows are intentionally omitted. Filtering removed
unrelated tree contents/history and therefore rewrote commit IDs and parent
relationships. It retained authorship,
commit attribution and selected blob contents. The source tip itself was
pruned because it added no selected content. The retained source commit
`52223a0f935f7364f54a82d69af894a579f2424f` maps to the raw import tip, whose
selected files match the later source tip. An extracted ID must not be used
as a workharbor source revision.

The reviewed extraction evidence reports exact source/import tip blob matches,
allowlisted trees for all 69 retained commits, passing `git fsck`, and a
verified standalone bundle cloned into a second isolated repository with the
same tip/tree. Gitleaks v8.30.1 history, tree and commit-message scans reported
exit 0 and no leaks with nonzero scanned bytes; the history scanner reported
68 scanned commits while Git retained 69. These are recorded extraction checks,
not newly run scans of subsequent package changes. The reviewed bundle digest
was `689df4a1aa4aed86532548a5549ec6fba1507c40f7b55301cab1074f83c5544f`.
Environment dumps, private staging paths, raw diagnostic logs and credentials
are deliberately not distributed as provenance.

## Licence, omissions and removal boundary

[LICENSE](LICENSE) is unchanged EUPL-1.2, with its existing notices. Original
authorship remains in the retained Git history; imported text is not represented
as newly authored. Subsequent package documentation uses the same licence.

Root AGENTS.md, `.claude/settings.json`, supervisor/product code, design and
threat-model policy, tools/scripts, board/landing/build infrastructure, hooks
and credentials were not selected. Runtime tools stay workharbor-side.

The historical removal candidates in original-import.json are exactly the 29
current role/profile/command source paths. They are review candidates, never
cleanup authorization. LICENSE stays in both repositories. The mixed
`docs/content/docs/manual/sessions-and-agents.md` requires section edits:
reusable roles, delegation, review, handover and context moved into crewbook;
product usage/security, project board/worktree/build/landing instructions stay
workharbor-side. The historical-only worker path is not a current removal
candidate. No source cleanup was performed by this package work.

## Transformations after raw import

These ordinary crewbook commits are distinct from the unmodified raw import:

| Commit | Transformation |
| --- | --- |
| `7e4f1e1f405cc97c7f7483d2067e23036397abb1` (#1) | Added README, SKILL and crewbook.json; routed package resources through trusted CREWBOOK_ROOT; relocated the manual. |
| `feac649c3571bd659f83b719743fc0de6878260f` (#2) | Added project-policy composition, precedence and missing-input prerequisites. |
| `4a34cb0a0216327fb8c28e988e25e3dfd5e08ec2` (#3) | Renamed active roles/profiles/commands to cb-*; made team/configuration guidance portable; separated crewbook/workharbor example profiles; replaced Hugo with GFM. |
| `6991fae2e3e35e00f5b6fd9283004c476a487c8d` (#4) | Separated coordinator starts from direct leaf execution and recorded single lifecycle ownership. |
| `a632d67cbefc888a2d9d6e2464bc4dbcb313b3da` (#6) | Recorded original extraction paths, blobs/digests, retained commit mappings and removal boundary. |
| `403b924dc99f36695c7f99f9127850c7046cd0be` and `f6aadff623cf3e9c567b417951592ed970d1d849` (#8) | Added standard-library Go inventory/export primitives and maintenance CLI; declared the current distribution set and its generated inventory. Maintenance code remains outside the text artifact. |

The first five post-import commits were rebased to use Werner's verified Git
author/committer identity. Their file contents and messages were preserved;
the table names the current local-history IDs. This maintenance rebase is
separate from the original filter-repo rewrite: the raw import revision,
selected blobs and extraction commit map were not changed.

#6 completes the provenance narrative and, in a separate change, distribution
verification and the coordinated consumer schema documentation.
Later edits are recorded in crewbook Git history and their issue references;
the original selection/map remain historical evidence. The distribution
inventory records current bytes independently, including changed and added
resources. It is neither an upstream sync list nor a workharbor deletion list.
