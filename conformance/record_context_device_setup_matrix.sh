#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"

models=(
  xdj-rx3
  cdj-3000
  cdj-2000nxs2
  xdj-xz
  xdj-az
  xdj-1000mk2
  unknown-mixer
  unknown-djm
)

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
    xdj-rx3) echo "$script_dir/runs/xdj-rx3-player-11.json" ;;
    cdj-3000) echo "$script_dir/runs/cdj-3000-player-1.json" ;;
    cdj-2000nxs2) echo "$script_dir/runs/cdj-2000nxs2-player-2.json" ;;
    xdj-xz) echo "$script_dir/runs/xdj-xz-player-3.json" ;;
    xdj-az) echo "$script_dir/runs/xdj-az-player-4.json" ;;
    xdj-1000mk2) echo "$script_dir/runs/xdj-1000mk2-player-5.json" ;;
    unknown-mixer) echo "$script_dir/runs/unknown-mixer-player-6.json" ;;
    unknown-djm) echo "$script_dir/runs/unknown-djm-player-6.json" ;;
    *) echo "unknown model: $1" >&2; return 2 ;;
  esac
}

for model in "${models[@]}"; do
  identity=$(identity_for "$model")
  test -f "$identity"
  test ! -e "$script_dir/goldens/rekordbox-7.2.19/$model/context-device-setup-extended.json"
  test ! -e "$script_dir/goldens/rekordbox-7.2.19/$model/context-device-setup-legacy.json"

  echo "=== $model: reset and launch ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"

  echo "=== $model: record and immediate repeat ==="
  "$script_dir/record_device_model.sh" "$identity" "$model" \
    context-device-setup-extended context-device-setup-legacy
done

echo "=== Context device/setup matrix: complete ==="
