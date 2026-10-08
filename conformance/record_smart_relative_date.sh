#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <result.json> [auto|record|repeat]" >&2
  exit 2
fi

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/smart-relative-date-matrix"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly suite="$script_dir/suites/smart-relative-date-matrix.json"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly anchor="2032-03-31T12:00:00"
readonly result=$(realpath -m "$1")
readonly phase=${2:-auto}
readonly evidence="$root/data/experiments/smart-relative-date-matrix/clock.log"

mkdir -p "$(dirname -- "$result")" "$(dirname -- "$evidence")"
: >"$evidence"

cleanup() {
  status=$?
  trap - EXIT
  set +e
  echo "=== restore host clock ===" >>"$evidence"
  "$script_dir/guest_clock.sh" restore >>"$evidence" 2>&1
  echo "=== restore play-paths fixture ===" >>"$evidence"
  "$script_dir/activate_fixture.sh" "$baseline" >>"$evidence" 2>&1
  exit "$status"
}
trap cleanup EXIT

echo "=== original guest clock ===" >>"$evidence"
"$script_dir/guest_clock.sh" show >>"$evidence" 2>&1
"$script_dir/activate_fixture.sh" "$fixture"
echo "=== controlled guest clock ===" >>"$evidence"
"$script_dir/guest_clock.sh" set "$anchor" >>"$evidence" 2>&1
"$script_dir/start_oracle_ui.sh"
"$script_dir/oracle_record.sh" \
  "$suite" "$fixture/manifest.json" "$identity" "$result" "$phase"
