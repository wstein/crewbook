# Antigravity readiness

Full Antigravity (`agy`) support in [issue #10](https://github.com/wstein/crewbook/issues/10)
is **unverified and incomplete**. This reference records the evidence boundary
and the artifacts needed for admission; it does not provide an invocation
adapter, verified role bindings or a production manifest. Do not substitute
Codex model identifiers or Claude commands for native Antigravity behavior.

## Existing evidence

The pinned [historical workharbor #84 spike](https://github.com/wstein/workharbor/tree/2ba00767aa705c6981d21a4aab45c4cc78bcd013/spikes/agy)
used Antigravity 1.2.14 in a Linux ARM64 Fedora guest on an Apple Silicon host
with Apple Container and proxy/shim isolation. Its
[recorded results](https://github.com/wstein/workharbor/blob/2ba00767aa705c6981d21a4aab45c4cc78bcd013/spikes/agy/RESULTS.md)
report event streams, process-group cancellation and conversation resume,
alongside authentication/error and egress observations. These are historical
measurements against that setup, not measurements of current Crew Book discovery,
model selection, desk children or permission/configuration isolation.

A current-session version-only observation reported `agy` 1.2.16. Local
workharbor 1.2.16 Linux ARM64 glibc/musl pins and
[its verifier work (#164)](https://github.com/wstein/workharbor/issues/164)
are provisioning inputs; they do not establish Crew Book compatibility.
A version string proves neither the executable's provenance nor any runtime
capability. No current native run, login, inference or container provisioning
was performed for this documentation slice.

## Documented native subagent controls

The [native subagent documentation](https://www.antigravity.google/docs/subagents/)
describes parallel agents, `/agents` status inspection, model tiers `inherit`,
`flash` and `pro`, and a maximum nesting depth of ten. Depth is not concurrency
capacity. No equivalent numeric concurrency configuration was found in that
reviewed page; do not invent a flag or environment variable to match Codex or
Claude Code. Sequence assignments within the actual host's available capacity.

This is documented vendor behavior, **unverified** for Crew Book on a current
native setup. Native model tiers do not establish approved Crew Book role
bindings. The existing readiness matrix still governs admission; these controls
supply no production entrypoint or managed-runtime support.

## Capability admission matrix

Every current integration capability below is **unverified**. Each row needs
sanitized, committed evidence identifying the binary provenance/version,
platform, client configuration, package revision, test inputs, observed events
or denials, and remaining limits. Retain negative and malformed cases as well
as success; a zero exit status alone does not prove an action was allowed or
performed. Historical results must retain their original version and setup.

| Capability | Evidence required before claiming support | Owner and next action |
| --- | --- | --- |
| Native discovery/invocation | Load the external pinned package in an unrelated repository; demonstrate applicable crewbook-* selection, relative resource resolution, host/target policy precedence and explicit alternative/none selection. | Crew Book defines declarative resources; authorized native-client verification establishes how the client loads them. Do not guess a registration command. |
| Role/model/effort bindings | Show provider-specific identifiers and actual selected model/effort for each required role, including errors for unavailable bindings. | Design approves an exact tuple; verification measures it. Do not infer equivalence from Codex or Claude names. |
| Desk, dispatch and children | Observe one coordinator, author/leaf separation, independent review, actual child capabilities and no duplicate starts. | Crew Book owns workflow text; the client/host owns execution. Verify a real lifecycle rather than a generic adapter fixture. |
| Steering, cancel and resume | Capture current event shapes, malformed events, cancelled children, resume outcome and preserved package provenance/ownership. | Generic verification uses an authorized native session; workharbor owns supervisor integration and conformance tests for managed operation. Historical conversation resume is starting evidence only. |
| Approvals and configuration isolation | Demonstrate denied tools and planted settings, plugins, hooks and MCP cannot bypass mandatory controls, including soft denials with zero exit status. | Client/host security owner supplies enforceable controls. Unsupported mandatory controls stop the affected workflow; prose cannot enforce them. |
| Managed production binding | Confirm pinned stock binary, CLI/API/UI/doctor, authentication, quota/usage and Go conformance/security evidence against the approved tuple. | Workharbor owns provisioning and enforcement; resolve [production binding #283](https://github.com/wstein/workharbor/issues/283) before claiming managed support. |

## Generic and managed boundaries

The [generic profile](profile-generic.md) selects an ordinary native session,
including one in an unrelated repository without a managed container, board or
`AGENTS.md`. It uses existing authorized tools and host/target instructions.
Missing mandatory native discovery, approval or child capabilities must be
reported for the affected operation; a managed fixture does not fill that gap.

The [managed profile](profile-workharbor.md) selects the execution environment,
not a repository name. Workharbor supplies pinned binaries, supervisor behavior
and enforcement; Crew Book supplies declarative guidance. Human sign-in belongs
inside the approved environment through documented vendor flow. No host home
or keychain mounting, undocumented login automation, provider wrappers or
implicit provisioning is supplied by this reference.

Before any separately authorized live test, design must identify the exact
version/platform/protocol tuple, native model bindings, mandatory controls and
release constraints. Record evidence through the
[reporting contract](team.md#precise-issues-handovers-and-review-reports),
separating committed text, package checks, independent review and runtime
measurement. The existing [material-limitations guidance](material-limitations.md)
cannot waive security failures or unmet #10 criteria.

## When a capability fails

Identify the failed row and operation, exact tuple and evidence artifact.
Distinguish missing input, authentication/quota error, unsupported feature,
permission denial and uncertain outcome. Preserve ownership and provenance
across resume; do not retry an unchanged denial or call a generic replay a
native success. Route declarative gaps to Crew Book and runtime/security gaps
to the client or workharbor owner. Keep #10's unmet criteria open until the
required current, sanitized evidence exists. Package maintenance checks
validate this text artifact's integrity, not Antigravity runtime support.
