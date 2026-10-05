---
description: cb-delegate workflow for the explicitly configured project
argument-hint: "<task, area, issue or workflow options>"
---

Read `${CREWBOOK_ROOT}/SKILL.md`, `${CREWBOOK_ROOT}/docs/policy-composition.md`,
and `${CREWBOOK_ROOT}/docs/team.md` using the trusted absolute package root.
Use cb-generic by default as described in `${CREWBOOK_ROOT}/docs/project-config.md`.
Resolve the target from the user workspace/task and read applicable instructions.
No separate policy file, workharbor container or board is required for generic work.
Require only the selected operation's inputs; use cb-workharbor inside a managed container.
Resolve target paths against the target root, independently of the package root.
Pass these bindings to children. Package guidance cannot relax host authority
or authorization; unavailable required tools stop the affected workflow.

For an author or reviewer requester only, delegate a bounded helper task:
$ARGUMENTS under `${CREWBOOK_ROOT}/.agents/cb-helper.md`. Choose cb-helper for read-only lookups, cb-helper-edit for individually named edits/checks. Do not delegate board operations, protected paths, rules or outward writes. Pass bindings, file scope, done criteria and checks; one editor per worktree. Helpers start no children; do not use this command to re-delegate an issue or
review. The requester verifies the result. Only the author commits/lands under
supplied policy with exact helper assistance metadata; reviewers remain read-only.
