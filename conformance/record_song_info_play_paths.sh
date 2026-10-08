#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/../.." && pwd)
readonly fixture="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly suite="$script_dir/suites/generated/song-info-play-paths.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/song-info-play-paths.json"
readonly candidate="$golden.next"
readonly guestctl="$root/rekordbox-link-export-research/guest-control/guestctl"

prepare_guest_paths() {
  "$guestctl" powershell \
    '$root = "C:/Users/Research/link-export-conformance/play-paths"; Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $root; New-Item -ItemType Directory -Force -Path "$root/org-existing-dir" | Out-Null; [IO.File]::WriteAllBytes("$root/org-existing.bin", [Text.Encoding]::ASCII.GetBytes("link-export-path-sentinel")); [IO.File]::WriteAllBytes("$root/org-zero-byte.bin", [byte[]]::new(0)); Write-Output "Play-path sentinels are ready."'
}

test -f "$fixture/manifest.json"
test -f "$identity"
test -f "$suite"
test ! -e "$golden"
test ! -e "$candidate"

echo "=== song-info-play-paths: activate ==="
"$script_dir/activate_fixture.sh" "$fixture"
prepare_guest_paths
"$script_dir/start_oracle_ui.sh"
echo "=== song-info-play-paths: record ==="
"$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
  "$identity" "$candidate" record

echo "=== song-info-play-paths: reset and restart ==="
"$script_dir/activate_fixture.sh" "$fixture"
prepare_guest_paths
"$script_dir/start_oracle_ui.sh"
echo "=== song-info-play-paths: independent repeat ==="
"$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
  "$identity" "$candidate" repeat

mv "$candidate" "$golden"
echo "=== song-info-play-paths: promoted ==="
