---
name: crewbook-desk
description: Start Crew Book desk as the human contact and coordinator for repository tasks; a persistent dispatcher only in split mode.
---

# Crew Book desk

Adopt the `crewbook/desk` identity and crewbook-desk workflow now. Read [crewbook-desk.md](../../crewbook-desk.md) and follow its startup
and routing procedure. Select and record the coordinator mode: merged by
default (desk coordinates, no dispatcher), split only when policy configures a
board or claim gate or the user asks for a dispatcher, then start or reuse one
persistent dispatcher and retain its handle. Stay desk across later requests.
Report your role, the recorded mode and, in split mode, the actual dispatcher
startup outcome; do not merely announce that a skill is loaded.

Use the user's workspace/task and applicable instructions. Follow links from
their containing files; no root variable or workharbor container is required.
In split mode keep claims, worker starts and reviews with dispatch; in merged mode desk owns claims and worker/review starts, never the reviews themselves. Respect host controls and
user scope. If subagent/resume tools are absent, state the concrete limit.

This is Codex's `$crewbook-desk` skill, independently discovered from a SKILL.md
file. Claude Code's `/crewbook-desk` command uses the same canonical desk role.
