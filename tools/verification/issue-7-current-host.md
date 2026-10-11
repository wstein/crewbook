# Issue 7: current-host board verification

> **Historical evidence, not a current claim.** This file documents the host state and source revision of 2026-10-11 (CrewBook candidate base `897483f26b901521875d1d469c682ddafc8eb6bb`, Workharbor source `c27fc9e3bb0961086d57de97f4aeed2259485503`). That revision is behind current `main`, and the quoted commit hashes are not ancestors of it; later changes may have altered the sources, procedures and host this file describes. Re-measure before relying on it. The evidence below is preserved unchanged. The live board, saved-view and workflow observations were read-only measurements on that date and can no longer be reproduced from this repository.

Verdict: **partial**. Read-only API measurements confirm both configured project identities and core fields. A stale saved project-10 filter and missing project-6 queue views prevent claiming the legacy view requirement complete. Saved UI sorting/grouping and actual workflow triggers/actions remain unverified. Missing verification is not a successful fix.

## Setup and authorization

- Measured 2026-10-11, approximately 10:38–10:40 UTC, on native Linux aarch64 (kernel 7.0.14-orbstack; glibc 2.41), Python 3.13.5, gh 2.102.0.
- CrewBook candidate base: `897483f26b901521875d1d469c682ddafc8eb6bb`; assigned author: Codex gpt-6.1-sol, medium reasoning effort, `crewbook/verify`.
- Workharbor source: `c27fc9e3bb0961086d57de97f4aeed2259485503`; `scripts/board-snapshot.sh` SHA-256 `82af174f808ecfbd0367420472b563d3b838f9d2003d83dca4ef7018c6cba4bc`.
- Only configured-project reads were authorized: CrewBook `tools/board.py` `load`/`graphql` READ; Workharbor `scripts/board-snapshot.sh` metadata/schema/card READ. Issue data came through REST. The dispatcher remains the sole card writer.
- No board/view/settings/workflow writes, forced live failures, closure tests, builds, installation, push or publication occurred. Default execution failed before commands with `bwrap: Can't mount proc on /proc: Operation not permitted`; scoped escalation ran the authorized reads/checks.

## Live observations

| Project | Repository | Owner | Node | Status field |
| --- | --- | --- | --- | --- |
| [10](https://github.com/users/wstein/projects/10) | wstein/crewbook | wstein | `PVT_kwHNjWrOAZaiCg` | `PVTSSF_lAHNjWrOAZaiCs4ZFhhm` |
| [6](https://github.com/users/wstein/projects/6) | wstein/workharbor | wstein | `PVT_kwHNjWrOAZVCuA` | `PVTSSF_lAHNjWrOAZVCuM4ZAYRL` |

Both field reads returned exactly `Todo`, `In progress`, `Blocked`, `In review`, `Done`; neither has `Ready to push`. Both have single-select Priority `P1/P2/P3`, built-in `Assignees` of type `ASSIGNEES`, and built-in Milestone. Issue 7's literal six-status list is stale against the current five-status/human-merge workflow; reconcile the issue wording through the coordinator rather than restore an obsolete option.

CrewBook Session options are `crewbook/desk`, `crewbook/dispatch`, `crewbook/design`, `crewbook/review`, `crewbook/platform`, `crewbook/runtime`, `crewbook/docs`, `crewbook/verify`, `crewbook/spikes`, `Werner`. Workharbor retains `wh/design`, `wh/platform`, `wh/runtime`, `wh/review`, `wh/verify`, `wh/docs`, `wh/spikes`, `Werner`. This measures actual options, without asserting every configured role needs an option.

CrewBook `load()` returned 81 repository-filtered cards; #7 was OPEN/In progress, #41 OPEN/In progress, #120 OPEN/In review. Every observed Done card was CLOSED. This establishes observed placement/state, not workflow causation or a write by this author. Workharbor refreshed 481 repository-scoped items; #535 was OPEN/In progress, Session wh/platform, Priority P2. Preservation is bounded to this author making no mutation; concurrent coordinator work is not a before/after equality claim.

### Saved view metadata

All connections read completely: `hasNextPage` was false, including each view's visible-field connection. Project 10 returned these saved filters (JSON values preserved from the response):

| View | Layout | Filter |
| --- | --- | --- |
| [Roadmap](https://github.com/users/wstein/projects/10/views/1) | TABLE_LAYOUT | `"-is:closed"` |
| [Board](https://github.com/users/wstein/projects/10/views/2) | BOARD_LAYOUT | `null` |
| [Dispatch queue](https://github.com/users/wstein/projects/10/views/3) | TABLE_LAYOUT | `"repo:wstein/crewbook is:issue -is:closed status:\"Todo\""` |
| [Active work](https://github.com/users/wstein/projects/10/views/4) | TABLE_LAYOUT | `"repo:wstein/crewbook is:issue -is:closed status:\"In progress\""` |
| [Review queue](https://github.com/users/wstein/projects/10/views/5) | TABLE_LAYOUT | `"repo:wstein/crewbook is:issue -is:closed status:\"In review\""` |
| [Blocked work](https://github.com/users/wstein/projects/10/views/6) | TABLE_LAYOUT | `"repo:wstein/crewbook is:issue -is:closed status:\"Blocked\""` |
| [Release and milestones](https://github.com/users/wstein/projects/10/views/7) | TABLE_LAYOUT | `"repo:wstein/crewbook is:issue -is:closed status:\"Ready to push\""` |

The five named queue/milestone views expose fields in order: Title, Status, Priority, Assignees, Session, Milestone. Existing Roadmap and Board are also present. **Release and milestones filters only the absent Ready to push status; it includes no current status.** This is a concrete stale configuration, not proof of how GitHub renders it.

Proposed small reconciliation for design/human decision: if the intended view is open milestone work, remove only `status:"Ready to push"`, retaining `repo:wstein/crewbook is:issue -is:closed` and existing fields. Then save/reload the intended milestone grouping and Priority sort in the UI. If the intended view is reviewed release readiness, choose explicit PR readiness semantics separately. No saved-view change is authorized by this verification assignment.

Project 6 returned only Roadmap (TABLE_LAYOUT, filter `"-is:closed "`) and Board (BOARD_LAYOUT, filter null). The five scoped dispatch/active/review/blocked/milestone views are absent in this complete metadata read. The legacy issue requirement for views on both projects is therefore not fully demonstrated. Preserve project 6 and have the coordinator/design decide the intended scope; do not create views implicitly.

### Workflow metadata boundary

Both projects returned the same enabled states: Auto-add sub-issues to project, Auto-add to project, Item added to project, Item closed and Item reopened enabled; Auto-close issue, Pull request linked to issue and Pull request merged disabled. These are names/enabled flags only. Actual trigger filters, action values, ownership/revision conditions, automatic Done behavior, reopening behavior and absence of unsafe cross-updates were not exercised. No screenshot or save/reload evidence was supplied.

## Offline source audit

`python3 -B -m unittest discover -s tools -p 'test_board.py' -v` exited 0: `Ran 23 tests in 0.087s`, `OK`. This is credential-free fake-gh coverage, separate from live reads.

| Requirement | Existing executable coverage |
| --- | --- |
| Failed write and bounded retry | `test_failed_write_retried_once_then_pending`: two attempts, unchanged card, pending error |
| Uncertain applied outcome | `test_uncertain_write_applied_is_not_repeated`: read-back observes applied status, one mutation |
| Failed read-back | `test_readback_failure_reports_unknown_outcome`: pending/unknown outcome retained |
| Stale state | `test_stale_state_after_failed_write_is_not_retried`: changed status refuses retry |
| Wrong mapping and repository isolation | `test_wrong_project_id_fails_without_writing`, `test_other_repo_card_is_not_found`: no mutation |
| Read-back mismatch and idempotency | `test_read_back_mismatch_fails`, `test_idempotent` |
| Closure-only Done | Open/unverified state refused before writes; closed issue moves once and becomes idempotent |
| Unrelated cards and sync conservatism | One-card move preserves another card; sync tests preserve review/ready/Done and closed cards, unreadable registry refuses changes |

These fixtures model transport loss by raising BoardError, not an actual subprocess wall-clock timeout. Wrong-project coverage exercises an unavailable project and repository filtering; it does not prove all real project mappings or credentials safe. The helper derives option IDs from live Status and validates CLOSED before Done. Ownership/exact-review prerequisites remain coordinator workflow rules, not authorization enforced by this helper; tests do not establish native enforcement or successful protected transitions. No concrete executable defect within the assigned scope was reproduced, so no behavior change or manufactured failing test was added. Coordinate pending/drained recovery policy with #16.

## Reproduction and retained output

Approved CrewBook calls used `board.graphql(query, id=board.PROJECT_ID)` for project identity and fields/views/workflows plus `board.load()` for cards. Queries selected project metadata and paginated-connection pageInfo; all returned a single complete page. View numbers were read separately through the same helper to construct public view URLs. The field/view/workflow selections use the core READ fields in Workharbor's `connection_read`; no direct gh project command or issue GraphQL was used. Reproduce those CrewBook reads from the assigned source root with the following Python (each connection must report `hasNextPage: false`; otherwise paginate before making a completeness claim):

```python
import sys
import json
sys.path.insert(0, "tools")
import board

selections = {
    "fields": "... on ProjectV2Field{id name dataType} "
              "... on ProjectV2SingleSelectField{id name dataType options{id name}}",
    "views": "id number name layout filter configuration{visibleFields(first:100)"
             "{nodes{... on ProjectV2FieldCommon{id}} pageInfo{hasNextPage}}}",
    "workflows": "id name enabled",
}
for connection, selection in selections.items():
    query = ("query($id:ID!){node(id:$id){... on ProjectV2{id number url "
             "owner{... on User{login} ... on Organization{login}} "
             + connection + "(first:100){nodes{" + selection
             + "} pageInfo{hasNextPage endCursor}}}}}")
    print(json.dumps(board.graphql(query, id=board.PROJECT_ID), indent=2))
print(json.dumps(board.load(), indent=2))
```

Workharbor commands ran from its repository with `WHR_BOARD_SNAPSHOT` naming a private writable scratch file:

```sh
bash scripts/board-snapshot.sh metadata schema
bash scripts/board-snapshot.sh card 535 --refresh
```

Both exited 0. Card stdout, preserved without edits:

```text
#535	In progress	wh/platform	P2	Tool watchdog: warn after 10 minutes without output, abort after 30
```

Private raw JSON outputs remain in the private assignment evidence directory; the coordinator retains its locator privately. These are local measurement records, not published package artifacts. CrewBook records preserve the helper's decoded data, not a claim of signed GitHub provenance. SHA-256 records:

```text
f7091f4956cdd060af722a49c38094efffc648ee3ebf44edbaefc808cea0d11e  cb-identity.json
e21ed3d6b225e89069b63296ec82fdf2df3aab5b7ca408d5bf2702ddbb52d3f0  cb-fields.json
3afbac61b0f17a060f3bf048ab2a816a8206681fb23767f8ffc396e34a03c030  cb-views.json
8a702bf973b5b465541bb46bd6ddbf59ae9199300dc6073e057aba388e7f5af5  cb-workflows.json
ece4bc8ec64ea28a61e845a3cc0dea9fe96ebd6f6c9cf7ff698224b9e554453c  cb-load.json
d4e6fbc8b6d0b8df055bcdfd0823d431b665aacc2c8e59eaa1be9793843914a4  cb-view-numbers.json
b7910ab621dd946abf1b9a9fca90f9afdab1ea90fb86dd64c7bed335cdccb1b6  wh-schema.json
d609e690fe5cefe4653561b2db0acbe0b70cd3b3357f1010afa315d8ef6329bc  wh-board.json
13462d4df380e7368b08c0f1d830fe54f57a3daa675feaaeb8a2ef6173f33079  wh-card-535.json
```

Initial REST lookup used a mistaken repository name and returned 404; corrected `gh api repos/wstein/crewbook/issues/7` and its comments endpoint returned current issue evidence. No write followed the failed lookup.

## Remaining gates

- Coordinator reconciles stale issue wording and the saved project-10 milestone filter with current workflow semantics.
- Design resolves whether project-6 additional views are still required while preserving its current board.
- Human UI evidence must demonstrate saved/reloaded Priority ordering, milestone grouping and workflow trigger/action configuration on both boards.
- A separately authorized live behavior plan is needed for closure/reopen or workflow mutations; metadata alone cannot establish conservative automation.
- Ownership/exact-review transition and pending/drained requirements need current policy/native evidence; this maintenance report grants no new writer authority.

## Source checks

Passed: 23 board tests; source package layout/inventory check; nonempty redacted Gitleaks 8.30.1 history/tree/message scans; whitespace check. No new executable behavior was introduced. Native macOS execution was unavailable and was not claimed. UI behavior and live failure/closure experiments were skipped because this assignment authorized reads only.
