#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "usage: $0 <result.json> [auto|record|repeat] [suite.json]" >&2
  exit 2
fi

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/smart-numeric-boundaries"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly suite=$(realpath -m "${3:-$script_dir/suites/smart-numeric-boundaries.json}")
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly result=$(realpath -m "$1")
readonly phase=${2:-auto}

mkdir -p "$(dirname -- "$result")"

cleanup() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap cleanup EXIT

"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
"$script_dir/oracle_record.sh" \
  "$suite" "$fixture/manifest.json" "$identity" "$result" "$phase"
