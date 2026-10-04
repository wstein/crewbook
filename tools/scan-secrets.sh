#!/usr/bin/env bash
set -euo pipefail
root=${1:?usage: scan-secrets.sh ABSOLUTE_ROOT PINNED_GITLEAKS}
scanner=${2:?usage: scan-secrets.sh ABSOLUTE_ROOT PINNED_GITLEAKS}
test "$("$scanner" version)" = '8.30.1'
export GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_GLOBAL=/dev/null
export GIT_TERMINAL_PROMPT=0 GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=credential.helper GIT_CONFIG_VALUE_0=''
export SSH_AUTH_SOCK='' GIT_SSH_COMMAND='ssh -oBatchMode=yes -oIdentityAgent=none'
cd "$root"
test "$(pwd -P)" = "$root"
test "$(git rev-parse --is-shallow-repository)" = false
test "$(git rev-list --all --count)" -gt 0
test -n "$(git ls-files)"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
options=(--config "$root/tools/gitleaks.toml" --redact=100 --no-banner --no-color --log-level info --exit-code 1 --timeout 180 --ignore-gitleaks-allow --gitleaks-ignore-path "$temporary/no-ignore")
verify_scan() {
  awk -v required="$1" '
    / ERR | FTL / { bad = 1 }
    /[1-9][0-9]* commits scanned\./ { commits = 1 }
    /scanned ~[1-9][0-9]* bytes/ { bytes = 1 }
    END { exit !(bytes && !bad && (required != "history" || commits)) }
  ' "$temporary/log" || { printf 'scanner failed or scanned no content\n' >&2; exit 1; }
}
"$scanner" git "${options[@]}" --log-opts='--all --full-history' "$root" > "$temporary/log" 2>&1 || { printf 'history scan rejected; matches withheld\n' >&2; exit 1; }
verify_scan history
"$scanner" dir "${options[@]}" "$root" > "$temporary/log" 2>&1 || { printf 'tree scan rejected; matches withheld\n' >&2; exit 1; }
verify_scan tree
git log --all --format='%B' | "$scanner" stdin "${options[@]}" > "$temporary/log" 2>&1 || { printf 'message scan rejected; matches withheld\n' >&2; exit 1; }
verify_scan messages
printf 'nonempty full history, working tree and commit messages scanned with redaction\n' >&2
