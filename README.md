![CrewBook](https://raw.githubusercontent.com/wstein/crewbook/main/assets/banner.png)

# CrewBook

[![License: EUPL-1.2](https://img.shields.io/badge/license-EUPL--1.2-blue.svg)](LICENSE)
[![Package checks](https://github.com/wstein/crewbook/actions/workflows/check.yml/badge.svg?branch=main)](https://github.com/wstein/crewbook/actions/workflows/check.yml)
[![CodeQL](https://github.com/wstein/crewbook/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/wstein/crewbook/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/wstein/crewbook/badge)](https://scorecard.dev/viewer/?uri=github.com/wstein/crewbook)

## What it is

CrewBook helps a coding agent work through software tasks: understand the
request, make a focused change, check it, and explain the result. It is plain
text and metadata (plus one read-only usage report script,
`scripts/usage_report.py`); no settings, hooks or permission allowlists ship.
The package and skill id is `crewbook`. Your client supplies the tools, and your
repository instructions and authorization govern the work.

Without a command, CrewBook guidance applies to ordinary repository work. To
start the coordinated workflow (desk, with authors and independent reviewers
for larger tasks), invoke it explicitly. A bare invocation starts desk; it is
not a load-only command ([SKILL.md](SKILL.md)).

Client behaviour below is **unverified** unless stated: native loading has not
been measured (issue #41 is postponed). Static package checks do not establish
native runtime behaviour.

## Codex

Install (see [installation](docs/installation.md)):

```sh
mkdir -p ~/.agents/skills
ln -s /absolute/path/crewbook ~/.agents/skills/crewbook
```

Inspect an existing destination before replacing it. Restart Codex or open a new session. Then, in your target repository:

```sh
codex -m gpt-6.1-sol -c model_reasoning_effort="low" -c agents.max_concurrent_threads_per_session=8 '$crewbook'
```

Keep the single quotes so the shell passes `$crewbook` literally. Add a task to
the same message, for example: `$crewbook Fix the failing date-format test, run
the relevant checks, and explain what changed.`

What the repo files show:

- `agents/openai.yaml` sets the display name, a default prompt and
  `allow_implicit_invocation: true`, so ordinary requests can select CrewBook
  without `$crewbook`.
- `.agents/` holds the role files (`crewbook-desk.md`, `crewbook-code.md`,
  `crewbook-review.md` and others) and the optional `$crewbook-desk` alias skill
  in `.agents/skills/crewbook-desk`, installed separately.
- Unverified: installed native startup, the alias discovery and managed
  execution. A desk/dispatch delegation was observed once in a Codex session;
  merged mode, the default, has no observed trace in any client.

## Claude Code

CrewBook documents `$` for Codex only; for Claude the packaged entrypoint is the slash command
`/crewbook-desk`. Registration is a proposal, not a proven installation
([details](docs/installation.md#claude-code-registration-unverified)):

```sh
mkdir -p ~/.claude/agents ~/.claude/commands
ln -s /absolute/path/crewbook/.claude/agents/crewbook-*.md ~/.claude/agents/
ln -s /absolute/path/crewbook/.claude/commands/crewbook-*.md ~/.claude/commands/
```

The guide also links the skill at `~/.claude/skills/crewbook` (also unverified).
Then, in your target repository:

```sh
CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=8 CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2 claude --model sonnet '/crewbook-desk'
```

The variables set subagent concurrency and nesting depth (documented in the
installation guide, not measured; split mode needs depth 3).

What the repo files show:

- `.claude/commands/` holds the slash commands (`crewbook-desk`,
  `crewbook-review`, `crewbook-code`, `crewbook-docs`, `crewbook-ui`, `crewbook-release` and others);
  `.claude/agents/` holds the role profiles (worker, reviewer, dispatch and
  others).
- Shipping these files does not register them. Whether Claude lists them, and
  whether relative links in them resolve from `~/.claude`, is unverified.
- `$crewbook` is documented for Codex only; its use in Claude is not claimed.

## Read more

| Need | Read |
| --- | --- |
| Skill behaviour and role selection | [SKILL.md](SKILL.md) |
| Installation, updates, client support | [docs/installation.md](docs/installation.md) |
| Team roles, review and handoffs | [docs/team.md](docs/team.md) |
| Project setup | [docs/project-config.md](docs/project-config.md) |
| Instructions, trust, permissions | [docs/policy-composition.md](docs/policy-composition.md) |
| Maintenance commands and tests | [tools/README.md](https://github.com/wstein/crewbook/blob/main/tools/README.md) |
| Antigravity (`agy`): no approved entrypoint | [docs/antigravity.md](docs/antigravity.md) |

Contributing: [CONTRIBUTING.md](https://github.com/wstein/crewbook/blob/main/CONTRIBUTING.md), [code of conduct](https://github.com/wstein/crewbook/blob/main/.github/CODE_OF_CONDUCT.md). Licence: EUPL-1.2
([LICENSE](LICENSE)); imported from historical WorkHarbor source, see
[PROVENANCE.md](PROVENANCE.md).
