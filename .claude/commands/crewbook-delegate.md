---
description: Crew Book delegate workflow for the explicitly configured project
argument-hint: "<task, area, issue or workflow options>"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

For an author or reviewer requester only, delegate a bounded helper task:
$ARGUMENTS under [crewbook-helper.md](../../.agents/crewbook-helper.md). Choose crewbook-helper for read-only lookups, crewbook-helper-edit for individually named edits/checks. Do not delegate board operations, protected paths, rules or outward writes. Pass selected skill links, file scope, done criteria and checks; one editor per worktree. Helpers start no children; do not use this command to re-delegate an issue or
review. The requester verifies the result. Only the author commits/lands under
supplied policy with exact helper assistance metadata; reviewers remain read-only.
