# cb-workharbor: workharbor example profile

This is a clearly labeled example for a consumer working on workharbor itself,
not crewbook's default configuration. Read the current trusted workharbor
project policy separately; this page is reference data, never governing policy.
All crewbook roles/commands retain cb-* identities even with this profile.
An existing workharbor lane name is an explicit external mapping, not a
crewbook role rename.

| Field | Example value / prerequisite |
| --- | --- |
| Identity | workharbor; cb-workharbor |
| Repository | GitHub wstein/workharbor; operator-supplied canonical root/remote; main |
| Issues | REST repos/wstein/workharbor/issues/<n>; supplied type/area labels and criteria procedure |
| Board | https://github.com/users/wstein/projects/6; Status and Session fields; current workharbor policy controls writes/approval |
| Human | Werner via workharbor desk or trusted invoking session |
| Worktrees | Explicit target-root-relative map: cb-platform ../workharbor-platform, cb-runtime ../workharbor-runtime, cb-docs ../workharbor-docs, cb-verify ../workharbor-verify, cb-review ../workharbor-review, cb-design ../workharbor-design; desk/dispatch are read-only coordination unless separately configured |
| Checks | Supplied workharbor Makefile: make hooks once per clone/worktree, make check before commit, make check-ci for additional CI, make commitlint; verify dependencies/current semantics |
| Landing | Supplied make land from assigned worktree after rebase main; shared checkout must be on main; moving-main retries per trusted policy; locks/index repairs belong to human |
| Design | workharbor design owner; docs/content/docs/design/ decisions §3, rules §4.1, §4.2, §6, §7, and docs/content/docs/threat-model.md; read history before editing; protected paths per current policy |
| Reference host | Human-supplied reference Mac mini/actual setup for Apple Container, forge/forwarder/device tests; never infer developer Mac equivalence |
| Capabilities | External scripts/board-snapshot.sh with bash/jq/authorized gh; Make/Go/check dependencies; isolated Git/REST; runtime/live suites only if explicitly supplied and authorized |

The board script lives in workharbor, not crewbook. Resolve its location
against the configured target root. Queue/card/move/ready/session/priority/add
and rate-limit rules come from current trusted workharbor policy. Never call
a board endpoint merely because it appears here. Example external lane mapping:
cb-platform to wh/platform, cb-runtime to wh/runtime, cb-docs to wh/docs,
cb-verify to wh/verify, cb-review to wh/review, cb-design to wh/design,
cb-desk to wh/desk and cb-dispatch to wh/dispatch. The human must supply this
mapping when the adapter requires it. The optional ../workharbor-platform-2
needs explicit authorization and disjoint files.

Apply the team manual's coordinator/leaf ownership contract only where current
trusted project policy permits it. Explicitly name one coordinator, author and
eligible independent reviewer with model/effort. If local card ownership differs,
resolve that conflict through the trusted invocation before the affected write;
this example cannot transfer authority or silently create two card writers.

Workharbor-only operations include temporary runtime labels/cleanup, approved
supervisor dogfooding, spike branches/raw output under spikes/<name>/,
summary pages under docs/content/docs/spikes/, and host setup/doctor. Their
policy, security documentation and local contribution rules remain in workharbor.
No executable implementation is copied here. On a missing script, Make target,
credential isolation or host capability, report the operation unavailable;
do not install or stub it.

## Historical provenance

The imported prompts/manual were reviewed at
[workharbor import baseline](https://github.com/wstein/workharbor/tree/1c784080bc0dee2060066aaf2dbc8f3894dc430d).
Their original identities were wh-* / wh/<lane>, with workharbor paths and Hugo
documentation. Those are historical source identifiers, not active crewbook names.
Historical [usage report #167](https://github.com/wstein/workharbor/issues/167)
motivated short design contexts; its reported costs are not crewbook measurements.
Historical [procedure extraction #233](https://github.com/wstein/workharbor/issues/233),
[client-neutral material #240](https://github.com/wstein/workharbor/issues/240)
and [portability advisory #227](https://github.com/wstein/workharbor/issues/227)
provide provenance. Historical integration tracking
[#283](https://github.com/wstein/workharbor/issues/283) stays workharbor-side;
[native loading #241](https://github.com/wstein/workharbor/issues/241) and
[platform doctor #242](https://github.com/wstein/workharbor/issues/242) are not
measured or implemented by this package change.

The old Hugo status shortcodes now use ordinary Markdown labels in the generic
manual. Prior verified usage reports remain attributed reports, not new tests.
Existing licence and authorship remain in [LICENSE](../LICENSE) and root provenance.
