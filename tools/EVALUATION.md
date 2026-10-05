# Offline evaluation evidence foundation (#14)

Run a deterministic, credential-free synthetic scoring self-check with stock
Python 3.9 or newer:

```sh
/usr/bin/python3 -B -m unittest discover -s tools -p 'test_evaluation.py'
/usr/bin/python3 -B tools/evaluation.py tools/evaluation-fixture.json
```

This maintenance artifact is excluded from the declarative exported package.
It does not execute prompts, clients, target code, or model runs. The fixture
contains invented outcomes and zero-filled placeholder hashes, explicitly
labelled synthetic; its report is not evidence of guidance effectiveness.

The v1 JSON format is a bounded implementation assumption for this partial
work item, not a prescribed issue-wide or workharbor runtime contract. Use the
fixture as the complete field example. Unknown or duplicate fields are rejected.
Tasks name their acceptance criteria and assert a SHA-256 fixture pin; each
run reports boolean completion for every named criterion, meaningful checks,
policy violation and review finding counts, and optional human review seconds.
There is no invented numeric quality scale or combined quality/cost score.
Efficiency fields remain separate; `null` means unknown, including cost.
Counts and durations are nonnegative integers; billed USD may be a finite
nonnegative number. No inference is made from absent efficiency measurements.

Declare all arms and the repetition count before scoring. Every task/repetition/
arm slot must appear exactly once. Failed and missing slots require explanatory
notes and null outcomes, remain in the report, and contribute to separate sample
sizes. The report retains individual results rather than averaging unlike
outcomes or silently removing failed/unmatched runs. Criteria and adverse
outcomes precede efficiency in the source evidence schema.

Every run must assert the identical configuration: repository Git revision,
client, model, reasoning, hashes of actual loaded instructions, and an
environment SHA-256 fingerprint covering matched task/tool/permission/budget
settings. Unlike configurations are rejected; score them separately. These
pins are format-checked assertions, not verified runtime bindings or instruction
loads. The report also hashes the exact input evidence bytes for reproducibility.
Evidence must already be sanitized before input; this tool does not redact it.

Remaining #14 work includes representative pinned Go/security fixtures,
independent scoring/review, verified #9 bindings, isolated contexts, repeated
paired runs with randomized arm order, arm-specific loaded instruction evidence,
and operator-approved runtime runs. This first schema deliberately supports one
exact configuration per evidence document; cross-arm instruction changes need
an explicitly reviewed matching/comparison design before any causal analysis.
Failed/missing synthetic records exercise reporting only. No adoption gate can
be decided from this self-check. Agent execution and host enforcement remain
workharbor-owned; paid/live runs require separate authorization.
