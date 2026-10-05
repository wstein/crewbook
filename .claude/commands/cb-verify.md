---
description: cb-verify workflow for the explicitly configured project
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

Read `${CREWBOOK_ROOT}/.agents/cb-verify.md` and follow the supplied project policy. Assignment: $ARGUMENTS.

This command executes a leaf assignment directly in the invoking context; it
does not start another issue/review worker. Apply the manual's ownership table.
A missing assignment/eligible context is reported to the designated coordinator;
never delegate the same assignment to resolve it.
