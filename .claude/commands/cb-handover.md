---
description: cb-handover workflow for the explicitly configured project
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

Write a read-only handoff for the configured human: local commits relative to the configured remote/integration branch, issue trailers, exact reviewed SHAs, criteria met/unmet, blockers and unverified claims. Read only configured destinations and respect shared-checkout restrictions. Do not fetch or write implicitly. Missing review evidence means not ready; never push.

Include the named coordinator, author and independent reviewer, confirmed start
and ownership records, and whether landing/card operations were unavailable.
