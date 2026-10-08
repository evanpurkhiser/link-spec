#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly experiment_dir="$root/data/experiments/song-info-sibling-errors"

matrices=(
  "rx3|status-player-11|$script_dir/runs/xdj-rx3-player-11-status.json"
  "cdj-3000|status-player-1|$script_dir/runs/cdj-3000-player-1-status.json"
  "rx3-matched|status-player-11-matched|$script_dir/runs/xdj-rx3-player-11-status.json"
)

for matrix in "${matrices[@]}"; do
  IFS='|' read -r name suffix identity <<<"$matrix"
  suite="$experiment_dir/status-errors-$suffix-suite.json"

  for run in 1 2; do
    output="$experiment_dir/status-$name-run-$run.json"
    if [[ -e $output ]]; then
      echo "=== status $name malformed run $run: already complete ==="
      continue
    fi

    echo "=== status $name malformed run $run: reset and launch ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$output" record
  done
done
