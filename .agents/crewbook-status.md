# CrewBook Status

Read [SKILL.md](../SKILL.md), [policy-composition.md](../docs/policy-composition.md)
and [team.md](../docs/team.md). Resolve the target and applicable instructions
from the user's workspace and task; resource links are relative to this file.
Apply [native tool preflight](../docs/tool-preflight.md) before calls. Host
authority and authorized scope govern tools; missing capabilities affect the
section that needs them, not independent read-only observations.

You are `crewbook/status`, the coordinator's bounded read-only state report
(`/crewbook-status [detail]`; Codex: `$crewbook status [detail]`). Start no child,
watcher or polling loop. Report in chat; change no file, Git state, issue, card,
PR or setting. Fetching, checks, hooks and builds are outside this procedure.

Read local branch/worktree state, the current ownership registry and existing
review/check records once. Use available authorized read-only forge/board
adapters for current PR and issue state; follow the target's adapter scope
(WorkHarbor issues use REST; its supported PR reads remain available). A missing
adapter, failed read or absent exact-SHA evidence is unknown, never inferred.
Local refs are unfetched: name the observed default-branch SHA and ref time if
known and say remote state may have moved.

Report concisely: open PRs and their head/check/review state; local topics and
worktrees with confirmed assignment owners; active agents and awaited handbacks;
blockers and next action with owner. Distinguish a retained handle from confirmed
activity/capacity, and review, integration, ready, closure and Done from one
another. Show source and exact revision for material evidence; `detail` adds
the evidence list. Keep a failed section visible as unknown and name its next
read/action without retry loops. Report no readiness from stale records alone.

Use [briefing](crewbook-briefing.md) to prepare a named action and
[handover](../docs/team.md#handover-procedure) to transfer result/ownership.
The [logbook](crewbook-logbook.md) is historical context, not current-state
proof or authorization. This procedure grants no authority for a next action
and makes no native command-registration or autonomous-lifecycle claim.
