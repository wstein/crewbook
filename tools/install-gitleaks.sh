#!/usr/bin/env bash
set -euo pipefail
destination=${1:?usage: install-gitleaks.sh NEW_DESTINATION}
test ! -e "$destination"
case "$(uname -s)/$(uname -m)" in
  Linux/x86_64)
    platform=linux_x64
    digest=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
    ;;
  Darwin/arm64)
    platform=darwin_arm64
    digest=b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5
    ;;
  *) printf 'unsupported scanner installation platform\n' >&2; exit 1 ;;
esac
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
archive="gitleaks_8.30.1_${platform}.tar.gz"
curl --fail --location --silent --show-error --retry 2 --max-time 120 \
  "https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/$archive" \
  --output "$temporary/$archive"
printf '%s  %s\n' "$digest" "$temporary/$archive" > "$temporary/checksums"
if command -v sha256sum >/dev/null; then
  sha256sum --check "$temporary/checksums"
else
  shasum -a 256 --check "$temporary/checksums"
fi
tar -xzf "$temporary/$archive" -C "$temporary" gitleaks
install -m 0755 "$temporary/gitleaks" "$destination"
