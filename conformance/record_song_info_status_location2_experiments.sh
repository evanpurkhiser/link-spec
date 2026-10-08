#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly experiment_dir="$root/data/experiments/song-info-status-location2"
families=(
  delivery-only-header
  play-zero
  play-primary
  play-location2
  display-primary
  display-location2
  delivery-primary
  malformed-prefix
  delivery-only-header-same-connection
  play-zero-same-connection
  play-primary-same-connection
  play-location2-same-connection
  display-primary-same-connection
  display-location2-same-connection
  delivery-primary-same-connection
)

if [[ $# -gt 0 ]]; then
  families=("$@")
fi

for family in "${families[@]}"; do
  suite="$experiment_dir/$family-suite.json"
  test -f "$suite"

  for run in 1 2; do
    output="$experiment_dir/$family-run-$run.json"
    if [[ -e $output ]]; then
      echo "=== status location2 $family run $run: already complete ==="
      continue
    fi

    recorded=false
    for attempt in 1 2 3; do
      echo "=== status location2 $family run $run: attempt $attempt ==="
      if ! "$script_dir/activate_fixture.sh" "$fixture"; then
        sleep 5
        continue
      fi
      if ! "$script_dir/start_oracle_ui.sh"; then
        sleep 5
        continue
      fi
      if "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
        "$identity" "$output" record; then
        recorded=true
        break
      fi

      rm -f "$output"
    done
    [[ $recorded == true ]]
  done
done
