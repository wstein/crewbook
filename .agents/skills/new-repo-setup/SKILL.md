---
name: new-repo-setup
description: Checklist for preparing a new repository so CI and the pull request workflow run smoothly; workflow triggers, required checks, pinned actions, repository files, bots and the settings only the owner sets.
---

# New repository setup

Use this when a repository is created from a template or from scratch, or when
a repository's CI starts to feel slow, doubled or stuck. Reference
implementation: the owner's template `wstein/flix-template` (workflows,
`dependabot.yml`, `AGENTS.md`, `CLAUDE.md`). Host authority and the user's scope
outrank this checklist. Never change repository settings, rulesets, tags or git
identity; list them for the owner instead.

## 1. Triggers and concurrency

- [ ] `push` only on the default branch; `pull_request` for topic branches. A
      topic push plus its pull request otherwise runs everything twice.
- [ ] `concurrency: { group: ${{ github.workflow }}-${{ github.ref }},
      cancel-in-progress: ${{ github.event_name == 'pull_request' }} }`. Never
      cancel default-branch or release runs.

## 2. Required checks

When the repository has a ruleset or branch protection, require only checks
that always report.

- [ ] One aggregate job (`suite` or `check`) with `if: always()` that fails on
      failed, cancelled or unexpectedly skipped `needs`. Require that job only.
- [ ] Never require per-shard or per-matrix-leg checks: a job skipped inside a
      matrix reports under the unexpanded name and stays pending.
- [ ] No workflow-level `paths-ignore` for a required workflow: the check is
      never started and the pull request waits forever.
- [ ] Docs-only gating: a `changes` job and `if:` on the heavy jobs only, only
      for `pull_request`, failing closed (unknown means run). Example:
      sourcesteward PR #117.

## 3. Workflow hygiene

- [ ] Pin every action by commit SHA with a version comment
      (`uses: actions/checkout@<sha> # v7.0.1`).
- [ ] `.github/dependabot.yml` with the `github-actions` ecosystem, monthly,
      `commit-message.prefix: ci`. Pins rot without it.
- [ ] `permissions: contents: read` at workflow level; write scopes per job.

## 4. Repository files

- [ ] `AGENTS.md`: test and check commands, layout, Conventional Commits.
      `CLAUDE.md` (and Copilot instructions) only point to it.
- [ ] `LICENSE`, `.editorconfig`, SPDX headers if the family uses them.
- [ ] A smoke test, and one local command (`make check` or equivalent) that
      runs the same things CI runs, so authors push green.

## 5. Bots and automation

- [ ] A lock-only updater must not build.
- [ ] A pull request created with `GITHUB_TOKEN` does not trigger CI. Dispatch
      the workflow with the expected head SHA, or use an App token (owner
      decision). Say so in the PR body.
- [ ] Bundle all changes of one automation run into one pull request. With a
      `strict` up-to-date rule every merge turns the other open pull requests
      BEHIND.

## 6. Timing

- [ ] Measure queue time against run time before optimising anything.
- [ ] Keep jobs under about 10 minutes; shard by measured weights.
- [ ] Never run the same suite twice (see step 1); cache what is safe to cache.

## 7. Template drift

A GitHub template copies files once and no settings, so derived repositories
drift. Consider `copier` when at least three repositories derive from one
template; do not add it earlier.

## What the owner must set by hand

- [ ] Rebase-merge only (linear history) and delete branch on merge.
- [ ] Ruleset or branch protection requiring only the aggregate check; decide
      on `strict` knowing step 5.
- [ ] Auto-merge, if wanted.
- [ ] Actions permissions (default read-only token, whether Actions may create
      pull requests) and the App token, if used.
- [ ] Dependabot and security features.
