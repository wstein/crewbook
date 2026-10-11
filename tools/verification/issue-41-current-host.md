# Issue #41: bounded current-host native evidence

> **Historical evidence, not a current claim.** This file documents the host state and source revision of 2026-10-11 (source `897483f26b901521875d1d469c682ddafc8eb6bb`). That revision is behind current `main`, and the quoted commit hashes are not ancestors of it; later changes may have altered the sources, procedures and host this file describes. Re-measure before relying on it. The evidence below is preserved unchanged.

Measured 2026-10-11 against source base
`897483f26b901521875d1d469c682ddafc8eb6bb`. This maintenance-only record
supplements [issue #41](https://github.com/wstein/crewbook/issues/41);
it does not change the distributed instructions or their unverified claims.
The authorized reference is this interactive host session, not every Codex
installation. No builds, installations, logins or publication were performed.

## Setup and identity boundary

The host supplies collaboration tools, a 17-agent concurrency ceiling, and
workspace-write execution with automatic escalation review. The ceiling is tool
metadata, not a saturation measurement or a count of currently free slots.
The session assignment permits four authors and three independent reviewers;
this probe adds only one bounded read-only helper. Before spawning, `df -Pk .`
exited 0 and reported 841627288 KiB available. No build cache was used or changed.

The author was assigned `gpt-6.1-sol`, medium; the fresh helper spawn explicitly
requested `gpt-6.1-sol`, low, with `fork_turns="none"`, following the
[helper mapping](../../README.md). The spawn returned a child handle. The
returned metadata did not independently attest the serving model or effort;
the requested values are observable, actual model enforcement is unverified.
Tool provenance and exact app/client-host version are not exposed by the
available collaboration metadata. Installed CLI versions below are separate
observations, not identification of the app hosting these tools.

Commands ran in the assigned source worktree. Platform/version command output
was:

```text
$ uname -srm                         [exit 0]
Linux 7.0.14-orbstack-00380-ga7e0a2dc9535 aarch64
$ python3 --version                  [exit 0]
Python 3.13.5
$ codex --version                    [exit 0]
codex-cli 0.162.1
$ claude --version                   [exit 0]
2.1.296 (Claude Code)
$ agy --version                      [exit 0]
1.3.3
```

`codex --help` exited 0 and advertised `-m/--model`, `-c/--config`,
`-s/--sandbox`, `resume` and other CLI operations. Only version/help were run;
these options do not establish native nested-session or discovery behavior.
No attribution of the `agy` wrapper's implementation or vendor was inferred.

Known-entrypoint metadata was inspected with Python `shutil.which`,
`Path.is_symlink` and `Path.resolve`, emitting only categories:

| Entrypoint | Present | Symlink | Resolved category |
| --- | --- | --- | --- |
| `codex` | yes | no | existing file |
| `claude` | yes | no | existing file |
| `agy` | yes | no | existing file |
| `antigravity` | no | unavailable | absent |
| Installed `crewbook` skill root | yes | yes | directory, distinct from assigned source root |

Resolved private paths, agent handles and credential data are intentionally
absent. No credential stores or client configuration files were inspected.

## Native collaboration trace

This is one bounded trial, not an efficiency benchmark. The existing split
chain was desk (depth 0), dispatcher (1), this verification author (2).
The author's `spawn_agent` created exactly one fresh helper (3). No additional
helpers, recursive issue workers or saturation attempts were started.

| Step | Native operation and sanitized result |
| --- | --- |
| Start | `spawn_agent` requested the explicit helper model/effort and fresh context; returned one child handle. |
| Link read | Helper read `AGENTS.md`, `SKILL.md`, `.agents/crewbook-helper.md`, then `docs/policy-composition.md` relative to `SKILL.md`; read command exited 0 after reviewed escalation. |
| Child response | `CB41-NONCE-A-20261011`; `relative_link=docs/policy-composition.md`; `first_heading=# Policy composition contract`. |
| Message | Author used `send_message` to that same child with `CB41-MESSAGE-B-20261011`; child final response was exactly `CB41-MESSAGE-B-20261011`. |
| Followup | After that completion, author used `followup_task` on the same handle; child final response contained `CB41-FOLLOWUP-C-20261011` and retained original `CB41-NONCE-A-20261011`. |

Native child messages and completions reached the nested author. This proves
one nested parent's ability to create, message and resume its own child here.
It contradicts a universal claim that only the primary chat can communicate
with subchats, but does not establish support in other hosts or clients.
It does not test merged desk re-entry into the primary session.

Separately, a read-only Python check resolved
`docs/policy-composition.md` from the known installed skill symlink, exited 0
and emitted:

```text
installed_entrypoint=readable
relative_link=docs/policy-composition.md
target_category=regular-file
first_heading=# Policy composition contract
```

This measures filesystem link resolution, not `$crewbook` discovery, alias
registration, native skill loading, or Claude symlink behavior.

## Execution and write boundary

The author's default `pwd` and file-discovery commands failed before command
execution, exit 1:

```text
bwrap: Can't mount proc on /proc: Operation not permitted
```

The helper independently observed the same default `pwd` failure. Its single
reviewed `require_escalated` read command exited 0. Author metadata/read/check
commands also used reviewed escalation after the initial failure.
These results establish an unavailable default execution sandbox and successful
approved operations outside that failing path. They do not measure a native
filesystem write denial, unrestricted sandbox access or permission enforcement.
The optional unique Git-common-directory write probe was skipped. No registry
file, Git control file or other agent's scratch file was touched by a probe.
Ordinary authoring/commit operations for this record are not sandbox benchmarks.

## Per-client acceptance matrix

“Unverified” means no successful native measurement of that criterion. CLI
presence or help output does not upgrade that status.

| Issue #41 criterion | Current Codex tool host | Claude | Antigravity |
| --- | --- | --- | --- |
| Exact host version | Unavailable; installed CLI version above is separate | Native host unverified; installed CLI metadata only | Native host unverified; wrapper metadata only |
| Merged-mode child completion re-entry to primary | Unverified; split nested-author completion observed only | Unverified | Unverified |
| Relative links inside subagents | Measured once by fresh helper, with approved read | Unverified | Unverified |
| Relative links through installed symlink | Filesystem read measured; native loading unverified | `~/.claude` resolution unverified | Unverified |
| Command frontmatter/model pinning | Actual model propagation/enforcement unverified | Desk-on-Sonnet pinning unverified | Unverified |
| Spawn depth 2/3 by mode | Split chain reached depth 3; mode-specific limits and merged depth 2 unverified | Unverified | Unverified |
| Same child resumable | Same completed handle followup measured once | Unverified | Unverified |
| Subagent talks to its own subagents | Nested author message/followup measured once | Unverified | Unverified |
| `.git` main/worktree/common-directory sandbox writes | Unverified; default runner failed before execution; optional write probe skipped | Unverified | Unverified |
| `--setting-sources ""` suppression of project agents | Not tested; unverified where applicable | Unverified | Unverified |
| `$crewbook` / `$crewbook-desk` discovery and native entrypoints | Unverified; metadata/root resolution only | Unverified | No approved entrypoint tested; unverified |
| SDK/settings/runtime enforcement | Unverified | Unverified | Unverified |
| Behavior or efficiency benchmark | Not performed; no matched with/without trials | Not performed | Not performed |

The measured subset is partial evidence for #41, not issue completion or
independent review clearance. Missing verification is not a successful fix.
Further native sessions require separately authorized reference setups; no
installation, subscription automation or legal conclusion follows from this record.

## Source verification

This is prose evidence only, so no executable behavior or prompt parser test
was added. Existing maintenance checks, package integrity, local links and the
existing pinned Gitleaks 8.30.1 scanner are the applicable checks. Their exact
results are recorded in the author handoff for the candidate revision.
