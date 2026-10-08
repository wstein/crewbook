#!/usr/bin/env python3
"""Read-only usage report for Claude Code session logs (stdlib only, Python 3.9+).

Reads session jsonl files (including subagents/*.jsonl) passively and locally;
nothing is sent anywhere. Output contains only counts, token numbers, hashed
agent ids, model names and role labels. It never emits prompt or response text,
file paths or secrets. Costs are ESTIMATES from a user-supplied price table.

Usage: usage_report.py [PATH ...] [--prices FILE] [--top N] [--json | --html FILE]
PATH defaults to $CREWBOOK_USAGE_PATH, then ~/.claude/projects.

Heuristics (estimates, unverified):
  resume    a gap above --resume-gap seconds (default 1800) between two
            consecutive requests of one agent counts as one resume/restart.
  loop tick requests are grouped into bursts separated by more than 60 s idle;
            if an agent has >= 5 bursts whose start-to-start gaps are nearly
            regular (spread <= 10% of the median), it is flagged as a possible
            loop/cron with that interval and mean cost per burst.
  role      matched only from structured sidecar agentType/description labels;
            prompt content is never inspected. No match gives "unknown".
"""
import argparse
import hashlib
import html
import json
import math
import os
import re
import sys
from datetime import datetime

SCHEMA_VERSION = 1
FIELDS = ("input", "output", "cache_read", "cache_write")
USAGE_KEYS = {"input": "input_tokens", "output": "output_tokens",
              "cache_read": "cache_read_input_tokens",
              "cache_write": "cache_creation_input_tokens"}
# Whole-word keywords; agentType is checked before description. Review/design
# are role words only in agentType ("address review feedback" is not a reviewer).
TYPE_WORDS = {"dispatch": "dispatch", "dispatcher": "dispatch", "reviewer": "reviewer",
              "review": "reviewer", "designer": "design", "design": "design",
              "author": "author", "worker": "author", "desk": "desk"}
DESC_WORDS = {"dispatcher": "dispatch", "reviewer": "reviewer", "designer": "design",
              "author": "author", "worker": "author", "desk": "desk"}
# Safe model-id shape: only strings matching this are ever emitted, so new
# ids price and report without a code change while arbitrary text stays out.
MODEL_RE = re.compile(r"^claude-[a-z0-9.-]{1,40}$")
MAX_LINE = 8 * 1024 * 1024
TOKEN_MAX = 10 ** 15
BURST_IDLE = 60.0
NOTICE = "Costs are estimates from a user-supplied price table, not vendor-verified."


def blank():
    return {k: 0 for k in FIELDS}


def to_int(v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0 or v > TOKEN_MAX:
        return None
    return v


def parse_ts(v):
    if not isinstance(v, str):
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
    except (ValueError, OverflowError, OSError):
        return None


def hash_id(v):
    return hashlib.sha256(str(v).encode("utf-8", "replace")).hexdigest()[:8]


def match_role(label):
    """label is "agentType\ndescription"; whole words only, agentType first."""
    typ, _, desc = label.partition("\n")
    for text, words in ((typ, TYPE_WORDS), (desc, DESC_WORDS)):
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            if w in words:
                return words[w]
    return None


def label_text(meta_path):
    try:
        if os.path.islink(meta_path):
            return ""
        with open(meta_path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError, RecursionError, OverflowError):
        return ""
    if not isinstance(d, dict):
        return ""
    parts = [d[k][:200] if isinstance(d.get(k), str) else ""
             for k in ("agentType", "description")]
    return "\n".join(parts) if any(parts) else ""


def valid_model(m):
    return isinstance(m, str) and MODEL_RE.fullmatch(m) is not None


def find_files(roots, stats=None):
    def onerror(_e):
        if stats is not None:
            stats["walk_errors"] += 1

    out = []
    for root in roots:
        if os.path.islink(root):
            continue
        if os.path.isfile(root):
            out.append(root)
            continue
        for dp, dn, fn in os.walk(root, followlinks=False, onerror=onerror):
            dn.sort()
            out.extend(p for p in (os.path.join(dp, f) for f in sorted(fn) if f.endswith(".jsonl"))
                       if not os.path.islink(p))
    return out


class Collector:
    def __init__(self, resume_gap):
        self.resume_gap = resume_gap
        self.recs = {}          # (msg id, request id) -> record
        self.roles = {}         # agent key -> role
        self.stats = {"files": 0, "lines": 0, "malformed_lines": 0, "duplicates": 0,
                      "no_dedupe_key": 0, "bad_usage": 0, "unknown_model": 0,
                      "no_timestamp": 0, "unreadable_files": 0, "walk_errors": 0}

    def add_file(self, path):
        base = os.path.basename(path)
        m = re.match(r"^agent-(.+)\.jsonl$", base)
        file_agent = m.group(1) if m else "main-" + os.path.splitext(base)[0]
        label = ""
        if m:
            label = label_text(path[:-len(".jsonl")] + ".meta.json")
        role = match_role(label) if label else None
        if role:
            self.roles.setdefault(file_agent, role)
        try:
            if os.path.islink(path):
                raise OSError("symlink")
            fh = open(path, "r", encoding="utf-8", errors="replace")
        except OSError:
            self.stats["unreadable_files"] += 1
            return
        self.stats["files"] += 1
        try:
            with fh:
                self.read_lines(fh, file_agent, label)
        except OSError:
            self.stats["unreadable_files"] += 1

    def read_lines(self, fh, file_agent, label):
        while True:
            line = fh.readline(MAX_LINE + 1)
            if not line:
                return
            if len(line) > MAX_LINE and not line.endswith("\n"):
                while True:  # drain the rest of the oversized line
                    chunk = fh.readline(MAX_LINE)
                    if not chunk or chunk.endswith("\n"):
                        break
                self.stats["lines"] += 1
                self.stats["malformed_lines"] += 1
                continue
            if not line.strip():
                continue
            self.stats["lines"] += 1
            try:
                o = json.loads(line)
            except (ValueError, RecursionError, OverflowError):
                self.stats["malformed_lines"] += 1
                continue
            if not isinstance(o, dict):
                self.stats["malformed_lines"] += 1
                continue
            try:
                self.add_obj(o, file_agent, label)
            except (OverflowError, RecursionError, ValueError):
                self.stats["bad_usage"] += 1

    def add_obj(self, o, file_agent, label):
        aid = o.get("agentId") if isinstance(o.get("agentId"), str) and o.get("agentId") else file_agent
        role = match_role(label) if label else None
        if role:
            self.roles.setdefault(aid, role)
        if o.get("type") == "assistant":
            self.add_assistant(o, aid, file_agent, label)

    def add_assistant(self, o, aid, file_agent, label):
        msg = o.get("message")
        usage = msg.get("usage") if isinstance(msg, dict) else None
        if not isinstance(usage, dict):
            self.stats["bad_usage"] += 1
            return
        mid = msg.get("id")
        rid = o.get("requestId")
        if not (isinstance(mid, str) and mid and isinstance(rid, str) and rid):
            self.stats["no_dedupe_key"] += 1
            return
        vals = {}
        for k, src in USAGE_KEYS.items():
            n = to_int(usage.get(src))
            if n is None:
                if src in usage:
                    self.stats["bad_usage"] += 1
                n = 0
            vals[k] = n
        model = msg.get("model")
        if not valid_model(model):
            model = "unknown"
        ts = parse_ts(o.get("timestamp"))
        key = (mid, rid)
        prev = self.recs.get(key)
        if prev is not None:
            # Streamed duplicates repeat the same request: keep the max per field.
            self.stats["duplicates"] += 1
            for k in FIELDS:
                prev["v"][k] = max(prev["v"][k], vals[k])
            if prev["model"] == "unknown":
                prev["model"] = model
            if prev["ts"] is None:
                prev["ts"] = ts
            return
        self.recs[key] = {"agent": aid, "file_agent": file_agent, "model": model,
                          "v": vals, "ts": ts, "order": len(self.recs)}


PRICE_MAX = 1e12


def valid_price(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    try:
        f = float(x)
    except OverflowError:
        return False
    return math.isfinite(f) and 0 <= f <= PRICE_MAX


def load_prices(path):
    """Return (table, problem). table None: no prices; "unreadable": file or JSON
    unusable (fatal); "invalid": schema or value problem (cost n/a, warn).
    problem names the issue without echoing values."""
    if not path:
        return None, None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError, RecursionError, OverflowError):
        return "unreadable", "price table cannot be read or is not valid JSON"
    models = d.get("models") if isinstance(d, dict) else None
    if not isinstance(models, dict) or not models:
        return "invalid", "price table needs a non-empty \"models\" object"
    table = {}
    for n, (name, p) in enumerate(models.items(), 1):
        if not isinstance(p, dict):
            return "invalid", "price entry #%d is not an object" % n
        for k in FIELDS:
            if k not in p:
                return "invalid", "price entry #%d lacks field %s" % (n, k)
            if not valid_price(p[k]):
                return "invalid", ("price entry #%d field %s must be a finite "
                                   "non-negative number" % (n, k))
        table[str(name).lower()] = {k: float(p[k]) for k in FIELDS}
    return table, None


def price_for(table, model):
    if model == "unknown":
        return None
    low = model.lower()
    if low in table:
        return table[low]
    best = None
    for name in table:
        if name in low and (best is None or len(name) > len(best)):
            best = name
    return table[best] if best else None


def cost_of(v, p):
    return sum(v[k] * p[k] for k in FIELDS) / 1e6


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def analyse_times(recs):
    """Return (loop dict or None, burst count) from request timestamps of one agent."""
    ts = sorted(r["ts"] for r in recs if r["ts"] is not None)
    starts = [ts[0]] if ts else []
    for a, b in zip(ts, ts[1:]):
        if b - a > BURST_IDLE:
            starts.append(b)
    loop = None
    if len(starts) >= 5:
        gaps = [b - a for a, b in zip(starts, starts[1:])]
        med = median(gaps)
        if med > 0:
            spread = median([abs(g - med) for g in gaps])
            if spread <= 0.1 * med:
                loop = {"bursts": len(starts), "interval_s": int(round(med))}
    return loop, len(starts)


def build(col, table, top, resume_gap):
    groups = {}
    for r in col.recs.values():
        role = col.roles.get(r["agent"]) or col.roles.get(r["file_agent"]) or "unknown"
        g = groups.setdefault((r["agent"], r["model"], role), [])
        g.append(r)
    # Timing belongs to an agent's complete timeline, before model grouping.
    timelines = {}
    for recs in groups.values():
        for r in recs:
            timelines.setdefault(r["agent"], []).append(r)
    timing = {}
    for aid, recs in timelines.items():
        ordered = sorted((r for r in recs if r["ts"] is not None),
                         key=lambda r: (r["ts"], r["order"]))
        resume_models = {}
        for a, b in zip(ordered, ordered[1:]):
            if b["ts"] - a["ts"] > resume_gap:
                resume_models[b["model"]] = resume_models.get(b["model"], 0) + 1
        loop, bursts = analyse_times(recs)
        # Attribute the agent loop once, to the model at its first request.
        loop_model = ordered[0]["model"] if ordered else None
        agent_cost = 0.0 if isinstance(table, dict) else None
        if agent_cost is not None:
            for r in ordered:  # timestamped records only, matching the burst count
                p = price_for(table, r["model"])
                if p is None:
                    agent_cost = None
                    break
                agent_cost += cost_of(r["v"], p)
            if agent_cost is not None and not math.isfinite(agent_cost):
                agent_cost = None
        timing[aid] = (resume_models, loop, bursts, loop_model, agent_cost)
    rows = []
    row_unpriced_by_id = {}
    unpriced = 0
    for (aid, model, role), recs in groups.items():
        v = blank()
        for r in recs:
            for k in FIELDS:
                v[k] += r["v"][k]
        last = max(recs, key=lambda r: (r["ts"] if r["ts"] is not None else -1, r["order"]))
        ctx = last["v"]["input"] + last["v"]["cache_read"] + last["v"]["cache_write"]
        resume_models, agent_loop, bursts, loop_model, agent_cost = timing[aid]
        resumes = resume_models.get(model, 0)
        loop = agent_loop if model == loop_model else None
        col.stats["no_timestamp"] += sum(1 for r in recs if r["ts"] is None)
        cost = None
        row_unpriced = 0
        if isinstance(table, dict):
            p = price_for(table, model)
            if p is not None:
                try:
                    cost = cost_of(v, p)
                except OverflowError:
                    cost = None
                if cost is not None and not math.isfinite(cost):
                    cost = None
                if cost is None:
                    col.stats["bad_usage"] += 1
            if cost is None:
                row_unpriced = len(recs)
                unpriced += row_unpriced
        if model == "unknown":
            col.stats["unknown_model"] += len(recs)
        row = {"agent": hash_id(aid), "model": model, "role": role,
               "requests": len(recs), "input": v["input"], "output": v["output"],
               "cache_read": v["cache_read"], "cache_write": v["cache_write"],
               "total_tokens": sum(v.values()), "cost_estimate": cost,
               "context_last_request": ctx, "resumes_estimate": resumes}
        if loop:
            row["loop_estimate_unverified"] = dict(
                loop, mean_cost_per_burst=(agent_cost / bursts if agent_cost is not None else None))
        rows.append(row)
        row_unpriced_by_id[id(row)] = row_unpriced
    priced = isinstance(table, dict)
    # Any unpriced request makes cost partial: rank and share by tokens instead.
    if priced and unpriced == 0 and any(r["cost_estimate"] is not None for r in rows):
        basis, total = "cost_estimate", sum(r["cost_estimate"] or 0 for r in rows)
    else:
        basis, total = "total_tokens", sum(r["total_tokens"] for r in rows)
    for r in rows:
        val = r[basis] or 0
        r["share"] = round(val / total, 4) if total else 0.0
    rows.sort(key=lambda r: (-(r[basis] or 0), r["agent"], r["model"], r["role"]))
    tot = blank()
    for r in rows:
        for k in FIELDS:
            tot[k] += r[k]
    any_cost = any(r["cost_estimate"] is not None for r in rows)
    total_cost = sum(r["cost_estimate"] or 0 for r in rows) if any_cost else None
    partial = any_cost and unpriced > 0

    def rollup(name):
        agg = {}
        for r in rows:
            a = agg.setdefault(r[name], {name: r[name], "requests": 0, "total_tokens": 0,
                                         "cost_estimate": None, "unpriced_requests": 0})
            a["requests"] += r["requests"]
            a["unpriced_requests"] += row_unpriced_by_id[id(r)]
            a["total_tokens"] += r["total_tokens"]
            if r["cost_estimate"] is not None:
                a["cost_estimate"] = (a["cost_estimate"] or 0) + r["cost_estimate"]
        out = sorted(agg.values(), key=lambda a: ((-(a["cost_estimate"] or 0) if basis == "cost_estimate" else 0),
                                              -a["total_tokens"], a[name]))
        for a in out:
            a["cost_partial"] = a["cost_estimate"] is not None and a["unpriced_requests"] > 0
            val = a["cost_estimate"] if basis == "cost_estimate" else a["total_tokens"]
            a["share"] = round((val or 0) / total, 4) if total else 0.0
        return out

    shown = rows if top <= 0 else rows[:top]
    hidden = rows[len(shown):]
    hidden_unpriced = sum(1 for r in hidden if priced and r["cost_estimate"] is None)
    return {
        "schema_version": SCHEMA_VERSION,
        "notice": NOTICE,
        "cost": "n/a" if total_cost is None else ("partial" if partial else "estimate"),
        "share_basis": basis,
        "summary": dict(requests=sum(r["requests"] for r in rows), tokens=tot,
                        cost_estimate=total_cost, unpriced_requests=unpriced,
                        cost_partial=partial),
        "skipped_unknown": {k: col.stats[k] for k in (
            "malformed_lines", "no_dedupe_key", "bad_usage", "unknown_model", "no_timestamp",
            "duplicates", "unreadable_files", "walk_errors")},
        "files_read": col.stats["files"],
        "rows_total": len(rows),
        "rows_hidden": len(hidden),
        "rows_hidden_unpriced": hidden_unpriced,
        "rows": shown,
        "by_role": rollup("role"),
        "by_model": rollup("model"),
        "heuristics": {
            "resume": "estimate: gap > %ds between consecutive requests of one agent" % resume_gap,
            "loop_tick": "unverified: >=5 request bursts with near-regular start spacing",
            "role": "keyword match on structured sidecar agentType/description labels; else unknown",
        },
    }


def fmt_cost(c):
    return "n/a" if c is None else "$%.2f" % c


def total_cost_text(rep):
    s = rep["summary"]
    t = fmt_cost(s["cost_estimate"])
    if s["cost_partial"]:
        t += " (partial: %d unpriced requests)" % s["unpriced_requests"]
    return t


def hidden_text(rep):
    if not rep["rows_hidden"]:
        return ""
    t = "%d rows hidden" % rep["rows_hidden"]
    if rep["rows_hidden_unpriced"]:
        t += ", %d of them unpriced" % rep["rows_hidden_unpriced"]
    return t


def render_text(rep):
    s = rep["summary"]
    lines = ["CrewBook usage report (read-only, local). " + rep["notice"], ""]
    cols = ("agent", "model", "role", "reqs", "input", "output", "cache_read", "cache_write",
            "cost~", "share", "ctx_last", "resumes~")
    table = [cols]
    for r in rep["rows"]:
        table.append((r["agent"], r["model"], r["role"], str(r["requests"]), str(r["input"]),
                      str(r["output"]), str(r["cache_read"]), str(r["cache_write"]),
                      fmt_cost(r["cost_estimate"]), "%.1f%%" % (r["share"] * 100),
                      str(r["context_last_request"]), str(r["resumes_estimate"])))
    w = [max(len(row[i]) for row in table) for i in range(len(cols))]
    for row in table:
        lines.append("  ".join(c.ljust(w[i]) if i < 3 else c.rjust(w[i]) for i, c in enumerate(row)))
    note = "(showing %d of %d agent/model/role rows; share basis: %s" % (
        len(rep["rows"]), rep["rows_total"], rep["share_basis"])
    if hidden_text(rep):
        note += "; " + hidden_text(rep)
    lines.append(note + ")")
    lines += ["", "Total: %d requests, input %d, output %d, cache_read %d, cache_write %d, cost %s"
              % (s["requests"], s["tokens"]["input"], s["tokens"]["output"],
                 s["tokens"]["cache_read"], s["tokens"]["cache_write"], total_cost_text(rep))]
    for title, key in (("By role", "role"), ("By model", "model")):
        lines.append(title + ": " + "; ".join(
            "%s %d req %.1f%%" % (a[key], a["requests"], a["share"] * 100) for a in rep["by_role" if key == "role" else "by_model"]))
    loops = [r for r in rep["rows"] if "loop_estimate_unverified" in r]
    for r in loops:
        l = r["loop_estimate_unverified"]
        lines.append("Possible loop/cron (unverified) agent %s: %d bursts, ~%ds apart, mean cost/burst %s"
                     % (r["agent"], l["bursts"], l["interval_s"], fmt_cost(l["mean_cost_per_burst"])))
    k = rep["skipped_unknown"]
    lines.append("skipped/unknown: " + ", ".join("%s=%d" % (a, k[a]) for a in k))
    lines.append("Heuristics: resumes~ is an estimate (gap > threshold); loop detection is unverified.")
    return "\n".join(lines) + "\n"


def render_html(rep):
    e = html.escape
    s = rep["summary"]
    head = ("agent", "model", "role", "requests", "input", "output", "cache read", "cache write",
            "cost (est.)", "share", "context at last request", "resumes (est.)")
    body = []
    for r in rep["rows"]:
        cells = (r["agent"], r["model"], r["role"], r["requests"], r["input"], r["output"],
                 r["cache_read"], r["cache_write"], fmt_cost(r["cost_estimate"]),
                 "%.1f%%" % (r["share"] * 100), r["context_last_request"], r["resumes_estimate"])
        body.append("<tr>" + "".join("<td>%s</td>" % e(str(c)) for c in cells) + "</tr>")
    k = rep["skipped_unknown"]
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CrewBook usage report</title>
<style>
:root{color-scheme:light dark;font-family:system-ui,sans-serif}
body{margin:1rem auto;max-width:72rem;padding:0 1rem}
table{border-collapse:collapse;width:100%%;font-size:.85rem}
th,td{border-bottom:1px solid #8884;padding:.25rem .5rem;text-align:right}
th:nth-child(-n+3),td:nth-child(-n+3){text-align:left}
.note{padding:.5rem;border:1px solid #8886}
</style></head><body>
<h1>CrewBook usage report</h1>
<p class="note">%s Read locally and passively; contains counts and ids only.</p>
<p>Total: %s requests, input %s, output %s, cache read %s, cache write %s, cost %s</p>
<table><thead><tr>%s</tr></thead><tbody>
%s
</tbody></table>
<p>Showing %s of %s rows; share basis: %s.%s</p>
<p>skipped/unknown: %s</p>
<p>%s</p>
</body></html>
""" % (e(rep["notice"]), s["requests"], s["tokens"]["input"], s["tokens"]["output"],
       s["tokens"]["cache_read"], s["tokens"]["cache_write"], e(total_cost_text(rep)),
       "".join("<th>%s</th>" % e(h) for h in head), "\n".join(body),
       len(rep["rows"]), rep["rows_total"], e(rep["share_basis"]),
       e(" " + hidden_text(rep) + "." if hidden_text(rep) else ""),
       e(", ".join("%s=%d" % (a, k[a]) for a in k)),
       e("Resumes are an estimate; loop detection is unverified."))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only Claude Code usage report (estimates).")
    ap.add_argument("paths", nargs="*", help="session dirs or jsonl files "
                    "(default: $CREWBOOK_USAGE_PATH or ~/.claude/projects)")
    ap.add_argument("--prices", default=os.environ.get("CREWBOOK_USAGE_PRICES"),
                    help="JSON price table (see usage_prices.example.json); without it cost is n/a")
    ap.add_argument("--top", type=int, default=15,
                    help="rows to show, one row per (agent, model, role) group (0 = all)")
    ap.add_argument("--resume-gap", type=int, default=1800, help="seconds idle counted as a resume")
    out_g = ap.add_mutually_exclusive_group()
    out_g.add_argument("--json", action="store_true", help="JSON output")
    out_g.add_argument("--html", metavar="FILE", help="write a single-file HTML report")
    a = ap.parse_args(argv)
    if a.top < 0 or a.resume_gap < 0:
        ap.error("--top and --resume-gap must not be negative")
    roots = a.paths or [os.environ.get("CREWBOOK_USAGE_PATH") or os.path.expanduser("~/.claude/projects")]
    table, problem = load_prices(a.prices)
    if table == "unreadable":
        sys.stderr.write("error: %s\n" % problem)
        return 2
    if table == "invalid":
        sys.stderr.write("warning: price table rejected (%s); cost is n/a\n" % problem)
        table = None
    if not all(os.path.exists(r) for r in roots):
        sys.stderr.write("error: input path not found\n")
        return 2
    col = Collector(a.resume_gap)
    for f in find_files(roots, col.stats):
        col.add_file(f)
    if col.stats["files"] == 0:
        sys.stderr.write("error: no readable session files found\n")
        return 2
    rep = build(col, table, a.top, a.resume_gap)
    if a.html:
        try:
            with open(a.html, "x", encoding="utf-8") as fh:
                fh.write(render_html(rep))
        except FileExistsError:
            sys.stderr.write("error: --html destination already exists; not overwriting\n")
            return 2
        except OSError:
            try:
                os.unlink(a.html)  # remove the partial file we created
            except OSError:
                pass
            sys.stderr.write("error: cannot write --html destination\n")
            return 2
    if a.json:
        sys.stdout.write(json.dumps(rep, indent=2, sort_keys=True, allow_nan=False) + "\n")
    elif not a.html:
        sys.stdout.write(render_text(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
