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

Run it as a background shell command (for example Bash with
`run_in_background`), not in the foreground:

```sh
WATCH_REPOS="owner/one owner/two" bash <path>/scripts/pr-watch/pr-watch.sh --until-event
```

`WATCH_REPOS` is space-separated `owner/name`; unset, it watches the repository
of the current directory. The first poll records a silent baseline. The command
exits 0 right after the first actionable event and prints one line per event:

```text
EVT <seq> <repo>#<n> <sha8> <kind> | <detail>
```

Modes: `--until-event` (this skill's default), `--stream` (print every event,
never exit; for a monitor or relay), `--snapshot` (one line per open PR, then
exit).

## Event kinds

Actionable (they end an `--until-event` run):

- `checks-green` with `READY-CANDIDATE` (draft PR based on `main`) or `READY` (non-draft) in the detail: review or merge decision point.
- `checks-red` unless the class is `stack-merge-shape`. Classes: `real-failure`
  (a test failed), `flake-infra` (runner or network trouble; usually rerun),
  `unknown` (needs a look).
- `conflict` with `READY-PR` (a non-draft PR has a merge conflict).
- `merged` (the detail lists other open PRs to check for restack), `new-pr`,
  `closed`.

Reported but not ending the run: `ready-changed`, `head-changed`,
`conflict-cleared`, other `checks-*` transitions, a `checks-red` classed
`stack-merge-shape` (expected for stacked PRs; resolves when the parent
merges). `watch idle-timeout` and `watch stopped` end the run and mean the
watcher is no longer running.

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

Restart rule: after handling an event, start the same `--until-event` command
again. State persists, so nothing already reported is repeated. Never act twice
on the same `id` or `seq`.

## Liveness, stop, idle

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

## Helper rule

The coordinator does not read raw CI logs. The script already classifies a red
check as `stack-merge-shape`, `real-failure`, `flake-infra` or `unknown` and puts
the first failing test or error line in the detail. When deeper triage is
needed, hand it to a cheapest-tier helper (for example Haiku) on demand, naming
the PR, sha and run; the helper reports only what is new beyond the event detail.
