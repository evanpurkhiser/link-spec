#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-mutation-duplicate-slot"
readonly baseline="$script_dir/fixtures/generated/play-paths"

models=(xdj-rx3-status cdj-3000-status)
if [[ $# -gt 0 ]]; then
  models=("$@")
fi

restore() {
  local status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

identity_for() {
  case "$1" in
    xdj-rx3-status) echo "$script_dir/runs/xdj-rx3-player-11-status.json" ;;
    cdj-3000-status) echo "$script_dir/runs/cdj-3000-player-1-status.json" ;;
    *) echo "unknown status model: $1" >&2; return 2 ;;
  esac
}

player_for() {
  case "$1" in
    xdj-rx3-status) echo 11 ;;
    cdj-3000-status) echo 1 ;;
    *) echo "unknown status model: $1" >&2; return 2 ;;
  esac
}

for model in "${models[@]}"; do
  identity=$(identity_for "$model")
  player=$(player_for "$model")
  test -f "$identity"

  for setup in extended legacy; do
    suite_name="context-hot-cue-setter-status-player-$player-$setup"
    suite="$script_dir/suites/$suite_name.json"
    golden="$script_dir/goldens/rekordbox-7.2.19/$model/context-hot-cue-setter-status-$setup.json"
    candidate="$golden.next"
    recorded=false

    test -f "$suite"
    test ! -e "$golden"
    test ! -e "$candidate"
    mkdir -p "$(dirname -- "$golden")"

    for attempt in 1 2 3; do
      echo "=== $model / $suite_name: record attempt $attempt ==="
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

    echo "=== $model / $suite_name: independent repeat ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$candidate" repeat

    mv "$candidate" "$golden"
    echo "=== $model / $suite_name: promoted ==="
  done
done

echo "=== Context Hot Cue setter status matrix: complete ==="
