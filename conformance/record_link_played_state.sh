#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly suite="$script_dir/suites/link-played-state.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/link-played-state.json"
readonly candidate="$golden.next"
readonly evidence="$lab/data/experiments/played-track-state/transition-reset"
readonly settings_dir="$lab/data/experiments/played-track-state/settings"
readonly reset_settings="$settings_dir/reset.settings"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_settings='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/rekordbox3.settings'
readonly guest_played='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/AnotherHistories.xml'
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly snapshot_dir="$evidence/guest-baseline"
readonly runner="$script_dir/pinned/link-export-conformance"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
restored=false

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
    false)
      sha256=''
      ;;
    *)
      echo "unexpected existence result for $guest_path: $exists" >&2
      return 1
      ;;
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
  local output=$1

  "$guestctl" powershell \
    "[xml]\$s = Get-Content -Raw -LiteralPath '$guest_settings'; \$names = 'PlayedTrackOption','LinkPlayedTrackOption'; @((\$s.PROPERTIES.VALUE | Where-Object { \$_.name -in \$names } | Sort-Object name | ForEach-Object { [ordered]@{name=[string]\$_.name;val=[int]\$_.val} })) | ConvertTo-Json" \
    >"$output"
  jq -e '
    length == 2 and
    ([.[].name] | sort) == ["LinkPlayedTrackOption","PlayedTrackOption"] and
    all(.[]; .val == 1)
  ' "$output" >/dev/null
}

prepare_phase() {
  local phase=$1

  "$script_dir/activate_fixture.sh" "$fixture"
  if [[ $phase == repeat ]]; then
    snapshot_guest_file "$guest_played" \
      "$evidence/record-shutdown-AnotherHistories.xml" \
      "$evidence/record-shutdown-AnotherHistories.state.json"
    jq -e '.exists == false' \
      "$evidence/record-shutdown-AnotherHistories.state.json" >/dev/null
  fi
  "$guestctl" copy-to "$reset_settings" "$guest_settings"
  "$guestctl" powershell \
    "Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath '$guest_played'"
  "$script_dir/start_oracle_ui.sh"
  capture_options "$evidence/$phase-options.json"
}

run_phase() {
  local phase=$1
  local started_at

  echo "=== Link-played state: $phase fresh fixture, settings, and process ==="
  prepare_phase "$phase"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell \
    '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "link-played-state-$phase-before" "$started_at" \
    "$evidence/$phase-health-before.json"
  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$candidate" "$phase"
  capture_health "link-played-state-$phase-after" "$started_at" \
    "$evidence/$phase-health-after.json"
}

write_receipt() {
  local baseline_played_sha256

  baseline_played_sha256=$(jq -r '.sha256 // "absent"' \
    "$snapshot_dir/AnotherHistories.xml.state.json")
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg settings_manifest_sha256 "$(sha256sum "$settings_dir/manifest.json" | cut -d' ' -f1)" \
    --arg reset_settings_sha256 "$(sha256sum "$reset_settings" | cut -d' ' -f1)" \
    --arg guest_baseline_settings_sha256 "$(sha256sum "$snapshot_dir/rekordbox3.settings" | cut -d' ' -f1)" \
    --arg guest_baseline_settings_state_sha256 "$(sha256sum "$snapshot_dir/rekordbox3.settings.state.json" | cut -d' ' -f1)" \
    --arg guest_baseline_played_sha256 "$baseline_played_sha256" \
    --arg guest_baseline_played_state_sha256 "$(sha256sum "$snapshot_dir/AnotherHistories.xml.state.json" | cut -d' ' -f1)" \
    --arg record_shutdown_played_state_sha256 "$(sha256sum "$evidence/record-shutdown-AnotherHistories.state.json" | cut -d' ' -f1)" \
    --arg repeat_shutdown_played_state_sha256 "$(sha256sum "$evidence/repeat-shutdown-AnotherHistories.state.json" | cut -d' ' -f1)" \
    --arg runner_sha256 "$(sha256sum "$runner" | cut -d' ' -f1)" \
    --arg pinned_manifest_sha256 "$(sha256sum "$pinned_manifest" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --arg record_options_sha256 "$(sha256sum "$evidence/record-options.json" | cut -d' ' -f1)" \
    --arg repeat_options_sha256 "$(sha256sum "$evidence/repeat-options.json" | cut -d' ' -f1)" \
    --arg record_health_before_sha256 "$(sha256sum "$evidence/record-health-before.json" | cut -d' ' -f1)" \
    --arg record_health_after_sha256 "$(sha256sum "$evidence/record-health-after.json" | cut -d' ' -f1)" \
    --arg repeat_health_before_sha256 "$(sha256sum "$evidence/repeat-health-before.json" | cut -d' ' -f1)" \
    --arg repeat_health_after_sha256 "$(sha256sum "$evidence/repeat-health-after.json" | cut -d' ' -f1)" \
    '{format:1,
      scope:"real Rekordbox 7.2.19 Link-played transition under reset options",
      completed_at:$completed_at,suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256,
      settings_manifest_sha256:$settings_manifest_sha256,
      reset_settings_sha256:$reset_settings_sha256,
      guest_baseline_settings_sha256:$guest_baseline_settings_sha256,
      guest_baseline_settings_state_sha256:$guest_baseline_settings_state_sha256,
      guest_baseline_played_sha256:$guest_baseline_played_sha256,
      guest_baseline_played_state_sha256:$guest_baseline_played_state_sha256,
      record_shutdown_played_state_sha256:$record_shutdown_played_state_sha256,
      repeat_shutdown_played_state_sha256:$repeat_shutdown_played_state_sha256,
      runner_sha256:$runner_sha256,
      pinned_manifest_sha256:$pinned_manifest_sha256,
      golden_sha256:$golden_sha256,
      record_options_sha256:$record_options_sha256,
      repeat_options_sha256:$repeat_options_sha256,
      record_health_before_sha256:$record_health_before_sha256,
      record_health_after_sha256:$record_health_after_sha256,
      repeat_health_before_sha256:$repeat_health_before_sha256,
      repeat_health_after_sha256:$repeat_health_after_sha256,
      case_count:19,process_count:2,exact_repeat:true,
      guest_state_restored:true}' >"$evidence/receipt.json.next"
  mv "$evidence/receipt.json.next" "$evidence/receipt.json"
}

test -f "$fixture/manifest.json"
test -f "$baseline/manifest.json"
test -f "$identity"
test -f "$suite"
test -f "$reset_settings"
test -f "$settings_dir/manifest.json"
test -x "$runner"
test -f "$pinned_manifest"
test "$(sha256sum "$runner" | cut -d' ' -f1)" = \
  "$(jq -er .runner.sha256 "$pinned_manifest")"
test ! -e "$golden"
test ! -e "$candidate"
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

run_phase record
run_phase repeat

mv "$candidate" "$golden"
"$script_dir/activate_fixture.sh" "$baseline"
snapshot_guest_file "$guest_played" \
  "$evidence/repeat-shutdown-AnotherHistories.xml" \
  "$evidence/repeat-shutdown-AnotherHistories.state.json"
jq -e '.exists == false' \
  "$evidence/repeat-shutdown-AnotherHistories.state.json" >/dev/null
restore_guest_file \
  "$snapshot_dir/rekordbox3.settings" \
  "$snapshot_dir/rekordbox3.settings.state.json"
restore_guest_file \
  "$snapshot_dir/AnotherHistories.xml" \
  "$snapshot_dir/AnotherHistories.xml.state.json"
restored=true
write_receipt

echo "=== Link-played state transition: promoted and guest state restored ==="
