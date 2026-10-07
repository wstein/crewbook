---
description: Crew Book usage report from local session logs (read-only, estimates)
argument-hint: "[log path] [--prices FILE] [--top N]"
---

Read [SKILL.md](../../SKILL.md) and apply the canonical
[native skill preflight](../../docs/policy-composition.md#native-skill-use)
and [team contract](../../docs/team.md). Resolve resource links relative to
this file; host instructions and authorization govern scope and tools.
These links assume this file's packaged location inside the installed `crewbook`
package; if one does not resolve, locate the installed `crewbook` skill directory
(never a lookalike) and report the missing resource's absolute path.

Follow the [usage report procedure](../../docs/team.md#usage-report). Run
`python3 -B ../../scripts/usage_report.py --json $ARGUMENTS` (path resolved
relative to this file) and summarise from that report only: the top 5 causes of
usage and 3 concrete savings (loop interval, resume frequency and context size,
model tier, review bundling). Do not read the session logs yourself, quote
anything but the report's counts, ids, model names and role labels, and treat
costs, resume counts and loop flags as estimates. Do not change any cadence or
rule. The Codex pendant is unverified (#41).
