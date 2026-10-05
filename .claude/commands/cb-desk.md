---
description: cb-desk workflow for the explicitly configured project
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

Read [cb-desk.md](../../.agents/cb-desk.md) and follow the supplied project policy. Assignment: $ARGUMENTS.

Apply the role's explicit coordinator designation and the manual's ownership
table. Do not create overlapping coordinators or duplicate worker starts.

On startup, follow cb-desk's persistent dispatcher procedure: start or reuse
one cb-dispatch subagent automatically, retain its handle and route subsequent
work through it. Desk remains the human contact; dispatch owns issue/review
starts. Missing client subagent/resume support is reported explicitly.
