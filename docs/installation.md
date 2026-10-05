# Installation and client support

Use `crewbook` as the package and skill identifier; “Crew Book” is the
reader-facing name. This guide covers installation, client entrypoints and
requested model mappings. The [README](../README.md) introduces first use.

## Install, update, uninstall


For Codex, install one copy of the skillset in `~/.agents/skills/crewbook`. For a local source checkout, use an absolute
symlink; keep it outside the target repository's instruction directories:

```sh
mkdir -p ~/.agents/skills
ln -s /absolute/path/crewbook ~/.agents/skills/crewbook
```

If that destination already exists, inspect it before replacing anything.
An existing legacy `cb-crewbook` symlink already points to the renamed skill;
keep that single installation rather than adding a duplicate.
Restart Codex or open a new session to refresh discovery. `agents/openai.yaml`
enables implicit invocation: ordinary repository requests can select Crewbook
automatically without switching roles. Explicit `$crewbook` starts desk
and its persistent dispatcher; it is not a load-only command. The host's
loaded skill uses relative links; no launcher or environment variable is
necessary. Routine coding, review, docs and verification use existing project
instructions without full team setup. Explicitly selected roles load immediately; assigned leaves stay leaves.

Start Codex from the target repository with eight subagent slots and desk
activation in one command:

```sh
codex -m gpt-6.1-sol -c model_reasoning_effort="low" -c agents.max_concurrent_threads_per_session=8 '$crewbook'
```

Keep the prompt single-quoted so the shell passes the skill name literally.
Desk is the primary session; eight is the recommended subagent capacity,
excluding desk. Six covers dispatch, two authors, two reviewers and design;
the extra two slots allow bounded helpers. This is a ceiling, not a request
to start eight agents. Crewbook still permits at most two concurrent code
authors. See [dynamic allocation](team.md#dynamic-agent-allocation).
Keep desk and its one dispatcher persistent. Start each new work item, design
batch and bounded helper/research/verification task in fresh context; resume
the same author for that item's fixes and same independent reviewer for its
finding corrections on each exact revision. Save compact durable records,
not full transcripts. Completed handles do not establish occupancy or available
capacity, and no release tool is assumed: host controls govern fresh starts.
See [context lifetimes](team.md#delegation-and-context) and
[capacity recovery](team.md#dispatch-supervision-and-recovery). Efficiency
and quality improvements remain unmeasured.
The installed skill and selected model must be available in the client.

The dedicated Codex desk skill is
[.agents/skills/cb-desk/SKILL.md](../.agents/skills/cb-desk/SKILL.md). Codex discovers
it when launched in the crewbook repository. To make `$cb-desk` available in
other repositories, install its folder in a user skill location too:

```sh
mkdir -p ~/.agents/skills
ln -s /absolute/path/crewbook/.agents/skills/cb-desk ~/.agents/skills/cb-desk
```

Inspect an existing destination before replacing it. Codex skills use `$`;
`.claude/commands/cb-desk.md` cannot register `/cb-desk` in Codex. The existing
`$crewbook` installation is sufficient to start desk without the optional
alias. See [official skill discovery](https://learn.chatgpt.com/docs/build-skills).

A symlink follows local edits; use a reviewed text export in the skill directory
when you need a fixed copy. Run the package check before export and preserve all
declared resources, licence and provenance. Both source and exported packages
include the Codex discovery metadata. This installation does not register Claude
commands or establish workharbor runtime compatibility. Workharbor's production
pin/adapter checks remain a separate integration contract.

To update a linked checkout, review and validate its changes. For a fixed copy,
validate a new export before switching registration for new sessions. Keep old
copies while active sessions use them. To uninstall a linked skill, remove only
the `crewbook` symlink (or its legacy installation name); retain the source checkout and target project policy.

## Entrypoints and support


- **Skill:** discover the installed `SKILL.md`; follow links relative to that file. It may also be loaded by absolute path. Its routing table selects a role without loading all
  prompts. Manual text loading and local path resolution can be checked without
  a live agent runtime.
- **Claude Code:** profiles are `.claude/agents/cb-*.md`; commands are
  `.claude/commands/cb-*.md` (including `/cb-code platform`, `/cb-desk`,
  `/cb-review`, `/cb-delegate`, `/cb-board`, `/cb-land` and `/cb-handover`). A
  client must register/load these files from the installed skill directory; merely setting an environment variable does not register slash
  commands or profiles. Automatic discovery from an external mount is
  **unverified**. Existing `model: sonnet`, `opus` and `haiku` pins remain
  Claude profile values.
- **Codex:** select `SKILL.md` or load a selected role by absolute path from the installed skill. `.claude` files are reference data, not Codex registration.
  Model selection is a separate launcher setting, not a rewrite of Claude YAML:

  | Claude role tier | Codex model | Reasoning effort |
  | --- | --- | --- |
  | Sonnet | `gpt-6.1-sol` | low |
  | Opus | `gpt-6.1-sol` | medium |
  | Haiku | `gpt-6-luna` | medium |

  These are requested mappings, not measured claims about availability or
  equivalence. Native Codex discovery is enabled by `agents/openai.yaml`; child model
  propagation still depends on the host.
- **workharbor:** mounted provisioning and enforcement are
  **conceptual/unverified**, tracked in historical workharbor integration issue #283. This package supplies
  no enforcement, tool permissions or workharbor runtime adapter.

Explicit `$crewbook` (Codex) or `/cb-desk` (Claude Code) enters
`crewbook/desk` through the canonical cb-desk workflow
and automatically starts or reuses one pinned cb-dispatch
subagent. Desk stays the human contact and routes later work through the same
handle; dispatch owns claims and worker/review starts. The dispatch child is
pinned to Sonnet for Claude and `gpt-6.1-sol` with low reasoning effort for Codex. Idle dispatch yields and
is resumed by desk. This requires client subagent/resume support and does not
create a background daemon. See the [team manual](team.md).

Public issue/review profiles and direct role commands execute as leaves, never
re-delegating their assignment. Only cb-dispatch or an explicitly designated
session coordinator starts those workers; cb-desk routes unless designated in
its place. The manual defines single ownership and a counted lifecycle example.

The [target Git history guidance](git-history.md) resolves linear and
authorized non-linear integration from target instructions and session choices,
with static decision walkthroughs.
The [team manual](team.md) covers roles, delegation, independent review,
handoffs and context. For configured team workflows, select applicable trusted project configuration:
[cb-generic](profile-generic.md) is the default for any repository in
the current native session, without a workharbor container or board;
[cb-workharbor](profile-workharbor.md) applies to any repository inside
a workharbor-managed container. Both profiles use the target repository's
instructions, destinations and checks; neither selects a specific repository.
Board and landing capabilities belong to the target project or supervisor;
none is shipped here. Missing host capability
means report the affected workflow as unavailable; do not fetch a substitute
from the package or provision infrastructure implicitly.

Documentation is root README plus docs/*.md in GitHub-flavored Markdown,
without Hugo frontmatter, shortcodes or toolchain. Native client loading (#241)
and platform doctor (#242) are historical workharbor work items, not measured
capabilities here. Source checks and CI do not establish native runtime support.

Antigravity support remains incomplete; see the [readiness matrix](antigravity.md)
for historical evidence, current unverified capabilities and admission requirements.
