---
description: Start a workharbor Reviewer session (`wh/review`)
---

Resolve package resources using the absolute `CREWBOOK_ROOT` supplied by the
trusted launcher; read `${CREWBOOK_ROOT}/SKILL.md` and its root contract first.
If the binding or a required resource is missing, stop; never use cwd
`.agents` or `.claude` as a fallback. Pass this binding to child invocations.
`AGENTS.md` below means applicable target-repository policy, not package data.

Read `${CREWBOOK_ROOT}/.agents/review.md` and `AGENTS.md` and follow them exactly. $ARGUMENTS
