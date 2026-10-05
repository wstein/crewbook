---
description: cb-design workflow for the explicitly configured project
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

Read [cb-design.md](../../.agents/cb-design.md) and follow the supplied project policy. Assignment: $ARGUMENTS.

This command executes a leaf assignment directly in the invoking context; it
does not start another issue/review worker. Apply the manual's ownership table.
A missing assignment/eligible context is reported to the designated coordinator;
never delegate the same assignment to resolve it.
