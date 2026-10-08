#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly suite="$script_dir/suites/generated/song-info-siblings.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/song-info-siblings.json"
readonly candidate="$golden.next"

test -f "$fixture/manifest.json"
test -f "$identity"
test -f "$suite"
test ! -e "$golden"
test ! -e "$candidate"

echo "=== song-info-siblings: activate ==="
"$script_dir/activate_fixture.sh" "$fixture"
echo "=== song-info-siblings: launch ==="
"$script_dir/start_oracle_ui.sh"
echo "=== song-info-siblings: record and repeat ==="
"$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
  "$identity" "$candidate"

mv "$candidate" "$golden"
echo "=== song-info-siblings: promoted ==="
