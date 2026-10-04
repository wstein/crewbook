---
description: cb-handover workflow for the explicitly configured project
---

Read `${CREWBOOK_ROOT}/SKILL.md`, `${CREWBOOK_ROOT}/docs/policy-composition.md`,
and `${CREWBOOK_ROOT}/docs/team.md` using the trusted absolute package root.
Verify separately supplied trusted project policy and the selected project
configuration in `${CREWBOOK_ROOT}/docs/project-config.md` before mutation.
Resolve target paths against the supplied target root, never cwd discovery.
Pass these bindings to children. Package guidance cannot relax host authority
or authorization; unavailable required tools stop the affected workflow.

Write a read-only handoff for the configured human: local commits relative to the configured remote/integration branch, issue trailers, exact reviewed SHAs, criteria met/unmet, blockers and unverified claims. Read only configured destinations and respect shared-checkout restrictions. Do not fetch or write implicitly. Missing review evidence means not ready; never push.

Include the named coordinator, author and independent reviewer, confirmed start
and ownership records, and whether landing/card operations were unavailable.
