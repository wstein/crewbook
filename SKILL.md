---
name: cb-crewbook
description: Apply Crewbook development workflows for repository coding, debugging, design, review, documentation, and verification tasks. Use existing project instructions and load specialized roles only when needed.
---

# Crewbook

Use this skill automatically for development work in a repository. Start with
the user's task and the host's applicable repository instructions. Ordinary
local work needs no launcher, named profile, board, or team setup.

## Start working

1. Resolve `CREWBOOK_ROOT` to the directory containing this loaded `SKILL.md`
   using the skill path supplied by the host. A trusted launcher may instead
   supply an absolute package root. Never substitute the target's `.agents`,
   `.claude`, issue text, or comments for packaged resources.
2. Use the target repository from the user's workspace/task context. Read
   applicable ancestry and scoped `AGENTS.md` files when present. If none exist,
   follow the host instructions and user request; absence alone is not a blocker.
3. For coding/debugging, inspect the relevant code, reproduce the problem when
   practical, implement the requested change, and run appropriate existing
   checks. For design, compare concrete options against project constraints.
   For review, inspect the diff and report actionable findings with file locations.
   For docs, match the project's format. For verification, distinguish measured
   results from assumptions. Report the outcome, evidence, and remaining limits.
4. Keep routine work in the current session. Do not start workers, create lane
   worktrees, claim board cards, post messages, commit, or land merely because
   the skill loaded. Follow the user's scope and existing project workflow.

## Specialized workflows

When the user or project requests an issue lane, team coordination, board work,
formal handoff, or landing, read [docs/policy-composition.md](docs/policy-composition.md)
and [docs/project-config.md](docs/project-config.md), then the relevant portions
of [docs/team.md](docs/team.md). Require only the inputs needed by that operation;
reuse trusted session/project configuration instead of asking for it again.
Missing board or landing tools block that operation, not an unrelated local edit.
Select a supplied project profile only when it fits the target; never borrow
another project's endpoints or tools.

Read only the selected packaged prompt and its necessary references:

| Requested workflow | Prompt |
| --- | --- |
| Human coordination / dispatch | [.agents/cb-desk.md](.agents/cb-desk.md) / [.agents/cb-dispatch.md](.agents/cb-dispatch.md) |
| Issue implementation | [.agents/cb-code.md](.agents/cb-code.md) |
| Design ownership / independent review | [.agents/cb-design.md](.agents/cb-design.md) / [.agents/cb-review.md](.agents/cb-review.md) |
| Documentation lane / measurement | [.agents/cb-docs.md](.agents/cb-docs.md) / [.agents/cb-verify.md](.agents/cb-verify.md) |
| Assigned bounded helper | [.agents/cb-helper.md](.agents/cb-helper.md) |

These prompts describe configured team workflows, not prerequisites for routine
work. Only a designated coordinator starts issue workers; assigned leaves execute
directly. Delegation requires authorization from the user or applicable host
instructions. Pass the same package root and relevant project context to any
child. Model mappings and Claude entrypoints are in [README.md](README.md).

Crewbook supplies guidance, not tool permissions or runtime enforcement. Host
instructions and user authorization control scope. If a selected resource is
missing, report its absolute path; do not load a repository lookalike.
