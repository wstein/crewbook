---
description: cb-delegate workflow for the explicitly configured project
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

For an author or reviewer requester only, delegate a bounded helper task:
$ARGUMENTS under [cb-helper.md](../../.agents/cb-helper.md). Choose cb-helper for read-only lookups, cb-helper-edit for individually named edits/checks. Do not delegate board operations, protected paths, rules or outward writes. Pass selected skill links, file scope, done criteria and checks; one editor per worktree. Helpers start no children; do not use this command to re-delegate an issue or
review. The requester verifies the result. Only the author commits/lands under
supplied policy with exact helper assistance metadata; reviewers remain read-only.
