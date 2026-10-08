#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly index="$script_dir/data/link-played-multiplayer.json"
readonly identity_1="$script_dir/runs/xdj-rx3-player-1.json"
readonly identity_2="$script_dir/runs/xdj-rx3-player-2.json"
readonly goldens="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"
readonly evidence="$lab/data/experiments/played-track-state/multiplayer"
readonly settings_dir="$lab/data/experiments/played-track-state/settings"
readonly reset_settings="$settings_dir/reset.settings"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_settings='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/rekordbox3.settings'
readonly guest_played='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/AnotherHistories.xml'
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly snapshot_dir="$evidence/guest-baseline"
readonly runner="$script_dir/pinned/link-export-conformance"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
readonly phases=(
  link-played-multiplayer-player-1-prime
  link-played-multiplayer-player-2-insert
  link-played-multiplayer-player-1-remove
  link-played-multiplayer-player-2-remove
)
active_units=()
restored=false

runner_sha256=$(sha256sum "$runner" | cut -d' ' -f1)
[[ -x $runner ]]
[[ $runner_sha256 == "$(jq -er .runner.sha256 "$pinned_manifest")" ]]

close_browser() {
  agent-browser --session rekordbox-windows close >/dev/null 2>&1 || true
}

snapshot_guest_file() {
  local guest_path=$1 host_path=$2 metadata=$3 exists sha256
  exists=$("$guestctl" powershell \
    "if (Test-Path -LiteralPath '$guest_path') { 'true' } else { 'false' }" \
    | tr -d '\r[:space:]')
  case "$exists" in
    true)
      "$guestctl" copy-from "$guest_path" "$host_path"
      sha256=$(sha256sum "$host_path" | cut -d' ' -f1)
      ;;
    false) sha256='' ;;
    *) echo "unexpected existence result for $guest_path: $exists" >&2; return 1 ;;
  esac
  jq -n --arg guest_path "$guest_path" --argjson exists "$exists" \
    --arg sha256 "$sha256" \
    '{format:1,guest_path:$guest_path,exists:$exists,
      sha256:(if $sha256 == "" then null else $sha256 end)}' >"$metadata"
}

restore_guest_file() {
  local host_path=$1 metadata=$2 guest_path exists expected actual
  guest_path=$(jq -er .guest_path "$metadata")
  exists=$(jq -er .exists "$metadata")
  if [[ $exists == true ]]; then
    expected=$(jq -er .sha256 "$metadata")
    [[ $(sha256sum "$host_path" | cut -d' ' -f1) == "$expected" ]]
    "$guestctl" copy-to "$host_path" "$guest_path"
    actual=$("$guestctl" powershell \
      "(Get-FileHash -Algorithm SHA256 -LiteralPath '$guest_path').Hash.ToLowerInvariant()" \
      | tr -d '\r[:space:]')
    [[ $actual == "$expected" ]]
  else
    "$guestctl" powershell \
      "Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath '$guest_path'"
  fi
}

restore() {
  local status=$?
  trap - EXIT
  set +e
  for unit in "${active_units[@]}"; do
    systemctl --user stop "$unit.service" >/dev/null 2>&1 || true
  done
  close_browser
  if [[ $restored != true && -f $snapshot_dir/rekordbox3.settings.state.json ]]; then
    "$script_dir/activate_fixture.sh" "$baseline"
    restore_guest_file "$snapshot_dir/rekordbox3.settings" \
      "$snapshot_dir/rekordbox3.settings.state.json"
    restore_guest_file "$snapshot_dir/AnotherHistories.xml" \
      "$snapshot_dir/AnotherHistories.xml.state.json"
  fi
  exit "$status"
}
trap restore EXIT

start_identity() {
  local config=$1 unit=$2 manifest=$3
  local model player device_type generation mac address broadcast peer_address
  local source_port peers presence model_code peer_args=()
  model=$(jq -er .model "$config")
  player=$(jq -er .player "$config")
  device_type=$(jq -er .device_type "$config")
  generation=$(jq -er .generation "$config")
  mac=$(jq -er .mac "$config")
  address=$(jq -er .address "$config")
  broadcast=$(jq -er .broadcast "$config")
  peer_address=$(jq -r '.peer_address // empty' "$config")
  source_port=$(jq -r '.source_port // 0' "$config")
  peers=$(jq -r '.peers // 0' "$config")
  presence=$(jq -r '.presence // 1' "$config")
  model_code=$(jq -r '.model_code // 100' "$config")
  [[ -z $peer_address ]] || peer_args=(--peer-address "$peer_address")
  systemd-run --user --collect --unit="$unit" \
    --description="rekordbox Link-played multiplayer identity $player" \
    --working-directory="$script_dir" --property=RuntimeMaxSec=45m \
    python "$script_dir/identity_adapter.py" \
      --model "$model" --player "$player" --device-type "$device_type" \
      --generation "$generation" --mac "$mac" --address "$address" \
      --broadcast "$broadcast" --source-port "$source_port" --peers "$peers" \
      --presence "$presence" --model-code "$model_code" \
      --manifest "$manifest" "${peer_args[@]}"
  active_units+=("$unit")
}

click_link() {
  local console_url='https://18006.prk.network/' current_url
  current_url=$(agent-browser --session rekordbox-windows get url 2>/dev/null || true)
  if [[ $current_url != "$console_url" ]]; then
    agent-browser --session rekordbox-windows open "$console_url" >/dev/null
    agent-browser --session rekordbox-windows wait --load domcontentloaded >/dev/null
    agent-browser --session rekordbox-windows wait 3000 >/dev/null
  fi
  agent-browser --session rekordbox-windows wait 1000 >/dev/null
  rfb_click() {
    local x=$1 y=$2 attempt
    for attempt in 1 2 3; do
      if agent-browser --session rekordbox-windows eval \
        "(async()=>{const {default:UI}=await import('/app/ui.js'); const r=UI.rfb; r._sendMouse($x,$y,0); r._sendMouse($x,$y,1); await new Promise(done=>setTimeout(done,150)); r._sendMouse($x,$y,0);})()" \
        >/dev/null; then return; fi
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

wait_for_dbserver() {
  local attempt count
  for attempt in $(seq 1 60); do
    count=$("$guestctl" powershell \
      '@(Get-NetTCPConnection -State Listen -LocalPort 12523 -ErrorAction SilentlyContinue).Count' \
      | tr -d '\r[:space:]')
    [[ $count =~ ^[1-9][0-9]*$ ]] && return
    sleep 1
  done
  echo "dbserver listener did not become present" >&2
  return 1
}

capture_health() {
  local label=$1 since=$2 output=$3 attempt
  for attempt in 1 2 3 4 5; do
    if "$guestctl" powershell \
      "& '$guest_health' -Label '$label' -SinceUtc ([DateTime]::Parse('$since').ToUniversalTime())" \
      >"$output"; then return; fi
    sleep 3
  done
  return 1
}

capture_options() {
  local output=$1
  "$guestctl" powershell \
    "[xml]\$s = Get-Content -Raw -LiteralPath '$guest_settings'; \$names = 'PlayedTrackOption','LinkPlayedTrackOption'; @((\$s.PROPERTIES.VALUE | Where-Object { \$_.name -in \$names } | Sort-Object name | ForEach-Object { [ordered]@{name=[string]\$_.name;val=[int]\$_.val} })) | ConvertTo-Json" \
    >"$output"
  jq -e 'length == 2 and all(.[]; .val == 1)' "$output" >/dev/null
}

capture_identities() {
  local checkpoint=$1 unit_1=$2 unit_2=$3 manifest_1=$4 manifest_2=$5 output=$6
  local state_1 state_2 pid_1 pid_2
  state_1=$(systemctl --user show "$unit_1.service" -p ActiveState --value)
  state_2=$(systemctl --user show "$unit_2.service" -p ActiveState --value)
  pid_1=$(systemctl --user show "$unit_1.service" -p MainPID --value)
  pid_2=$(systemctl --user show "$unit_2.service" -p MainPID --value)
  [[ $state_1 == active && $state_2 == active && $pid_1 -gt 0 && $pid_2 -gt 0 ]]
  [[ $(jq -er .packet_sha256 "$manifest_1") == $(jq -er .packet_sha256 "$identity_1") ]]
  [[ $(jq -er .packet_sha256 "$manifest_2") == $(jq -er .packet_sha256 "$identity_2") ]]
  jq -n --arg checkpoint "$checkpoint" --arg state_1 "$state_1" \
    --arg state_2 "$state_2" --argjson pid_1 "$pid_1" --argjson pid_2 "$pid_2" \
    --arg manifest_1_sha256 "$(sha256sum "$manifest_1" | cut -d' ' -f1)" \
    --arg manifest_2_sha256 "$(sha256sum "$manifest_2" | cut -d' ' -f1)" \
    '{format:1,checkpoint:$checkpoint,players:[
      {player:1,active_state:$state_1,host_process_id:$pid_1,
       live_manifest_sha256:$manifest_1_sha256},
      {player:2,active_state:$state_2,host_process_id:$pid_2,
       live_manifest_sha256:$manifest_2_sha256}]}' >"$output"
}

execute_suite() {
  local run=$1 suite=$2 identity=$3 candidate=$4 output=$5 diff=$6
  local common=(--host 172.31.96.96 --suite "$suite" \
    --manifest "$fixture/manifest.json" --identity "$identity" \
    --backend rekordbox --backend-version 7.2.19 --golden "$candidate")
  if [[ $run == 1 ]]; then
    "$runner" record "${common[@]}"
    cp "$candidate" "$output"
  else
    "$runner" verify "${common[@]}" --actual "$output" --diff "$diff"
    [[ ! -s $diff ]]
  fi
}

write_run_receipt() {
  local run=$1 run_dir=$2 response_hashes health_hashes identity_hashes
  response_hashes=$(for phase in "${phases[@]}"; do
    jq -n --arg id "$phase" \
      --arg sha256 "$(sha256sum "$run_dir/$phase.json" | cut -d' ' -f1)" \
      '{id:$id,sha256:$sha256}'
  done | jq -s .)
  health_hashes=$(for path in "$run_dir"/*-health.json; do
    jq -n --arg name "$(basename "$path")" \
      --arg sha256 "$(sha256sum "$path" | cut -d' ' -f1)" \
      '{name:$name,sha256:$sha256}'
  done | jq -s 'sort_by(.name)')
  identity_hashes=$(for path in "$run_dir"/identities-*.json; do
    jq -n --arg name "$(basename "$path")" \
      --arg sha256 "$(sha256sum "$path" | cut -d' ' -f1)" \
      '{name:$name,sha256:$sha256}'
  done | jq -s 'sort_by(.name)')
  jq -n --argjson run "$run" --arg runner_sha256 "$runner_sha256" \
    --arg options_sha256 "$(sha256sum "$run_dir/options.json" | cut -d' ' -f1)" \
    --arg player_1_manifest_sha256 "$(sha256sum "$run_dir/player-1-live.json" | cut -d' ' -f1)" \
    --arg player_2_manifest_sha256 "$(sha256sum "$run_dir/player-2-live.json" | cut -d' ' -f1)" \
    --argjson responses "$response_hashes" --argjson health "$health_hashes" \
    --argjson identity_checkpoints "$identity_hashes" \
    '{format:1,run:$run,runner_sha256:$runner_sha256,
      options_sha256:$options_sha256,
      player_1_manifest_sha256:$player_1_manifest_sha256,
      player_2_manifest_sha256:$player_2_manifest_sha256,
      responses:$responses,health:$health,
      identity_checkpoints:$identity_checkpoints,
      simultaneous_identity_count:2,same_rekordbox_process:true}' \
    >"$run_dir/receipt.json.next"
  mv "$run_dir/receipt.json.next" "$run_dir/receipt.json"
}

"$vm/vmctl" isolation-check
test ! -e "$evidence/receipt.json"
mkdir -p "$snapshot_dir"
test ! -e "$snapshot_dir/rekordbox3.settings.state.json"
snapshot_guest_file "$guest_settings" "$snapshot_dir/rekordbox3.settings" \
  "$snapshot_dir/rekordbox3.settings.state.json"
jq -e '.exists == true' "$snapshot_dir/rekordbox3.settings.state.json" >/dev/null
snapshot_guest_file "$guest_played" "$snapshot_dir/AnotherHistories.xml" \
  "$snapshot_dir/AnotherHistories.xml.state.json"

for phase in "${phases[@]}"; do
  golden="$goldens/$phase.json"
  test ! -e "$golden"
  test ! -e "$golden.next"
done

for run in 1 2; do
  run_dir="$evidence/repeats/run-$run"
  mkdir -p "$run_dir"
  test ! -e "$run_dir/receipt.json"
  "$script_dir/activate_fixture.sh" "$fixture"
  "$guestctl" copy-to "$reset_settings" "$guest_settings"
  "$guestctl" powershell \
    "Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath '$guest_played'"
  "$script_dir/start_oracle_ui.sh"
  capture_options "$run_dir/options.json"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  unit_1="rekordbox-identity-link-played-multiplayer-$run-player-1"
  unit_2="rekordbox-identity-link-played-multiplayer-$run-player-2"
  start_identity "$identity_1" "$unit_1" "$run_dir/player-1-live.json"
  start_identity "$identity_2" "$unit_2" "$run_dir/player-2-live.json"
  sleep 10
  click_link
  wait_for_dbserver
  capture_health "link-played-multiplayer-run-$run-before" "$started_at" \
    "$run_dir/before-health.json"
  capture_identities before "$unit_1" "$unit_2" \
    "$run_dir/player-1-live.json" "$run_dir/player-2-live.json" \
    "$run_dir/identities-before.json"

  for phase in "${phases[@]}"; do
    suite="$script_dir/$(jq -er --arg id "$phase" '.sequence[] | select(.id == $id) | .suite' "$index")"
    player=$(jq -er --arg id "$phase" '.sequence[] | select(.id == $id) | .player' "$index")
    if [[ $player == 1 ]]; then phase_identity=$identity_1; else phase_identity=$identity_2; fi
    execute_suite "$run" "$suite" "$phase_identity" "$goldens/$phase.json.next" \
      "$run_dir/$phase.json" "$run_dir/$phase.diff.txt"
    capture_health "link-played-multiplayer-run-$run-after-$phase" "$started_at" \
      "$run_dir/after-$phase-health.json"
    capture_identities "after-$phase" "$unit_1" "$unit_2" \
      "$run_dir/player-1-live.json" "$run_dir/player-2-live.json" \
      "$run_dir/identities-after-$phase.json"
  done
  systemctl --user stop "$unit_1.service" "$unit_2.service"
  write_run_receipt "$run" "$run_dir"
done

for phase in "${phases[@]}"; do
  mv "$goldens/$phase.json.next" "$goldens/$phase.json"
done
"$script_dir/activate_fixture.sh" "$baseline"
restore_guest_file "$snapshot_dir/rekordbox3.settings" \
  "$snapshot_dir/rekordbox3.settings.state.json"
restore_guest_file "$snapshot_dir/AnotherHistories.xml" \
  "$snapshot_dir/AnotherHistories.xml.state.json"
restored=true

jq -n --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
  --arg settings_manifest_sha256 "$(sha256sum "$settings_dir/manifest.json" | cut -d' ' -f1)" \
  --arg declaration_index_sha256 "$(sha256sum "$index" | cut -d' ' -f1)" \
  --arg identity_1_sha256 "$(sha256sum "$identity_1" | cut -d' ' -f1)" \
  --arg identity_2_sha256 "$(sha256sum "$identity_2" | cut -d' ' -f1)" \
  --arg run_1_receipt_sha256 "$(sha256sum "$evidence/repeats/run-1/receipt.json" | cut -d' ' -f1)" \
  --arg run_2_receipt_sha256 "$(sha256sum "$evidence/repeats/run-2/receipt.json" | cut -d' ' -f1)" \
  --arg runner_sha256 "$runner_sha256" \
  '{format:1,scope:"real Rekordbox 7.2.19 two-player Link-played ownership",
    completed_at:$completed_at,fixture_manifest_sha256:$fixture_manifest_sha256,
    settings_manifest_sha256:$settings_manifest_sha256,
    declaration_index_sha256:$declaration_index_sha256,
    identity_1_sha256:$identity_1_sha256,identity_2_sha256:$identity_2_sha256,
    run_1_receipt_sha256:$run_1_receipt_sha256,
    run_2_receipt_sha256:$run_2_receipt_sha256,runner_sha256:$runner_sha256,
    identity_count:2,phase_count:4,case_count:28,run_count:2,
    suite_execution_count:8,exact_repeat:true,
    same_process_per_run:true,guest_state_restored:true}' \
  >"$evidence/receipt.json.next"
mv "$evidence/receipt.json.next" "$evidence/receipt.json"

echo "=== Two-player Link-played ownership sequence promoted and guest restored ==="
