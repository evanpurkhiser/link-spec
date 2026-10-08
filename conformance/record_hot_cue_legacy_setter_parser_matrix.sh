#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly root=$(cd -- "$lab/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-legacy-ordinals"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly matrix="$script_dir/data/hot-cue-legacy-setter-parser-matrix.json"
readonly getter_suite="$script_dir/suites/generated/hot-cue-legacy-setter-parser/hot-cue-legacy-setter-parser-read-after.json"
readonly evidence_root="$lab/data/experiments/hot-cue-bank/legacy-setter-parser"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly guest_database='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/master.db'
readonly options='/mnt/documents/multimedia/djing/rekordbox/options.json'
readonly python="$root/rekordbox-windows/.venv/bin/python"

restore() {
  local status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

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
    'Get-Process rekordbox -ErrorAction SilentlyContinue | Stop-Process -Force; $deadline = (Get-Date).AddSeconds(30); while (@(Get-Process rekordbox -ErrorAction SilentlyContinue).Count -gt 0 -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 250 }; if (@(Get-Process rekordbox -ErrorAction SilentlyContinue).Count -gt 0) { throw "rekordbox did not stop before same-database restart" }'
}

file_sha256() {
  local path=$1

  if [[ -f $path ]]; then
    sha256sum "$path" | cut -d' ' -f1
  fi
}

write_receipt() {
  local variant=$1
  local run=$2
  local suite=$3
  local destination=$4
  local started_at=$5
  local getter_artifact=$6
  local restart_artifact=$7

  jq -n \
    --arg variant "$variant" \
    --argjson run "$run" \
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
    '{format:1, variant:$variant, run:$run, started_at:$started_at,
      suite_sha256:$suite_sha256, setter_sha256:$setter_sha256,
      health_sha256:$health_sha256,
      database_snapshot_sha256:$database_snapshot_sha256,
      getter_artifact:$getter_artifact, getter_sha256:$getter_sha256,
      restart_artifact:$restart_artifact, restart_sha256:$restart_sha256,
      restart_health_sha256:($restart_health_sha256 | select(length > 0) // null),
      restart_database_snapshot_sha256:($restart_database_snapshot_sha256 | select(length > 0) // null)}' \
    >"$destination/complete.json.next"
  mv "$destination/complete.json.next" "$destination/complete.json"
}

run_once() {
  local variant=$1
  local run=$2
  local suite=$3
  local destination="$evidence_root/$variant/run-$run"
  local setter="$destination/setter.json"
  local getter="$destination/getter.json"
  local getter_artifact
  local getter_unavailable_outcome
  local restart_artifact
  local started_at

  if [[ -e $destination/complete.json ]]; then
    echo "=== $variant run $run: already complete ==="
    return
  fi

  test ! -e "$destination"
  mkdir -p "$destination"

  echo "=== $variant run $run: reset and isolated launch ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')

  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$setter" record 2>&1 | tee "$destination/setter.log"

  capture_health "$variant-run-$run-after-setter" "$started_at" \
    "$destination/health.json"
  capture_database "$destination/database"

  if jq -e '.rekordbox_process_count > 0' "$destination/health.json" >/dev/null; then
    if REKORDBOX_LINK_MAX_ATTEMPTS=1 \
      "$script_dir/oracle_record.sh" "$getter_suite" "$fixture/manifest.json" \
        "$identity" "$getter" record 2>&1 | tee "$destination/getter.log"; then
      getter_artifact=getter.json
    else
      if grep -Eq \
        'dbserver connection .* failed: connection timed out' \
        "$destination/getter.log"; then
        getter_unavailable_outcome=dbserver-connect-timeout
      elif grep -Eq \
        'port query .* failed: connection timed out' \
        "$destination/getter.log"; then
        getter_unavailable_outcome=port-query-timeout
      else
        return 1
      fi

      capture_health "$variant-run-$run-after-getter-unavailable" "$started_at" \
        "$destination/health-after-getter-unavailable.json"
      jq -n \
        --arg reason 'The post-setter Link Export server stopped accepting connections' \
        --arg outcome "$getter_unavailable_outcome" \
        --arg getter_log_sha256 "$(sha256sum "$destination/getter.log" | cut -d' ' -f1)" \
        --arg health_sha256 "$(sha256sum "$destination/health-after-getter-unavailable.json" | cut -d' ' -f1)" \
        '{skipped:true, outcome:$outcome, reason:$reason,
          getter_log_sha256:$getter_log_sha256,
          health_sha256:$health_sha256}' \
        >"$destination/getter-skipped.json"
      getter_artifact=getter-skipped.json
    fi
  else
    jq -n \
      --arg reason 'Rekordbox was not alive after the isolated setter probe' \
      --arg outcome 'process-exited' \
      '{skipped:true, outcome:$outcome, reason:$reason}' \
      >"$destination/getter-skipped.json"
    getter_artifact=getter-skipped.json
  fi

  if [[ $getter_artifact == getter.json ]] && \
    jq -e '.behavior.cases[0].outcome == "raw_reply"' "$getter" >/dev/null; then
    jq -n \
      --arg reason 'Immediate getter returned a complete raw reply' \
      '{skipped:true, reason:$reason}' >"$destination/restart-skipped.json"
    restart_artifact=restart-skipped.json
  else
    echo "=== $variant run $run: same-database process restart ==="
    stop_rekordbox
    "$script_dir/start_oracle_ui.sh"
    "$script_dir/oracle_record.sh" "$getter_suite" "$fixture/manifest.json" \
      "$identity" "$destination/restart-getter.json" record \
      2>&1 | tee "$destination/restart-getter.log"
    capture_health "$variant-run-$run-after-restart" "$started_at" \
      "$destination/health-after-restart.json"
    capture_database "$destination/database-after-restart"
    restart_artifact=restart-getter.json
  fi

  write_receipt "$variant" "$run" "$suite" "$destination" "$started_at" \
    "$getter_artifact" "$restart_artifact"
}

mapfile -t variants < <(jq -r '.variants[].id' "$matrix")
if [[ $# -gt 0 ]]; then
  variants=("$@")
fi

test -f "$fixture/manifest.json"
test -f "$identity"
test -f "$getter_suite"
mkdir -p "$evidence_root"
if [[ ! -e $evidence_root/baseline.json ]]; then
  "$python" "$lab/tools/snapshot_hot_cue_mutation.py" \
    "$fixture/master.db" "$options" "$evidence_root/baseline.json"
fi

for variant in "${variants[@]}"; do
  suite="$script_dir/suites/generated/hot-cue-legacy-setter-parser/hot-cue-legacy-setter-parser-$variant.json"
  test -f "$suite"
  run_once "$variant" 1 "$suite"
  run_once "$variant" 2 "$suite"
done

echo "=== Legacy Hot Cue setter parser matrix: complete ==="
