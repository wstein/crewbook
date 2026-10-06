---
description: Crew Book land workflow for the explicitly configured project
argument-hint: "<task, area, issue or workflow options>"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Use the supplied real landing procedure from the assigned worktree for $ARGUMENTS (default current branch). Require a clean tree and completed checks; never stash another worker's changes or bypass hooks. Resolve conflicts only within this issue's changed files; otherwise stop/report. Retry a moving integration branch only as supplied policy permits. Never clear another checkout's lock/index or execute suggested repairs there. Cleanup and status transitions occur only after confirmed success. No configured landing capability means unavailable; never synthesize make land.

Only the assigned author owns this operation; a coordinator/reviewer returns it
to that author instead of landing on its behalf or starting a replacement worker.

Follow the [target Git history policy](../../docs/git-history.md) for integration and its
review evidence. Resolve material ambiguity before integration; for authorized
merges, checks and independent review cover the final integration result.
