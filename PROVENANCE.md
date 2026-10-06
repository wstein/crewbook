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
| `7e4f1e1f405cc97c7f7483d2067e23036397abb1` (#1) | Added README, SKILL and crewbook.json; routed package resources through an explicit package-root binding (subsequently replaced by relative links); relocated the manual. |
| `feac649c3571bd659f83b719743fc0de6878260f` (#2) | Added project-policy composition, precedence and missing-input prerequisites. |
| `4a34cb0a0216327fb8c28e988e25e3dfd5e08ec2` (#3) | Renamed active roles/profiles/commands to cb-*; made team/configuration guidance portable; separated crewbook/workharbor example profiles; replaced Hugo with GFM. Superseded: `cb-*` names were later replaced by `crewbook-*` (#37, `404ac06`); row kept as history. |
| `6991fae2e3e35e00f5b6fd9283004c476a487c8d` (#4) | Separated coordinator starts from direct leaf execution and recorded single lifecycle ownership. |
| `a632d67cbefc888a2d9d6e2464bc4dbcb313b3da` (#6) | Recorded original extraction paths, blobs/digests, retained commit mappings and removal boundary. |
| `403b924dc99f36695c7f99f9127850c7046cd0be` and `f6aadff623cf3e9c567b417951592ed970d1d849` (#8) | Added standard-library Go inventory/export primitives and maintenance CLI; declared the current distribution set and its generated inventory. Maintenance code remains outside the text artifact. |
| `c74283d40f940603954f7a7a3ee768921d3613cc` | Added Codex discovery metadata to the declared/exported text package; metadata alone does not establish native loading. It declares `agents/openai.yaml` in the package inventory; the file itself is created by `b68f57e8c3f4ab10a4203b363f066e81628dd336`. |
| `5d32e178ac4112fa17fc965f038e7fa8678c7e50` | Made the native workspace/task and applicable instructions sufficient for ordinary use without a launcher; separated skill resources from the target context. |
| `4dea50b35a3b28d1a194591df23e3cb1bf08abb5` | Replaced the crewbook-specific profile with cb-generic defaults and selected cb-workharbor by managed-container execution environment for any target repository; removed fixed project destinations/checks. Superseded: `cb-*` names were later replaced by `crewbook-*` (#37, `404ac06`); row kept as history. |
| `2aaacf00b694d6489492f9ea30a89434ef020115` | Applied generic defaults across roles, profiles and commands: session assignments and exclusive checkouts need no mandatory board or persistent lane setup, while configured managed claim gates and authorization remain in force. |
| `87dd1cde1aa1f76dc522e963d0e67308fe84d191` | Replaced Go maintenance source with standard-library Python 3.9+ CLI, filesystem/layout/inventory/export and runtime-contract checks; ported failure/scanner fixtures and Python CI/CodeQL. Removed the Markdown prompt-content validator and Goldmark dependency; maintenance code remains outside the text export. |
| `0c649fb68e7bc35bdae370c9d0eb6926210aac48` | Replaced package-root bindings and launcher propagation with relative links resolved from each loaded resource; retained target repository paths in independent task context. |
| `b9a01b6098b009c27316ad421b69fed165939b5b` | Added automatic pinned persistent dispatcher startup/reuse through desk, with retained handles, coordinator-owned claims/worker starts and explicit client lifecycle limits; added the Claude dispatcher profile. |
| `b68f57e8c3f4ab10a4203b363f066e81628dd336` | Made explicit Crewbook invocation enter desk and keep that role across turns; specified the dispatch model/effort while preserving direct leaf assignments and implicit local-work behavior. |
| `8efd2b26ac23decc8d58511423154b06f477be6f` | Added the dedicated Codex cb-desk skill and invocation metadata with a canonical desk-role link; distinguished optional user installation from Claude slash commands. Superseded: `cb-*` names were later replaced by `crewbook-*` (#37, `404ac06`); row kept as history. |
| `cb65560d1e8fdf5d75a86372b75121ae5dd6db29` | Renamed the public skill entrypoint to crewbook and updated invocation/discovery documentation and metadata; kept the canonical cb-desk workflow and optional alias. Superseded: `cb-*` names were later replaced by `crewbook-*` (#37, `404ac06`); row kept as history. |
| `bad8f3cec1eb15d791890290c9de88f4f82c7b6e`, `6a3725f5eeaa9bb39c94009a83bff3b29f666610`, `d9ec79baf1eeeb3ef039d3e8c44ba1b162c21b84` and `033b85ac835065b3a627cb450aad1c60ea09d97c` (Helper hardening, review-note identity, link preamble) | Helper untrusted-data and check-reporting rules; project-policy-configurable review-note identity (default `crewbook/review`); link-assumption sentence in all Claude profiles/commands; Claude install procedure marked UNVERIFIED (native loading and subagent link resolution unmeasured); the coordinator assignment exempted from the untrusted-data rule (033b85a). |
| `56de44fd499ade4ebb9311ae92f67e15f724c73d` (Delegated authoring worktrees) | Delegated authoring agents work in dedicated worktrees that the coordinator assigns from a clean idle slot (creating one only when none is eligible and authorized) and records; implicit local sessions keep the current checkout. The rule is stated once in the team manual and linked from role, profile and configuration text. |
| `25681a8bc6f10544737a4a15c686074e48852313`, `36a432fa26f2020a1481c3f7a78a5ccffcd7d84a`, `4c9bb8551d2dea6164e2d6594a5de1e0ea92a309` and `92142e77cd333971edf3f1745b256b56c1476703` (Desk-merged coordinator mode) | Desk is the default designated coordinator (merged mode) following the single canonical coordinator procedure; a persistent dispatcher applies only in split mode selected by a configured board/claim gate or user request. Added a durable keyed registry/handoff file, bounded merged-mode supervision, mode-aware identity and capacity text, and split-only desk safety-net model tests. Native behavior remains unverified. |

The first five post-import commits were rebased to use Werner's verified Git
author/committer identity. Their file contents and messages were preserved;
the table names the current local-history IDs. This maintenance rebase is
separate from the original filter-repo rewrite: the raw import revision,
selected blobs and extraction commit map were not changed. The 10
commits that a maintenance rebase re-identified ("remapped") were also rewritten;
this is inferred from committer dates (2026-10-05 07:21-07:22, later than the
author dates), not independently proven.

The table records transformations observed in local Git history, not a new
extraction or proof of publication, independent review or live compatibility.
Later edits are recorded in crewbook Git history and their issue references;
the original selection/map remain historical evidence. The distribution
inventory records current bytes independently, including changed and added
resources. It is neither an upstream sync list nor a workharbor deletion list.

## Current verification and remaining runtime boundary

The original extraction revisions, selected blobs, filtering allowlist, commit
map, licence and removal boundary remain unchanged by these transformations.
The current [distribution contract](docs/distribution.md) separately describes
Python maintenance checks and the deterministic inventory/export format.
Updating that inventory accepts reviewed current bytes; it does not synchronize
upstream, repeat historical scans or prove native client loading.

No production `workharbor.json`, trusted installation pin or approved measured
native adapter version/model/effort tuple is supplied here. Production provider
validation and managed live loading remain external work in
[workharbor #283](https://github.com/wstein/workharbor/issues/283); the production
criterion in [crewbook #6](https://github.com/wstein/crewbook/issues/6) remains
unmet. Do not infer a loadable default from metadata, target model mappings,
synthetic provider fixtures or passing offline checks. Generic native-session
use does not require this production manifest/provider. Missing runtime inputs
stop the dependent runtime operation explicitly, without invented bindings or
substitute enforcement.
