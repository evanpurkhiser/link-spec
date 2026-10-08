#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-mutation-duplicate-slot"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly matrix="$script_dir/data/hot-cue-setter-parser-matrix.json"

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

for variant in "${variants[@]}"; do
  record_mode=$(jq -r --arg id "$variant" \
    '.variants[] | select(.id == $id) | .record_mode' "$matrix")
  [[ -n $record_mode ]]
  if [[ $record_mode == lifecycle ]]; then
    echo "=== $variant: delegated to the lifecycle recorder ==="
    continue
  fi
  [[ $record_mode == golden ]]

  suite="$script_dir/suites/generated/hot-cue-setter-parser/hot-cue-setter-parser-$variant.json"
  golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3-status/hot-cue-setter-parser-$variant.json"
  candidate="$golden.next"
  recorded=false

  test -f "$suite"
  test ! -e "$candidate"
  if [[ -f $golden ]]; then
    echo "=== $variant: canonical golden already exists; skipping ==="
    continue
  fi

  for attempt in 1 2 3; do
    echo "=== $variant: record attempt $attempt ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"

    if "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$candidate" record; then
      recorded=true
      break
    fi

    rm -f "$candidate" "$golden.actual.json"
  done
  [[ $recorded == true ]]

  echo "=== $variant: independent fixture-reset repeat ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$candidate" repeat

  mv "$candidate" "$golden"
  echo "=== $variant: promoted ==="
done

echo "=== Extended Hot Cue setter parser matrix: complete ==="
