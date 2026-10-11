# Run metrics procedure

This procedure records evidence for [model/effort choices](team.md#model-effort-matrix)
and worker allocation. It does not collect native timing or establish provider
performance. The coordinator records one delegated run at each handback,
including resumed author, reviewer, design, docs and helper runs, before reporting
the outcome. Use the configured evidence destination, or the session handoff
when none exists. Recording never authorizes an external write.

## Preserve observations first

An optional private CSV/TSV or Markdown ledger can use these columns:

```text
ref run role model effort revision source date tokens minutes rounds high medium low ci_first_try clear candidate_ready review_start findings_return corrected_candidate clear_at
```

`ref` identifies the issue/PR; `run` distinguishes the initial run and resumes.
`revision` is the exact source SHA; `source` identifies the observed handback,
review record, check result or timestamp event. Record actual model/effort,
including authorized substitutions. Use `unknown` for any unavailable value;
zero means an observed zero. Keep sensitive paths, handles and raw transcripts
out of public records. A ledger is evidence, not a required registry extension.

Tokens and minutes are **incremental per run**. If a client reports cumulative
usage, subtract the previous observed cumulative value from the same agent's
current value; retain both source observations. A missing baseline, reset,
ambiguous units or model estimate leaves the delta unknown. Do not subtract
between agents or treat a cumulative total as a resume's incremental cost.
Issue #108's historical figures are indicative cumulative observations; they
are not a calibrated dataset and cannot fill missing deltas or timestamps.

Record rounds and findings by severity, CI first-try result and CLEAR only when
observed. At CLEAR or merge, put the final PR results on the final author and
CLEAR reviewer records; intermediate runs do not repeat the final counts.
Distinguish initial review and correction rounds from a separate rebase/delta
review in the evidence so scopes can be compared. Count each review response
as one round; retain unresolved findings and unavailable CI as unknown.

For turnaround, retain observed candidate-ready, review-start, findings-return,
corrected-candidate and CLEAR timestamps with exact revision and source. Derive
elapsed intervals only between available observations in the same timeline;
missing timestamps, model estimates and synthetic traces leave turnaround
unknown. A run's wall time is separate from queue/review turnaround. This adds
no `RUNS.tsv` fields or registry keys and implements no timing collector.

Synthetic example only (invented reference and SHA; no measured run):

```text
ref: #9999999; run: initial; role: author; model: gpt-6.1-sol; effort: medium
revision: 0000000000000000000000000000000000000000; source: synthetic-example
date: unknown; tokens: unknown; minutes: unknown; rounds: unknown
high: unknown; medium: unknown; low: unknown; ci_first_try: unknown; clear: unknown
candidate_ready: unknown; review_start: unknown; findings_return: unknown
corrected_candidate: unknown; clear_at: unknown
```

## Optional numeric report

The existing stdlib-only `scripts/runs_report.py record ...` appends validated
numeric rows to local, git-ignored `.work/RUNS.tsv`, creating schema/header:

```text
# crewbook-runs schema=1
date ref role model effort tokens minutes rounds high medium low ci_first_try clear
```

The actual separator is a tab. See `python3 scripts/runs_report.py record --help`
for flags; `report --file PATH` prints a summary and `--json` gives structured
output. This script accepts no free text, source SHA, timing events or unknown
numeric values. Preserve those in the evidence ledger. Append a numeric row
only when its values are known; never replace missing tokens/minutes/findings
with zero or unknown CLEAR with `n` merely to satisfy the schema. Its default
zero findings/rounds and `clear=n` are not unknown markers. `ci_first_try=-`
is supported. Records with incomplete evidence can remain ledger-only.

The report groups by role/model/effort and derives tokens and minutes per
CLEAR, rounds per PR, findings per PR by severity and CI first-try rate.
Tokens per CLEAR include costs of uncleared PRs. A PR spanning efforts has
its CLEAR in only one group; cost comparisons across those groups are
indicative, not verified. Beside each metric and each comparison group, report
complete-observation sample size `n`, unknown count, omitted count and the
relevant evidence-ledger denominator, naming the unit (runs, PRs or observed
intervals). Include ledger-only runs in that denominator; the script's numeric
rows and distinct-PR count do not describe missing evidence. State the selection
rule and do not silently drop unknown or omitted observations. Report coverage
for each compared group separately; incomplete coverage limits the aggregate
and any comparison.

## Ten-PR follow-up

A report group needs at least ten distinct **real PRs** before it loses the
script's `not enough data` marker. That count alone does not establish complete
usage, matched scope or a benefit. The coordinator opens the first summary in
a follow-up issue only when publication is authorized, linking source records
and exact revisions, known/missing metric coverage and comparable setup/scope.
Compare medium versus high effort for shared logic separately by provider;
keep native host/model differences explicit. Do not calibrate the matrix from
synthetic examples, historical cumulative figures or fewer than ten real PRs.
Until sufficient comparable observations exist, efficiency and turnaround
benefits remain unverified; retain missing-data gates in the handoff.
