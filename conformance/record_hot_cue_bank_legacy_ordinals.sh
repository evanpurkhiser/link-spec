#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/../.." && pwd)
readonly lab="$root/rekordbox-link-export-research"
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-legacy-ordinals"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly suite="$script_dir/suites/hot-cue-bank-legacy-ordinals.json"
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-legacy-ordinals.json"
readonly candidate="$golden.next"
readonly evidence="$lab/data/experiments/hot-cue-bank/legacy-ordinals"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_database='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/master.db'
readonly options='/mnt/documents/multimedia/djing/rekordbox/options.json'

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
test ! -e "$evidence"
mkdir -p "$evidence"

echo '=== legacy ordinals: activate and record ==='
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
"$script_dir/oracle_record.sh" \
  "$suite" "$fixture/manifest.json" "$identity" "$candidate" record

echo '=== legacy ordinals: capture live database state ==='
"$guestctl" copy-from "$guest_database" "$evidence/live-after-master.db"
"$guestctl" copy-from "${guest_database}-wal" "$evidence/live-after-master.db-wal"
"$guestctl" copy-from "${guest_database}-shm" "$evidence/live-after-master.db-shm"
"$root/rekordbox-windows/.venv/bin/python" \
  "$lab/tools/snapshot_hot_cue_mutation.py" \
  "$evidence/live-after-master.db" "$options" "$evidence/live-after.json"

echo '=== legacy ordinals: reset, restart, and independently repeat ==='
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
"$script_dir/oracle_record.sh" \
  "$suite" "$fixture/manifest.json" "$identity" "$candidate" repeat

mv "$candidate" "$golden"
echo '=== legacy ordinals: promoted ==='
