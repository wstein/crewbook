# Issue 44: current-host question and decision audit

> **Historical evidence, not a current claim.** This file documents the host state and source revision of 2026-10-11 (source `897483f26b901521875d1d469c682ddafc8eb6bb`). That revision is behind current `main`, and the quoted commit hashes are not ancestors of it; later changes may have altered the sources, procedures and host this file describes. Re-measure before relying on it. The evidence below is preserved unchanged.

Audited 2026-10-11 against source
`897483f26b901521875d1d469c682ddafc8eb6bb` and the
[current issue 44 body](https://github.com/wstein/crewbook/issues/44), read through
GitHub REST with `updated_at: 2026-10-11T02:44:16Z`, state `open`.
This is source-only maintenance evidence; it changes no distributed guidance,
registry, decision log, issue or board. The coordinator owns outward updates.

The current v3 acceptance has two checked guidance criteria. Its existing
progress entry names independent review at
`e797c856cbcb9aee6d96f37e3932bb291c3fe2b9` under issue 120; this audit preserves
that attribution rather than claiming a new native result. The six unchecked
historical criteria remain a retained record, interpreted under the issue's
explicit v3 supersession rule. No checklist or closure is inferred here.

## Criteria and source evidence

| Criterion | Current source and audit outcome |
| --- | --- |
| Current: consistent standing defaults, question classes and desk guidance; reuse authorization for routine writes | [Decision log](../../docs/project-config.md#decision-log) keeps standing defaults proposed until human approval and distinguishes consequential classes. [Desk](../../.agents/crewbook-desk.md) reuses authorized topic push, PR and issue/card scope. [Human-request contract](../../docs/team.md#human-request-contract) defines that scope and the host-control boundary. Guidance present; native operation unmeasured. |
| Current: completion verification, ownership, stable IDs and non-defaulted consequential decisions | [Human-request contract](../../docs/team.md#human-request-contract) requires criterion verification and closure readback, and reserves issue/card writes to the coordinator. [Decision log](../../docs/project-config.md#decision-log) reserves log writes and ID allocation to desk, gives stable reply grammar, and keeps consequential answers explicit. Guidance present. |
| Historical: desk block cap, reply grammar and pointer | [Desk](../../.agents/crewbook-desk.md) specifies at most three stable-ID items per turn, queued counts, explicit-answer sentence and routine-only prefilled reply line; it links to the canonical log rules. Implemented as prose. |
| Historical: decision-log subsection and unchanged registry grammar | [Decision log](../../docs/project-config.md#decision-log) defines path, keys, states, sole writer, expiry and evidence boundary separately from the [registry](../../docs/project-config.md#coordinator-mode-and-registry). Implemented as prose; no runtime writer measured. |
| Historical: design supplies IDs and merged desk shows at most three | [Team manual](../../docs/team.md) instead requires unnumbered ASK proposals; desk alone allocates IDs, with the cap in every mode. The later canonical ownership contract supersedes literal proposer-assigned IDs and merged-only wording. Do not restore them to satisfy the old text. |
| Historical: dispatch zero-to-one-line change | [Dispatch handback](../../.agents/crewbook-dispatch.md) now has existing ASK, duplicate-hint and desk-allocation guidance. This historical change-size constraint is not a reason to delete later compatible ownership guidance. This audit changes zero dispatch lines. |
| Historical: human-approved standing defaults before first use; veto line | The [canonical rule and example](../../docs/project-config.md#needs-you-example) require approval before class or expiry defaulting, and a veto line for defaults. This audit has no verified approval or first-use evidence and applies no defaults. Source presence cannot satisfy the human-approval criterion. |
| Historical: both supported Pythons and independent Opus review of prompt changes | This maintenance-only addition changes no prompt. Available `python3` and `/usr/bin/python3` both report 3.13.5; they do not establish Python 3.9.6 execution. Historical dual-version and exact Opus review completion are not established by this audit. Independent review of this new candidate remains a separate coordinator step. |

## Manual boundary walkthrough

Read the desk output rules, decision-log rules, dispatcher ASK schema and team
human-request contract together; no prompt-content parser or wording test was
added. The source gives these outcomes:

- A routine write already within the human request proceeds under actual host
  controls without another decision item. A local-only request supplies no
  outward-write authority; an actual host rejection still blocks publication.
- A routine question without an approved standing-default class cannot silently
  default at the next dependent operation. With no recommendation it blocks
  that operation; other independent authorized work can continue.
- Security-control relaxation, money, product direction, release scope/order,
  merge, tag, release and deployment remain consequential and never default.
  A recommendation cannot supply their explicit human answer. Agents never
  perform the human merge, tag, release or deployment operations.
- Desk alone assigns new IDs and writes decision entries. Dispatch's `ASK <k>`
  is local numbering; a `dup=` hint is checked by desk, and the log supplies
  evidence rather than authorization. This leaf allocated no ID and wrote no
  private decision entry.
- New revision or operation invalidates reuse where required; defaults and
  answers never grant later authority. Partial work keeps issue 44 open.

These are manual source observations, not observed compliance in Claude,
Codex or Antigravity. No native loading, live adapter, provider, runtime,
reply-handling or permission-enforcement experiment was performed. The issue's
historical roughly 70-question and 80-percent figures were not reproduced;
this audit supplies no question-volume or efficiency measurement.

## Verification and remaining work

The source-only `tools/` destination is already excluded by the
[package policy](../package-policy.json); no distributed inventory update or
artifact export is needed. Proportionate checks are recorded below after
execution. No artifact, image, CLI release or documentation build is authorized
or performed. Broader runtime and measurement work remains outside this audit.

- `python3 -B tools/crewbook-package.py check --root <worktree>` passed:
  source layout and inventory valid; runtime compatibility not established.
- Changed-link walkthrough confirmed all 12 relative targets and their supplied
  anchors resolve; the issue endpoint was read through REST as noted above.
- `git diff --check` passed.
- `bash tools/scan-secrets.sh <worktree> /opt/bundledock/toolbox/bin/gitleaks`
  passed with version 8.30.1: nonempty all-ref history, current tree and commit
  messages scanned with redaction. No reports or raw matches are retained.
- The broad unittest suite and Python 3.9.6 run were not repeated for this
  maintenance prose addition. No behavior change needs a manufactured failing
  test; no native or historical measurement gap is represented as passing.
