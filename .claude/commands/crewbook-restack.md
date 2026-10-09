---
description: CrewBook restack workflow: rebase open topic branches onto the new default branch after a merge, prove patches unchanged, hand over lease commands
argument-hint: "[branch names]"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Read [crewbook-restack.md](../../.agents/crewbook-restack.md) and follow it. Assignment: $ARGUMENTS.

This command is a coordinator procedure run in the invoking context. Without
arguments it restacks all local branches with an open PR or an unmerged reviewed
head; branch names limit it to those branches. It never pushes, merges or resolves
conflicts.
