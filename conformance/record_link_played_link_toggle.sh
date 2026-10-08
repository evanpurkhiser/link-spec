#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly prime_suite="$script_dir/suites/link-played-persistence-prime.json"
readonly post_suite="$script_dir/suites/link-played-link-toggle-post.json"
readonly goldens="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"
readonly evidence="$lab/data/experiments/played-track-state/link-toggle"
readonly settings_dir="$lab/data/experiments/played-track-state/settings"
readonly reset_settings="$settings_dir/reset.settings"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_settings='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/rekordbox3.settings'
readonly guest_played='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/AnotherHistories.xml'
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly snapshot_dir="$evidence/guest-baseline"
readonly runner="$script_dir/pinned/link-export-conformance"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
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
  [[ -z $peer_address ]] || peer_args=(--peer-address "$peer_address")
  systemd-run --user --collect --unit="$unit" \
    --description="rekordbox Link-played LINK-toggle identity" \
    --working-directory="$script_dir" --property=RuntimeMaxSec=30m \
    python "$script_dir/identity_adapter.py" \
      --model "$model" --player "$player" --device-type "$device_type" \
      --generation "$generation" --mac "$mac" --address "$address" \
      --broadcast "$broadcast" --source-port "$source_port" --peers "$peers" \
      --presence "$presence" --model-code "$model_code" "${peer_args[@]}"
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
  local expected=$1 attempt count
  for attempt in $(seq 1 60); do
    count=$(dbserver_listener_count)
    if [[ $expected == present && $count =~ ^[1-9][0-9]*$ ]]; then return; fi
    if [[ $expected == absent && $count == 0 ]]; then return; fi
    sleep 1
  done
  echo "dbserver listener did not become $expected" >&2
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

execute_suite() {
  local run=$1 suite=$2 candidate=$3 output=$4 diff=$5
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

write_transition() {
  local mode=$1 inactive=$2 ready=$3 output=$4
  jq -n --arg mode "$mode" --argjson inactive "$inactive" --argjson ready "$ready" \
    '{format:1,mode:$mode,transition_checkpoint_listener_count:$inactive,
      ready_listener_count:$ready}' >"$output"
}

write_run_receipt() {
  local id=$1 mode=$2 run=$3 run_dir=$4 health_hashes
  health_hashes=$(for path in "$run_dir"/*-health.json; do
    jq -n --arg name "$(basename "$path")" \
      --arg sha256 "$(sha256sum "$path" | cut -d' ' -f1)" \
      '{name:$name,sha256:$sha256}'
  done | jq -s 'sort_by(.name)')
  jq -n --arg id "$id" --arg mode "$mode" --argjson run "$run" \
    --arg prime_sha256 "$(sha256sum "$run_dir/prime.json" | cut -d' ' -f1)" \
    --arg post_sha256 "$(sha256sum "$run_dir/post.json" | cut -d' ' -f1)" \
    --arg transition_sha256 "$(sha256sum "$run_dir/transition.json" | cut -d' ' -f1)" \
    --arg options_sha256 "$(sha256sum "$run_dir/options.json" | cut -d' ' -f1)" \
    --arg runner_sha256 "$runner_sha256" --argjson health_sha256 "$health_hashes" \
    '{format:1,id:$id,mode:$mode,run:$run,
      prime_sha256:$prime_sha256,post_sha256:$post_sha256,
      transition_sha256:$transition_sha256,options_sha256:$options_sha256,
      runner_sha256:$runner_sha256,health_sha256:$health_sha256,
      same_process:true}' >"$run_dir/receipt.json.next"
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

for mode in control toggle; do
  prime_golden="$goldens/link-played-link-toggle-$mode-prime.json"
  post_golden="$goldens/link-played-link-toggle-$mode-post.json"
  prime_candidate="$prime_golden.next"
  post_candidate="$post_golden.next"
  test ! -e "$prime_golden"
  test ! -e "$post_golden"
  test ! -e "$prime_candidate"
  test ! -e "$post_candidate"
  for run in 1 2; do
    id="$mode-run-$run"
    run_dir="$evidence/repeats/$id"
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
    unit="rekordbox-identity-link-played-link-toggle-$mode-$run"
    start_identity "$unit"
    sleep 8
    click_link
    wait_for_dbserver present
    capture_health "link-played-link-toggle-$id-before" "$started_at" \
      "$run_dir/before-health.json"
    execute_suite "$run" "$prime_suite" "$prime_candidate" \
      "$run_dir/prime.json" "$run_dir/prime.diff.txt"
    capture_health "link-played-link-toggle-$id-after-prime" "$started_at" \
      "$run_dir/after-prime-health.json"

    if [[ $mode == toggle ]]; then
      click_link
      wait_for_dbserver absent
      inactive_count=$(dbserver_listener_count)
      capture_health "link-played-link-toggle-$id-inactive" "$started_at" \
        "$run_dir/inactive-health.json"
      click_link
      wait_for_dbserver present
      ready_count=$(dbserver_listener_count)
      capture_health "link-played-link-toggle-$id-reactivated" "$started_at" \
        "$run_dir/reactivated-health.json"
    else
      inactive_count=$(dbserver_listener_count)
      capture_health "link-played-link-toggle-$id-control-boundary" "$started_at" \
        "$run_dir/control-boundary-health.json"
      ready_count=$(dbserver_listener_count)
      capture_health "link-played-link-toggle-$id-control-ready" "$started_at" \
        "$run_dir/control-ready-health.json"
    fi
    write_transition "$mode" "$inactive_count" "$ready_count" \
      "$run_dir/transition.json"
    execute_suite "$run" "$post_suite" "$post_candidate" \
      "$run_dir/post.json" "$run_dir/post.diff.txt"
    capture_health "link-played-link-toggle-$id-after-post" "$started_at" \
      "$run_dir/after-post-health.json"
    systemctl --user stop "$unit.service"
    write_run_receipt "$id" "$mode" "$run" "$run_dir"
  done
  mv "$prime_candidate" "$prime_golden"
  mv "$post_candidate" "$post_golden"
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
  --arg prime_suite_sha256 "$(sha256sum "$prime_suite" | cut -d' ' -f1)" \
  --arg post_suite_sha256 "$(sha256sum "$post_suite" | cut -d' ' -f1)" \
  --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
  --arg runner_sha256 "$runner_sha256" \
  '{format:1,scope:"real Rekordbox 7.2.19 Link-played LINK-toggle lifecycle",
    completed_at:$completed_at,fixture_manifest_sha256:$fixture_manifest_sha256,
    settings_manifest_sha256:$settings_manifest_sha256,
    prime_suite_sha256:$prime_suite_sha256,post_suite_sha256:$post_suite_sha256,
    identity_sha256:$identity_sha256,runner_sha256:$runner_sha256,
    mode_count:2,run_count:4,suite_execution_count:8,
    exact_repeat:true,same_process_per_run:true,guest_state_restored:true}' \
  >"$evidence/receipt.json.next"
mv "$evidence/receipt.json.next" "$evidence/receipt.json"

echo "=== Link-played LINK-toggle lifecycle promoted and guest restored ==="
