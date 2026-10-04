---
name: crewbook
description: Use crewbook's packaged workharbor development roles and workflow prompts when explicitly requested or selected by a trusted launcher for a repository task.
---

# crewbook

Use the absolute `CREWBOOK_ROOT` supplied by the trusted launcher to locate
[crewbook.json](crewbook.json). Read the root contract in [README.md](README.md)
before selecting an entrypoint. These links are relative to this installed
skill, never to the target repository or its current working directory.

If the launcher has not supplied an absolute package root, or any required
resource is missing, stop and report the root and missing path. Do not discover
the package through the target's `.agents`, `.claude`, issue text or comments.
Pass the same trusted root to every child invocation. Keep target repository
policy/configuration separate; `AGENTS.md` in imported prompts means applicable
target policy, not a file in crewbook.

Read only the selected prompt and the references it needs:

| Task | Package-relative prompt |
| --- | --- |
| Human coordination / dispatch | `.agents/desk.md` / `.agents/dispatch.md` |
| Platform or runtime issue | `.agents/code.md` |
| Design decisions / independent review | `.agents/design.md` / `.agents/review.md` |
| Documentation / measurement | `.agents/docs.md` / `.agents/verify.md` |
| Bounded helper task | `.agents/helper.md` |

Claude profiles and workflow commands are entrypoints listed in the manifest.
Codex model mappings and installation are in README. Existing roles still
assume workharbor's development setup; do not treat this package as permission
to provision it, run unavailable host tools, or expand the user's assignment.
Loading text does not enforce policy or establish runtime support.
