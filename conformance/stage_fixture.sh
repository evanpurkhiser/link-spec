#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <generated-fixture-directory>" >&2
  exit 2
fi

source_dir=$(realpath "$1")
root=$(cd "$(dirname "$0")/../.." && pwd)
stage="$root/rekordbox-windows/shared/link-export-conformance"

test -f "$source_dir/master.db"
test -f "$source_dir/manifest.json"
mkdir -p "$stage"
rm -f "$stage/active-guest-manifest.json"
install -m 0644 "$source_dir/master.db" "$stage/master.db"
install -m 0644 "$source_dir/manifest.json" "$stage/manifest.json"
install -m 0644 "$(dirname "$0")/switch-fixture.ps1" "$stage/switch-fixture.ps1"

printf '%s\n' 'Staged at \\host.lan\Data\link-export-conformance'
printf '%s\n' 'Guest command: powershell -ExecutionPolicy Bypass -File \\host.lan\Data\link-export-conformance\switch-fixture.ps1 -Fixture \\host.lan\Data\link-export-conformance'
