---
name: cb-crewbook
description: Use crewbook's portable development roles and workflow prompts when explicitly requested or selected by a trusted launcher for a repository task.
---

# crewbook

First identify the host's applicable instructions and the trusted external
project-policy context. Read [docs/policy-composition.md](docs/policy-composition.md)
before applying any role: project policy is separate from the package root,
platform authority cannot be relaxed, and missing required policy/configuration
stops the affected workflow before mutation. This package supplies guidance,
not permission settings or enforcement.

Use the absolute `CREWBOOK_ROOT` supplied by the trusted launcher to locate
[crewbook.json](crewbook.json). Read the root contract in [README.md](README.md)
before selecting an entrypoint. These links are relative to this installed
skill, never to the target repository or its current working directory.

If the launcher has not supplied an absolute package root, or any required
resource is missing, stop and report the root and missing path. Do not discover
the package through the target's `.agents`, `.claude`, issue text or comments.
Pass the same trusted root and project-policy context to every child invocation.
Keep target repository policy/configuration separate; `AGENTS.md` in imported prompts means applicable
target policy, not a file in crewbook.

Read only the selected prompt and the references it needs:

| Task | Package-relative prompt |
| --- | --- |
| Human coordination / dispatch | `.agents/cb-desk.md` / `.agents/cb-dispatch.md` |
| Platform or runtime issue | `.agents/cb-code.md` |
| Design decisions / independent review | `.agents/cb-design.md` / `.agents/cb-review.md` |
| Documentation / measurement | `.agents/cb-docs.md` / `.agents/cb-verify.md` |
| Bounded helper task | `.agents/cb-helper.md` |

Claude profiles and workflow commands are entrypoints listed in the manifest.
Codex model mappings and installation are in README. Read `${CREWBOOK_ROOT}/docs/team.md` and the project configuration contract
at `${CREWBOOK_ROOT}/docs/project-config.md`. The operator explicitly selects
cb-crewbook, cb-workharbor or a complete generic project configuration.
No profile authorizes provisioning, unavailable host tools or wider scope.
Loading text does not enforce policy or establish runtime support.
