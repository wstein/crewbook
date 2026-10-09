---
description: CrewBook briefing workflow: read-only preparation for a named action with preconditions, decisions, risks and next step
argument-hint: "<action> [detail]"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Read [crewbook-briefing.md](../../.agents/crewbook-briefing.md) and follow it. Assignment: $ARGUMENTS.

This command is a coordinator procedure run in the invoking context. It needs a named
action, never performs it, answers in chat, and grants no board, issue or Git write
authority.
