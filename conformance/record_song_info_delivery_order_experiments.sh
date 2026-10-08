#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly experiment_dir="$root/data/experiments/song-info-delivery-order"
experiments=(repeated-identical controls-forward controls-reversed)

if [[ $# -gt 0 ]]; then
  experiments=("$@")
fi

for name in "${experiments[@]}"; do
  suite="$experiment_dir/$name-suite.json"
  test -f "$suite"

  for run in 1 2; do
    output="$experiment_dir/$name-run-$run.json"
    test ! -e "$output"

    echo "=== $name run $run: reset and launch ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    echo "=== $name run $run: record ==="
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$output" record
  done
done
