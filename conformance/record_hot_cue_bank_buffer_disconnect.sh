#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly fixture="$script_dir/fixtures/generated/hot-cue-banks"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly warmup_suite="$script_dir/suites/hot-cue-bank-buffer-disconnect-warmup.json"
readonly post_suite="$script_dir/suites/hot-cue-bank-buffer-disconnect-post.json"
readonly evidence="$lab/data/experiments/hot-cue-bank/buffer-disconnect"
readonly absence_seconds=40
readonly runner="$script_dir/pinned/link-export-conformance"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
active_units=()
pending_outputs=()

if [[ ! -x $runner ]]; then
  echo "pinned conformance runner is absent or not executable: $runner" >&2
  exit 1
fi
runner_sha256=$(sha256sum "$runner" | cut -d' ' -f1)
expected_runner_sha256=$(jq -er .runner.sha256 "$pinned_manifest")
[[ $runner_sha256 == "$expected_runner_sha256" ]]
echo "Using conformance runner $runner (SHA-256 $runner_sha256)"

restore() {
  local status=$?
  trap - EXIT
  set +e
  for unit in "${active_units[@]}"; do
    systemctl --user stop "$unit.service" >/dev/null 2>&1 || true
  done
  if ((${#pending_outputs[@]})); then
    rm -f "${pending_outputs[@]}"
  fi
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

start_identity() {
  local unit=$1
  local model player device_type generation mac address broadcast peer_address
  local source_port peers presence model_code peer_args=()

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
  if [[ -n $peer_address ]]; then
    peer_args=(--peer-address "$peer_address")
  fi

  systemd-run --user --collect --unit="$unit" \
    --description="rekordbox Hot Cue buffer disconnect identity" \
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
  systemctl --user stop "$1.service"
}

click_link() {
  local console_url='https://18006.prk.network/'
  local current_url

  current_url=$(agent-browser --session rekordbox-windows get url 2>/dev/null || true)
  if [[ $current_url != "$console_url" ]]; then
    agent-browser --session rekordbox-windows open "$console_url" >/dev/null
    agent-browser --session rekordbox-windows wait --load domcontentloaded >/dev/null
    agent-browser --session rekordbox-windows wait 3000 >/dev/null
  fi
  agent-browser --session rekordbox-windows wait 1000 >/dev/null

  rfb_click() {
    local x=$1
    local y=$2
    local attempt

    for attempt in 1 2 3; do
      if agent-browser --session rekordbox-windows eval \
        "(async()=>{const {default:UI}=await import('/app/ui.js'); const r=UI.rfb; r._sendMouse($x,$y,0); r._sendMouse($x,$y,1); await new Promise(done=>setTimeout(done,150)); r._sendMouse($x,$y,0);})()" \
        >/dev/null; then
        return
      fi

      ((attempt < 3)) || return 1
      agent-browser --session rekordbox-windows open "$console_url" >/dev/null
      agent-browser --session rekordbox-windows wait --load domcontentloaded >/dev/null
      agent-browser --session rekordbox-windows wait 2000 >/dev/null
    done
  }

  rfb_click 824 52
  agent-browser --session rekordbox-windows wait 500 >/dev/null
  rfb_click 221 419
  rfb_click 462 419
  rfb_click 497 389
  agent-browser --session rekordbox-windows wait 500 >/dev/null
  rfb_click 25 495
  agent-browser --session rekordbox-windows wait 8000 >/dev/null
}

record_suite() {
  local suite=$1
  local output=$2

  "$runner" record \
    --host 172.31.96.96 --suite "$suite" --manifest "$fixture/manifest.json" \
    --identity "$identity" --backend rekordbox --backend-version 7.2.19 \
    --golden "$output"
}

record_with_activation() {
  local suite=$1
  local output=$2
  local attempt log

  for attempt in 1 2 3; do
    log="$output.attempt-$attempt.log"
    rm -f "$output"
    if record_suite "$suite" "$output" 2>&1 | tee "$log"; then
      return
    fi
    if ! grep -Eq \
      'Link Export is disabled|port query .* timed out|port query .* failed: connection timed out|dbserver connection .* failed: connection timed out' \
      "$log"; then
      return 1
    fi
    if ((attempt < 3)); then
      echo "LINK unavailable after rejoin; retrying activation ($((attempt + 1))/3)." >&2
      click_link
    fi
  done

  return 1
}

modes=(control rejoin)
if [[ $# -gt 0 ]]; then
  modes=("$@")
fi

"$vm/vmctl" isolation-check
mkdir -p "$evidence"

for mode in "${modes[@]}"; do
  case "$mode" in
    control|rejoin) ;;
    *) echo "unknown mode: $mode" >&2; exit 2 ;;
  esac

  for run in 1 2; do
    warmup="$evidence/$mode-run-$run-warmup.json"
    post="$evidence/$mode-run-$run-post.json"
    warmup_candidate="$warmup.next"
    post_candidate="$post.next"
    if [[ -e $warmup && -e $post ]]; then
      echo "=== Hot Cue buffer $mode run $run: already complete ==="
      continue
    fi
    test ! -e "$warmup"
    test ! -e "$post"
    rm -f "$warmup_candidate" "$post_candidate"
    pending_outputs=("$warmup_candidate" "$post_candidate")

    echo "=== Hot Cue buffer $mode run $run: reset and launch ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    before_unit="rekordbox-hot-cue-buffer-$mode-$run-before"
    start_identity "$before_unit"
    sleep 8
    click_link
    record_suite "$warmup_suite" "$warmup_candidate"

    if [[ $mode == rejoin ]]; then
      stop_identity "$before_unit"
      echo "=== Hot Cue buffer rejoin run $run: absent for $absence_seconds seconds ==="
      sleep "$absence_seconds"
      after_unit="rekordbox-hot-cue-buffer-$mode-$run-after"
      start_identity "$after_unit"
      sleep 8
      click_link
      record_with_activation "$post_suite" "$post_candidate"
      stop_identity "$after_unit"
    else
      record_suite "$post_suite" "$post_candidate"
      stop_identity "$before_unit"
    fi

    mv "$warmup_candidate" "$warmup"
    mv "$post_candidate" "$post"
    pending_outputs=()
  done
done

echo "=== Hot Cue buffer disconnect matrix: complete ==="
