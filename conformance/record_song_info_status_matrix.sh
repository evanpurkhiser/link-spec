#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
suite_names=(
  song-info-siblings
  song-info-sibling-render
  song-info-sibling-pagination
  song-info-sibling-legacy
)

if [[ $# -gt 0 ]]; then
  suite_names=("$@")
fi

record_matrix() {
  local model_directory=$1
  local identity=$2
  local suite_suffix=$3
  local suite_name suite golden candidate

  for suite_name in "${suite_names[@]}"; do
    suite="$script_dir/suites/generated/$suite_name$suite_suffix.json"
    golden="$script_dir/goldens/rekordbox-7.2.19/$model_directory/$suite_name.json"
    candidate="$golden.next"

    test -f "$suite"
    test -f "$identity"
    if [[ -e $golden ]]; then
      echo "=== $model_directory / $suite_name: already complete ==="
      continue
    fi
    rm -f "$candidate"
    mkdir -p "$(dirname -- "$golden")"

    recorded=false
    for attempt in 1 2 3; do
      echo "=== $model_directory / $suite_name: attempt $attempt ==="
      "$script_dir/activate_fixture.sh" "$fixture"
      "$script_dir/start_oracle_ui.sh"
      if [[ $suite_name == song-info-sibling-errors ]]; then
        if "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
          "$identity" "$candidate" record; then
          "$script_dir/activate_fixture.sh" "$fixture"
          "$script_dir/start_oracle_ui.sh"
          if "$script_dir/oracle_record.sh" "$suite" \
            "$fixture/manifest.json" "$identity" "$candidate" repeat; then
            recorded=true
            break
          fi
        fi
      elif "$script_dir/oracle_record.sh" "$suite" \
        "$fixture/manifest.json" "$identity" "$candidate"; then
          recorded=true
          break
      fi

      rm -f "$candidate"
      rm -f "$golden.actual.json"
    done
    [[ $recorded == true ]]

    mv "$candidate" "$golden"
    echo "=== $model_directory / $suite_name: promoted ==="
  done
}

record_matrix \
  xdj-rx3-status \
  "$script_dir/runs/xdj-rx3-player-11-status.json" \
  -status-player-11

record_matrix \
  cdj-3000-status \
  "$script_dir/runs/cdj-3000-player-1-status.json" \
  -status-player-1
