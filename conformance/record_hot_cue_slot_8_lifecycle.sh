#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly root=$(cd -- "$lab/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-mutation-duplicate-slot"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly profile=${1:-slot-00000008}
case "$profile" in
  slot-00000008)
    readonly matrix="$script_dir/data/hot-cue-slot-8-lifecycle-matrix.json"
    readonly evidence_root="$lab/data/experiments/hot-cue-bank/extended-setter-parser/slot-00000008-lifecycle"
    readonly profile_label="slot-8"
    ;;
  returned-slots-ffffffff)
    readonly matrix="$script_dir/data/hot-cue-returned-slots-ffffffff-lifecycle-matrix.json"
    readonly evidence_root="$lab/data/experiments/hot-cue-bank/extended-setter-parser/returned-slots-ffffffff-lifecycle"
    readonly profile_label="returned-slots-ffffffff"
    ;;
  *)
    echo "unknown lifecycle profile: $profile" >&2
    exit 2
    ;;
esac
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

copy_optional() {
  local guest_path=$1
  local host_path=$2

  if [[ $("$guestctl" powershell "[bool](Test-Path '$guest_path')" | tr -d '\r') == True ]]; then
    "$guestctl" copy-from "$guest_path" "$host_path"
  fi
}

capture_snapshot() (
  local output=$1
  local temporary

  temporary=$(mktemp -d)
  trap 'rm -rf "$temporary"' EXIT
  "$guestctl" copy-from "$guest_database" "$temporary/master.db"
  copy_optional "${guest_database}-wal" "$temporary/master.db-wal"
  copy_optional "${guest_database}-shm" "$temporary/master.db-shm"
  "$python" "$lab/tools/snapshot_hot_cue_mutation.py" \
    "$temporary/master.db" "$options" "$output"
)

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

write_receipt() {
  local run=$1
  local destination=$2
  local started_at=$3

  jq -n \
    --argjson run "$run" \
    --arg started_at "$started_at" \
    --arg observation_suite_sha256 "$(sha256sum "$observation_suite" | cut -d' ' -f1)" \
    --arg restart_suite_sha256 "$(sha256sum "$restart_suite" | cut -d' ' -f1)" \
    --arg observation_sha256 "$(sha256sum "$destination/observation.json" | cut -d' ' -f1)" \
    --arg health_after_observation_sha256 "$(sha256sum "$destination/health-after-observation.json" | cut -d' ' -f1)" \
    --arg snapshot_after_observation_sha256 "$(sha256sum "$destination/snapshot-after-observation.json" | cut -d' ' -f1)" \
    --arg restart_getter_sha256 "$(sha256sum "$destination/restart-getter.json" | cut -d' ' -f1)" \
    --arg health_after_restart_sha256 "$(sha256sum "$destination/health-after-restart.json" | cut -d' ' -f1)" \
    --arg snapshot_after_restart_sha256 "$(sha256sum "$destination/snapshot-after-restart.json" | cut -d' ' -f1)" \
    '{format:1, run:$run, started_at:$started_at,
      observation_suite_sha256:$observation_suite_sha256,
      restart_suite_sha256:$restart_suite_sha256,
      observation_sha256:$observation_sha256,
      health_after_observation_sha256:$health_after_observation_sha256,
      snapshot_after_observation_sha256:$snapshot_after_observation_sha256,
      restart_getter_sha256:$restart_getter_sha256,
      health_after_restart_sha256:$health_after_restart_sha256,
      snapshot_after_restart_sha256:$snapshot_after_restart_sha256}' \
    >"$destination/complete.json.next"
  mv "$destination/complete.json.next" "$destination/complete.json"
}

readonly observation_suite="$script_dir/$(jq -er .observation_suite "$matrix")"
readonly restart_suite="$script_dir/$(jq -er .restart_getter_suite "$matrix")"
readonly replicates=$(jq -er .replicates "$matrix")

test -f "$observation_suite"
test -f "$restart_suite"
mkdir -p "$evidence_root/observations"

for run in $(seq 1 "$replicates"); do
  destination="$evidence_root/observations/run-$run"
  if [[ -f $destination/complete.json ]]; then
    echo "=== $profile_label lifecycle run $run: already complete ==="
    continue
  fi

  test ! -e "$destination"
  mkdir -p "$destination"
  echo "=== $profile_label lifecycle run $run: setter and immediate getter ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')

  "$script_dir/oracle_record.sh" "$observation_suite" "$fixture/manifest.json" \
    "$identity" "$destination/observation.json" record \
    2>&1 | tee "$destination/observation.log"
  capture_health "$profile_label-run-$run-after-observation" "$started_at" \
    "$destination/health-after-observation.json"
  capture_snapshot "$destination/snapshot-after-observation.json"

  echo "=== $profile_label lifecycle run $run: same-database process restart ==="
  "$guestctl" powershell \
    'Get-Process rekordbox -ErrorAction SilentlyContinue | Stop-Process -Force; $deadline = (Get-Date).AddSeconds(30); while (@(Get-Process rekordbox -ErrorAction SilentlyContinue).Count -gt 0 -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 250 }; if (@(Get-Process rekordbox -ErrorAction SilentlyContinue).Count -gt 0) { throw "rekordbox did not stop before same-database restart" }'
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" "$restart_suite" "$fixture/manifest.json" \
    "$identity" "$destination/restart-getter.json" record \
    2>&1 | tee "$destination/restart-getter.log"
  capture_health "$profile_label-run-$run-after-restart" "$started_at" \
    "$destination/health-after-restart.json"
  capture_snapshot "$destination/snapshot-after-restart.json"
  write_receipt "$run" "$destination" "$started_at"
done

echo "=== Extended Hot Cue $profile_label lifecycle matrix: complete ==="
