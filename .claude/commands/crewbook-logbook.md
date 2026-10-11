---
description: CrewBook logbook workflow: append local session history with safe monthly rotation
argument-hint: "[title]"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Read [crewbook-logbook.md](../../.agents/crewbook-logbook.md) and follow it. Assignment: $ARGUMENTS.

This command is a coordinator procedure run in the invoking context. It writes
only ignored local logbook files within the active request, reconciles uncertain
appends and preserves old entries. It starts no child or scheduled work.
