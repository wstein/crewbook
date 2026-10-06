---
description: Crew Book board workflow for the explicitly configured project
argument-hint: "<task, area, issue or workflow options>"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Check only the configured board and permitted lane/card scope against configured issues and integration branch. Without --fix, read only. With --fix, repair only authorized own-lane cards using supplied tooling and approval rules. Report missing/incorrect status, absent ownership, review SHA mismatches and criteria without evidence. A board configured as none makes this command unavailable; never route to an example board.

For issue lifecycle cards, the designated coordinator is the sole writer under
the manual's ownership table. Authors/reviewers report outcomes to that owner;
this command grants neither ownership nor review approval.
