#!/usr/bin/env bash
# Tests for pr-watch.sh against a fake gh (fixtures/gh). No network, no long-running processes.
HERE=$(cd "$(dirname "$0")" && pwd)
SCRIPT=$HERE/../../scripts/pr-watch/pr-watch.sh
FIX=$HERE/fixtures
ROOT=$(mktemp -d "${TMPDIR:-/tmp}/pr-watch-test.XXXXXX")
trap 'rm -rf "${ROOT:?}"' EXIT
PASS=0; FAILN=0
export WATCH_REPOS="acme/widgets"
RF=acme_widgets

ok()   { PASS=$((PASS+1)); echo "ok   - $1"; }
bad()  { FAILN=$((FAILN+1)); echo "FAIL - $1"; echo "       $2"; }
assert_empty() { if [ -z "$OUT" ]; then ok "$1"; else bad "$1" "expected no output, got: $OUT"; fi; }
assert_has()   { if grep -Fq -- "$2" <<< "$OUT"; then ok "$1"; else bad "$1" "missing '$2' in: $OUT"; fi; }
assert_lacks() { if grep -Fq -- "$2" <<< "$OUT"; then bad "$1" "unexpected '$2' in: $OUT"; else ok "$1"; fi; }
assert_lines() { local n; n=$(printf '%s\n' "$OUT" | grep -c '^EVT'); if [ "$n" = "$2" ]; then ok "$1"; else bad "$1" "expected $2 EVT lines, got $n: $OUT"; fi; }
assert_eq()    { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "expected '$3' got '$2'"; fi; }

new_world() { # fresh world/state/report
  rm -rf "${ROOT:?}/w" "${ROOT:?}/s"; mkdir -p "$ROOT/w/runs" "$ROOT/w/runview" "$ROOT/w/logs" "$ROOT/w/view" "$ROOT/s"
  export WORLD=$ROOT/w WATCH_STATE_DIR=$ROOT/s WATCH_REPORT=$ROOT/report.jsonl
  rm -f "${WATCH_REPORT:?}"; unset WATCH_MAX_IDLE_SECONDS WATCH_MAX_IDLE_HOURS
}
sha() { printf '%s%032d' "$1" 0; } # 8-char prefix given
# mkpr N draft mergeable sha8 base spec   (spec tokens: g3 = 3 success, p2 = 2 pending, f1 = 1 failure)
mkpr() {
  local spec=$6 checks="[]" t c i
  for t in $(grep -o '[gpf][0-9]*' <<< "$spec"); do
    c=${t:1}; for ((i=0;i<c;i++)); do
      case ${t:0:1} in
        g) checks=$(jq -c '. + [{status:"COMPLETED",conclusion:"SUCCESS"}]' <<< "$checks");;
        p) checks=$(jq -c '. + [{status:"IN_PROGRESS",conclusion:""}]' <<< "$checks");;
        f) checks=$(jq -c '. + [{status:"COMPLETED",conclusion:"FAILURE"}]' <<< "$checks");;
      esac
    done
  done
  jq -c -n --argjson n "$1" --argjson d "$2" --arg m "$3" --arg s "$(sha "$4")" --arg b "$5" --argjson c "$checks" \
    '{number:$n,title:"PR \($n)",isDraft:$d,mergeable:$m,mergeStateStatus:"CLEAN",headRefOid:$s,baseRefName:$b,statusCheckRollup:$c}'
}
setprs() { jq -s -c '.' > "$WORLD/$RF.prs.json"; } # reads PR objects on stdin
run() { OUT=$(bash "$SCRIPT" "$@" 2>&1 < /dev/null); RC=$?; }
once() { WATCH_ONCE=1 run "$@"; }
calls() { grep -c "^$1" "$WORLD/calls.log" 2>/dev/null || true; }
setup_red() { # setup_red sha8 logname runid jobid
  local s; s=$(sha "$1")
  echo "[{\"databaseId\":$3,\"conclusion\":\"failure\",\"event\":\"pull_request\"}]" > "$WORLD/runs/$s.json"
  echo "{\"jobs\":[{\"databaseId\":$4,\"conclusion\":\"failure\",\"name\":\"test\"}]}" > "$WORLD/runview/$3.json"
  cp "$FIX/logs/$2.log" "$WORLD/logs/$4.log"
}
export PATH=$FIX:$PATH

echo "== baseline / quiet =="
new_world
{ mkpr 1 true MERGEABLE aaaa1111 main p5; mkpr 2 false MERGEABLE bbbb2222 main g3; } | setprs
once; assert_empty "baseline is silent"
[ -f "$ROOT/s/$RF.json" ] && ok "baseline state persisted" || bad "baseline state persisted" "no state file"
assert_eq "baseline: exactly one gh call per repo" "$(calls 'pr list')" 1
assert_eq "baseline: no other gh calls" "$(wc -l < "$WORLD/calls.log")" 1
once; assert_empty "restart with unchanged data is silent"
once; assert_empty "second restart silent"
once --snapshot
assert_has "snapshot table row" "acme/widgets#1 draft MERGEABLE aaaa1111 pending main"
assert_has "snapshot ready row" "acme/widgets#2 ready MERGEABLE bbbb2222 green main"

echo "== pending counts, UNKNOWN flaps =="
new_world
mkpr 1 true MERGEABLE aaaa1111 main p5 | setprs; once
for spec in p3 p2 p1 p4; do mkpr 1 true MERGEABLE aaaa1111 main $spec | setprs; once; assert_empty "pending count $spec is no event"; done
for m in UNKNOWN MERGEABLE UNKNOWN UNKNOWN MERGEABLE; do mkpr 1 true $m aaaa1111 main p4 | setprs; once; assert_empty "mergeable $m ignored"; done
assert_eq "only pr list calls were made" "$(wc -l < "$WORLD/calls.log")" "$(calls 'pr list')"

echo "== debounce =="
new_world
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once
mkpr 1 true MERGEABLE aaaa1111 main g2 | setprs; once; assert_empty "one-poll green blip: nothing"
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once; assert_empty "blip gone: nothing"
mkpr 1 true MERGEABLE aaaa1111 main g2 | setprs; once; assert_empty "first green poll: nothing yet"
once; assert_lines "second consecutive green (restart in between) emits once" 1
assert_has "checks-green draft on main is READY-CANDIDATE" "EVT 1 acme/widgets#1 aaaa1111 checks-green | all checks green READY-CANDIDATE"
once; assert_empty "unchanged afterwards: silent"
echo "-- ready + green, draft on non-main"
new_world
{ mkpr 1 false MERGEABLE aaaa1111 main p1; mkpr 2 true MERGEABLE bbbb2222 feat p1; } | setprs; once
{ mkpr 1 false MERGEABLE aaaa1111 main g1; mkpr 2 true MERGEABLE bbbb2222 feat g1; } | setprs; once; once
assert_has "ready PR green -> READY" "#1 aaaa1111 checks-green | all checks green READY"
assert_lacks "ready PR is not READY-CANDIDATE" "READY-CANDIDATE"
assert_has "draft on non-main has no flag" "#2 bbbb2222 checks-green | all checks green"
assert_lines "two events" 2

echo "== conflict =="
new_world
{ mkpr 1 false MERGEABLE aaaa1111 main g1; mkpr 2 true MERGEABLE bbbb2222 main g1; } | setprs; once
{ mkpr 1 false CONFLICTING aaaa1111 main g1; mkpr 2 true CONFLICTING bbbb2222 main g1; } | setprs; once; assert_empty "conflict needs 2 polls"
{ mkpr 1 false UNKNOWN aaaa1111 main g1; mkpr 2 true CONFLICTING bbbb2222 main g1; } | setprs; once
assert_has "ready PR conflict flagged" "#1 aaaa1111 conflict | CONFLICTING base=main READY-PR"
assert_has "draft PR conflict reported" "#2 bbbb2222 conflict | CONFLICTING base=main"
assert_lacks "draft conflict has no READY-PR" "#2 bbbb2222 conflict | CONFLICTING base=main READY-PR"
{ mkpr 1 false MERGEABLE aaaa1111 main g1; mkpr 2 true MERGEABLE bbbb2222 main g1; } | setprs; once; once
assert_has "conflict-cleared emitted" "conflict-cleared"

echo "== ready-changed, head-changed, new-pr =="
new_world
mkpr 1 true MERGEABLE aaaa1111 main g1 | setprs; once
mkpr 1 false MERGEABLE aaaa1111 main g1 | setprs; once; once
assert_has "ready-changed" "#1 aaaa1111 ready-changed | draft->ready"
mkpr 1 false MERGEABLE cccc3333 main p1 | setprs; once; once
assert_has "head-changed" "#1 cccc3333 head-changed | aaaa1111->cccc3333"
{ mkpr 1 false MERGEABLE cccc3333 main p1; mkpr 7 true MERGEABLE dddd4444 main p1; } | setprs; once
assert_has "new-pr" "#7 dddd4444 new-pr | title=\"PR 7\" draft=true base=main"

echo "== checks-red classification =="
for case in "real real-failure" "stack stack-merge-shape" "infra flake-infra" "unknown unknown"; do
  set -- $case; log=$1; want=$2
  new_world
  mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once
  setup_red aaaa1111 "$log" 111 9001
  mkpr 1 true MERGEABLE aaaa1111 main f1p1 | setprs; once; assert_empty "$want: first red poll silent (debounce)"
  once; EV=$OUT
  assert_has "$want: classified" "#1 aaaa1111 checks-red | $want: "
  assert_lines "$want: single event" 1
  assert_eq "$want: one run list call" "$(calls 'run list')" 1
  assert_eq "$want: one log fetch" "$(calls 'api')" 1
  once; assert_empty "$want: no repeat"
  OUT=$EV
  case $want in
    real-failure) assert_has "real-failure quotes test name and error line" "first=TestX err=x_test.go:42: got 3, want 4" ;;
    unknown) assert_has "unknown quotes ##[error] line" "##[error]Something odd happened in step 4" ;;
    flake-infra) assert_has "infra quotes signature" "The runner has received a shutdown signal" ;;
    stack-merge-shape) assert_has "stack quotes signature" "Unexpected synthetic merge parents" ;;
  esac
done
echo "-- red with pending checks is red at once; ANSI stripped"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once
setup_red aaaa1111 real 111 9001
mkpr 1 true MERGEABLE aaaa1111 main f1p3 | setprs; once; once
assert_has "red despite pending" "checks-red | real-failure"
assert_lacks "no escape sequences" $'\033'

echo "== idempotent ids / state returning =="
new_world
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once
cp "$ROOT/s/$RF.json" "$ROOT/prev.json"
setup_red aaaa1111 real 111 9001
mkpr 1 true MERGEABLE aaaa1111 main f1 | setprs; once; once; assert_lines "red emitted" 1
cp "$ROOT/prev.json" "$ROOT/s/$RF.json"   # simulate crash between emit and state save: ids survive
once; once; assert_empty "same id never emitted twice after state loss"
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once; once; assert_empty "back to pending: silent"
mkpr 1 true MERGEABLE aaaa1111 main f1 | setprs; once; once
assert_lines "red again after state returned to something else" 1

echo "== merged / closed / seq =="
new_world
{ mkpr 1 false MERGEABLE aaaa1111 main g1; mkpr 2 true MERGEABLE bbbb2222 main g1; mkpr 3 true MERGEABLE cccc3333 feat g1; } | setprs; once
echo '{"state":"MERGED","mergeCommit":{"oid":"eeeeeeee99999999"},"mergedAt":"2026-10-21T12:00:00Z","baseRefName":"main"}' > "$WORLD/view/${RF}_1.json"
{ mkpr 2 true MERGEABLE bbbb2222 main g1; mkpr 3 true MERGEABLE cccc3333 feat g1; } | setprs; once
assert_has "merged with merge sha and restack list" "EVT 1 acme/widgets#1 aaaa1111 merged | merge=eeeeeeee base=main at=2026-10-21T12:00:00Z check-restack: #2 #3"
once; assert_empty "merged not repeated"
echo '{"state":"CLOSED","mergeCommit":null,"mergedAt":null,"baseRefName":"feat"}' > "$WORLD/view/${RF}_3.json"
mkpr 2 true MERGEABLE bbbb2222 main g1 | setprs; once
assert_has "closed; seq continues across restart" "EVT 2 acme/widgets#3 cccc3333 closed"
assert_eq "report has both lines" "$(jq -s 'length' "$WATCH_REPORT")" 2
echo "-- gh failure keeps state"
touch "$WORLD/$RF.fail"; once; assert_empty "gh failure silent"
rm -f "${WORLD:?}/${RF:?}.fail"; once; assert_empty "after recovery nothing re-announced"

echo "== until-event / stream / valves =="
new_world
{ mkpr 1 true MERGEABLE aaaa1111 main p1; mkpr 2 true MERGEABLE bbbb2222 feat p1; } | setprs
WATCH_ONCE=1 run --until-event
assert_empty "until-event baseline: no output"; assert_eq "until-event baseline rc" "$RC" 0
# only a non-actionable event (draft on non-main goes green): loop keeps going until the idle valve ends it
{ mkpr 1 true MERGEABLE aaaa1111 main p1; mkpr 2 true MERGEABLE bbbb2222 feat g1; } | setprs
WATCH_MAX_IDLE_SECONDS=3 WATCH_INTERVAL=1 run --until-event
assert_has "non-actionable event printed" "#2 bbbb2222 checks-green | all checks green"
assert_has "non-actionable event did not end until-event (idle valve did)" "watch idle-timeout"
# actionable event: exits 0 right after it (needs two polls for the debounce)
{ mkpr 1 true MERGEABLE aaaa1111 main g1; mkpr 2 true MERGEABLE bbbb2222 feat g1; } | setprs
WATCH_MAX_IDLE_SECONDS=100 WATCH_INTERVAL=1 run --until-event
assert_eq "until-event rc 0 after first actionable" "$RC" 0
assert_has "actionable EVT printed" "#1 aaaa1111 checks-green | all checks green READY-CANDIDATE"
assert_lacks "stopped after the actionable line (no idle line)" "idle-timeout"
WATCH_ONCE=1 run --until-event; assert_empty "restart after actionable event repeats nothing"
echo "-- alive per poll, silence, STOP, idle"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
rm -f "${ROOT:?}/s/alive"; once; a1=$(cat "$ROOT/s/alive"); sleep 1; once; a2=$(cat "$ROOT/s/alive")
if [ "$a1" != "$a2" ]; then ok "alive updated on each poll ($a1 -> $a2)"; else bad "alive updated" "$a1 == $a2"; fi
assert_empty "stdout empty when nothing changes"
touch "$ROOT/s/STOP"; WATCH_INTERVAL=1 run --stream
assert_has "STOP file ends the loop" "watch stopped | STOP file"; assert_eq "STOP rc" "$RC" 0
rm -f "${ROOT:?}/s/STOP"
WATCH_MAX_IDLE_SECONDS=2 WATCH_INTERVAL=1 run --stream
assert_has "idle timeout line" "watch idle-timeout | no events for"
assert_has "seq monotonic across watch lines" "EVT 2 watch idle-timeout"
echo "-- SIGTERM logs stopped"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
WATCH_INTERVAL=30 bash "$SCRIPT" > "$ROOT/sig.out" 2>&1 &
pid=$!; sleep 1; kill -TERM $pid; wait $pid 2>/dev/null
if jq -e 'select(.kind=="stopped" and .repo=="" and .pr==0 and .detail=="signal received")' "$WATCH_REPORT" > /dev/null; then ok "SIGTERM writes stopped line to report"; else bad "SIGTERM" "$(cat "$WATCH_REPORT")"; fi
assert_eq "stdout silent on SIGTERM" "$(cat "$ROOT/sig.out")" ""

echo "== jsonl formats =="
new_world
{ mkpr 1 true MERGEABLE aaaa1111 main p1; mkpr 2 false MERGEABLE bbbb2222 main p1; } | setprs; once
{ mkpr 1 true MERGEABLE aaaa1111 main g1; mkpr 2 false MERGEABLE bbbb2222 main g1; } | setprs; once; once
EV=$OUT
assert_has "stdout line format unchanged" "EVT 1 acme/widgets#1 aaaa1111 checks-green | all checks green READY-CANDIDATE"
if grep -Ev '^EVT [0-9]+ [^ ]+#[0-9]+ [0-9a-f]{8} [a-z-]+ \| ' <<< "$EV" | grep -q .; then bad "all stdout lines match EVT format" "$EV"; else ok "all stdout lines match EVT format"; fi
n=0; badl=0; while IFS= read -r l; do n=$((n+1)); jq -e . <<< "$l" > /dev/null 2>&1 || badl=$((badl+1)); done < "$WATCH_REPORT"
assert_eq "every report line is valid JSON ($n lines)" "$badl" 0
assert_eq "report line has documented fields" "$(jq -c '[.seq,.repo,.pr,.sha,.kind,.class,.id]' <<< "$(head -1 "$WATCH_REPORT")")" '[1,"acme/widgets",1,"aaaa1111","checks-green","","acme/widgets#1:aaaa1111:checks-green:"]'
assert_eq "no non-JSON files: state is plain JSON" "$(jq -e . "$ROOT/s/$RF.json" > /dev/null && echo y)" y
assert_eq "emitted.jsonl lines are JSON" "$(jq -s 'length' "$ROOT/s/emitted.jsonl")" 2
echo "-- seq strictly increasing across restarts; dedupe survives restart; truncated last line tolerated"
{ mkpr 1 true MERGEABLE aaaa1111 main f1; mkpr 2 false MERGEABLE bbbb2222 main g1; } | setprs
setup_red aaaa1111 real 111 9001
once; once
assert_has "next seq continues" "EVT 3 acme/widgets#1 aaaa1111 checks-red"
assert_eq "seq strictly increasing in report" "$(jq -s '[.[].seq] as $s | ($s == ($s|sort)) and ($s|length == ($s|unique|length))' "$WATCH_REPORT")" true
printf '{"id":"acme/widgets#9:zzzz:checks-gr' >> "$ROOT/s/emitted.jsonl"   # truncated, no newline
printf '{"seq":99,"t":"2026' >> "$WATCH_REPORT"
{ mkpr 1 true MERGEABLE aaaa1111 main f1; mkpr 2 false MERGEABLE bbbb2222 main g1; } | setprs
once; once; assert_empty "truncated last lines: no failure, no repeat"
{ mkpr 1 true MERGEABLE aaaa1111 main g1; mkpr 2 false MERGEABLE bbbb2222 main g1; } | setprs
once; once; assert_has "event after truncated line still works" "#1 aaaa1111 checks-green"
valid=$(while IFS= read -r l; do jq -e . <<< "$l" > /dev/null 2>&1 && echo y; done < "$WATCH_REPORT" | wc -l)
total=$(wc -l < "$WATCH_REPORT")
assert_eq "truncated fragment healed onto its own line (only it is invalid)" "$((total - valid))" 1
assert_eq "meta events: repo empty, pr 0" "$(WATCH_MAX_IDLE_SECONDS=0 WATCH_ONCE=1 bash "$SCRIPT" > /dev/null; tail -1 "$WATCH_REPORT" | jq -c '[.repo,.pr,.kind]')" '["",0,"idle-timeout"]'

echo "== repository and state defaults =="
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs
unset WATCH_REPOS WATCH_STATE_DIR WATCH_REPORT
FAKE_HOME=$ROOT/home; mkdir -p "$FAKE_HOME"
OUT=$(cd "$ROOT" && HOME=$FAKE_HOME XDG_STATE_HOME= WATCH_ONCE=1 bash "$SCRIPT" 2>&1 < /dev/null); RC=$?
assert_eq "no WATCH_REPOS: current-directory repo is polled" "$(grep -c '^pr list -R acme/widgets' "$WORLD/calls.log")" 1
[ -f "$FAKE_HOME/.local/state/pr-watch/acme_widgets.json" ] && ok "default state under HOME/.local/state/pr-watch" || bad "default state dir" "missing"
[ -f "$FAKE_HOME/.local/state/pr-watch/watch-report.jsonl" ] && ok "default report inside the state dir" || bad "default report" "missing"
OUT=$(cd "$ROOT" && HOME=$FAKE_HOME XDG_STATE_HOME=$ROOT/xdg WATCH_ONCE=1 bash "$SCRIPT" 2>&1 < /dev/null)
[ -f "$ROOT/xdg/pr-watch/acme_widgets.json" ] && ok "XDG_STATE_HOME honoured" || bad "XDG_STATE_HOME" "missing"
touch "$WORLD/norepo"
OUT=$(cd "$ROOT" && HOME=$FAKE_HOME WATCH_ONCE=1 bash "$SCRIPT" 2>&1 < /dev/null); RC=$?
assert_eq "no repo and no WATCH_REPOS: exit 2" "$RC" 2
assert_has "usage names WATCH_REPOS" "WATCH_REPOS"
export WATCH_REPOS="acme/widgets"

echo
echo "passed=$PASS failed=$FAILN"
[ "$FAILN" = 0 ]
