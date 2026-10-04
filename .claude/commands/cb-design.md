---
description: cb-design workflow for the explicitly configured project
---

Read `${CREWBOOK_ROOT}/SKILL.md`, `${CREWBOOK_ROOT}/docs/policy-composition.md`,
and `${CREWBOOK_ROOT}/docs/team.md` using the trusted absolute package root.
Verify separately supplied trusted project policy and the selected project
configuration in `${CREWBOOK_ROOT}/docs/project-config.md` before mutation.
Resolve target paths against the supplied target root, never cwd discovery.
Pass these bindings to children. Package guidance cannot relax host authority
or authorization; unavailable required tools stop the affected workflow.

Read `${CREWBOOK_ROOT}/.agents/cb-design.md` and follow the supplied project policy. Assignment: $ARGUMENTS.

This command executes a leaf assignment directly in the invoking context; it
does not start another issue/review worker. Apply the manual's ownership table.
A missing assignment/eligible context is reported to the designated coordinator;
never delegate the same assignment to resolve it.
