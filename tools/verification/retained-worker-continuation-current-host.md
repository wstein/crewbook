# Retained completed worker: current tool-host continuation evidence

This bounded observation was recorded on 2026-10-13 for
[issue 26](https://github.com/wstein/crewbook/issues/26). It measures an actual
retained completed reviewer continuing through a named exact-artifact verdict
on the current API tool host. This source maintenance record is excluded from
the distributed skill by the existing `tools/` classification. It changes no
runtime behavior or guidance and does not establish issue acceptance or closure.

## Scope and artifact identity

The coordinator observed the existing same-item reviewer in host-reported
`completed` state and retained its ownership and handle. The reviewer's prior
candidate was `ebbcc7c10152722ef948be8c9ee5bfc9c16ef7e8`. The bounded follow-up
requested an independent read-only review of the continuation guidance at:

| Artifact | Exact Git identity |
| --- | --- |
| Source revision | `8fe5e900938c3195564b216794d2f3fc31d486e3` |
| `docs/team.md` blob | `a177d1d78360363fb7009ac07543232b19db354a` |
| `.agents/crewbook-dispatch.md` blob | `628b76b2b8cae7d7a47b2605a4cb476507711ffc` |
| Named awaited result | `worker-continuation-guidance-verdict` |

The measured surface was the API tool host exposing
`collaboration.followup_task` and coordinator UTC clock observations. The shell
reported Linux `7.0.14-orbstack-00380-ga7e0a2dc9535 aarch64` and Python 3.13.5.
These are shell platform observations, not a native Codex CLI/app build version;
no client version was supplied or measured. Private handles and raw transcripts
remain in the coordinator's private evidence; this record uses the stable role
label **retained reviewer**.

The executed command was `collaboration.followup_task` with the same retained
reviewer as target and the bounded exact-artifact assignment above. Its exit
status is **N/A**: this collaboration tool returns acceptance, not a numeric
shell exit code. The observed result was accepted on the same canonical handle,
followed by the named `CLEAR` verdict below. Log reference: the coordinator's
private 2026-10-13 retained-worker continuation measurement, summarized in this
record; private handles and raw transcript are intentionally not reproduced.

## Observed continuation

| Coordinator observation (UTC, 2026-10-13) | Actual event and outcome |
| --- | --- |
| `03:40:49` | Coordinator recorded the prior `completed` state and bounded continuation request for the retained reviewer and exact candidate above. |
| `03:41:17` | Actual `collaboration.followup_task` call was accepted on the same canonical task handle. No duplicate worker or owner was started. |
| `03:41:35` | Coordinator received the same retained reviewer's acknowledgment of the requested source revision and team blob. The acknowledgment explicitly was not the verdict. |
| `03:42:35` | Coordinator received the named `worker-continuation-guidance-verdict`: `CLEAR`, no findings, for the exact source revision and both blobs above. This was an independent read-only source guidance review. |

The coordinator retained the obligation after tool acceptance and acknowledgment,
then validated the owner, named result and exact artifacts on receipt of the
verdict. These are coordinator observation/receipt clocks, not worker-internal
timestamps, precise arrival times or a latency benchmark. Tool acceptance and
acknowledgment alone did not establish completion; the named verdict supplied
the observed result.

## Evidence boundary

The [2026-10-11 issue-26 record](issue-26-current-host.md) remains a historical
partial measurement of a delayed handback and steering while an author was
active. It did not measure continuation from a completed worker. Likewise, the
credential-free recovery replays described in [tools/README.md](../README.md)
model continuation decisions; their passing fixtures do not establish native
host behavior. This later observation separately establishes one actual
completed-reviewer continuation on the measured host through its exact-artifact
verdict, without replacing those earlier records or broadening their claims.

This observation does not establish running-worker updates, race recovery,
other providers or clients, automatic release or capacity semantics, background
survival after the parent ends, a daemon, or technical enforcement of guidance.
It also does not independently review this new evidence document: that remains
a separate exact-revision review obligation before readiness. No builds,
exports, installations, publication, tags or merges were part of this record's
authoring checks.

## Source checks

The following existing offline checks ran on the exact source revision above,
before adding this source-only Markdown record:

| Check | Observed result |
| --- | --- |
| `python3 -B -m unittest discover -s tools -p 'test_*.py'` | Exit 0; 324 tests in 5.556 seconds; `OK (skipped=1)`. |
| `python3 -B tools/crewbook-package.py check --root "$CHECKOUT"` | Exit 0; `source layout and inventory valid; runtime compatibility not established`. |

`$CHECKOUT` denotes the assigned isolated checkout. The author verified the Git
identities above directly. No executable behavior changed, so no artificial
failing regression or prompt-content parser was added. Existing layout and
inventory verification also applies after adding this excluded evidence file;
its outcome is retained in the author handback with the committed candidate SHA.
