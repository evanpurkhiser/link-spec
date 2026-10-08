#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly experiment_dir="$root/data/experiments/song-info-status-location2"
readonly suite="$experiment_dir/malformed-prefix-same-connection-suite.json"

for run in 1 2; do
  output="$experiment_dir/malformed-prefix-same-connection-run-$run.json"
  evidence="$experiment_dir/malformed-prefix-same-connection-run-$run.log"
  if [[ -e $evidence ]]; then
    echo "=== malformed same-connection failure run $run: already complete ==="
    continue
  fi

  captured=false
  for attempt in 1 2 3; do
    attempt_log=$(mktemp)
    echo "=== malformed same-connection failure run $run: attempt $attempt ==="
    if ! "$script_dir/activate_fixture.sh" "$fixture"; then
      rm -f "$attempt_log"
      sleep 5
      continue
    fi
    if ! "$script_dir/start_oracle_ui.sh"; then
      rm -f "$attempt_log"
      sleep 5
      continue
    fi

    if "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$output" record 2>&1 | tee "$attempt_log"; then
      rm -f "$attempt_log" "$output"
      echo "expected dbserver connection closure, but suite completed" >&2
      exit 1
    fi
    rm -f "$output"

    if grep -q 'dbserver closed the connection' "$attempt_log"; then
      mv "$attempt_log" "$evidence"
      captured=true
      break
    fi
    rm -f "$attempt_log"
  done
  [[ $captured == true ]]
done
