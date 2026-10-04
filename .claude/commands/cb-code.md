---
description: cb-code workflow for the explicitly configured project
argument-hint: "<task, area, issue or workflow options>"
---

Read `${CREWBOOK_ROOT}/SKILL.md`, `${CREWBOOK_ROOT}/docs/policy-composition.md`,
and `${CREWBOOK_ROOT}/docs/team.md` using the trusted absolute package root.
Verify separately supplied trusted project policy and the selected project
configuration in `${CREWBOOK_ROOT}/docs/project-config.md` before mutation.
Resolve target paths against the supplied target root, never cwd discovery.
Pass these bindings to children. Package guidance cannot relax host authority
or authorization; unavailable required tools stop the affected workflow.

Read `${CREWBOOK_ROOT}/.agents/cb-code.md` and follow the supplied project policy. Assignment: $ARGUMENTS. The named area selects a configured lane; if no issue is supplied, request an assignment from cb-design and wait.
