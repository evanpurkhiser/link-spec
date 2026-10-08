#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$root/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly fixture="$script_dir/fixtures/generated/full"
readonly rx3_identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly cdj_identity="$script_dir/runs/cdj-3000-player-1.json"
readonly experiment_dir="$root/data/experiments/song-info-delivery-order"
readonly warmup_suite="$experiment_dir/identity-warmup-six-suite.json"
readonly post_suite="$experiment_dir/identity-post-rejoin-eight-suite.json"
readonly absence_seconds=40
active_units=()

stop_identities() {
  for unit in "${active_units[@]}"; do
    systemctl --user stop "$unit.service" >/dev/null 2>&1 || true
  done
}
trap stop_identities EXIT

start_identity() {
  local identity=$1
  local unit=$2
  local model player device_type generation mac address broadcast peer_address
  local source_port peers presence model_code

  model=$(jq -er .model "$identity")
  player=$(jq -er .player "$identity")
  device_type=$(jq -er .device_type "$identity")
  generation=$(jq -er .generation "$identity")
  mac=$(jq -er .mac "$identity")
  address=$(jq -er .address "$identity")
  broadcast=$(jq -er .broadcast "$identity")
  peer_address=$(jq -r '.peer_address // empty' "$identity")
  source_port=$(jq -r '.source_port // 0' "$identity")
  peers=$(jq -r '.peers // 0' "$identity")
  presence=$(jq -r '.presence // 1' "$identity")
  model_code=$(jq -r '.model_code // 100' "$identity")

  local peer_args=()
  if [[ -n $peer_address ]]; then
    peer_args=(--peer-address "$peer_address")
  fi

  systemd-run --user --collect --unit="$unit" \
    --description="rekordbox Delivery identity lifecycle" \
    --working-directory="$script_dir" \
    --property=RuntimeMaxSec=15m \
    python "$script_dir/identity_adapter.py" \
      --model "$model" --player "$player" --device-type "$device_type" \
      --generation "$generation" --mac "$mac" --address "$address" \
      --broadcast "$broadcast" --source-port "$source_port" --peers "$peers" \
      --presence "$presence" --model-code "$model_code" "${peer_args[@]}"
  active_units+=("$unit")
}

stop_identity() {
  local unit=$1
  systemctl --user stop "$unit.service"
}

click_link() {
  agent-browser --session rekordbox-windows get url >/dev/null
  agent-browser --session rekordbox-windows wait 1000 >/dev/null
  agent-browser --session rekordbox-windows mouse move 205 500 >/dev/null
  agent-browser --session rekordbox-windows mouse down >/dev/null
  agent-browser --session rekordbox-windows mouse up >/dev/null
  agent-browser --session rekordbox-windows wait 3000 >/dev/null
}

record_suite() {
  local suite=$1
  local identity=$2
  local output=$3

  python3 "$script_dir/protocol_runner.py" record \
    --host 172.31.96.96 --suite "$suite" --manifest "$fixture/manifest.json" \
    --identity "$identity" --backend rekordbox --backend-version 7.2.19 \
    --golden "$output"
}

modes=(same-rejoin cdj-replacement)
if [[ $# -gt 0 ]]; then
  modes=("$@")
fi

"$vm/vmctl" isolation-check

for mode in "${modes[@]}"; do
  case "$mode" in
    same-rejoin) post_identity=$rx3_identity ;;
    cdj-replacement) post_identity=$cdj_identity ;;
    *) echo "unknown lifecycle mode: $mode" >&2; exit 2 ;;
  esac

  for run in 1 2; do
    warmup_output="$experiment_dir/identity-$mode-run-$run-warmup.json"
    post_output="$experiment_dir/identity-$mode-run-$run-post.json"
    if [[ -e $warmup_output && -e $post_output ]]; then
      echo "=== identity $mode run $run: already complete ==="
      continue
    fi
    test ! -e "$warmup_output"
    test ! -e "$post_output"

    echo "=== identity $mode run $run: reset and launch ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"

    before_unit="rekordbox-identity-lifecycle-$mode-$run-before"
    after_unit="rekordbox-identity-lifecycle-$mode-$run-after"
    start_identity "$rx3_identity" "$before_unit"
    sleep 8
    click_link

    echo "=== identity $mode run $run: six-call warmup ==="
    record_suite "$warmup_suite" "$rx3_identity" "$warmup_output"

    echo "=== identity $mode run $run: absent for $absence_seconds seconds ==="
    stop_identity "$before_unit"
    sleep "$absence_seconds"

    start_identity "$post_identity" "$after_unit"
    sleep 8
    click_link

    echo "=== identity $mode run $run: eight post-rejoin probes ==="
    if ! record_suite "$post_suite" "$post_identity" "$post_output"; then
      rm -f "$post_output"
      stop_identity "$after_unit"
      echo "=== port query not ready; wait 30 seconds and renew identity ==="
      sleep 30
      after_unit="$after_unit-retry"
      start_identity "$post_identity" "$after_unit"
      sleep 8
      click_link
      record_suite "$post_suite" "$post_identity" "$post_output"
    fi
    stop_identity "$after_unit"
  done
done
