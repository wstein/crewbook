# Crew Book

Crew Book helps a coding agent work through software tasks: understand the
request, make a focused change, check it, and explain the result. It supplies
reusable guidance for coding, review, documentation and verification, plus a
coordinated workflow for larger tasks with authors and independent reviewers.

The package and skill are named `crewbook`; invoke the skill as `$crewbook`.
It contains text and metadata. Your agent client supplies the tools, and your
repository instructions and authorization govern the work.

## Install in Codex

From a local source checkout, link the skill into your user skill directory:

```sh
mkdir -p ~/.agents/skills
ln -s /absolute/path/crewbook ~/.agents/skills/crewbook
```

Inspect an existing destination before replacing it. Keep one installation;
an existing legacy `cb-crewbook` link can continue to serve that purpose.
Restart Codex or open a new session to refresh skill discovery.
See [installation and client support](docs/installation.md) for fixed copies,
updates, uninstalling, Claude Code entrypoints and the optional `$crewbook-desk` alias.

## Try a first task

Open your target repository in Codex and ask for a concrete change, for example:

> Fix the failing date-format test, run the relevant checks, and explain what changed.

Crew Book can apply automatically to ordinary repository work. This uses the
current session and your project's instructions; it does not start desk or a
dispatcher. You do not need a board, container or full team setup.

To start the coordinated workflow explicitly, enter:

```text
$crewbook
```

This starts **crewbook/desk**: desk stays your point of contact and starts or
reuses one persistent dispatcher to organize assignments and reviews. Add your
task to the same message, or give it next. A bare invocation starts desk; it is
not a load-only command. Startup requires the client's subagent and resume
support, and reports any actual tool limits. It does not create a background daemon.

## Start Codex with desk

From the target repository, with the skill installed and model available:

```sh
codex -m gpt-6.1-sol -c model_reasoning_effort="low" -c agents.max_concurrent_threads_per_session=8 '$crewbook'
```

Keep the single quotes so the shell passes `$crewbook` literally. Eight is the
recommended **subagent capacity**, excluding desk; it is a ceiling, not a
request to start eight agents. Crew Book permits up to two authors and two
independent reviewers within the host's actual capacity. Desk and dispatch use
`gpt-6.1-sol` with low reasoning effort in Codex.

The requested role mappings are Sonnet → `gpt-6.1-sol`/low,
Opus → `gpt-6.1-sol`/medium and Haiku → `gpt-6-luna`/medium.
See [client support and model mappings](docs/installation.md#entrypoints-and-support)
for the full table and availability limits, and the
[team manual](docs/team.md#dynamic-agent-allocation) for allocation and context lifetimes.
These settings and static package checks do not establish native runtime behavior.

## Clients

- **Codex:** use `$crewbook`; `$crewbook-desk` is an optional separately installed
  alias. Desk/dispatch delegation has been observed in a Codex session;
  installed native startup and managed execution remain unverified.
- **Claude Code:** `/crewbook-desk` and role wrappers are packaged, but the client
  must register/load them. Native loading and external-mount discovery remain
  unverified; shipping the files does not register commands automatically.
- **Antigravity (`agy`):** there is no approved production entrypoint or binding.
  See the [readiness matrix](docs/antigravity.md) for evidence and admission
  requirements; full support is not established.

See [installation and client support](docs/installation.md) for entrypoints,
requested [model mappings](docs/installation.md#entrypoints-and-support) and
[role selection](SKILL.md#specialized-workflows).

## Find the details

| Need | Read |
| --- | --- |
| Skill behavior and role selection | [Skill entrypoint](SKILL.md) |
| Installation, updates and client support | [Installation guide](docs/installation.md) |
| Team roles, independent review and handoffs | [Team manual](docs/team.md) |
| Local or managed project setup | [Project configuration](docs/project-config.md) |
| Instructions, trust and permissions | [Policy composition](docs/policy-composition.md) |
| Git integration and review evidence | [Git history guidance](docs/git-history.md) |
| Package manifest, exports and runtime pins | [Distribution contract](docs/distribution.md) |
| Source maintenance commands and tests | [Maintenance guide](tools/README.md) |
| Antigravity support limits | [Readiness matrix](docs/antigravity.md) |

Crew Book is intended to be workharbor's default replaceable skill set,
installed outside work repositories. Workharbor production runtime integration
still awaits a supported binding; the [distribution contract](docs/distribution.md)
records that boundary. Generic native-session use does not require that integration.

## Contributing

For source changes, issues and pull requests, see the
[contributor guide](https://github.com/wstein/crewbook/blob/main/CONTRIBUTING.md).
It links the source checks, review process and private security reporting route.

## Licence and provenance

This EUPL-1.2 package was imported from
[historical workharbor source](https://github.com/wstein/workharbor/tree/c6bbb7bcd903ea3027285baa9237f4ad179a9bb7).
[PROVENANCE.md](PROVENANCE.md) records the original import and later transformations.
[LICENSE](LICENSE) retains EUPL-1.2 and its existing notices. Keep the licence,
provenance and attribution when redistributing or updating; do not relabel
imported material as newly authored. New package documentation uses the same licence.
