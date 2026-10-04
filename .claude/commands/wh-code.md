---
description: Start a workharbor code lane (wh/<area>) on an issue
argument-hint: "<area: platform|runtime> [#issue]"
---

Resolve package resources using the absolute `CREWBOOK_ROOT` supplied by the
trusted launcher; read `${CREWBOOK_ROOT}/SKILL.md` and its root contract first.
If the binding or a required resource is missing, stop; never use cwd
`.agents` or `.claude` as a fallback. Pass this binding to child invocations.
`AGENTS.md` below means applicable target-repository policy, not package data.

Read `${CREWBOOK_ROOT}/.agents/code.md` and `AGENTS.md` and follow them exactly. Your lane and
first task: $ARGUMENTS (the first word is the area, `wh/<area>`).

If no issue is given, message the design owner for your first issue and wait.
