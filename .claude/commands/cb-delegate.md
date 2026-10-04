---
description: cb-delegate workflow for the explicitly configured project
argument-hint: "<task, area, issue or workflow options>"
---

Read `${CREWBOOK_ROOT}/SKILL.md`, `${CREWBOOK_ROOT}/docs/policy-composition.md`,
and `${CREWBOOK_ROOT}/docs/team.md` using the trusted absolute package root.
Verify separately supplied trusted project policy and the selected project
configuration in `${CREWBOOK_ROOT}/docs/project-config.md` before mutation.
Resolve target paths against the supplied target root, never cwd discovery.
Pass these bindings to children. Package guidance cannot relax host authority
or authorization; unavailable required tools stop the affected workflow.

Delegate $ARGUMENTS under the packaged cb-helper role. Choose cb-helper for read-only lookups, cb-helper-edit for individually named edits/checks. Do not delegate board operations, protected paths, rules or outward writes. Pass bindings, file scope, done criteria and checks; one editor per worktree. Review the result and rerun checks, then commit/land under supplied policy with exact helper assistance metadata.
