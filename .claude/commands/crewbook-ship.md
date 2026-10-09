---
description: CrewBook ship workflow: push, draft PR, review status and ready for one CLEARed SHA
argument-hint: "<branch> <full SHA> <issue> <CLEAR evidence> [base]"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Read [crewbook-ship.md](../../.agents/crewbook-ship.md) and follow it. Assignment: $ARGUMENTS.

This command is a coordinator procedure run in the invoking context. A missing
branch, SHA or CLEAR evidence is reported as blocked; never infer them.
