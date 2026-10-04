---
description: Start a workharbor Technical writer session (`wh/docs`)
---

Resolve package resources using the absolute `CREWBOOK_ROOT` supplied by the
trusted launcher; read `${CREWBOOK_ROOT}/SKILL.md` and its root contract first.
If the binding or a required resource is missing, stop; never use cwd
`.agents` or `.claude` as a fallback. Pass this binding to child invocations.
Before applying this entrypoint, read
`${CREWBOOK_ROOT}/references/policy-composition.md` and identify host instructions.
`AGENTS.md` below means separately supplied trusted project policy, not package
data. Verify required policy/configuration before mutation; package guidance
cannot relax host authority or approval boundaries. Pass the applicable
project-policy context to children alongside the root.

Read `${CREWBOOK_ROOT}/.agents/docs.md` and `AGENTS.md` and follow them exactly. $ARGUMENTS
