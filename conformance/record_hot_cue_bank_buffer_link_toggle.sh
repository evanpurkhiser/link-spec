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
readonly evidence="$lab/data/experiments/hot-cue-bank/buffer-link-toggle/repeats"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly runner="$script_dir/pinned/link-export-conformance"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
active_units=()

runner_sha256=$(sha256sum "$runner" | cut -d' ' -f1)
expected_runner_sha256=$(jq -er .runner.sha256 "$pinned_manifest")
[[ -x $runner ]]
[[ $runner_sha256 == "$expected_runner_sha256" ]]
echo "Using conformance runner $runner (SHA-256 $runner_sha256)"

restore() {
  local status=$?

  trap - EXIT
  set +e
  for unit in "${active_units[@]}"; do
    systemctl --user stop "$unit.service" >/dev/null 2>&1 || true
  done
  close_browser
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

close_browser() {
  agent-browser --session rekordbox-windows close >/dev/null 2>&1 || true
}

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
    --description="rekordbox Hot Cue buffer LINK-toggle identity" \
    --working-directory="$script_dir" \
    --property=RuntimeMaxSec=30m \
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
  close_browser
}

dbserver_listener_count() {
  "$guestctl" powershell \
    '@(Get-NetTCPConnection -State Listen -LocalPort 12523 -ErrorAction SilentlyContinue).Count' \
    | tr -d '\r[:space:]'
}

wait_for_dbserver() {
  local expected=$1
  local attempt count

  for attempt in $(seq 1 60); do
    count=$(dbserver_listener_count)
    if [[ $expected == present && $count =~ ^[1-9][0-9]*$ ]]; then
      return
    fi
    if [[ $expected == absent && $count == 0 ]]; then
      return
    fi
    sleep 1
  done

  echo "dbserver listener did not become $expected" >&2
  return 1
}

capture_health() {
  local label=$1
  local since=$2
  local output=$3
  local attempt

  for attempt in 1 2 3 4 5; do
    if "$guestctl" powershell \
      "& '$guest_health' -Label '$label' -SinceUtc ([DateTime]::Parse('$since').ToUniversalTime())" \
      >"$output"; then
      return
    fi
    sleep 3
  done
  return 1
}

record_suite() {
  local suite=$1
  local output=$2

  "$runner" record \
    --host 172.31.96.96 --suite "$suite" --manifest "$fixture/manifest.json" \
    --identity "$identity" --backend rekordbox --backend-version 7.2.19 \
    --golden "$output"
}

write_transition() {
  local mode=$1
  local output=$2
  local inactive_count=$3
  local reactivated_count=$4

  jq -n \
    --arg mode "$mode" \
    --argjson inactive_count "$inactive_count" \
    --argjson reactivated_count "$reactivated_count" \
    '{format:1,mode:$mode,
      transition_checkpoint_listener_count:$inactive_count,
      ready_listener_count:$reactivated_count}' \
    >"$output"
}

write_receipt() {
  local id=$1
  local mode=$2
  local run_dir=$3
  local receipt="$run_dir/receipt.json"
  local health_hashes

  health_hashes=$(
    for path in "$run_dir"/*-health.json; do
      jq -n \
        --arg name "$(basename "$path")" \
        --arg sha256 "$(sha256sum "$path" | cut -d' ' -f1)" \
        '{name:$name,sha256:$sha256}'
    done | jq -s 'sort_by(.name)'
  )

  jq -n \
    --arg id "$id" \
    --arg mode "$mode" \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg warmup_suite_sha256 "$(sha256sum "$warmup_suite" | cut -d' ' -f1)" \
    --arg post_suite_sha256 "$(sha256sum "$post_suite" | cut -d' ' -f1)" \
    --arg warmup_sha256 "$(sha256sum "$run_dir/warmup.json" | cut -d' ' -f1)" \
    --arg post_sha256 "$(sha256sum "$run_dir/post.json" | cut -d' ' -f1)" \
    --arg transition_sha256 "$(sha256sum "$run_dir/transition.json" | cut -d' ' -f1)" \
    --arg runner_sha256 "$runner_sha256" \
    --argjson health_sha256 "$health_hashes" \
    '{format:1,scope:"real Rekordbox 7.2.19 Hot Cue buffer LINK-toggle lifecycle",
      id:$id,mode:$mode,completed_at:$completed_at,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256,
      warmup_suite_sha256:$warmup_suite_sha256,
      post_suite_sha256:$post_suite_sha256,
      warmup_sha256:$warmup_sha256,post_sha256:$post_sha256,
      transition_sha256:$transition_sha256,
      runner_sha256:$runner_sha256,
      health_sha256:$health_sha256}' >"$receipt.next"
  mv "$receipt.next" "$receipt"
}

modes=(control toggle)
if [[ $# -gt 0 ]]; then
  modes=("$@")
fi

"$vm/vmctl" isolation-check
mkdir -p "$evidence"

for mode in "${modes[@]}"; do
  case "$mode" in
    control|toggle) ;;
    *) echo "unknown mode: $mode" >&2; exit 2 ;;
  esac

  for run in 1 2; do
    id="$mode-run-$run"
    run_dir="$evidence/$id"
    receipt="$run_dir/receipt.json"
    mkdir -p "$run_dir"

    if [[ -f $receipt ]]; then
      expected=$(jq -er .warmup_sha256 "$receipt")
      actual=$(sha256sum "$run_dir/warmup.json" | cut -d' ' -f1)
      [[ $actual == "$expected" ]]
      expected=$(jq -er .post_sha256 "$receipt")
      actual=$(sha256sum "$run_dir/post.json" | cut -d' ' -f1)
      [[ $actual == "$expected" ]]
      echo "=== Hot Cue buffer LINK-toggle $id: receipt exists; skipping ==="
      continue
    fi
    if find "$run_dir" -mindepth 1 -maxdepth 1 -type f | grep -q .; then
      echo "$id has incomplete evidence; inspect it before resuming" >&2
      exit 1
    fi

    echo "=== Hot Cue buffer LINK-toggle $id: fresh fixture and process ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
    started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
    unit="rekordbox-identity-hot-cue-buffer-link-toggle-$mode-$run"
    start_identity "$unit"
    sleep 8
    click_link
    wait_for_dbserver present
    capture_health "hot-cue-buffer-link-toggle-$id-before" "$started_at" \
      "$run_dir/before-health.json"

    record_suite "$warmup_suite" "$run_dir/warmup.json"
    capture_health "hot-cue-buffer-link-toggle-$id-after-warmup" "$started_at" \
      "$run_dir/after-warmup-health.json"

    if [[ $mode == toggle ]]; then
      click_link
      wait_for_dbserver absent
      inactive_count=$(dbserver_listener_count)
      capture_health "hot-cue-buffer-link-toggle-$id-inactive" "$started_at" \
        "$run_dir/inactive-health.json"
      click_link
      wait_for_dbserver present
      reactivated_count=$(dbserver_listener_count)
      capture_health "hot-cue-buffer-link-toggle-$id-reactivated" "$started_at" \
        "$run_dir/reactivated-health.json"
    else
      inactive_count=$(dbserver_listener_count)
      capture_health "hot-cue-buffer-link-toggle-$id-control-boundary" "$started_at" \
        "$run_dir/control-boundary-health.json"
      reactivated_count=$(dbserver_listener_count)
      capture_health "hot-cue-buffer-link-toggle-$id-control-ready" "$started_at" \
        "$run_dir/control-ready-health.json"
    fi
    write_transition "$mode" "$run_dir/transition.json" \
      "$inactive_count" "$reactivated_count"

    record_suite "$post_suite" "$run_dir/post.json"
    capture_health "hot-cue-buffer-link-toggle-$id-after-post" "$started_at" \
      "$run_dir/after-post-health.json"
    stop_identity "$unit"
    write_receipt "$id" "$mode" "$run_dir"
    echo "=== Hot Cue buffer LINK-toggle $id: promoted ==="
  done
done

echo "=== Hot Cue buffer LINK-toggle lifecycle matrix: complete ==="
