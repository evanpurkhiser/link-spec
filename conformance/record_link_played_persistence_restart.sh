#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly prime_suite="$script_dir/suites/link-played-persistence-prime.json"
readonly restart_suite="$script_dir/suites/link-played-persistence-restart.json"
readonly goldens="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"
readonly evidence="$lab/data/experiments/played-track-state/persistence-restart"
readonly settings_dir="$lab/data/experiments/played-track-state/settings"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_settings='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/rekordbox3.settings'
readonly guest_played='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/AnotherHistories.xml'
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly snapshot_dir="$evidence/guest-baseline"
readonly runner="$script_dir/pinned/link-export-conformance"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
readonly variants=(reset link-persist ordinary-persist persist)
restored=false

file_sha256() {
  if [[ -f $1 ]]; then
    sha256sum "$1" | cut -d' ' -f1
  else
    printf 'absent\n'
  fi
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

  echo "failed to capture guest health after five attempts" >&2
  return 1
}

snapshot_guest_file() {
  local guest_path=$1
  local host_path=$2
  local metadata=$3
  local exists sha256

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

  jq -n \
    --arg guest_path "$guest_path" \
    --argjson exists "$exists" \
    --arg sha256 "$sha256" \
    '{format:1,guest_path:$guest_path,exists:$exists,
      sha256:(if $sha256 == "" then null else $sha256 end)}' >"$metadata"
}

restore_guest_file() {
  local host_path=$1
  local metadata=$2
  local guest_path exists expected actual

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
  if [[ $restored != true && -f $snapshot_dir/rekordbox3.settings.state.json ]]; then
    "$script_dir/activate_fixture.sh" "$baseline"
    restore_guest_file \
      "$snapshot_dir/rekordbox3.settings" \
      "$snapshot_dir/rekordbox3.settings.state.json"
    restore_guest_file \
      "$snapshot_dir/AnotherHistories.xml" \
      "$snapshot_dir/AnotherHistories.xml.state.json"
  fi
  exit "$status"
}
trap restore EXIT

capture_options() {
  local variant=$1
  local output=$2
  local played link

  played=$(jq -er --arg state "$variant" \
    '.variants[] | select(.state == $state) | .values.PlayedTrackOption' \
    "$settings_dir/manifest.json")
  link=$(jq -er --arg state "$variant" \
    '.variants[] | select(.state == $state) | .values.LinkPlayedTrackOption' \
    "$settings_dir/manifest.json")
  "$guestctl" powershell \
    "[xml]\$s = Get-Content -Raw -LiteralPath '$guest_settings'; \$names = 'PlayedTrackOption','LinkPlayedTrackOption'; @((\$s.PROPERTIES.VALUE | Where-Object { \$_.name -in \$names } | Sort-Object name | ForEach-Object { [ordered]@{name=[string]\$_.name;val=[int]\$_.val} })) | ConvertTo-Json" \
    >"$output"
  jq -e \
    --argjson played "$played" \
    --argjson link "$link" '
      length == 2 and
      (map({key:.name,value:.val}) | from_entries) == {
        PlayedTrackOption:$played,LinkPlayedTrackOption:$link
      }
    ' "$output" >/dev/null
}

clean_shutdown() {
  local output=$1

  "$guestctl" powershell \
    "\$started = [DateTime]::UtcNow; \$processes = @(Get-Process rekordbox -ErrorAction SilentlyContinue); if (\$processes.Count -ne 1) { throw \"Expected one rekordbox process, found \$(\$processes.Count)\" }; \$rekordboxPid = \$processes[0].Id; if (-not \$processes[0].CloseMainWindow()) { throw 'CloseMainWindow was rejected' }; \$deadline = (Get-Date).AddSeconds(60); while (@(Get-Process -Id \$rekordboxPid -ErrorAction SilentlyContinue).Count -gt 0 -and (Get-Date) -lt \$deadline) { Start-Sleep -Milliseconds 250 }; if (@(Get-Process -Id \$rekordboxPid -ErrorAction SilentlyContinue).Count -gt 0) { throw 'rekordbox did not exit cleanly within 60 seconds' }; Get-Process rekordboxAgent,edb_streamd -ErrorAction SilentlyContinue | Stop-Process -Force; [ordered]@{format=1;process_id=\$rekordboxPid;close_main_window_accepted=\$true;forced_rekordbox_termination=\$false;started_at=\$started.ToString('o');completed_at=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json" \
    >"$output"
  jq -e '
    .format == 1 and .process_id > 0 and
    .close_main_window_accepted == true and
    .forced_rekordbox_termination == false
  ' "$output" >/dev/null
}

start_process() {
  local variant=$1
  local stage=$2
  local run=$3
  local options=$4
  local before_health=$5
  local started_at

  "$script_dir/start_oracle_ui.sh"
  capture_options "$variant" "$options"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell \
    '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "link-played-persistence-$variant-run-$run-$stage-before" \
    "$started_at" "$before_health"
  printf '%s\n' "$started_at"
}

record_suite() {
  local suite=$1
  local golden=$2
  local phase=$3

  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$golden" "$phase"
}

write_run_receipt() {
  local variant=$1
  local run=$2
  local run_dir=$3
  local phase=$4
  local prime_target=$5
  local restart_target=$6

  jq -n \
    --arg variant "$variant" \
    --argjson run "$run" \
    --arg phase "$phase" \
    --arg prime_sha256 "$(sha256sum "$prime_target" | cut -d' ' -f1)" \
    --arg restart_sha256 "$(sha256sum "$restart_target" | cut -d' ' -f1)" \
    --arg prime_options_sha256 "$(sha256sum "$run_dir/prime-options.json" | cut -d' ' -f1)" \
    --arg restart_options_sha256 "$(sha256sum "$run_dir/restart-options.json" | cut -d' ' -f1)" \
    --arg prime_shutdown_sha256 "$(sha256sum "$run_dir/prime-shutdown.json" | cut -d' ' -f1)" \
    --arg restart_shutdown_sha256 "$(sha256sum "$run_dir/restart-shutdown.json" | cut -d' ' -f1)" \
    --arg prime_played_state_sha256 "$(sha256sum "$run_dir/prime-shutdown-AnotherHistories.state.json" | cut -d' ' -f1)" \
    --arg prime_played_sha256 "$(file_sha256 "$run_dir/prime-shutdown-AnotherHistories.xml")" \
    --arg restart_played_state_sha256 "$(sha256sum "$run_dir/restart-shutdown-AnotherHistories.state.json" | cut -d' ' -f1)" \
    --arg restart_played_sha256 "$(file_sha256 "$run_dir/restart-shutdown-AnotherHistories.xml")" \
    --arg prime_health_before_sha256 "$(sha256sum "$run_dir/prime-health-before.json" | cut -d' ' -f1)" \
    --arg prime_health_after_sha256 "$(sha256sum "$run_dir/prime-health-after.json" | cut -d' ' -f1)" \
    --arg restart_health_before_sha256 "$(sha256sum "$run_dir/restart-health-before.json" | cut -d' ' -f1)" \
    --arg restart_health_after_sha256 "$(sha256sum "$run_dir/restart-health-after.json" | cut -d' ' -f1)" \
    '{format:1,variant:$variant,run:$run,phase:$phase,
      prime_sha256:$prime_sha256,restart_sha256:$restart_sha256,
      prime_options_sha256:$prime_options_sha256,
      restart_options_sha256:$restart_options_sha256,
      prime_shutdown_sha256:$prime_shutdown_sha256,
      restart_shutdown_sha256:$restart_shutdown_sha256,
      prime_played_state_sha256:$prime_played_state_sha256,
      prime_played_sha256:$prime_played_sha256,
      restart_played_state_sha256:$restart_played_state_sha256,
      restart_played_sha256:$restart_played_sha256,
      prime_health_before_sha256:$prime_health_before_sha256,
      prime_health_after_sha256:$prime_health_after_sha256,
      restart_health_before_sha256:$restart_health_before_sha256,
      restart_health_after_sha256:$restart_health_after_sha256,
      same_database_restart:true,clean_shutdowns:2}' >"$run_dir/receipt.json.next"
  mv "$run_dir/receipt.json.next" "$run_dir/receipt.json"
}

run_once() {
  local variant=$1
  local run=$2
  local phase=$3
  local prime_target=$4
  local restart_target=$5
  local run_dir="$evidence/repeats/$variant/run-$run"
  local started_at

  mkdir -p "$run_dir"
  test ! -e "$run_dir/receipt.json"
  "$script_dir/activate_fixture.sh" "$fixture"
  "$guestctl" copy-to "$settings_dir/$variant.settings" "$guest_settings"
  "$guestctl" powershell \
    "Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath '$guest_played'"

  started_at=$(start_process "$variant" prime "$run" "$run_dir/prime-options.json" \
    "$run_dir/prime-health-before.json" | tail -n 1)
  record_suite "$prime_suite" "$prime_target" "$phase"
  capture_health "link-played-persistence-$variant-run-$run-prime-after" \
    "$started_at" "$run_dir/prime-health-after.json"
  clean_shutdown "$run_dir/prime-shutdown.json"
  snapshot_guest_file "$guest_played" \
    "$run_dir/prime-shutdown-AnotherHistories.xml" \
    "$run_dir/prime-shutdown-AnotherHistories.state.json"

  started_at=$(start_process "$variant" restart "$run" "$run_dir/restart-options.json" \
    "$run_dir/restart-health-before.json" | tail -n 1)
  record_suite "$restart_suite" "$restart_target" "$phase"
  capture_health "link-played-persistence-$variant-run-$run-restart-after" \
    "$started_at" "$run_dir/restart-health-after.json"
  clean_shutdown "$run_dir/restart-shutdown.json"
  snapshot_guest_file "$guest_played" \
    "$run_dir/restart-shutdown-AnotherHistories.xml" \
    "$run_dir/restart-shutdown-AnotherHistories.state.json"

  write_run_receipt "$variant" "$run" "$run_dir" "$phase" \
    "$prime_target" "$restart_target"
}

write_variant_receipt() {
  local variant=$1
  local directory="$evidence/repeats/$variant"
  local prime_golden="$goldens/link-played-persistence-$variant-prime.json"
  local restart_golden="$goldens/link-played-persistence-$variant-restart.json"

  jq -n \
    --arg variant "$variant" \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg prime_golden_sha256 "$(sha256sum "$prime_golden" | cut -d' ' -f1)" \
    --arg restart_golden_sha256 "$(sha256sum "$restart_golden" | cut -d' ' -f1)" \
    --arg run_1_receipt_sha256 "$(sha256sum "$directory/run-1/receipt.json" | cut -d' ' -f1)" \
    --arg run_2_receipt_sha256 "$(sha256sum "$directory/run-2/receipt.json" | cut -d' ' -f1)" \
    '{format:1,variant:$variant,completed_at:$completed_at,
      prime_golden_sha256:$prime_golden_sha256,
      restart_golden_sha256:$restart_golden_sha256,
      run_1_receipt_sha256:$run_1_receipt_sha256,
      run_2_receipt_sha256:$run_2_receipt_sha256,
      run_count:2,suite_execution_count:4,exact_repeat:true,
      clean_shutdown_count:4}' >"$directory/receipt.json.next"
  mv "$directory/receipt.json.next" "$directory/receipt.json"
}

test -f "$fixture/manifest.json"
test -f "$baseline/manifest.json"
test -f "$identity"
test -f "$prime_suite"
test -f "$restart_suite"
test -x "$runner"
test "$(sha256sum "$runner" | cut -d' ' -f1)" = \
  "$(jq -er .runner.sha256 "$pinned_manifest")"
test ! -e "$evidence/receipt.json"
mkdir -p "$snapshot_dir"
test ! -e "$snapshot_dir/rekordbox3.settings.state.json"

snapshot_guest_file "$guest_settings" \
  "$snapshot_dir/rekordbox3.settings" \
  "$snapshot_dir/rekordbox3.settings.state.json"
jq -e '.exists == true' "$snapshot_dir/rekordbox3.settings.state.json" >/dev/null
snapshot_guest_file "$guest_played" \
  "$snapshot_dir/AnotherHistories.xml" \
  "$snapshot_dir/AnotherHistories.xml.state.json"

for variant in "${variants[@]}"; do
  prime_golden="$goldens/link-played-persistence-$variant-prime.json"
  restart_golden="$goldens/link-played-persistence-$variant-restart.json"
  prime_candidate="$prime_golden.next"
  restart_candidate="$restart_golden.next"
  test ! -e "$prime_golden"
  test ! -e "$restart_golden"
  test ! -e "$prime_candidate"
  test ! -e "$restart_candidate"

  run_once "$variant" 1 record "$prime_candidate" "$restart_candidate"
  run_once "$variant" 2 repeat "$prime_candidate" "$restart_candidate"
  mv "$prime_candidate" "$prime_golden"
  mv "$restart_candidate" "$restart_golden"
  write_variant_receipt "$variant"
done

"$script_dir/activate_fixture.sh" "$baseline"
restore_guest_file \
  "$snapshot_dir/rekordbox3.settings" \
  "$snapshot_dir/rekordbox3.settings.state.json"
restore_guest_file \
  "$snapshot_dir/AnotherHistories.xml" \
  "$snapshot_dir/AnotherHistories.xml.state.json"
restored=true

jq -n \
  --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
  --arg settings_manifest_sha256 "$(sha256sum "$settings_dir/manifest.json" | cut -d' ' -f1)" \
  --arg prime_suite_sha256 "$(sha256sum "$prime_suite" | cut -d' ' -f1)" \
  --arg restart_suite_sha256 "$(sha256sum "$restart_suite" | cut -d' ' -f1)" \
  --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
  --arg runner_sha256 "$(sha256sum "$runner" | cut -d' ' -f1)" \
  --arg reset_receipt_sha256 "$(sha256sum "$evidence/repeats/reset/receipt.json" | cut -d' ' -f1)" \
  --arg link_persist_receipt_sha256 "$(sha256sum "$evidence/repeats/link-persist/receipt.json" | cut -d' ' -f1)" \
  --arg ordinary_persist_receipt_sha256 "$(sha256sum "$evidence/repeats/ordinary-persist/receipt.json" | cut -d' ' -f1)" \
  --arg persist_receipt_sha256 "$(sha256sum "$evidence/repeats/persist/receipt.json" | cut -d' ' -f1)" \
  '{format:1,
    scope:"real Rekordbox 7.2.19 played-option persistence/restart matrix",
    completed_at:$completed_at,fixture_manifest_sha256:$fixture_manifest_sha256,
    settings_manifest_sha256:$settings_manifest_sha256,
    prime_suite_sha256:$prime_suite_sha256,
    restart_suite_sha256:$restart_suite_sha256,
    identity_sha256:$identity_sha256,runner_sha256:$runner_sha256,
    variant_receipts:{reset:$reset_receipt_sha256,
      "link-persist":$link_persist_receipt_sha256,
      "ordinary-persist":$ordinary_persist_receipt_sha256,
      persist:$persist_receipt_sha256},
    variant_count:4,run_count:8,suite_execution_count:16,
    clean_shutdown_count:16,exact_repeat:true,
    guest_state_restored:true}' >"$evidence/receipt.json.next"
mv "$evidence/receipt.json.next" "$evidence/receipt.json"

echo "=== Played-option persistence/restart matrix promoted and guest restored ==="
