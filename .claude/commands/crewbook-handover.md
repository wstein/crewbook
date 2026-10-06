---
description: Crew Book handover workflow for the explicitly configured project
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Write a read-only handoff for the configured human: local commits relative to the configured remote/integration branch, issue trailers, exact reviewed SHAs, criteria met/unmet, blockers and unverified claims. Read only configured destinations and respect shared-checkout restrictions. Do not fetch or write implicitly. Missing review evidence means not ready; never push.

Include the named coordinator, author and independent reviewer, confirmed start
and ownership records, and whether landing/card operations were unavailable.
