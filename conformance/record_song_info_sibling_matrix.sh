#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
suites=(render pagination errors legacy)

if [[ $# -gt 0 ]]; then
  suites=("$@")
fi

for suffix in "${suites[@]}"; do
  suite="$script_dir/suites/generated/song-info-sibling-$suffix.json"
  golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/song-info-sibling-$suffix.json"
  candidate="$golden.next"

  test -f "$fixture/manifest.json"
  test -f "$identity"
  test -f "$suite"
  test ! -e "$golden"
  test ! -e "$candidate"

  echo "=== song-info-sibling-$suffix: activate ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  echo "=== song-info-sibling-$suffix: launch ==="
  "$script_dir/start_oracle_ui.sh"
  echo "=== song-info-sibling-$suffix: record and repeat ==="
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$candidate"

  mv "$candidate" "$golden"
  echo "=== song-info-sibling-$suffix: promoted ==="
done
