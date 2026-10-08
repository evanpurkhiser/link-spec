#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-pagination"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly suite="$script_dir/suites/hot-cue-bank-pagination.json"
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-pagination.json"
readonly candidate="$golden.next"

restore() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

test ! -e "$golden"
test ! -e "$candidate"

echo '=== Hot Cue Bank pagination: activate and record ==='
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
"$script_dir/oracle_record.sh" \
  "$suite" "$fixture/manifest.json" "$identity" "$candidate" record

echo '=== Hot Cue Bank pagination: reset and repeat ==='
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
"$script_dir/oracle_record.sh" \
  "$suite" "$fixture/manifest.json" "$identity" "$candidate" repeat

mv "$candidate" "$golden"
echo '=== Hot Cue Bank pagination: promoted ==='
