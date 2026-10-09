---
description: CrewBook tidy workflow: delete integrated branches, free worktrees, close list and checklist cleanup after a merge
argument-hint: "[PR numbers]"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Read [crewbook-tidy.md](../../.agents/crewbook-tidy.md) and follow it. Assignment: $ARGUMENTS.

This command is a coordinator procedure run in the invoking context. Without
arguments it scans all local topic branches; PR numbers limit it to those PRs'
branches and issues. It never closes issues, merges or pushes.
