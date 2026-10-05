---
description: cb-land workflow for the explicitly configured project
argument-hint: "<task, area, issue or workflow options>"
---

Read [SKILL.md](../../SKILL.md), [policy-composition.md](../../docs/policy-composition.md),
and [team.md](../../docs/team.md).
Use cb-generic by default as described in [project-config.md](../../docs/project-config.md).
Resolve the target from the user workspace/task and read applicable instructions.
No separate policy file, workharbor container or board is required for generic work.
Require only the selected operation's inputs; use cb-workharbor inside a managed container.
Resolve these links relative to this file. Use the user workspace for target paths.
Pass the task, checkout and applicable instructions to children. Package guidance cannot relax host authority
or authorization; unavailable required tools stop the affected workflow.

Use the supplied real landing procedure from the assigned worktree for $ARGUMENTS (default current branch). Require a clean tree and completed checks; never stash another worker's changes or bypass hooks. Resolve conflicts only within this issue's changed files; otherwise stop/report. Retry a moving integration branch only as supplied policy permits. Never clear another checkout's lock/index or execute suggested repairs there. Cleanup and status transitions occur only after confirmed success. No configured landing capability means unavailable; never synthesize make land.

Only the assigned author owns this operation; a coordinator/reviewer returns it
to that author instead of landing on its behalf or starting a replacement worker.
