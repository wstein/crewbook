#!/usr/bin/env bash
# Tests for pr-watch.sh against a fake gh (fixtures/gh). No network, no long-running processes.
HERE=$(cd "$(dirname "$0")" && pwd)
SCRIPT=${PR_WATCH_SCRIPT:-$HERE/../../scripts/pr-watch/pr-watch.sh}
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
  jq -c -n --argjson n "$1" --argjson d "$2" --arg m "$3" --arg s "$(sha "$4")" --arg b "$5" --argjson c "$checks" --arg h "${PRHEAD:-topic}" --arg ti "${PRTITLE:-}" --arg au "${PRAUTHOR:-someone}" \
    '{number:$n,title:(if $ti == "" then "PR \($n)" else $ti end),isDraft:$d,mergeable:$m,mergeStateStatus:"CLEAN",headRefOid:$s,headRefName:$h,author:{login:$au},baseRefName:$b,statusCheckRollup:$c}'
}
setprs() { jq -s -c '.' > "$WORLD/$RF.prs.json"; } # reads PR objects on stdin
# run: the script under a 60 s watchdog; a hang (missing STOP handler, idle timeout, ...) fails instead of blocking the suite
run() {
  local p w
  rm -f "$ROOT/timedout"
  bash "$SCRIPT" "$@" > "$ROOT/run.out" 2>&1 < /dev/null & p=$!
  ( i=0; while [ $i -lt 300 ] && kill -0 $p 2>/dev/null; do sleep 0.2; i=$((i+1)); done
    if kill -0 $p 2>/dev/null; then touch "$ROOT/timedout"; kill -TERM $p 2>/dev/null; sleep 1; kill -KILL $p 2>/dev/null; fi ) > /dev/null 2>&1 & w=$!
  wait $p; RC=$?
  kill $w 2>/dev/null; wait $w 2>/dev/null
  OUT=$(cat "$ROOT/run.out")
  if [ -e "$ROOT/timedout" ]; then bad "run $* finished within 60 s" "hung; output: $OUT"; fi
}
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
assert_eq "baseline: no other gh calls" "$(($(wc -l < "$WORLD/calls.log")))" 1
once; assert_empty "restart with unchanged data is silent"
once; assert_empty "second restart silent"
once --snapshot
assert_has "snapshot table row" "acme/widgets#1 draft MERGEABLE aaaa1111 pending main"
assert_has "snapshot ready row" "acme/widgets#2 ready MERGEABLE bbbb2222 green main"

echo "== pending counts, UNKNOWN flaps =="
new_world
mkpr 1 true MERGEABLE aaaa1111 main p5 | setprs; once
for spec in p3 p2 p1 p4; do mkpr 1 true MERGEABLE aaaa1111 main $spec | setprs; once; assert_empty "pending count $spec is no event"
  assert_eq "pending count $spec: state key unchanged, no candidate" "$(jq -c '[.prs["1"].cur.checks, .prs["1"].cand]' "$ROOT/s/$RF.json")" '["pending",null]'; done
for m in UNKNOWN MERGEABLE UNKNOWN UNKNOWN MERGEABLE; do mkpr 1 true $m aaaa1111 main p4 | setprs; once; assert_empty "mergeable $m ignored"; done
assert_eq "only pr list calls were made" "$(($(wc -l < "$WORLD/calls.log")))" "$(calls 'pr list')"

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
for case in "real real-failure" "stack stack-merge-shape" "infra flake-infra" "unknown unknown" "pyunit real-failure" "tap real-failure" "make real-failure" "nested real-failure" "noprefix unknown" "stackreal real-failure" "stackplain unknown" "osc real-failure"; do
  set -- $case; log=$1; want=$2
  export WATCH_STACK_SIGNATURES='Unexpected synthetic merge parents|PR must target repository main'
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
  case $log in
    real) assert_has "real-failure quotes test name and error line" "first=TestX err=x_test.go:42: got 3, want 4" ;;
    pyunit) assert_has "python unittest: test name and error line" "first=test_shell_suite err=AssertionError: 1 != 0" ;;
    tap) assert_has "TAP: failing test name" "first=widget renders err=not ok 3 - widget renders" ;;
    make) assert_has "make: target and error line" "first=[Makefile:12: test] Error 1 err=make: *** [Makefile:12: test] Error 1" ;;
    nested) assert_has "echoed signature lines ignored, real failure quoted" "first=test_real err=AssertionError: boom" ;;
    noprefix) assert_has "##[error] without timestamp prefix is not an annotation" "unknown: no ##[error] line in log" ;;
    unknown) assert_has "unknown quotes ##[error] line" "##[error]Something odd happened in step 4" ;;
    infra) assert_has "infra quotes signature" "The runner has received a shutdown signal" ;;
    stackreal) assert_has "real failure wins over a stack signature" "first=TestX err=x_test.go:7: boom" ;;
    stackplain) assert_has "stack phrase outside an annotation is not stack-merge-shape" "unknown: ##[error]Process completed" ;;
    osc) assert_has "OSC 52 and CSI sequences removed from the detail" "first=TestX err=x_test.go:42: got 3 want 4"
         assert_lacks "no ESC in stdout" $'\033'; assert_lacks "no BEL in stdout" $'\007'; assert_lacks "OSC payload gone" QUJD
         assert_eq "report detail has no control characters" "$(jq -r '.detail' "$WATCH_REPORT" | LC_ALL=C grep -c '[[:cntrl:]]' || true)" 0
         assert_eq "report is valid JSON" "$(jq -s 'length > 0' "$WATCH_REPORT")" true ;;
    stack) assert_has "stack quotes signature" "Unexpected synthetic merge parents" ;;
  esac
done
unset WATCH_STACK_SIGNATURES
echo "-- stack-merge-shape needs WATCH_STACK_SIGNATURES (default off) and is not actionable"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once
setup_red aaaa1111 stack 111 9001
mkpr 1 true MERGEABLE aaaa1111 main f1p1 | setprs; once; once
assert_has "signatures unset: annotation is just unknown" "checks-red | unknown: ##[error]Unexpected synthetic merge parents"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once
setup_red aaaa1111 stack 111 9001
mkpr 1 true MERGEABLE aaaa1111 main f1p1 | setprs; once
WATCH_STACK_SIGNATURES='Unexpected synthetic merge parents' WATCH_MAX_IDLE_SECONDS=3 WATCH_INTERVAL=1 run --until-event
assert_has "stack-merge-shape red reported" "checks-red | stack-merge-shape: ##[error]Unexpected synthetic merge parents"
assert_has "stack-merge-shape red does not end --until-event" "idle-timeout"
echo "-- several failed jobs: the highest-priority class wins"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once
s1=$(sha aaaa1111); echo "[{\"databaseId\":111,\"conclusion\":\"failure\",\"event\":\"pull_request\"}]" > "$WORLD/runs/$s1.json"
echo '{"jobs":[{"databaseId":9001,"conclusion":"failure"},{"databaseId":9002,"conclusion":"failure"},{"databaseId":9003,"conclusion":"failure"}]}' > "$WORLD/runview/111.json"
cp "$FIX/logs/infra.log" "$WORLD/logs/9001.log"; cp "$FIX/logs/unknown.log" "$WORLD/logs/9002.log"; cp "$FIX/logs/noprefix.log" "$WORLD/logs/9003.log"
mkpr 1 true MERGEABLE aaaa1111 main f1 | setprs; once; once
assert_has "unknown outranks flake-infra" "checks-red | unknown: ##[error]Something odd"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p2 | setprs; once
echo "[{\"databaseId\":111,\"conclusion\":\"failure\",\"event\":\"pull_request\"}]" > "$WORLD/runs/$s1.json"
echo '{"jobs":[{"databaseId":9001,"conclusion":"failure"},{"databaseId":9002,"conclusion":"failure"}]}' > "$WORLD/runview/111.json"
cp "$FIX/logs/unknown.log" "$WORLD/logs/9001.log"; cp "$FIX/logs/real.log" "$WORLD/logs/9002.log"
mkpr 1 true MERGEABLE aaaa1111 main f1 | setprs; once; once
assert_has "real-failure outranks unknown" "checks-red | real-failure: first=TestX"
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
assert_eq "log cache: replay after state loss fetched no second log" "$(calls 'api')" 1
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
echo "-- gh output that is not a PR array keeps state"
new_world
{ mkpr 1 true MERGEABLE aaaa1111 main p1; } | setprs; once
echo '{"message":"API rate limit exceeded"}' > "$WORLD/$RF.prs.json"; once; assert_empty "non-array gh output: silent"
{ mkpr 1 true MERGEABLE aaaa1111 main p1; } | setprs; once; assert_empty "unusable output left no phantom events"
assert_eq "state kept the PR" "$(jq -r '.prs["1"].cur.sha' "$ROOT/s/$RF.json")" aaaa1111
echo '{"message":"x"}' > "$WORLD/$RF.prs.json"; once; once; once; assert_has "3 unusable polls count as failures" "watch error | acme/widgets: gh failed 3 times"

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
assert_eq "restart line is the last line" "$(printf '%s\n' "$OUT" | tail -n1 | cut -c1-8)" "restart:"
assert_has "restart line carries WATCH_REPOS and WATCH_STATE_DIR" "restart: WATCH_REPOS=acme/widgets WATCH_STATE_DIR=$ROOT/s bash "
assert_has "restart line ends with --until-event" "--until-event"
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

echo "== conflict on draft PRs, quiet new-pr =="
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
mkpr 1 true CONFLICTING aaaa1111 main p1 | setprs; once
WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_has "draft conflict is actionable" "#1 aaaa1111 conflict | CONFLICTING base=main"
assert_lacks "draft conflict ends the run (no idle)" "idle-timeout"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
mkpr 1 true CONFLICTING aaaa1111 main p1 | setprs; once
WATCH_QUIET_CONFLICT_DRAFT=1 WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_has "WATCH_QUIET_CONFLICT_DRAFT=1: draft conflict still reported" "#1 aaaa1111 conflict |"
assert_has "WATCH_QUIET_CONFLICT_DRAFT=1: draft conflict not actionable" "idle-timeout"
new_world
mkpr 1 false MERGEABLE aaaa1111 main p1 | setprs; once
mkpr 1 false CONFLICTING aaaa1111 main p1 | setprs; once
WATCH_QUIET_CONFLICT_DRAFT=1 WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_lacks "WATCH_QUIET_CONFLICT_DRAFT=1: ready conflict stays actionable" "idle-timeout"
new_world
mkpr 1 true CONFLICTING aaaa1111 main p1 | setprs; once
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_has "conflict-cleared is reported" "conflict-cleared"
assert_has "conflict-cleared is not actionable" "idle-timeout"
echo "-- WATCH_QUIET_NEW"
newpr() { # newpr head author: baseline PR 1, then PR 2 appears
  new_world
  mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
  { mkpr 1 true MERGEABLE aaaa1111 main p1; PRHEAD=$1 PRAUTHOR=$2 mkpr 2 true MERGEABLE bbbb2222 main p1; } | setprs
}
newpr feat/x alice; WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_has "default (empty) quiet list: new-pr actionable" "#2 bbbb2222 new-pr |"
assert_lacks "default: run ended at new-pr" "idle-timeout"
newpr feat/x alice; WATCH_QUIET_NEW="docs/ feat/" WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_has "quiet branch prefix: new-pr still printed" "#2 bbbb2222 new-pr |"
assert_has "quiet branch prefix: not actionable" "idle-timeout"
assert_eq "quiet new-pr logged to jsonl" "$(jq -c 'select(.kind=="new-pr") | [.pr,.class]' "$WATCH_REPORT")" '[2,"quiet"]'
newpr fix/x alice; WATCH_QUIET_NEW="docs/ feat/" WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_lacks "non-matching prefix stays actionable" "idle-timeout"
newpr other/x alice; WATCH_QUIET_NEW="author:alice" WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_has "quiet author: not actionable" "idle-timeout"
newpr other/x bob; WATCH_QUIET_NEW="author:alice" WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_lacks "other author stays actionable" "idle-timeout"

echo "== single-instance lock =="
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs
WATCH_INTERVAL=30 bash "$SCRIPT" --stream > "$ROOT/a.out" 2>&1 &
apid=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -L "$ROOT/s/lock" ] && break; sleep 1; done
assert_eq "lock target names the running instance" "$(readlink "$ROOT/s/lock")" "$apid"
run --stream; assert_eq "second instance refused: exit 3" "$RC" 3
assert_has "refusal names the pid" "pid $apid"
WATCH_ONCE=1 run --stream; assert_eq "WATCH_ONCE run does not take or check the lock" "$RC" 0
run --snapshot; assert_eq "snapshot does not take the lock" "$RC" 0
assert_eq "lock still held by the first instance" "$(readlink "$ROOT/s/lock")" "$apid"
kill -TERM $apid; wait $apid 2>/dev/null
[ ! -e "$ROOT/s/lock" ] && [ ! -L "$ROOT/s/lock" ] && ok "lock released on SIGTERM" || bad "lock released on SIGTERM" "still there"
echo "-- stale locks"
sleep 0 & dead=$!; wait $dead; ln -s "$dead" "$ROOT/s/lock"
WATCH_MAX_IDLE_SECONDS=0 WATCH_INTERVAL=1 run --stream
assert_eq "dead-pid lock taken over" "$RC" 0
assert_eq "takeover logged" "$(jq -c 'select(.kind=="lock-takeover") | .kind' "$WATCH_REPORT")" '"lock-takeover"'
[ ! -L "$ROOT/s/lock" ] && [ ! -L "$ROOT/s/lock.takeover" ] && ok "lock and takeover mutex released after normal exit" || bad "lock released after exit" "still there"
sleep 30 & other=$!
ln -s "$other" "$ROOT/s/lock"
WATCH_MAX_IDLE_SECONDS=0 WATCH_INTERVAL=1 run --stream
assert_eq "live non-pr-watch pid lock taken over" "$RC" 0
kill $other 2>/dev/null; wait $other 2>/dev/null
sleep 0 & dead=$!; wait $dead; ln -s "$dead" "$ROOT/s/lock"; ln -s "$dead" "$ROOT/s/lock.takeover"
tk0=$(jq -c 'select(.kind=="lock-takeover")' "$WATCH_REPORT" | wc -l | tr -d ' ')
WATCH_MAX_IDLE_SECONDS=0 WATCH_INTERVAL=1 run --stream
assert_eq "stale takeover file of a dead pid does not block a takeover" "$RC" 0
assert_eq "takeover completed past the stale takeover file" "$(jq -c 'select(.kind=="lock-takeover")' "$WATCH_REPORT" | wc -l | tr -d ' ')" $((tk0 + 1))
[ ! -L "$ROOT/s/lock.takeover" ] && [ ! -L "$ROOT/s/lock" ] && ok "stale takeover file cleared, lock released" || bad "stale takeover file cleared" "still there"
touch "$ROOT/s/STOP"; run --stream
assert_eq "STOP run exits 0" "$RC" 0
[ ! -L "$ROOT/s/lock" ] && ok "lock released after STOP" || bad "lock released after STOP" "still there"
rm -f "${ROOT:?}/s/STOP"
echo "-- concurrent starts: exactly one reaches the poll loop"
race() { # race <instances>: start them at once; wait for the losers; set MARKS and LOSERS; stop the winner
  local i q pids="" t
  rm -f "$ROOT"/race.*.out; : > "$ROOT/marker"
  for ((i=0;i<$1;i++)); do
    WATCH_TEST_MARKER=$ROOT/marker WATCH_INTERVAL=30 bash "$SCRIPT" --stream > "$ROOT/race.$i.out" 2>&1 < /dev/null &
    pids="$pids $!"
  done
  for t in $(seq 1 100); do
    LOSERS=$(grep -l '^pr-watch: ' "$ROOT"/race.*.out 2>/dev/null | wc -l | tr -d ' ')
    [ "$LOSERS" -ge $(($1 - 1)) ] && break; sleep 0.1
  done
  sleep 0.3
  MARKS=$(($(wc -l < "$ROOT/marker"))); LOSERS=$(grep -l '^pr-watch: ' "$ROOT"/race.*.out 2>/dev/null | wc -l | tr -d ' ')
  for q in $pids; do kill -TERM $q 2>/dev/null; done
  for q in $pids; do wait $q 2>/dev/null; done
}
fail_trials=0
for trial in $(seq 1 20); do
  new_world; mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs
  race 10
  if [ "$MARKS" != 1 ] || [ "$LOSERS" != 9 ]; then fail_trials=$((fail_trials+1)); echo "       trial $trial: $MARKS instances ran, $LOSERS refused"; fi
  [ -L "$ROOT/s/lock" ] && fail_trials=$((fail_trials+1))
done
assert_eq "20 trials of 10 simultaneous starts: exactly one instance each, lock released" "$fail_trials" 0
fail_trials=0
for trial in $(seq 1 10); do
  new_world; mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs
  sleep 0 & dead=$!; wait $dead; ln -s "$dead" "$ROOT/s/lock"
  race 10
  tk=$(jq -c 'select(.kind=="lock-takeover")' "$WATCH_REPORT" | wc -l | tr -d ' ')
  if [ "$MARKS" != 1 ] || [ "$LOSERS" != 9 ] || [ "$tk" -gt 1 ]; then fail_trials=$((fail_trials+1)); echo "       trial $trial: $MARKS ran, $LOSERS refused, $tk takeovers"; fi
done
assert_eq "10 trials of 10 simultaneous takers of a stale lock: exactly one wins (at most one takeover logged)" "$fail_trials" 0

echo "-- a plain directory at the lock path (left by an early version) is refused, never entered"
new_world; mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs
mkdir "$ROOT/s/lock"
race 10
assert_eq "directory at lock path: no instance reaches the poll loop" "$MARKS" 0
assert_eq "directory at lock path: all 10 refuse" "$LOSERS" 10
OUT=$(cat "$ROOT"/race.0.out); assert_has "directory refusal names the path" "is a directory"
[ -z "$(ls -A "$ROOT/s/lock")" ] && ok "nothing created inside the directory" || bad "nothing created inside the directory" "$(ls -A "$ROOT/s/lock")"
rmdir "$ROOT/s/lock"

echo "== free-text sanitizing =="
new_world
PRTITLE=$'x\x1ffalse\x1fmain' mkpr 1 true MERGEABLE aaaa1111 feat p1 | setprs; once
PRTITLE=$'x\x1ffalse\x1fmain' mkpr 1 true MERGEABLE aaaa1111 feat g1 | setprs; once; once
assert_has "title with field separators: green is reported" "#1 aaaa1111 checks-green | all checks green"
assert_lacks "title cannot flip draft/base (no READY marker)" "READY"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
{ mkpr 1 true MERGEABLE aaaa1111 main p1; PRTITLE=$'a\x1fb\x1ec\033[2Jd\re@@NUL@@f' mkpr 2 true MERGEABLE bbbb2222 main p1 | sed 's/@@NUL@@/\\u0000/'; } | setprs; once
assert_has "separators, ESC sequences, CR and NUL removed from the title" 'title="a b cd e f" draft=true base=main'
assert_lacks "no ESC on stdout" $'\033'
assert_eq "quiet decision uses the real head branch, not a shifted field" "$(PRHEAD=feat/x PRTITLE=$'q\x1ffalse' mkpr 3 true MERGEABLE cccc3333 main p1 | jq -r .headRefName)" feat/x
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
{ mkpr 1 true MERGEABLE aaaa1111 main p1; PRHEAD=feat/x PRTITLE=$'t\x1ftrue\x1fmain\x1fdocs/\x1fbob' mkpr 2 true MERGEABLE bbbb2222 main p1; } | setprs
WATCH_QUIET_NEW="docs/" WATCH_MAX_IDLE_SECONDS=3 WATCH_INTERVAL=1 run --until-event
assert_has "title cannot spoof the head branch for WATCH_QUIET_NEW: still actionable" "#2 bbbb2222 new-pr |"
assert_lacks "run ended at the new-pr" "idle-timeout"

echo "== default branch, watch error / recovered, empty repos =="
new_world
export FAKE_DEFAULT_BRANCH=trunk
mkpr 1 true MERGEABLE aaaa1111 trunk p1 | setprs; once
mkpr 1 true MERGEABLE aaaa1111 trunk g1 | setprs; once; once
assert_has "draft on the default branch (trunk) is READY-CANDIDATE" "checks-green | all checks green READY-CANDIDATE"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
mkpr 1 true MERGEABLE aaaa1111 main g1 | setprs; once; once
assert_lacks "draft on main is no candidate when the default branch is trunk" "READY-CANDIDATE"
assert_eq "default branch looked up once per repo (cached)" "$(calls 'repo view')" 1
touch "$WORLD/nodefbranch"; rm -f "$ROOT/s/cache/"*.defbranch
mkpr 2 true MERGEABLE bbbb2222 main p1 | setprs; once
unset FAKE_DEFAULT_BRANCH
new_world
{ mkpr 1 true MERGEABLE aaaa1111 main p1; } | setprs; once
printf 'gh: HTTP 401 \033[31mbad\033[0m credentials\nsecond line\n' > "$WORLD/$RF.fail"
once; assert_empty "failed poll 1: silent"; once; assert_empty "failed poll 2: silent"
once; assert_has "failed poll 3: one watch error" "EVT 1 watch error | acme/widgets: gh failed 3 times: gh: HTTP 401 bad credentials"
assert_lacks "error text has no ESC" $'\033'; assert_lacks "only the first stderr line" "second line"
once; assert_empty "failed poll 4: no repeat"
rm -f "${WORLD:?}/${RF:?}.fail"; once
assert_has "recovery announced" "watch recovered | acme/widgets: gh works again after 4 failed polls"
once; assert_empty "recovery announced once"
mkdir -p "$ROOT/s/cache"; echo 2 > "$ROOT/s/cache/$RF.fails"; touch "$WORLD/$RF.fail"
WATCH_INTERVAL=1 run --until-event
assert_has "watch error is actionable (ends --until-event)" "watch error | acme/widgets: gh failed 3 times"
assert_eq "until-event rc" "$RC" 0
rm -f "${WORLD:?}/${RF:?}.fail"
touch "$WORLD/norepo"
OUT=$(cd "$ROOT" && WATCH_REPOS="   " HOME=$FAKE_HOME WATCH_ONCE=1 bash "$SCRIPT" 2>&1 < /dev/null); RC=$?
assert_eq "blank WATCH_REPOS and no repository: exit 2" "$RC" 2
rm -f "${WORLD:?}/norepo"

echo "== actionability, tombstones =="
new_world
{ mkpr 1 true MERGEABLE aaaa1111 main p1; mkpr 2 true MERGEABLE bbbb2222 main p1; } | setprs; once
echo '{"state":"MERGED","mergeCommit":{"oid":"eeeeeeee00000000"},"mergedAt":"2026-10-21T12:00:00Z","baseRefName":"main"}' > "$WORLD/view/${RF}_1.json"
mkpr 2 true MERGEABLE bbbb2222 main p1 | setprs
WATCH_MAX_IDLE_SECONDS=4 WATCH_INTERVAL=1 run --until-event
assert_has "merged reported" "#1 aaaa1111 merged |"
assert_lacks "merged ends --until-event" "idle-timeout"
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
for round in 1 2; do
  mkpr 1 true CONFLICTING aaaa1111 main p1 | setprs; once; once
  assert_has "conflict round $round emitted (tombstone lets it repeat)" "#1 aaaa1111 conflict | CONFLICTING"
  mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once; once
  assert_has "conflict-cleared round $round emitted" "conflict-cleared"
done
new_world
mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once
for round in 1 2; do
  mkpr 1 false MERGEABLE aaaa1111 main p1 | setprs; once; once
  assert_has "draft->ready round $round emitted" "draft->ready"
  mkpr 1 true MERGEABLE aaaa1111 main p1 | setprs; once; once
  assert_has "ready->draft round $round emitted" "ready->draft"
done

echo "== bash 3.2 compatibility (static) =="
hits=$(grep -nE 'declare +-A|mapfile|readarray|\$\{[A-Za-z_]+(,,|\^\^|,|\^)\}|&>>|local +-n|\[\[ +-v|printf +.*%\(|coproc|\|&' "$SCRIPT" || true)
assert_eq "script uses no bash 4+ syntax" "$hits" ""

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
valid=$(while IFS= read -r l; do jq -e . <<< "$l" > /dev/null 2>&1 && echo y; done < "$WATCH_REPORT" | wc -l | tr -d " ")
total=$(($(wc -l < "$WATCH_REPORT")))
assert_eq "truncated fragment healed onto its own line (only it is invalid)" "$((total - valid))" 1
assert_eq "report: new event sits on its own valid line after the fragment" "$(tail -1 "$WATCH_REPORT" | jq -r '.kind')" checks-green
once; once; assert_empty "dedupe survived the truncated emitted.jsonl line (no repeat)"
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
[ -f "$ROOT/xdg/pr-watch/acme_widgets.json" ] && ok "XDG_STATE_HOME honored" || bad "XDG_STATE_HOME" "missing"
rm -f "$WORLD/calls.log"
OUT=$(cd "$ROOT" && WATCH_REPOS="   " HOME=$FAKE_HOME XDG_STATE_HOME=$ROOT/xdg WATCH_ONCE=1 bash "$SCRIPT" 2>&1 < /dev/null); RC=$?
assert_eq "blank WATCH_REPOS falls back to the current-directory repo" "$(grep -c '^pr list -R acme/widgets' "$WORLD/calls.log")" 1
touch "$WORLD/norepo"
OUT=$(cd "$ROOT" && HOME=$FAKE_HOME WATCH_ONCE=1 bash "$SCRIPT" 2>&1 < /dev/null); RC=$?
assert_eq "no repo and no WATCH_REPOS: exit 2" "$RC" 2
assert_has "usage names WATCH_REPOS" "WATCH_REPOS"
export WATCH_REPOS="acme/widgets"

echo
echo "passed=$PASS failed=$FAILN"
[ "$FAILN" = 0 ]
