#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
models=(xdj-xz xdj-az xdj-1000mk2 unknown-mixer)

if [[ $# -gt 0 ]]; then
  models=("$@")
fi

for model in "${models[@]}"; do
  case "$model" in
    xdj-xz)
      identity="$script_dir/runs/xdj-xz-player-11-status.json"
      ;;
    xdj-az)
      identity="$script_dir/runs/xdj-az-player-11-status.json"
      ;;
    xdj-1000mk2)
      identity="$script_dir/runs/xdj-1000mk2-player-11-status.json"
      ;;
    unknown-mixer)
      identity="$script_dir/runs/unknown-mixer-player-1-status.json"
      ;;
    cdj-2000nexus)
      identity="$script_dir/runs/cdj-2000nexus-player-1-genuine-status.json"
      ;;
    *)
      echo "unknown status model: $model" >&2
      exit 2
      ;;
  esac

  suite="$script_dir/suites/generated/display-song-info-status-$model.json"
  golden="$script_dir/goldens/rekordbox-7.2.19/$model-status/display-song-info.json"
  candidate="$golden.next"

  test -f "$fixture/manifest.json"
  test -f "$identity"
  test -f "$suite"
  test ! -e "$golden"
  test ! -e "$candidate"
  mkdir -p "$(dirname -- "$golden")"

  echo "=== $model: activate ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  echo "=== $model: launch ==="
  "$script_dir/start_oracle_ui.sh"
  echo "=== $model: record and repeat ==="
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$candidate"

  mv "$candidate" "$golden"
  echo "=== $model: promoted ==="
done
