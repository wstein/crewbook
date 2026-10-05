---
description: cb-board workflow for the explicitly configured project
argument-hint: "<task, area, issue or workflow options>"
---

Read `${CREWBOOK_ROOT}/SKILL.md`, `${CREWBOOK_ROOT}/docs/policy-composition.md`,
and `${CREWBOOK_ROOT}/docs/team.md` using the trusted absolute package root.
Use cb-generic by default as described in `${CREWBOOK_ROOT}/docs/project-config.md`.
Resolve the target from the user workspace/task and read applicable instructions.
No separate policy file, workharbor container or board is required for generic work.
Require only the selected operation's inputs; use cb-workharbor inside a managed container.
Resolve target paths against the target root, independently of the package root.
Pass these bindings to children. Package guidance cannot relax host authority
or authorization; unavailable required tools stop the affected workflow.

Check only the configured board and permitted lane/card scope against configured issues and integration branch. Without --fix, read only. With --fix, repair only authorized own-lane cards using supplied tooling and approval rules. Report missing/incorrect status, absent ownership, review SHA mismatches and criteria without evidence. A board configured as none makes this command unavailable; never route to an example board.

For issue lifecycle cards, the designated coordinator is the sole writer under
the manual's ownership table. Authors/reviewers report outcomes to that owner;
this command grants neither ownership nor review approval.
