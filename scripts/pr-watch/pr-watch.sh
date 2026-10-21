#!/usr/bin/env bash
# pr-watch.sh - PR watcher that does the thinking; a relay only forwards its EVT lines.
# Usage: bash pr-watch.sh [--snapshot | --stream | --until-event]
#   --stream (default): print every EVT, never exit (Monitor use).
#   --until-event: exit 0 right after the first actionable EVT (checks-green READY-CANDIDATE/READY, checks-red
#     except stack-merge-shape, conflict READY-PR, merged, new-pr, closed); other transitions
#     are printed and reported but do not end the run. Restart repeats nothing (persistent state).
#   --snapshot: print one line per open PR and exit.
#   Event log: <report> (JSON Lines, append-only); dedupe: <state>/emitted.jsonl.
#   Each poll writes an ISO time to <state>/alive. File <state>/STOP ends the loop. WATCH_MAX_IDLE_HOURS (default 8)
#   or WATCH_MAX_IDLE_SECONDS (test hook) ends it after that long without an actionable event.
# Repositories: WATCH_REPOS (space separated owner/name). If unset, the repository of the current
#   directory (`gh repo view --json nameWithOwner`).
# Env: WATCH_REPOS, WATCH_INTERVAL (s, default 60), WATCH_ONCE=1 (one poll, exit),
#      WATCH_MAX_IDLE_HOURS (default 8),
#      WATCH_STATE_DIR (default ${XDG_STATE_HOME:-$HOME/.local/state}/pr-watch, outside any checkout),
#      WATCH_REPORT (default <state dir>/watch-report.jsonl)
# Single instance: a second run on the same state dir exits 3 naming the running pid; a stale lock (pid gone or not a
#   pr-watch process) is taken over. --snapshot and WATCH_ONCE=1 never take the lock.
# WATCH_QUIET_NEW: space separated head-branch prefixes and/or author:<login>; a matching new-pr is logged but not actionable.
# WATCH_QUIET_CONFLICT_DRAFT=1: a conflict on a draft PR is not actionable.
# Actionable (ends --until-event): checks-green with READY-CANDIDATE/READY; checks-red unless stack-merge-shape;
#   conflict (draft or ready); merged; closed; new-pr unless quiet. Never: conflict-cleared, ready-changed, head-changed,
#   other checks transitions.
# Read-only gh calls only. Per poll: one `gh pr list` per repo (+ extra calls only on a transition to red / a vanished PR).
export GH_PROMPT_DISABLED=1
REPOS=${WATCH_REPOS:-}
if [ -z "$REPOS" ]; then
  REPOS=$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null) || REPOS=
  if [ -z "$REPOS" ]; then
    echo "pr-watch: set WATCH_REPOS (space separated owner/name) or run inside a GitHub repository checkout" >&2
    exit 2
  fi
fi
STATE=${WATCH_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/pr-watch}
REPORT=${WATCH_REPORT:-$STATE/watch-report.jsonl}
INTERVAL=${WATCH_INTERVAL:-60}
SNAPSHOT=0
MODE=stream
case "${1:-}" in
  --snapshot) SNAPSHOT=1 ;;
  --until-event) MODE=until ;;
  --stream|"") ;;
  *) echo "usage: pr-watch.sh [--snapshot|--stream|--until-event]" >&2; exit 2 ;;
esac
MAX_IDLE=${WATCH_MAX_IDLE_SECONDS:-$(awk -v h="${WATCH_MAX_IDLE_HOURS:-8}" 'BEGIN{printf "%d", h*3600}')}
ACTIONABLE=0
LAST_ACTION=$(date +%s)

mkdir -p "$STATE/cache" "$(dirname "$REPORT")" || exit 1
TMP=$(mktemp -d "$STATE/tmp.XXXXXX") || exit 1
LOCK=$STATE/lock
HAVE_LOCK=0
cleanup() {
  rm -rf "$TMP"
  if [ "$HAVE_LOCK" = 1 ]; then rm -rf "$LOCK"; fi
}
trap cleanup EXIT
trap 'report_note stopped "signal received"; exit 0' TERM INT
IDS=$STATE/emitted.jsonl
SEQF=$STATE/seq
touch "$IDS"
[ -f "$SEQF" ] || echo 0 > "$SEQF"
touch "$REPORT"

JQ_DEFS='
def cls:
  (. // []) as $c
  | ($c | map(select(((.conclusion // "") | IN("FAILURE","CANCELLED","TIMED_OUT","ACTION_REQUIRED","STARTUP_FAILURE")) or ((.state // "") | IN("FAILURE","ERROR")))) | length) as $f
  | ($c | map(select(((.status // "COMPLETED") != "COMPLETED") or ((.state // "") | IN("PENDING","EXPECTED")))) | length) as $p
  | if $f > 0 then "red" elif $p > 0 then "pending" elif ($c | length) > 0 then "green" else "none" end;
'

JQ_POLL=$JQ_DEFS'
def norm($p; $prev): {
  title: (($p.title // "") | gsub("[\n\r\t]"; " ")),
  draft: $p.isDraft,
  conflict: (if $p.mergeable == "CONFLICTING" then true elif $p.mergeable == "MERGEABLE" then false
             elif $prev != null then $prev.conflict else false end),
  sha: ($p.headRefOid[0:8]), full: $p.headRefOid, head: ($p.headRefName // ""), author: (($p.author.login) // ""), base: $p.baseRefName, checks: ($p.statusCheckRollup | cls) };
def cmpk: del(.title, .full, .head, .author);
def trans($c; $n; $k): ($n + {n: ($k | tonumber)}) as $b | [
  (if $c.draft != $n.draft then $b + {kind: "ready-changed", to: (if $n.draft then "draft" else "ready" end)} else empty end),
  (if $c.conflict != $n.conflict then $b + {kind: (if $n.conflict then "conflict" else "conflict-cleared" end)} else empty end),
  (if $c.sha != $n.sha then $b + {kind: "head-changed", old: $c.sha} else empty end),
  (if $c.checks != $n.checks then
     (if $c.checks == "green" then $b + {kind: "_leave", what: "green", sha: $c.sha} else empty end),
     (if $c.checks == "red" then $b + {kind: "_leave", what: "red", sha: $c.sha} else empty end),
     (if $n.checks == "green" then $b + {kind: "checks-green"} elif $n.checks == "red" then $b + {kind: "checks-red"} else empty end)
   else empty end) ];
($old[0].prs // {}) as $op
| (reduce $new[0][] as $p ({}; ($p.number | tostring) as $k | ($op[$k] // null) as $o
    | .[$k] = norm($p; (if $o == null then null elif $o.cand != null then $o.cand else $o.cur end)))) as $obs
| (reduce ($obs | keys[]) as $k ({prs: {}, events: []};
    $obs[$k] as $n | ($op[$k] // null) as $o
    | if $base == 1 then .prs[$k] = {cur: $n, cand: null}
      elif $o == null then .prs[$k] = {cur: $n, cand: null} | .events += [$n + {n: ($k | tonumber), kind: "new-pr"}]
      elif ($n | cmpk) == ($o.cur | cmpk) then .prs[$k] = {cur: $n, cand: null}
      elif $o.cand != null and ($o.cand | cmpk) == ($n | cmpk) then .prs[$k] = {cur: $n, cand: null} | .events += trans($o.cur; $n; $k)
      else .prs[$k] = {cur: $o.cur, cand: $n}
      end)) as $r
| ($op | with_entries(select($obs[.key] == null))) as $gone
| {state: {prs: ($r.prs + $gone)}, events: $r.events,
   gone: [$gone | to_entries[] | {n: (.key | tonumber), sha: .value.cur.sha}],
   open: ($obs | keys | map(tonumber))}
'

sha8() { printf '%s' "${1:0:8}"; }

# ---- emission -------------------------------------------------------------
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

jappend() { # jappend <file> <compact json>: one complete line per append; heal a truncated last line first
  if [ -s "$1" ] && [ -n "$(tail -c1 "$1")" ]; then printf '\n' >> "$1"; fi
  printf '%s\n' "$2" >> "$1"
}

next_seq() { NSEQ=$(( $(cat "$SEQF") + 1 )); echo "$NSEQ" > "$SEQF.new" && mv "$SEQF.new" "$SEQF"; }

# emitted.jsonl is the single dedupe source: {"id":..,"seq":..} adds, {"drop":prefix,"seq":..} tombstones.
drop_ids() { # drop_ids <prefix>: forget ids starting with prefix (state returned to something else)
  jappend "$IDS" "$(jq -cn --arg p "$1" --argjson s "$(cat "$SEQF")" '{drop: $p, seq: $s}')"
}

id_seen() { # id_seen <id>; truncated or garbage lines are ignored
  jq -Rne --arg id "$1" 'reduce (inputs | fromjson? | objects) as $o ({};
      if $o.drop != null then with_entries(select(.key | startswith($o.drop) | not))
      elif $o.id != null then .[$o.id] = 1 else . end) | has($id)' "$IDS" > /dev/null 2>&1
}

rlog() { # rlog seq repo pr sha kind class detail id
  jappend "$REPORT" "$(jq -cn --argjson seq "$1" --arg t "$(now)" --arg repo "$2" --argjson pr "$3" --arg sha "$4" \
    --arg kind "$5" --arg class "$6" --arg detail "$7" --arg id "$8" \
    '{seq: $seq, t: $t, repo: $repo, pr: $pr, sha: $sha, kind: $kind, detail: $detail, class: $class, id: $id}')"
}

report_note() { # report_note kind detail: report only (no stdout)
  next_seq
  rlog "$NSEQ" "" 0 "" "$1" "" "$2" ":0:$1:"
}

meta() { # meta kind detail: printed + reported watch line with the next seq
  next_seq
  printf 'EVT %s watch %s | %s\n' "$NSEQ" "$1" "$2"
  rlog "$NSEQ" "" 0 "" "$1" "" "$2" ":0:$1:"
}

quiet_new() { # quiet_new <head branch> <author>: matches WATCH_QUIET_NEW (head-branch prefixes and/or author:<login>)
  local t
  for t in ${WATCH_QUIET_NEW:-}; do
    case $t in
      author:*) [ "$2" = "${t#author:}" ] && return 0 ;;
      *) case $1 in "$t"*) return 0;; esac ;;
    esac
  done
  return 1
}

is_actionable() { # is_actionable kind cls detail
  case $1 in
    checks-green) case $3 in *READY-CANDIDATE*|*READY) return 0;; esac; return 1 ;;
    checks-red) [ "$2" != stack-merge-shape ] ;;
    conflict) case $3 in *READY-PR*) return 0;; esac; [ "${WATCH_QUIET_CONFLICT_DRAFT:-0}" != 1 ] ;;
    new-pr) [ "$2" != quiet ] ;;
    merged|closed) return 0 ;;
    *) return 1 ;;
  esac
}

emit() { # emit repo n sha kind class detail
  local repo=$1 n=$2 sha=$3 kind=$4 cls=$5 detail=$6 id pre
  id="$repo#$n:$sha:$kind:$cls"; pre="$repo#$n:$sha:"
  case $kind in
    conflict) drop_ids "${pre}conflict-cleared:" ;;
    conflict-cleared) drop_ids "${pre}conflict:" ;;
    ready-changed) drop_ids "${pre}ready-changed:" ;;
  esac
  if id_seen "$id"; then return; fi
  next_seq
  jappend "$IDS" "$(jq -cn --arg id "$id" --argjson s "$NSEQ" '{id: $id, seq: $s}')"
  printf 'EVT %s %s#%s %s %s | %s\n' "$NSEQ" "$repo" "$n" "$sha" "$kind" "$detail"
  rlog "$NSEQ" "$repo" "$n" "$sha" "$kind" "$cls" "$detail" "$id"
  if is_actionable "$kind" "$cls" "$detail"; then ACTIONABLE=1; LAST_ACTION=$(date +%s); fi
}

# ---- red-check classification --------------------------------------------
rank() { case $1 in real-failure) echo 4;; unknown) echo 3;; flake-infra) echo 2;; *) echo 1;; esac; }

classify_file() { # classify_file <cleaned log> -> "class<TAB>detail"
  # Cleaned log: ANSI and the leading timestamp removed; a genuine runner annotation starts the line with @@ANNOT@@
  # (it had "<timestamp> ##[error]"); echoed log lines (a second timestamp) are dropped, see clean_log.
  local f=$1 name err
  local real='--- FAIL: |^FAIL[[:space:]]|^FAIL: |^ERROR: test|^not ok |make: \*\*\*|Traceback \(most recent call last\)|AssertionError'
  if grep -Eq 'Unexpected synthetic merge parents|PR must target repository main' "$f"; then
    printf 'stack-merge-shape\t%s\n' "$(grep -Em1 'Unexpected synthetic merge parents|PR must target repository main' "$f" | cut -c1-200)"
    return
  fi
  if grep -Eq -- "$real" "$f"; then
    name=$(grep -Eom1 -- '--- FAIL: [^ ]+' "$f" | sed 's/--- FAIL: //')
    [ -n "$name" ] || name=$(grep -Em1 -- '^(FAIL|ERROR): [^ ]+' "$f" | awk '{print $2}')
    [ -n "$name" ] || name=$(grep -Em1 -- '^not ok [0-9]+' "$f" | sed 's/^not ok [0-9]*[ -]*//')
    [ -n "$name" ] || name=$(grep -Em1 -- 'make: \*\*\* ' "$f" | sed 's/^.*make: \*\*\* //')
    [ -n "$name" ] || name=$(grep -Em1 '^FAIL[[:space:]]' "$f" | awk '{print $2}')
    err=$(grep -Em1 -- '_test\.go:[0-9]+|Error:|AssertionError|panic:' "$f")
    [ -n "$err" ] || err=$(grep -Em1 -- "$real" "$f")
    printf 'real-failure\t%s\n' "$(printf 'first=%s err=%s' "$name" "$(printf '%s' "$err" | sed 's/^[[:space:]]*//')" | cut -c1-200)"
    return
  fi
  if grep -Eq 'The runner has received a shutdown signal|The operation was canceled|No space left on device|HTTP/[0-9.]+ 5[0-9][0-9]|returned error: 5[0-9][0-9]|HTTP (error )?5[0-9][0-9]|status code:? 5[0-9][0-9]' "$f"; then
    printf 'flake-infra\t%s\n' "$(grep -Em1 'The runner has received a shutdown signal|The operation was canceled|No space left on device|5[0-9][0-9]' "$f" | cut -c1-200)"
    return
  fi
  err=$(grep -m1 '^@@ANNOT@@' "$f" | sed 's/^@@ANNOT@@/##[error]/')
  printf 'unknown\t%s\n' "$(printf '%s' "${err:-no ##[error] line in log}" | cut -c1-200)"
}

clean_log() { # stdin: raw job log -> stdout: portable (BSD and GNU sed) clean-up
  local esc
  esc=$(printf '\033')
  sed -e "s/${esc}\\[[0-9;]*m//g" \
      -e 's/^[0-9]\{4\}-[0-9-]*T[0-9:.]*Z ##\[error\]/@@ANNOT@@/' \
      -e '/^[0-9]\{4\}-[0-9-]*T[0-9:.]*Z [0-9]\{4\}-[0-9-]*T[0-9:.]*Z /d' \
      -e 's/^[0-9]\{4\}-[0-9-]*T[0-9:.]*Z //'
}

classify_run() { # classify_run repo sha runid -> best "class<TAB>detail" for the run (cached)
  local repo=$1 sha=$2 run=$3 cache jid log best="" cur c
  cache="$STATE/cache/${repo//\//_}_${sha}_${run}.tsv"
  if [ -s "$cache" ]; then cat "$cache"; return; fi
  for jid in $(gh run view "$run" -R "$repo" --json jobs 2>/dev/null |
      jq -r '.jobs[]? | select((.conclusion // "") | ascii_downcase | IN("failure","cancelled","timed_out","startup_failure","action_required")) | .databaseId'); do
    log=$TMP/job.log
    if gh api --allow-escape-sequences "repos/$repo/actions/jobs/$jid/logs" 2>/dev/null |
        clean_log > "$log" && [ -s "$log" ]; then
      cur=$(classify_file "$log")
    else
      cur=$(printf 'unknown\tlog unavailable for job %s' "$jid")
    fi
    c=${cur%%$'\t'*}
    if [ -z "$best" ] || [ "$(rank "$c")" -gt "$(rank "${best%%$'\t'*}")" ]; then best=$cur; fi
  done
  if [ -n "$best" ]; then printf '%s\n' "$best" | tee "$cache"; fi
}

classify_red() { # classify_red repo sha -> "class: detail"
  local repo=$1 sha=$2 run best="" cur c
  for run in $(gh run list -R "$repo" --commit "$sha" --json databaseId,conclusion,event 2>/dev/null |
      jq -r '.[]? | select((.conclusion // "") | ascii_downcase | IN("failure","cancelled","timed_out","startup_failure","action_required","")) | .databaseId'); do
    cur=$(classify_run "$repo" "$sha" "$run")
    [ -n "$cur" ] || continue
    c=${cur%%$'\t'*}
    if [ -z "$best" ] || [ "$(rank "$c")" -gt "$(rank "${best%%$'\t'*}")" ]; then best=$cur; fi
  done
  [ -n "$best" ] || best=$(printf 'unknown\tno failed workflow run found for %s' "$sha")
  printf '%s: %s' "${best%%$'\t'*}" "${best#*$'\t'}"
}

# ---- polling --------------------------------------------------------------
poll_repo() {
  local repo=$1 sf base=0 list res open
  sf=$STATE/${repo//\//_}.json
  list=$TMP/list.json
  gh pr list -R "$repo" --state open --limit 60 \
    --json number,title,isDraft,mergeable,mergeStateStatus,headRefOid,headRefName,author,baseRefName,statusCheckRollup > "$list" 2>/dev/null || return 0
  jq -e 'type == "array"' "$list" > /dev/null 2>&1 || return 0
  if [ -f "$sf" ]; then cp "$sf" "$TMP/old.json"; else echo '{}' > "$TMP/old.json"; base=1; fi
  res=$TMP/res.json
  jq -c -n --argjson base "$base" --slurpfile old "$TMP/old.json" --slurpfile new "$list" "$JQ_POLL" > "$res" || return 0
  open=$(jq -r '.open | map("#\(.)") | join(" ")' "$res")

  local kind n sha title draft pbase to old what full head author detail cls
  while IFS=$'\x1f' read -r kind n sha title draft pbase to old what full head author; do
    [ -n "$kind" ] || continue
    case $kind in
      _leave) drop_ids "$repo#$n:$sha:checks-$what:" ;;
      new-pr) cls=""; quiet_new "$head" "$author" && cls=quiet
        emit "$repo" "$n" "$sha" new-pr "$cls" "title=\"$title\" draft=$draft base=$pbase" ;;
      ready-changed) emit "$repo" "$n" "$sha" ready-changed "$to" "$([ "$to" = ready ] && echo draft'->'ready || echo ready'->'draft)" ;;
      conflict) detail="CONFLICTING base=$pbase"; [ "$draft" = false ] && detail="$detail READY-PR"; emit "$repo" "$n" "$sha" conflict "" "$detail" ;;
      conflict-cleared) detail="mergeable again"; [ "$draft" = false ] && detail="$detail READY-PR"; emit "$repo" "$n" "$sha" conflict-cleared "" "$detail" ;;
      head-changed) emit "$repo" "$n" "$sha" head-changed "" "$old->$sha" ;;
      checks-green)
        detail="all checks green"
        if [ "$draft" = true ] && [ "$pbase" = main ]; then detail="$detail READY-CANDIDATE"; fi
        if [ "$draft" = false ]; then detail="$detail READY"; fi
        emit "$repo" "$n" "$sha" checks-green "" "$detail" ;;
      checks-red)
        detail=$(classify_red "$repo" "${full:-$sha}"); cls=${detail%%:*}
        emit "$repo" "$n" "$sha" checks-red "$cls" "$detail" ;;
    esac
  done < <(jq -r '.events[] | [.kind, .n, .sha, .title, .draft, .base, (.to // ""), (.old // ""), (.what // ""), .full, (.head // ""), (.author // "")] | map(tostring) | join("\u001f")' "$res")

  # PRs no longer in the open list: merged or closed (immediate, no debounce)
  local gn gsha view st mc others
  while IFS=$'\t' read -r gn gsha; do
    [ -n "$gn" ] || continue
    view=$(gh pr view "$gn" -R "$repo" --json state,mergeCommit,mergedAt,baseRefName 2>/dev/null) || continue
    st=$(jq -r '.state // ""' <<< "$view")
    others=$(jq -r --argjson n "$gn" '.open - [$n] | map("#\(.)") | join(" ")' "$res")
    case $st in
      MERGED)
        mc=$(jq -r '(.mergeCommit.oid // "")[0:8]' <<< "$view")
        emit "$repo" "$gn" "$gsha" merged "" "merge=${mc:-unknown} base=$(jq -r '.baseRefName // ""' <<< "$view") at=$(jq -r '.mergedAt // ""' <<< "$view") check-restack: ${others:-none}" ;;
      CLOSED) emit "$repo" "$gn" "$gsha" closed "" "closed without merge" ;;
      *) continue ;;
    esac
    jq -c --arg k "$gn" 'del(.state.prs[$k])' "$res" > "$res.new" && mv "$res.new" "$res"
  done < <(jq -r '.gone[] | [.n, .sha] | @tsv' "$res")

  jq -c '.state' "$res" > "$sf.new" && mv "$sf.new" "$sf"
}

snapshot() {
  local repo list
  for repo in $REPOS; do
    list=$TMP/list.json
    gh pr list -R "$repo" --state open --limit 60 \
      --json number,title,isDraft,mergeable,mergeStateStatus,headRefOid,headRefName,author,baseRefName,statusCheckRollup > "$list" 2>/dev/null || { echo "$repo: gh failed"; continue; }
    jq -r --arg r "$repo" "$JQ_DEFS"'
      .[] | "\($r)#\(.number) \(if .isDraft then "draft" else "ready" end) \(.mergeable) \(.headRefOid[0:8]) \(.statusCheckRollup | cls) \(.baseRefName)"' "$list"
  done
}

if [ "$SNAPSHOT" = 1 ]; then snapshot; exit 0; fi

# Single instance per state dir (not for --snapshot or WATCH_ONCE runs): lock directory with a pid file.
take_lock() {
  local pid
  if [ "${WATCH_ONCE:-0}" = 1 ]; then return 0; fi
  if ! mkdir "$LOCK" 2>/dev/null; then
    pid=$(cat "$LOCK/pid" 2>/dev/null)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && ps -p "$pid" -o command= 2>/dev/null | grep -q 'pr-watch'; then
      echo "pr-watch: already running for $STATE (pid $pid)" >&2
      exit 3
    fi
    rm -rf "$LOCK"
    if ! mkdir "$LOCK" 2>/dev/null; then
      echo "pr-watch: could not take the lock $LOCK" >&2
      exit 3
    fi
    report_note lock-takeover "stale lock of pid ${pid:-unknown} taken over"
  fi
  echo "$$" > "$LOCK/pid"
  HAVE_LOCK=1
}
take_lock

while :; do
  if [ -e "$STATE/STOP" ]; then meta stopped "STOP file"; exit 0; fi
  for r in $REPOS; do
    poll_repo "$r"
    if [ "$MODE" = until ] && [ "$ACTIONABLE" = 1 ]; then date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/alive"; exit 0; fi
  done
  date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/alive"
  if [ $(( $(date +%s) - LAST_ACTION )) -ge "$MAX_IDLE" ]; then
    meta idle-timeout "no events for $(awk -v s="$MAX_IDLE" 'BEGIN{printf "%g", s/3600}') hours"; exit 0
  fi
  [ "${WATCH_ONCE:-0}" = 1 ] && break
  sleep $(( INTERVAL + RANDOM % 5 )) & wait $!
done
