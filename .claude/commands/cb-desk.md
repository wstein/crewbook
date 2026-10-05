---
description: cb-desk workflow for the explicitly configured project
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.

Read [cb-desk.md](../../.agents/cb-desk.md) and follow the supplied project policy. Assignment: $ARGUMENTS.

Apply the role's explicit coordinator designation and the manual's ownership
table. Do not create overlapping coordinators or duplicate worker starts.

On startup, follow cb-desk's persistent dispatcher procedure: start or reuse
one cb-dispatch subagent automatically, retain its handle and route subsequent
work through it. Desk remains the human contact; dispatch owns issue/review
starts. Missing client subagent/resume support is reported explicitly.
