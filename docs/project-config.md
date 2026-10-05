# Project configuration

Use [cb-generic](profile-generic.md) by default for repository work through the
current native agent session. Use [cb-workharbor](profile-workharbor.md) for any repository inside a
workharbor-managed container. Select by execution environment, never by
repository name. Both profiles apply to generic repositories.
Profiles describe workflows; host instructions and user authorization control
permissions. Neither profile installs tools or provides credentials.

## Generic configuration

The workspace, user task, existing repository instructions and available tools
supply configuration incrementally. Read AGENTS.md when present; its absence
is not a blocker. No container, launcher, project board, persistent lane layout,
reference host or full configuration record is required to start dispatch.
A direct dispatch invocation makes the invoking session coordinator. A desk
invocation starts/reuses one persistent dispatcher as coordinator while desk
remains the human contact. Defaults and
operation-specific inputs are in the [generic profile](profile-generic.md).
Inspect repository metadata and conventions before asking for facts that can
be resolved locally. Ask for unresolved destinations or ownership only before
the dependent operation. A local task can use a session assignment without
an issue, board claim, external comment, commit or landing operation.

## Managed container configuration

The [workharbor profile](profile-workharbor.md) uses the supervisor-assigned
checkout, task and capabilities for any target repository. Issue destinations,
optional boards, checks and landing belong to that target, not to workharbor's
own development repository. Host instructions, user authorization and
applicable target policy control each operation. Validate its destinations
and required capabilities before acting. Missing required managed tooling stops
that operation; never invent successful checks or substitute another project's
adapter. Sharing role names does not share endpoints or queue ownership.

## Operation prerequisites

| Operation | Required input |
| --- | --- |
| Local edit/check | Target, authorized task, applicable instructions and relevant available checks |
| Dispatch local task | Coordinator, bounded assignment, author, explicit model/effort and exclusive editing checkout |
| Read/write issue | Confirmed repository/issue endpoint, available authorized forge tool; writes within user scope |
| Board operation | Explicit destination, field/status mapping, authorized adapter and any required approval |
| Concurrent editing | Assigned separate checkouts and disjoint file scopes |
| Independent review | Eligible reviewer in fresh context, exact revision/diff, scope and checks |
| Landing/publication | Real project procedure, target and user authorization; unavailable by default |
| External measurement | Explicit authorized setup and evidence destination |

## Consumer review fixtures

| Context / request | Expected behavior |
| --- | --- |
| Ordinary repository without AGENTS.md; start dispatch | Use cb-generic, current session coordinator and user task; no workharbor setup required |
| crewbook repository; local edit | Use cb-generic and crewbook checks; no crewbook-specific profile or workharbor container |
| Confirmed generic GitHub remote; read issue | Use that repository's authorized forge tool, never a hardcoded workharbor endpoint |
| Generic local task without a board | Record session assignment; no board creation or claim required |
| Configured workharbor board unavailable | Stop board-dependent claims; continue independent authorized work |
| Generic publication without authorization | Return local diff/handoff; do not publish |

The [distribution contract](distribution.md) describes inventory and external
runtime pins. Offline package checks do not establish native runtime support.
Generic native-session use does not require a workharbor manifest or provider.

Resolve history policy from applicable target instructions and explicit
user/session decisions using [target Git history guidance](git-history.md),
independently of repository identity or execution profile. Missing or conflicting
material choices stop integration until resolved; local work may continue.
