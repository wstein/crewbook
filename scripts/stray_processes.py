#!/usr/bin/env python3
"""Report stray test processes (read-only, stdlib only, Python 3.9+).

Lists processes that look like leftovers of a finished or runaway test run:
the command line names a Go/pytest/jest style temp test directory (a path
under /tmp, /var/tmp, /var/folders or $TMPDIR containing /Test<Name> or pytest-of-<user>)
and the process is orphaned (ppid 1) or has run longer than 10 minutes at more
than 80% CPU. It never kills anything; it prints the commands for the human.

  stray_processes.py            # runs: ps -axo pid=,ppid=,etime=,pcpu=,command=
  stray_processes.py --input F  # parse canned ps output from F ('-' = stdin)

False positive: a legitimate long run (make check-ci, go test -race) still
alive. Check elapsed time and the parent before acting; a process with a live
parent shell younger than the longest expected run is not stray.
"""
import argparse
import os
import re
import subprocess
import sys

PS_ARGS = ["ps", "-axo", "pid=,ppid=,etime=,pcpu=,command="]
MAX_SECONDS = 600
MAX_CPU = 80.0
CAP = 200
LINE = re.compile(r"\s*(\d+)\s+(\d+)\s+(\S+)\s+([0-9]+(?:\.[0-9]+)?)\s+(.*)")
TESTDIR = (r"(?:/Test[A-Za-z0-9_]*[^\s'\"/]*|/pytest-of-[^/\s'\"]+)(?:/[^\s'\"]*)?")
TESTNAME = re.compile(r"/(Test[A-Za-z0-9_]*?)(?:\d+)?(?:/|$)")


def temp_regex(tmpdir=None):
    roots = ["/private/var/folders", "/var/folders", "/private/tmp", "/tmp", "/var/tmp"]
    if tmpdir and tmpdir.startswith("/") and tmpdir not in ("/", ""):
        roots.append(tmpdir.rstrip("/"))
    alt = "|".join(re.escape(r) for r in roots)
    # The path must start at a token boundary, so /home/u/proj/tmp/TestX does not match.
    return re.compile(r"(?<![\w./-])(?P<dir>(?:%s)[^\s'\"]*?%s)" % (alt, TESTDIR))


def etime_seconds(text):
    """Parse ps etime [[dd-]hh:]mm:ss; None if malformed."""
    m = re.fullmatch(r"(?:(\d+)-)?(?:(\d+):)?(\d+):(\d+)", text)
    if not m:
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def parse(text):
    """Return (rows, unparsed). Splits on newline only: argv can hold U+2028."""
    rows, bad = [], 0
    for line in text.split("\n"):
        if not line.strip():
            continue
        m = LINE.fullmatch(line)
        age = etime_seconds(m.group(3)) if m else None
        if age is None:
            bad += 1
            continue
        rows.append({"pid": int(m.group(1)), "ppid": int(m.group(2)), "age": age,
                     "etime": m.group(3), "cpu": float(m.group(4)), "cmd": m.group(5)})
    return rows, bad


def clean(text, cap=CAP):
    """Printable ASCII only (escapes control, bidi, non-ASCII), capped."""
    out = "".join(c if " " <= c <= "~" else ascii(c)[1:-1] for c in text)
    return out if len(out) <= cap else out[:cap] + "..."


def find_stray(text, self_pid=None, tmpdir=None, verify=None):
    """Return (strays, unparsed). verify(pid) -> (ppid, cmd) or None, to re-check live."""
    rows, bad = parse(text)
    rx = temp_regex(tmpdir)
    out = []
    for p in rows:
        if p["pid"] == self_pid:
            continue
        m = rx.search(p["cmd"])
        if not m:
            continue
        orphan = p["ppid"] == 1
        busy = p["age"] > MAX_SECONDS and p["cpu"] > MAX_CPU
        if not (orphan or busy):
            continue
        if verify is not None and verify(p["pid"]) != (p["ppid"], p["cmd"]):
            continue
        t = TESTNAME.search(m.group("dir") + "/")
        reasons = []
        if orphan:
            reasons.append("orphaned (parent pid 1, the test run that started it is gone)")
        if busy:
            reasons.append("busy for over 10 minutes at over 80% CPU")
        p.update(tmpdir=m.group("dir"), test=t.group(1) if t else None,
                 why=" and ".join(reasons), orphan=orphan,
                 children=[r["pid"] for r in rows if r["ppid"] == p["pid"]])
        out.append(p)
    return out, bad


def render(strays, bad=0):
    lines = []
    if bad:
        lines.append("%d ps rows not parsed (unexpected format); results may be incomplete" % bad)
    if not strays:
        lines.append("no stray test processes")
        return "\n".join(lines) + "\n"
    for p in strays:
        lines += [
            "pid %d: age %s, cpu %.1f%%, ppid %d" % (p["pid"], p["etime"], p["cpu"], p["ppid"]),
            "  temp dir: %s" % clean(p["tmpdir"]),
            "  test: %s" % (p["test"] or "unknown"),
            "  why: looks stray, %s" % p["why"],
            "  command: %s" % clean(p["cmd"]),
            "  children (ppid %d): %s" % (p["pid"], ", ".join(map(str, p["children"])) or "none"),
            "  stop it: kill %d    (if it survives: kill -KILL %d)" % (p["pid"], p["pid"]),
            "  note: killing a shell can leave its children running; stop listed children too.",
            "",
        ]
    lines.append("nothing was killed; check the parent and elapsed time before running kill.")
    return "\n".join(lines) + "\n"


def run_ps(args, env_lc=True):
    env = dict(os.environ, LC_ALL="C")
    r = subprocess.run(args, capture_output=True, env=env, check=False)
    return r.stdout.decode("utf-8", errors="replace")


def live_verify(pid):
    rows, _ = parse(run_ps(["ps", "-p", str(pid), "-o", "pid=,ppid=,etime=,pcpu=,command="]))
    if len(rows) != 1 or rows[0]["pid"] != pid:
        return None
    return rows[0]["ppid"], rows[0]["cmd"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", help="canned ps output file ('-' = stdin)")
    a = ap.parse_args(argv)
    if a.input:
        raw = sys.stdin.buffer.read() if a.input == "-" else open(a.input, "rb").read()
        text, verify = raw.decode("utf-8", errors="replace"), None
    else:
        text, verify = run_ps(PS_ARGS), live_verify
    strays, bad = find_stray(text, os.getpid(), os.environ.get("TMPDIR"), verify)
    sys.stdout.write(render(strays, bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
