#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <generated-fixture-directory>" >&2
  exit 2
fi

readonly source_dir=$(realpath "$1")
readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/../.." && pwd)
readonly guestctl="$root/rekordbox-link-export-research/guest-control/guestctl"
readonly guest_stage='C:/Users/Research/link-export-conformance'
readonly host_marker="$root/rekordbox-windows/shared/link-export-conformance/active-guest-manifest.json"

test -f "$source_dir/master.db"
test -f "$source_dir/manifest.json"

"$guestctl" powershell \
  "New-Item -ItemType Directory -Force -Path '$guest_stage' | Out-Null; if (Test-Path '$guest_stage/active-guest-manifest.json') { Remove-Item -Force '$guest_stage/active-guest-manifest.json' }; Write-Output 'Guest staging directory is ready.'"
"$guestctl" copy-to "$source_dir/master.db" "$guest_stage/master.db"
"$guestctl" copy-to "$source_dir/manifest.json" "$guest_stage/manifest.json"
"$guestctl" copy-to "$script_dir/switch-fixture.ps1" "$guest_stage/switch-fixture.ps1"
"$guestctl" powershell \
  "Set-ExecutionPolicy -Scope Process Bypass -Force; & '$guest_stage/switch-fixture.ps1' -StopOnly" || true
"$guestctl" wait 30
switch_status=0
"$guestctl" powershell \
  "Set-ExecutionPolicy -Scope Process Bypass -Force; & '$guest_stage/switch-fixture.ps1' -Fixture '$guest_stage' -SkipStop" || switch_status=$?

mkdir -p "$(dirname -- "$host_marker")"
"$guestctl" copy-from "$guest_stage/active-guest-manifest.json" "$host_marker"

readonly expected=$(jq -er .database_sha256 "$source_dir/manifest.json")
readonly active=$(jq -er .database_sha256 "$host_marker")
if [[ $active != "$expected" ]]; then
  echo "guest activated $active, expected $expected" >&2
  exit 1
fi

if (( switch_status != 0 )); then
  echo "Fixture switch transport exited $switch_status; accepting the fresh, matching guest marker." >&2
fi

echo "Activated fixture $source_dir ($active)"
