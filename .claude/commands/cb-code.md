---
description: cb-code workflow for the explicitly configured project
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

Read [cb-code.md](../../.agents/cb-code.md) and follow the supplied project policy. Assignment: $ARGUMENTS. The named area selects a configured lane; if no issue is supplied, request an assignment from the designated coordinator and wait.

This command executes a leaf assignment directly; it starts no issue worker.
Apply the manual's ownership table and report missing assignment/context to
the designated coordinator instead of re-delegating.
