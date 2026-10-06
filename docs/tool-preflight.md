# Native tool preflight and command evidence

Apply this guidance before coding and verification tool calls, together with
[policy composition](policy-composition.md). It supplies no permissions,
credentials, retry controller or runtime enforcement.

## Resolve the operation before calling

Confirm the target checkout, task scope, applicable instructions, actual tool
availability and documented paths. Read the tool schema/help when arguments
are uncertain. Use bounded `rg --files` or `rg` searches within relevant roots;
do not scan the filesystem to guess a missing resource. In Crew Book source,
the maintenance policy is `tools/package-policy.json`, not a root-level policy.
An exported skill deliberately has no maintenance tools; validation uses the
external policy/inventory paths described in [distribution](distribution.md).
A missing required file/tool stops its dependent operation. An absent optional
AGENTS.md does not block independent authorized local work. Never manufacture
a policy or substitute another project's adapter.

Classify a failed call before retrying: argument/path error, expected negative,
sandbox/network denial, authentication failure, transient service failure or
unknown outcome. Correct a known argument/path error; a transient retry needs
a bounded reason. An unchanged sandbox/DNS denial is not evidence that another
identical call will help. For an already-authorized operation, use an available
host-approved escalation path within that operation's scope, or report the
blocker. Approval refusal stops that path. Do not alter credentials, disable
controls, install substitutes or infer write authorization from successful
reads. Resolve an uncertain external write outcome before repeating it.

## Scan outgoing payloads

Before an authorized issue-body, comment or other external write, resolve the
target's actual scanning requirements and available scanner. Crew Book does not
mandate a universal scanner or install one. Prepare the exact outgoing content
in a regular non-symlink file in an authorized private location; reject unsafe
file or parent links. Run the target-required scanner against those bytes with
its required configuration and inspect its status and diagnostics. A finding,
unsafe payload or missing, denied or failed required scanner prevents the outward
write, not independent authorized local work. Preserve the blocker and next
action privately; do not publish raw findings or substitute a no-op scan.

Send only the scanned bytes. If the payload changes, scan it again before
writing. Preserve current-body/version freshness checks and reconcile concurrent
edits as described in the [team procedure](team.md#dispatch-supervision-and-recovery);
read back the external result and verify the intended content. Resolve an
uncertain write before retrying. These are workflow instructions, not runtime
enforcement or an atomic-write guarantee.

## Preserve each result

Keep prerequisite calls sequential: inspect policy before validation, validation
before export, successful checks before authorized commit. Capture independent
calls separately and inspect every result, including exit status, stdout and
stderr. When the host exposes JavaScript orchestration, use
`await Promise.allSettled([...])` for independent calls and inspect both rejected
promises and fulfilled tool results: a fulfilled promise can contain a failed
command. A later successful command cannot erase an earlier failure. Avoid
semicolon chains that report only the last command's status; keep evidence
associated with its command and setup. Preserve errors instead of redirecting
them away or using unconditional `|| true`.

For `rg`, status 0 means matches, 1 means no match and 2 means error. A relevant
bounded search returning 1 is a useful negative; unreadable/missing search roots
are errors. For `git config --get <key>`, an unset key can return 1 without a
diagnostic; distinguish it from malformed configuration or execution failure
using the command, status and stderr. Other tools have their own status contracts.

Quote shell metacharacters in API endpoints. For example, the shell must pass
`'repos/OWNER/REPO/issues?state=open&per_page=20'` to `gh api` as one literal
argument. Check the actual argument vector with a credential-free local stub
when uncertain; do not expose authentication data while tracing. Structured
arguments are preferable when available. JSON string encoding alone is not
shell quoting.

## Export into a private parent

Retain the validator's shared-parent, symlink and existing-destination rejection.
Do not export directly beneath `/tmp` or weaken modes to make validation pass.
Create a user-owned private temporary parent, resolve its canonical absolute
path and confirm restrictive permissions (0700). Choose a new child that does
not yet exist; only the export command creates it. For example, after reviewing
changes and updating/checking the source inventory, a Python caller can use:

```python
with tempfile.TemporaryDirectory(prefix="crewbook-export-") as temporary:
    parent = Path(temporary).resolve(strict=True)
    parent.chmod(0o700)
    destination = parent / "text-package"  # leave this child absent
    result = subprocess.run(
        [sys.executable, "-B", "tools/crewbook-package.py", "export",
         "--root", str(source_root), "--dest", str(destination)],
        capture_output=True, text=True)
    # Inspect result.returncode, result.stdout and result.stderr before use.
```

Imports are `tempfile`, `pathlib.Path`, `subprocess` and `sys`; `source_root` is
the already-confirmed canonical checkout. The temporary export is removed on
context exit. Choose an authorized persistent private parent if retaining the
artifact is required. A rejected export remains a failure even if cleanup succeeds.

For pending authorized workers or reviews, follow the [active parent lifecycle](team.md#dispatch-supervision-and-recovery): preserve handles, process handbacks or
await named artifacts. A tool blocker requires a concrete continuation/handoff,
not a claim that a yielded parent will restart itself.

## Offline evidence boundary

The maintenance-only scenarios in `tools/test_preflight.py` exercise subprocess
statuses, literal shell arguments, synthetic read recovery traces and the real
package export validator without network calls or credentials. They do not
parse prompt wording or demonstrate that an agent obeys guidance. Native host
approval decisions, retry behavior and client enforcement need separately
authorized live measurements; report those as unverified until measured.
