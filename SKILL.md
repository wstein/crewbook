---
name: crewbook
description: Start Crew Book desk and its persistent dispatcher when explicitly invoked; otherwise apply repository coding, review, documentation and verification guidance.
---

# Crew Book

Use this skill automatically for development work in a repository. Start with
the user's task and the host's applicable repository instructions. Ordinary
local work needs no launcher, named profile, board, or team setup.

## Explicit invocation starts desk

When the user invokes `$crewbook`, adopt crewbook-desk immediately unless they
explicitly select another Crew Book role or ask only to inspect the skill.
Read [.agents/crewbook-desk.md](.agents/crewbook-desk.md) and its necessary references,
then start or reuse its one persistent dispatcher using available subagent
tools. Pin the dispatch child to Sonnet in Claude, or `gpt-6.1-sol` with
low reasoning effort in Codex; set these explicitly when starting it. Retain
the same child handle across requests and resume it when idle. A bare invocation is a desk startup request, not a request to load
instructions and wait for another activation command. Identify the desk session as
`crewbook/desk` (the crewbook-desk workflow) and report the dispatcher startup outcome, including actual tool
limits. Do not stop at “loaded”, “ready for your task” or a generic repository
collaborator identity. Keep desk active across later questions and requests.

If a task accompanies the invocation, route it through desk and the same
dispatcher. An explicit request for crewbook-code, crewbook-review or another role selects
that role directly; already-assigned author/reviewer leaves stay leaves.
A quoted transcript, mention of the skill or host-supplied skill text alone
is not a startup request. Implicit selection for ordinary repository work
uses the guidance below and does not activate desk or start a dispatcher.

Codex invokes skills with `$`: `$crewbook` starts desk; `$crewbook-desk` is the
optional dedicated skill in [.agents/skills/crewbook-desk/SKILL.md](.agents/skills/crewbook-desk/SKILL.md)
when discovered/installed. `/crewbook-desk` is a Claude Code command; shipping its
Markdown file does not register that slash command in Codex.

## Start working

1. Follow this skill's relative links from the file containing each link.
   Use the loaded skill files, not similarly named prompts in the target
   repository. No root variable, launcher or path binding is needed.
2. Use the target repository from the user's workspace/task context. Read
   applicable ancestry and scoped `AGENTS.md` files when present. If none exist,
   follow the host instructions and user request; absence alone is not a blocker.
3. For coding/debugging, inspect the relevant code, reproduce the problem when
   practical, implement the requested change, and run appropriate existing
   checks. For design, compare concrete options against project constraints.
   For review, inspect the diff and report actionable findings with file locations.
   For docs, match the project's format. For verification, distinguish measured
   results from assumptions. Report the outcome, evidence, and remaining limits.
4. For implicit use, keep routine work in the current session and checkout (delegated authors use dedicated worktrees per the
   [team manual](docs/team.md#delegated-authoring-worktrees)). Do not start workers, create lane
   worktrees, claim board cards, post messages, commit, or land merely because
   the skill loaded. Follow the user's scope and existing project workflow.

## Specialized workflows

When the user or project requests an issue lane, team coordination, board work,
formal handoff, or landing, read [docs/policy-composition.md](docs/policy-composition.md)
and [docs/project-config.md](docs/project-config.md), then the relevant portions
of [docs/team.md](docs/team.md). Require only the inputs needed by that operation;
reuse trusted session/project configuration instead of asking for it again.
Missing board or landing tools block that operation, not an unrelated local edit.
Local commits, local target integration and publication are separate operations.
Reuse established user/host authorization for its unchanged scope instead of
asking again; follow the target's actual checks, review order and integration
procedure. Permission for local integration does not imply permission to push
or publish. Generic work retains its local-diff default when authorization is absent.
Use [crewbook-generic](docs/profile-generic.md) by default for any repository in the
current native session, including the Crew Book repository itself. No workharbor container,
board or separate project-policy file is required. Select
[crewbook-workharbor](docs/profile-workharbor.md) for any repository inside a workharbor-managed
container; never borrow another project's endpoints or tools.

Read only the selected packaged prompt and its necessary references:

| Requested workflow | Prompt |
| --- | --- |
| Human coordination / dispatch | [.agents/crewbook-desk.md](.agents/crewbook-desk.md) / [.agents/crewbook-dispatch.md](.agents/crewbook-dispatch.md) |
| Issue implementation | [.agents/crewbook-code.md](.agents/crewbook-code.md) |
| Design ownership / independent review | [.agents/crewbook-design.md](.agents/crewbook-design.md) / [.agents/crewbook-review.md](.agents/crewbook-review.md) |
| Documentation lane / measurement | [.agents/crewbook-docs.md](.agents/crewbook-docs.md) / [.agents/crewbook-verify.md](.agents/crewbook-verify.md) |
| Assigned bounded helper | [.agents/crewbook-helper.md](.agents/crewbook-helper.md) |

These prompts describe configured team workflows, not prerequisites for routine
work. Only a designated coordinator starts issue workers; assigned leaves execute
directly. Delegation requires authorization from the user or applicable host
instructions. Pass links to the selected skill resources and relevant project context to
any child. Keep desk and its one dispatcher persistent; use fresh contexts for
new work items, design batches and bounded helper/research/verification tasks.
Reuse the same author for a work item's fixes and the same independent reviewer
for corrections to that item's findings on each exact revision. Preserve compact
durable records, not full transcripts, under the [context lifetime contract](docs/team.md#delegation-and-context).
Completion does not establish host capacity or a release capability; defer fresh
starts on confirmed full capacity rather than recycling unrelated contexts.
Model mappings and Claude entrypoints are in [README.md](README.md).

Crew Book supplies guidance, not tool permissions or runtime enforcement. Host
instructions and user authorization control scope. If a selected resource is
missing, report its absolute path; do not load a repository lookalike.

Follow the [target Git history policy](docs/git-history.md) for integration and its
review evidence. Resolve material ambiguity before integration; for authorized
merges, checks and independent review cover the final integration result.
