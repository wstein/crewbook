#!/usr/bin/env python3
"""Record and summarise delegated runs (stdlib only, Python 3.9+).

One tab-separated record per delegated run in a local, git-ignored file
(default .work/RUNS.tsv). The desk records each run at hand-back from the run's
usage line (see docs/team.md#run-records). Records hold only the fixed fields
below; values are validated so no free text, paths or secrets can be stored.

  runs_report.py record --date D --ref '#510' --role author --model sonnet \
      --effort medium --tokens 70800 --minutes 11.6 --rounds 3 \
      --high 0 --medium 2 --low 1 --ci y --clear y
  runs_report.py [report] [--file F] [--json]

Per (role, model, effort): tokens and minutes per CLEAR, review rounds per PR,
findings per PR (high/medium/low), CI first-try rate. A group with fewer than MIN_PRS distinct
PRs is marked 'not enough data'. Numbers are indicative, not verified.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

SCHEMA = "crewbook-runs schema=1"
COLUMNS = ("date", "ref", "role", "model", "effort", "tokens", "minutes", "rounds",
           "high", "medium", "low", "ci_first_try", "clear")
ROLES = {"desk", "dispatch", "author", "reviewer", "design", "helper", "docs", "other"}
MIN_PRS = 10
DEFAULT_FILE = os.path.join(".work", "RUNS.tsv")
WORD = re.compile(r"[A-Za-z0-9._-]{1,40}")
REF = re.compile(r"#?[0-9]{1,7}")
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
DIGITS = re.compile(r"[0-9]{1,12}")
INTS = ("tokens", "rounds", "high", "medium", "low")


def parse_row(line):
    """Return (dict, None) for a valid record, else (None, reason)."""
    f = line.split("\t")
    if len(f) != len(COLUMNS):
        return None, "wrong field count"
    r = dict(zip(COLUMNS, f))
    if not DATE.fullmatch(r["date"]):
        return None, "bad date"
    if not REF.fullmatch(r["ref"]):
        return None, "bad ref"
    if r["role"] not in ROLES:
        return None, "bad role"
    for k in ("model", "effort"):
        if not WORD.fullmatch(r[k]):
            return None, "bad " + k
    for k in INTS:
        if not DIGITS.fullmatch(r[k]):
            return None, "bad " + k
        r[k] = int(r[k])
    try:
        r["minutes"] = float(r["minutes"])
    except ValueError:
        return None, "bad minutes"
    if not 0 <= r["minutes"] < 100000:
        return None, "bad minutes"
    if r["ci_first_try"] not in ("y", "n", "-") or r["clear"] not in ("y", "n"):
        return None, "bad flag"
    r["ref"] = r["ref"].lstrip("#")
    return r, None


def load(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0].strip() != "# " + SCHEMA:
        raise ValueError("missing '# %s' first line" % SCHEMA)
    if len(lines) < 2 or lines[1].split("\t") != list(COLUMNS):
        raise ValueError("missing or changed header row")
    for ln in lines[2:]:
        if not ln.strip():
            continue
        r, why = parse_row(ln)
        if r:
            rows.append(r)
        else:
            bad += 1
    return rows, bad


def summarise(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["role"], r["model"], r["effort"])].append(r)
    out = []
    for (role, model, effort), rs in sorted(groups.items()):
        prs = {r["ref"] for r in rs}
        cleared = {r["ref"] for r in rs if r["clear"] == "y"}
        rounds = {}
        ci = {}
        for r in rs:  # per-PR value comes from the last row naming it
            if r["rounds"]:
                rounds[r["ref"]] = r["rounds"]
            if r["ci_first_try"] != "-":
                ci[r["ref"]] = r["ci_first_try"]
        n = len(cleared)
        out.append({
            "role": role, "model": model, "effort": effort, "runs": len(rs),
            "prs": len(prs), "clear": n,
            "tokens_per_clear": round(sum(r["tokens"] for r in rs) / n) if n else None,
            "minutes_per_clear": round(sum(r["minutes"] for r in rs) / n, 1) if n else None,
            "rounds_per_pr": round(sum(rounds.values()) / len(rounds), 2) if rounds else None,
            "findings_per_pr": {k: round(sum(r[k] for r in rs) / len(prs), 2)
                                for k in ("high", "medium", "low")},
            "ci_first_try_rate": round(sum(v == "y" for v in ci.values()) / len(ci), 2) if ci else None,
            "enough_data": len(prs) >= MIN_PRS,
        })
    return out


def fmt(v):
    return "n/a" if v is None else str(v)


def render(summary, bad):
    head = ("role", "model", "effort", "runs", "PRs", "tok/CLEAR", "min/CLEAR",
            "rounds/PR", "high/PR", "med/PR", "low/PR", "CI 1st", "note")
    lines = ["\t".join(head)]
    for s in summary:
        note = "" if s["enough_data"] else "not enough data (<%d PRs)" % MIN_PRS
        lines.append("\t".join(map(fmt, (
            s["role"], s["model"], s["effort"], s["runs"], s["prs"], s["tokens_per_clear"],
            s["minutes_per_clear"], s["rounds_per_pr"], *(s["findings_per_pr"][k] for k in ("high", "medium", "low")),
            s["ci_first_try_rate"], note))))
    if bad:
        lines.append("skipped %d invalid record(s)" % bad)
    return "\n".join(lines)


def record(a):
    vals = [a.date, a.ref, a.role, a.model, a.effort, a.tokens, a.minutes, a.rounds,
            a.high, a.medium, a.low, a.ci, a.clear]
    line = "\t".join(str(v) for v in vals)
    r, why = parse_row(line)
    if not r:
        sys.exit("invalid record: " + why)
    d = os.path.dirname(a.file)
    if d:
        os.makedirs(d, exist_ok=True)
    new = not os.path.exists(a.file) or os.path.getsize(a.file) == 0
    with open(a.file, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# %s\n%s\n" % (SCHEMA, "\t".join(COLUMNS)))
        fh.write(line + "\n")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd")
    rp = sub.add_parser("report")
    rp.add_argument("--file", default=DEFAULT_FILE)
    rp.add_argument("--json", action="store_true")
    rc = sub.add_parser("record")
    rc.add_argument("--file", default=DEFAULT_FILE)
    for k in ("date", "ref", "role", "model", "effort"):
        rc.add_argument("--" + k, required=True)
    rc.add_argument("--tokens", required=True)
    rc.add_argument("--minutes", required=True)
    for k in ("rounds", "high", "medium", "low"):
        rc.add_argument("--" + k, default="0")
    rc.add_argument("--ci", default="-", choices=("y", "n", "-"))
    rc.add_argument("--clear", default="n", choices=("y", "n"))
    a = p.parse_args(argv)
    if a.cmd == "record":
        record(a)
        return 0
    if a.cmd is None:
        a = rp.parse_args([])
    try:
        rows, bad = load(a.file)
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    s = summarise(rows)
    print(json.dumps({"schema": SCHEMA, "groups": s, "skipped": bad}, indent=1)
          if a.json else render(s, bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
