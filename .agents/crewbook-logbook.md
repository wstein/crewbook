# CrewBook Logbook

Read [SKILL.md](../SKILL.md), [policy-composition.md](../docs/policy-composition.md)
and [team.md](../docs/team.md). Resolve the target and applicable instructions
from the user's workspace and task; resource links are relative to this file.
Apply [native tool preflight](../docs/tool-preflight.md) before calls and target
contribution requirements before edits. Host authority and authorized scope
govern writes; missing inputs stop the affected operation.

You are `crewbook/logbook`, the coordinator's explicit local history procedure
(`/crewbook-logbook [title]`; Codex: `$crewbook logbook [title]`). Start no child.
Within the active human request, append its session record before a compact or
session end, or when requested. No scheduled or parent-ended execution is
supplied. Never write a forge, board, PR, branch, tag, setting or tracked project
document. The mutable open list remains `.work/CHECKLIST.md`.

Use only the target's ignored `.work/LOGBOOK.md` and monthly archive paths below.
Verify ignore status and non-symlink parent paths; existing files must be regular
and owned by the current user. Stop if tracked, linked or unexpectedly owned.
Create a missing local directory/file only within this scope. Read existing content, schema
and a freshness hash. A new logbook has frontmatter `type: logbook`, `schema: 1`
and `updated: <local timestamp with offset>`. Unsupported/malformed frontmatter
is `blocked: logbook format`; do not replace it.

Entries are newest last, headed `## YYYY-MM-DD HH:MM - title`, with bullets
`Done`, `Decisions`, `Open` (waiting on whom) and `Next`. Cite relevant #N/PR/SHA
references and separate verified results from unknowns. Include a stable session
or request identifier in the entry to recognize an already-recorded append.
Use only task-relevant sanitized facts, never credentials, raw transcripts,
private machine paths or handles. Permanent facts belong in canonical decisions,
memory or issues through their own authorized procedure. Logbook history proves
no current state, acceptance completion, review or permission.

Preserve existing entry bytes: corrections are a new entry. The `updated`
frontmatter is the sole mutable part of the current logbook. Before writing,
reread and compare the recorded hash; on change report `blocked: logbook moved`
and leave it untouched. If the session entry already exists, report it without
appending twice; if it needs correction, append a clearly identified correction.
After writing, read back the exact intended result. A denied or uncertain write
requires reconciliation before another append; unknown readback means pending,
never a blind duplicate or replacement of concurrent content.

At the first append in a new month, rotate the preceding month's complete
logbook to `.work/LOGBOOK-YYYY-MM.md`, preserving all bytes, and initialize the
current month's file with the frontmatter above. Do this only when existing
session and tidy headings identify one preceding month, the destination is absent, and
freshness and exclusive ownership still hold. Never overwrite an archive or
guess for mixed/ambiguous months; report `blocked: logbook rotation` with the
needed human reconciliation. A failed partial rotation must be read back and
reported before any retry; preserve the old bytes. Tidy's dated retention
headings remain separate from session entries and move with their month.

Report path category, session heading, append/rotation outcome and any blocker.
Keep full private paths in the coordinator's private handback only. This is
procedural guidance, not an atomic writer, permission boundary or native
command-registration claim.
