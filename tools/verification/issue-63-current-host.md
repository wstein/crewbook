# Issue 63: branch naming evidence on the current host

> **Historical evidence, not a current claim.** This file documents the host state and source revision of 2026-10-11 (source `897483f26b901521875d1d469c682ddafc8eb6bb`; the initial audit ran at `e797c856cbcb9aee6d96f37e3932bb291c3fe2b9`). That revision is behind current `main`, and the quoted commit hashes are not ancestors of it; later changes may have altered the sources, procedures and host this file describes. Re-measure before relying on it. The evidence below is preserved unchanged.

Measured on Linux with Python 3.13.5 on 2026-10-11, against source
`897483f26b901521875d1d469c682ddafc8eb6bb`. This source-only record closes the
earlier evidence gap without changing branch creation behavior or package policy.
The maintainer's issue scope decision of 2026-10-11 reconciles the specification
to the existing convention; the earlier six-category/two-word minimum no longer
applies. Independent exact-revision review remains a separate gate.

## Acceptance assessment

| Criterion | Evidence and result |
| --- | --- |
| Normative convention | `docs/team.md`, Branch naming, defines the single issue-first form, eight categories (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `spike`), decimal issue number without leading zeros or `#`, lowercase hyphen-separated alphanumeric slug bounded to 30 normalized characters, preferred 2–5 words with established one-word summaries allowed, and issue-less fallback. `docs/project-config.md`, Generic configuration, links this canonical definition. Source inspection matches the reconciled issue specification. |
| Coordinator and author alignment | `.agents/crewbook-desk.md` directs author assignments to the canonical convention and passes the branch to the author; `.agents/crewbook-dispatch.md` requires a fresh issue-first branch for each new item; `.agents/crewbook-code.md` uses the assigned branch and canonical convention. The author checklist in `docs/team.md` also requires the supplied current base and a fresh branch. These are instruction references, not measured client obedience. |
| Existing maintenance adapters | `tools/board.py` extracts the leading issue number from issue-first refs. `tools/dispatch_snapshot.py` renders safe branch tokens without interpreting slug/category structure. `tools/review_lines.py` parses review kind, exact SHA, role and model, independently of branch naming. The source-only `tools/git-hooks/reference-transaction` delegates to `tools/source_linear_history.py`, whose transaction guard checks only `refs/heads/main`; topic refs retain their names. Focused checks and the reproduction below pass. |
| Existing branches/worktrees | The canonical definition explicitly preserves existing branches and in-flight worktrees without retroactive renames/deletions. Existing snapshot fixtures use legacy `feat/a`; the reproduction renders new and legacy refs together, verifies unchanged fixture repository state, and checks canonical/legacy topic refs through the installed source-only hook. |

## Measured checks

The initial audit at `e797c856cbcb9aee6d96f37e3932bb291c3fe2b9` passed these
existing source checks, each with exit status 0:

```text
python3 -B -m unittest discover -s tools -p 'test_board.py' -v
Ran 23 tests; OK
python3 -B -m unittest discover -s tools -p 'test_dispatch_snapshot.py' -v
Ran 28 tests; OK
python3 -B -m unittest discover -s tools -p 'test_source_linear_history.py' -v
Ran 17 tests; OK
```

`git diff e797c856..897483f --` for the three implementation files, hook and
three test files above returned no differences. Those 68 results remain
evidence for unchanged executable bytes; the suite was not duplicated merely
because prose changed. The initial extra measurement had an import error for a
nonexistent helper `before`; correcting it to the actual helper `state` passed.
No failed execution is counted as successful evidence.

The following bounded reproduction uses existing isolated Git fixtures, writes
only temporary repositories, and runs from the source root with
`python3 -B`. It checks all eight categories on the current source, legacy
rendering, positive issue extraction and the invalid suffix order. The board
extractor is an operational signal parser, not a validator for the full naming
specification; category, slug normalization and length rules remain guidance.

```python
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("tools").resolve()))
from test_dispatch_snapshot import SnapshotTest, git, state
from test_source_linear_history import MainGuardTests
import board

names = [category + "/63-branch-naming" for category in
         ("feat", "fix", "docs", "refactor", "test", "chore", "ci", "spike")]
legacy = "docs/old-branch"
snapshot = SnapshotTest("test_golden_and_deterministic")
snapshot.setUp()
try:
    for name in names + [legacy]:
        git(snapshot.root, "branch", name, snapshot.sha_a)
    prior = state(snapshot.root)
    output = snapshot.render()
    for name in names + [legacy, "feat/a"]:
        assert name + " ahead=1 " + snapshot.sha_a in output, name
    assert state(snapshot.root) == prior
    for name in names:
        assert board.BRANCH.match(name).group(1) == "63", name
    assert board.BRANCH.match("docs/branch-naming-63") is None
    print("PASS eight-category snapshot rendering, legacy preservation and issue-first extraction")
finally:
    snapshot.doCleanups()

guard = MainGuardTests("test_allows_linear_and_other_refs")
guard.setUp()
try:
    for name in names + [legacy]:
        guard.git("update-ref", "refs/heads/" + name, guard.base)
        assert guard.git("rev-parse", name).stdout.strip() == guard.base
    print("PASS installed source-only hook accepts all eight categories and legacy topic refs")
finally:
    guard.doCleanups()
```

Current-source reproduction stdout (exit 0):

```text
PASS eight-category snapshot rendering, legacy preservation and issue-first extraction
PASS installed source-only hook accepts all eight categories and legacy topic refs
```

Current-source maintenance validation also passed with exit 0:

```text
python3 -B tools/crewbook-package.py check --root "$(pwd -P)"
source layout and inventory valid; runtime compatibility not established
git diff --check
```

The source-only `tools/` exclusion keeps this record outside the distributed
inventory. No inventory update was needed. The available Gitleaks binary reports
the required version 8.30.1; the repository's `tools/scan-secrets.sh` passed for
nonempty full history, working tree and commit messages with redaction.

## Limits

There is no Makefile in this repository and therefore no local `make land`
target to execute. `docs/git-history.md`, Landing pointer branch, identifies
WorkHarbor `make land` as legacy flow; no WorkHarbor landing implementation or
runtime was measured. The `.claude/commands/crewbook-land.md` resource is a prose
wrapper, not an executable landing script.

The distributed skill supplies no hooks or permission enforcement. The
source-only history hook was tested in disposable repositories; no live host
hook installation is claimed. Claude Code, Codex and Antigravity native branch
creation, macOS behavior and WorkHarbor landing remain unverified. This record
establishes current source guidance and Linux maintenance compatibility only.
No artifact, image, documentation build, release, push or integration was run.
