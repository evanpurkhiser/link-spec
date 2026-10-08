#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-mutation-duplicate-slot"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly matrix="$script_dir/data/hot-cue-declared-length-ffffffff-lifecycle-matrix.json"
readonly evidence="$lab/data/experiments/hot-cue-bank/extended-setter-parser/declared-length-ffffffff-lifecycle/observations"

restore() {
  local status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

mapfile -t variants < <(jq -r '.variants[].id' "$matrix")
if [[ $# -gt 0 ]]; then
  variants=("$@")
fi

mkdir -p "$evidence"
for variant in "${variants[@]}"; do
  suite="$script_dir/suites/generated/hot-cue-declared-length-ffffffff-lifecycle/hot-cue-declared-length-ffffffff-lifecycle-$variant.json"
  test -f "$suite"

  for run in 1 2 3; do
    output="$evidence/$variant-run-$run.json"
    if [[ -e $output ]]; then
      echo "=== $variant run $run: already complete ==="
      continue
    fi

    echo "=== $variant run $run: independent fixture/process observation ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$output" record
  done
done

echo "=== UINT32_MAX declared-length lifecycle matrix: complete ==="
