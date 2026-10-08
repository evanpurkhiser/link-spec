#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/delivery-wide-strings"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly suite="$script_dir/suites/generated/song-info-delivery-wide-strings.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/song-info-delivery-wide-strings.json"
readonly candidate="$golden.next"

test -f "$fixture/manifest.json"
test -f "$identity"
test -f "$suite"
test ! -e "$golden"
test ! -e "$candidate"

echo "=== song-info-delivery-wide-strings: activate ==="
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
echo "=== song-info-delivery-wide-strings: record ==="
"$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
  "$identity" "$candidate" record

echo "=== song-info-delivery-wide-strings: reset and restart ==="
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
echo "=== song-info-delivery-wide-strings: independent repeat ==="
"$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
  "$identity" "$candidate" repeat

mv "$candidate" "$golden"
echo "=== song-info-delivery-wide-strings: promoted ==="
