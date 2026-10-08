#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly root=$(cd -- "$lab/.." && pwd)
readonly vm="$root/rekordbox-windows"
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-legacy-ordinals"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly declaration="$script_dir/data/hot-cue-legacy-identical-request-history.json"
readonly getter_suite="$script_dir/suites/generated/hot-cue-legacy-setter-parser/hot-cue-legacy-setter-parser-read-after.json"
readonly evidence_root="$lab/data/experiments/hot-cue-bank/legacy-identical-request-history"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly guest_database='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/master.db'
readonly options='/mnt/documents/multimedia/djing/rekordbox/options.json'
readonly python="$root/rekordbox-windows/.venv/bin/python"

restore() {
  local status=$?
  local cleanup_status=0

  trap - EXIT
  set +e
  if "$guestctl" wait 30 >/dev/null 2>&1; then
    if ! "$script_dir/activate_fixture.sh" "$baseline"; then
      echo "Baseline restore encountered a live database handle; restarting the isolated VM" >&2
      "$vm/vmctl" isolated-restart &&
        "$guestctl" wait 180 &&
        "$vm/vmctl" isolation-check &&
        "$script_dir/activate_fixture.sh" "$baseline"
      cleanup_status=$?
    fi
  else
    cleanup_status=1
  fi

  if ((status == 0 && cleanup_status != 0)); then
    status=$cleanup_status
  fi
  exit "$status"
}
trap restore EXIT

file_sha256() {
  local path=$1

  if [[ -f $path ]]; then
    sha256sum "$path" | cut -d' ' -f1
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

copy_optional() {
  local guest_path=$1
  local host_path=$2

  if [[ $("$guestctl" powershell "[bool](Test-Path '$guest_path')" | tr -d '\r') == True ]]; then
    "$guestctl" copy-from "$guest_path" "$host_path"
  fi
}

capture_database() {
  local destination=$1

  mkdir -p "$destination"
  "$guestctl" copy-from "$guest_database" "$destination/master.db"
  copy_optional "${guest_database}-wal" "$destination/master.db-wal"
  copy_optional "${guest_database}-shm" "$destination/master.db-shm"
  "$python" "$lab/tools/snapshot_hot_cue_mutation.py" \
    "$destination/master.db" "$options" "$destination/snapshot.json"
}

stop_rekordbox() {
  "$guestctl" powershell \
    'Get-Process rekordbox -ErrorAction SilentlyContinue | Stop-Process -Force; $deadline = (Get-Date).AddSeconds(30); while (@(Get-Process rekordbox -ErrorAction SilentlyContinue).Count -gt 0 -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 250 }; if (@(Get-Process rekordbox -ErrorAction SilentlyContinue).Count -gt 0) { throw "rekordbox did not stop" }'
}

restart_isolated_vm() {
  local cycle=$1
  local phase=$2
  local output=$3
  local started_at completed_at active_state initial_state

  started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  initial_state=$(systemctl show rekordbox-windows-isolated.service \
    -p ActiveState --value)
  if [[ $initial_state == active ]]; then
    stop_rekordbox
    "$vm/vmctl" isolated-restart
  else
    "$vm/vmctl" isolated-start
  fi
  "$guestctl" wait 180
  "$vm/vmctl" isolation-check
  completed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  active_state=$(systemctl show rekordbox-windows-isolated.service \
    -p ActiveState --value)
  [[ $active_state == active ]]

  jq -n \
    --argjson cycle "$cycle" \
    --arg phase "$phase" \
    --arg started_at "$started_at" \
    --arg completed_at "$completed_at" \
    --arg initial_state "$initial_state" \
    --arg active_state "$active_state" \
    '{format:1, action:"isolated-vm-restart", cycle:$cycle, phase:$phase,
      started_at:$started_at, completed_at:$completed_at,
      initial_isolated_service_state:$initial_state,
      isolated_service_state:$active_state, isolation_gate:"passed"}' \
    >"$output"
}

write_phase_receipt() {
  local cycle=$1
  local phase=$2
  local suite=$3
  local destination=$4
  local started_at=$5
  local getter_artifact=$6
  local restart_artifact=$7

  jq -n \
    --argjson cycle "$cycle" \
    --arg phase "$phase" \
    --arg started_at "$started_at" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg setter_sha256 "$(sha256sum "$destination/setter.json" | cut -d' ' -f1)" \
    --arg health_sha256 "$(sha256sum "$destination/health.json" | cut -d' ' -f1)" \
    --arg database_snapshot_sha256 "$(sha256sum "$destination/database/snapshot.json" | cut -d' ' -f1)" \
    --arg getter_artifact "$getter_artifact" \
    --arg getter_sha256 "$(sha256sum "$destination/$getter_artifact" | cut -d' ' -f1)" \
    --arg restart_artifact "$restart_artifact" \
    --arg restart_sha256 "$(sha256sum "$destination/$restart_artifact" | cut -d' ' -f1)" \
    --arg restart_health_sha256 "$(file_sha256 "$destination/health-after-restart.json")" \
    --arg restart_database_snapshot_sha256 "$(file_sha256 "$destination/database-after-restart/snapshot.json")" \
    '{format:1, action:"request", cycle:$cycle, phase:$phase,
      started_at:$started_at, suite_sha256:$suite_sha256,
      setter_sha256:$setter_sha256, health_sha256:$health_sha256,
      database_snapshot_sha256:$database_snapshot_sha256,
      getter_artifact:$getter_artifact, getter_sha256:$getter_sha256,
      restart_artifact:$restart_artifact, restart_sha256:$restart_sha256,
      restart_health_sha256:($restart_health_sha256 | select(length > 0) // null),
      restart_database_snapshot_sha256:($restart_database_snapshot_sha256 | select(length > 0) // null)}' \
    >"$destination/complete.json.next"
  mv "$destination/complete.json.next" "$destination/complete.json"
}

run_request_phase() {
  local cycle=$1
  local phase=$2
  local suite=$3
  local destination=$4
  local setter="$destination/setter.json"
  local getter="$destination/getter.json"
  local getter_artifact getter_unavailable_outcome restart_artifact started_at

  mkdir -p "$destination"
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell \
    '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')

  REKORDBOX_LINK_MAX_ATTEMPTS=1 \
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$setter" record 2>&1 | tee "$destination/setter.log"

  capture_health "$phase-cycle-$cycle-after-setter" "$started_at" \
    "$destination/health.json"
  capture_database "$destination/database"

  if jq -e '.rekordbox_process_count > 0' "$destination/health.json" >/dev/null; then
    if REKORDBOX_LINK_MAX_ATTEMPTS=1 \
      "$script_dir/oracle_record.sh" "$getter_suite" "$fixture/manifest.json" \
        "$identity" "$getter" record 2>&1 | tee "$destination/getter.log"; then
      getter_artifact=getter.json
    else
      if grep -Eq 'dbserver connection .* failed: connection timed out' \
        "$destination/getter.log"; then
        getter_unavailable_outcome=dbserver-connect-timeout
      elif grep -Eq 'port query .* failed: connection timed out' \
        "$destination/getter.log"; then
        getter_unavailable_outcome=port-query-timeout
      else
        return 1
      fi

      capture_health "$phase-cycle-$cycle-after-getter-unavailable" "$started_at" \
        "$destination/health-after-getter-unavailable.json"
      jq -n \
        --arg outcome "$getter_unavailable_outcome" \
        --arg getter_log_sha256 "$(sha256sum "$destination/getter.log" | cut -d' ' -f1)" \
        --arg health_sha256 "$(sha256sum "$destination/health-after-getter-unavailable.json" | cut -d' ' -f1)" \
        '{skipped:true, outcome:$outcome,
          reason:"The post-setter Link Export server stopped accepting connections",
          getter_log_sha256:$getter_log_sha256, health_sha256:$health_sha256}' \
        >"$destination/getter-skipped.json"
      getter_artifact=getter-skipped.json
    fi
  else
    jq -n \
      '{skipped:true, outcome:"process-exited",
        reason:"Rekordbox was not alive after the isolated setter probe"}' \
      >"$destination/getter-skipped.json"
    getter_artifact=getter-skipped.json
  fi

  if [[ $getter_artifact == getter.json ]] && \
    jq -e '.behavior.cases[0].outcome == "raw_reply"' "$getter" >/dev/null; then
    jq -n \
      '{skipped:true, reason:"Immediate getter returned a complete raw reply"}' \
      >"$destination/restart-skipped.json"
    restart_artifact=restart-skipped.json
  else
    stop_rekordbox
    "$script_dir/start_oracle_ui.sh"
    "$script_dir/oracle_record.sh" "$getter_suite" "$fixture/manifest.json" \
      "$identity" "$destination/restart-getter.json" record \
      2>&1 | tee "$destination/restart-getter.log"
    capture_health "$phase-cycle-$cycle-after-restart" "$started_at" \
      "$destination/health-after-restart.json"
    capture_database "$destination/database-after-restart"
    restart_artifact=restart-getter.json
  fi

  write_phase_receipt "$cycle" "$phase" "$suite" "$destination" \
    "$started_at" "$getter_artifact" "$restart_artifact"
}

write_cycle_receipt() {
  local cycle=$1
  local directory=$2
  local phase_receipts restart_receipts

  phase_receipts=$(find "$directory" -mindepth 2 -maxdepth 2 \
    -type f -name complete.json -print0 | sort -z | while IFS= read -r -d '' path; do
      printf '%s  %s\n' "$(sha256sum "$path" | cut -d' ' -f1)" "${path#"$directory/"}"
    done)
  restart_receipts=$(find "$directory" -mindepth 1 -maxdepth 1 \
    -type f -name '*isolated-vm-restart.json' -print0 | sort -z | while IFS= read -r -d '' path; do
      printf '%s  %s\n' "$(sha256sum "$path" | cut -d' ' -f1)" "${path#"$directory/"}"
    done)

  jq -n \
    --argjson cycle "$cycle" \
    --arg declaration_sha256 "$(sha256sum "$declaration" | cut -d' ' -f1)" \
    --arg phase_receipts "$phase_receipts" \
    --arg restart_receipts "$restart_receipts" \
    '{format:1, cycle:$cycle, declaration_sha256:$declaration_sha256,
      phase_receipts:($phase_receipts | split("\n") | map(select(length > 0) |
        capture("^(?<sha256>[^ ]+)  (?<path>.+)$"))),
      restart_receipts:($restart_receipts | split("\n") | map(select(length > 0) |
        capture("^(?<sha256>[^ ]+)  (?<path>.+)$")))}' \
    >"$directory/complete.json"
}

phase_receipt_is_complete() {
  local cycle=$1
  local phase=$2
  local suite=$3
  local destination=$4
  local receipt="$destination/complete.json"
  local getter_artifact restart_artifact

  [[ -f $receipt ]] || return 1
  jq -e \
    --argjson cycle "$cycle" \
    --arg phase "$phase" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" '
      .format == 1 and .action == "request" and
      .cycle == $cycle and .phase == $phase and
      .suite_sha256 == $suite_sha256
    ' "$receipt" >/dev/null || return 1

  [[ $(jq -r .setter_sha256 "$receipt") == "$(sha256sum "$destination/setter.json" | cut -d' ' -f1)" ]] || return 1
  [[ $(jq -r .health_sha256 "$receipt") == "$(sha256sum "$destination/health.json" | cut -d' ' -f1)" ]] || return 1
  [[ $(jq -r .database_snapshot_sha256 "$receipt") == "$(sha256sum "$destination/database/snapshot.json" | cut -d' ' -f1)" ]] || return 1

  getter_artifact=$(jq -er .getter_artifact "$receipt") || return 1
  restart_artifact=$(jq -er .restart_artifact "$receipt") || return 1
  [[ $(jq -r .getter_sha256 "$receipt") == "$(sha256sum "$destination/$getter_artifact" | cut -d' ' -f1)" ]] || return 1
  [[ $(jq -r .restart_sha256 "$receipt") == "$(sha256sum "$destination/$restart_artifact" | cut -d' ' -f1)" ]] || return 1

  if [[ -f $destination/health-after-restart.json ]]; then
    [[ $(jq -r .restart_health_sha256 "$receipt") == "$(sha256sum "$destination/health-after-restart.json" | cut -d' ' -f1)" ]] || return 1
    [[ $(jq -r .restart_database_snapshot_sha256 "$receipt") == "$(sha256sum "$destination/database-after-restart/snapshot.json" | cut -d' ' -f1)" ]] || return 1
  else
    [[ $(jq -r .restart_health_sha256 "$receipt") == null ]] || return 1
    [[ $(jq -r .restart_database_snapshot_sha256 "$receipt") == null ]] || return 1
  fi
}

restart_receipt_is_complete() {
  local cycle=$1
  local phase=$2
  local path=$3

  [[ -f $path ]] || return 1
  jq -e --argjson cycle "$cycle" --arg phase "$phase" '
    .format == 1 and .action == "isolated-vm-restart" and
    .cycle == $cycle and .phase == $phase and
    .isolated_service_state == "active" and .isolation_gate == "passed"
  ' "$path" >/dev/null
}

test -f "$fixture/manifest.json"
test -f "$identity"
test -f "$getter_suite"
mkdir -p "$evidence_root"

cycles=$(jq -er .cycles "$declaration")
for cycle in $(seq 1 "$cycles"); do
  final="$evidence_root/cycle-$cycle"
  pending="$final.next"
  if [[ -f $final/complete.json ]]; then
    echo "=== identical-request history cycle $cycle: already complete ==="
    continue
  fi
  test ! -e "$final"
  mkdir -p "$pending"

  index=0
  mapfile -t phases < <(jq -c '.phases[]' "$declaration")
  for phase_json in "${phases[@]}"; do
    index=$((index + 1))
    action=$(jq -r .action <<<"$phase_json")
    phase=$(jq -r .id <<<"$phase_json")
    prefix=$(printf '%02d-%s' "$index" "$phase")

    if [[ $action == isolated-vm-restart ]]; then
      restart_path="$pending/$prefix-isolated-vm-restart.json"
      if restart_receipt_is_complete "$cycle" "$phase" "$restart_path"; then
        echo "=== cycle $cycle phase $phase: resuming complete VM restart receipt ==="
      else
        if [[ -e $restart_path ]]; then
          mv "$restart_path" "$restart_path.interrupted-$(date -u +%Y%m%dT%H%M%SZ)"
        fi
        restart_isolated_vm "$cycle" "$phase" "$restart_path"
      fi
      continue
    fi

    if ((index == 1)) && \
      [[ $(jq -r '.vm_state // "continuous"' <<<"$phase_json") == fresh-isolated-restart ]]; then
      restart_isolated_vm "$cycle" "$phase-before" \
        "$pending/$prefix-before-isolated-vm-restart.json"
    fi
    suite="$script_dir/$(jq -r .suite <<<"$phase_json")"
    test -f "$suite"
    destination="$pending/$prefix"
    if phase_receipt_is_complete "$cycle" "$phase" "$suite" "$destination"; then
      echo "=== cycle $cycle phase $phase: resuming complete phase receipt ==="
      continue
    fi
    if [[ -e $destination ]]; then
      interrupted="$destination.interrupted-$(date -u +%Y%m%dT%H%M%SZ)"
      test ! -e "$interrupted"
      mv "$destination" "$interrupted"
      echo "=== cycle $cycle phase $phase: quarantined incomplete evidence at $interrupted ==="
    fi
    run_request_phase "$cycle" "$phase" "$suite" "$destination"
  done

  write_cycle_receipt "$cycle" "$pending"
  mv "$pending" "$final"
done

echo "=== Legacy Hot Cue identical-request history: complete ==="
