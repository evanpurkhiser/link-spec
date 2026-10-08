#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly experiment_dir="$root/data/experiments/song-info-delivery-order"
families=(
  play-populated
  display-populated
  play-missing
  display-missing
  delivery-missing
  recognized-error
)

if [[ $# -gt 0 ]]; then
  families=("$@")
fi

for family in "${families[@]}"; do
  suite="$experiment_dir/family-$family-same-connection-suite.json"
  test -f "$suite"

  for run in 1 2; do
    output="$experiment_dir/family-$family-same-connection-run-$run.json"
    test ! -e "$output"

    echo "=== family-$family same connection run $run: reset and launch ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    echo "=== family-$family same connection run $run: record ==="
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$output" record
  done
done
