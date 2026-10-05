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

## Pinned task fixtures (partial #14)

Run the added credential-free, deterministic self-check on stock Python 3.9+:

```sh
/usr/bin/python3 -B -m unittest discover -s tools -p 'test_evaluation_fixtures.py'
/usr/bin/python3 -B tools/evaluation_fixtures.py
```

`evaluation-fixtures/pins.json` pins the exact bytes of two task JSON records
and their broken/correct Go examples. The scorer verifies all six file hashes
before scoring; these are actual SHA-256 digests, replacing no pins in the older
synthetic `evaluation-fixture.json`. Updating a fixture requires reviewing its
expectations, source examples and pins together. The files are maintenance-only
under the already excluded `tools/` tree; they add no runtime package dependency.

The shared-adapter task requires JSON and CLI callers to use shared normalization
and preserve an adapter denial. The path task requires static containment and
rejection of every symlink component. Its adversarial expectations include parent
traversal, absolute input, sibling-prefix escape, leaf/parent symlinks and nested
traversal. The broken path example passes its ordinary file case while failing
all six boundary cases. The correct examples pass the specified cases. These
finite examples are not production file-access implementations; a real opener
must address concurrent filesystem changes separately.

Tests specify the expected failures independently of the reference replay. The
Python implementation replays only two fixed local demonstrations; it never
executes the Go files or arbitrary submissions. Go is fixture data here, so no
compiler is required or measured. The Go examples and Python replays represent
the same small contracts; their equivalence has not been measured by execution.
The visible expected outcomes and correct examples make this a public self-check,
not a held-out corpus. Before any agent experiment, separate the evaluator's
oracle/correct sources from candidate task inputs and independently review that
boundary to prevent answer leakage. No hidden-test independence is claimed.

`score(task, observations)` reports each named criterion as pass, fail (with
expected/observed values), or unknown (absent/null). It rejects extra observation
names and unknown tasks; exact types matter, so `1` cannot stand in for `true`.
Completion requires every criterion to pass. Security/policy counts, review
findings, human review effort and efficiency remain null until separately
measured; neither missing outcomes nor unknown metrics become zero. This
report is separate from the evidence-document format in `evaluation.py` and
does not invent model bindings or convert replay outcomes into live runs.

This change supplies only two representative pinned task families and descriptive
scoring demonstrations. Authorization/config injection, process cleanup and
concurrency fixtures, broader independent adversarial calibration, matched
repeated randomized model runs, loaded-instruction evidence, verified native
bindings and task-specific adoption gates remain unmet. The bundled issue
criteria stay unchecked. Paid/live runs still require separate authorization;
no guidance-effectiveness, safety, efficiency or adoption claim follows here.
