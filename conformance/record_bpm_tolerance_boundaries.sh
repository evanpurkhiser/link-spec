#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/bpm-tolerance-boundaries"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly suite="$script_dir/suites/bpm-tolerance-boundaries.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/bpm-tolerance-boundaries.json"
readonly candidate="$golden.next"

cleanup() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap cleanup EXIT

test -f "$fixture/manifest.json"
test -f "$identity"
test -f "$suite"

if [[ -f $golden ]]; then
  echo "=== bpm-tolerance-boundaries: canonical golden already exists; skipping ==="
  exit 0
fi

if [[ -f $candidate ]]; then
  echo "=== bpm-tolerance-boundaries: resuming recorded candidate ==="
else
  echo "=== bpm-tolerance-boundaries: activate ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  echo "=== bpm-tolerance-boundaries: launch ==="
  "$script_dir/start_oracle_ui.sh"
  echo "=== bpm-tolerance-boundaries: record ==="
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$candidate" record
fi

echo "=== bpm-tolerance-boundaries: reset and restart ==="
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
echo "=== bpm-tolerance-boundaries: independent repeat ==="
"$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
  "$identity" "$candidate" repeat

mv "$candidate" "$golden"
echo "=== bpm-tolerance-boundaries: promoted ==="
