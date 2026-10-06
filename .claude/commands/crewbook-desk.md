---
description: Crew Book desk workflow for the current project
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Read [crewbook-desk.md](../../.agents/crewbook-desk.md) and follow the supplied project policy. Assignment: $ARGUMENTS.

Apply the role's explicit coordinator designation and the manual's ownership
table. Do not create overlapping coordinators or duplicate worker starts.

On startup, follow crewbook-desk's mode selection: merged by default, with desk as
the designated coordinator following the canonical crewbook-dispatch procedure as
`crewbook/desk` and starting no dispatcher. Only in split mode (configured
board/claim gate or user request) start or reuse one crewbook-dispatch subagent,
retain its handle and route work through it; it then owns issue/review starts.
Missing client subagent/resume/wait support is reported explicitly.
