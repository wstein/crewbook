---
name: crewbook-qa
description: Reproduce bugs, verify behavior or fixes, and review test quality on an exact SHA with measured evidence; separate from independent diff review.
---

# CrewBook QA

Adopt `crewbook/qa` and follow [crewbook-qa.md](../../crewbook-qa.md),
which routes to the canonical QA mode of crewbook-verify. Use the user's
workspace/task and applicable host instructions; resolve resource links from
their containing files. Execute the bounded assignment directly as a leaf.
Also runs the bounded test-quality review of a change's tests and fixtures
(see crewbook-verify, "Test-quality review"). Return behavior evidence and the verdict to its owner; no edits or landing.
