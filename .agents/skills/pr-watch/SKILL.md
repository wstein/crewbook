---
name: pr-watch
description: Watch open pull requests of one or more repositories without spending tokens; a script polls GitHub, classifies events and exits on the first actionable one so the agent restarts it instead of polling by sleeping.
---

# PR watch

Use this when work depends on pull request state (checks turning green or
red, a PR becoming mergeable, conflicts, merges, new or closed PRs) and you
would otherwise poll. Never poll by sleeping or by repeated `gh` calls; the
script does the polling and costs no model tokens while it waits. It makes
read-only `gh` calls only.

Script: [pr-watch.sh](../../../scripts/pr-watch/pr-watch.sh). It needs `bash`,
`gh` (authenticated) and `jq`. Run it with `bash`.

## Start

Two supported run patterns. Both print one line per event:

```text
EVT <seq> <repo>#<n> <sha8> <kind> | <detail>
```

`WATCH_REPOS` is space-separated `owner/name`; unset, it watches the repository
of the current directory. The first poll records a silent baseline.

**(a) Recommended: `--stream --actionable-only` under a persistent Monitor.**

```sh
WATCH_REPOS="owner/one owner/two" bash <path>/scripts/pr-watch/pr-watch.sh --stream --actionable-only
```

Only actionable events reach stdout (every event still goes to the report), and
the process keeps running, so each stdout line wakes the coordinator without
ending the watcher. The Monitor tool has its own maximum lifetime: re-arm it
when it expires (one expiry notice per period). Trade-off: depends on the host
having a persistent monitor.

**(b) `--until-event` as a background command** (for example Bash with
`run_in_background`):

```sh
WATCH_REPOS="owner/one owner/two" bash <path>/scripts/pr-watch/pr-watch.sh --until-event
```

It exits 0 right after the first actionable event and wakes the coordinator
only by exiting; its last stdout line is `restart: bash <script> --until-event`.
The coordinator MUST restart it in the same turn, or events go unseen. A
self-restarting wrapper loop is useless: a background command wakes the
coordinator only when it exits. Trade-off: works anywhere, but every event costs
a restart and "forgot to restart" is the failure mode.

Other modes: `--stream` (every event, never exits) and `--snapshot` (one line
per open PR, then exit).

## Event kinds

| Kind | Actionable (ends `--until-event`) | Notes |
| --- | --- | --- |
| `checks-green` | yes, if the detail has `READY-CANDIDATE` (draft PR based on `main`) or `READY` (non-draft) | review or merge decision point |
| `checks-red` | yes, unless class `stack-merge-shape` | classes: `real-failure` (a test failed), `flake-infra` (runner or network trouble; usually rerun), `unknown` (needs a look), `stack-merge-shape` (expected for stacked PRs; resolves when the parent merges) |
| `conflict` | yes, for draft and ready PRs (`READY-PR` in the detail marks a ready one) | `WATCH_QUIET_CONFLICT_DRAFT=1` makes a draft conflict non-actionable |
| `merged` | yes | the detail lists other open PRs to check for restack |
| `closed` | yes | closed without merge |
| `new-pr` | yes, unless quiet | `WATCH_QUIET_NEW` (space-separated head-branch prefixes and/or `author:<login>`, default empty) marks matching new PRs `class: quiet`: logged, not actionable |
| `conflict-cleared`, `ready-changed`, `head-changed`, other `checks-*` | no | reported only |

`watch idle-timeout` and `watch stopped` end the run and mean the watcher is
no longer running.

Check transitions are debounced: a state must hold for two consecutive polls,
so brief flaps produce nothing. Each event id (repo, PR, sha, kind, class) is
emitted once, across restarts.

## Read events, restart

Everything is in the state directory (`WATCH_STATE_DIR`, default
`${XDG_STATE_HOME:-$HOME/.local/state}/pr-watch`, never inside a checkout).
The event log is `watch-report.jsonl` there (`WATCH_REPORT` overrides): one JSON
object per line with `seq,t,repo,pr,sha,kind,detail,class,id`. Remember the last
`seq` you handled and read only newer events:

```sh
jq -c 'select(.seq > N)' "$STATE/watch-report.jsonl"
```

Restart rule (pattern b): after handling an event, start the same `--until-event` command
again. State persists, so nothing already reported is repeated. Never act twice
on the same `id` or `seq`.

## Liveness, stop, idle

- One instance per state directory: a second start exits 3 and names the
  running pid. A stale lock (pid gone, or not a pr-watch process) is taken over
  and logged as `lock-takeover`. `--snapshot` and `WATCH_ONCE=1` runs take no
  lock.
- Liveness: the file `alive` in the state directory holds the time of the last
  poll; a stale timestamp (several `WATCH_INTERVAL`s old, default 60 s) means the
  process is gone, so restart it.
- Stop: create a file named `STOP` in the state directory (the run records
  `stopped` and exits), or kill the process (it records `stopped` on TERM/INT).
  Remove `STOP` before the next start.
- Idle timeout: with no actionable event for `WATCH_MAX_IDLE_HOURS` (default 8)
  it reports `idle-timeout` and exits; restart if the watch is still wanted.
- Other knobs: `WATCH_INTERVAL` (seconds between polls, default 60),
  `WATCH_ONCE=1` (one poll, then exit).

## Waiting for a run

A cheap helper agent returns when its turn ends and cannot be woken by its own
background monitor. Never ask a helper to wait for a CI run or workflow to
finish. Start a background shell command that waits (an until-loop with `sleep`)
and prints one result line per job, and hand the finished run to the helper for
log triage.

## Helper rule

The coordinator does not read raw CI logs. The script already classifies a red
check as `stack-merge-shape`, `real-failure`, `flake-infra` or `unknown` and puts
the first failing test or error line in the detail. When deeper triage is
needed, hand it to a cheapest-tier helper (for example Haiku) on demand, naming
the PR, sha and run; the helper reports only what is new beyond the event detail.
