#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly root=$(cd -- "$lab/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-mutation-duplicate-slot"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly matrix="$script_dir/data/hot-cue-setter-seek-matrix.json"
readonly evidence_root="$lab/data/experiments/hot-cue-bank/extended-setter-seek"
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

complete_run_valid() {
  local destination=$1
  local variant=$2
  local run=$3
  local suite=$4
  local receipt="$destination/complete.json"
  local expected
  local actual
  local binding
  local field
  local path

  [[ -s $destination/setter.json ]] || return 1
  [[ -s $destination/health.json ]] || return 1
  [[ -s $destination/database-snapshot.json ]] || return 1
  [[ -s $receipt ]] || return 1
  [[ $(jq -er .variant "$receipt") == "$variant" ]] || return 1
  [[ $(jq -er .run "$receipt") == "$run" ]] || return 1

  for binding in \
    "suite_sha256:$suite" \
    "setter_sha256:$destination/setter.json" \
    "health_sha256:$destination/health.json" \
    "database_snapshot_sha256:$destination/database-snapshot.json"; do
    field=${binding%%:*}
    path=${binding#*:}
    expected=$(jq -er --arg field "$field" '.[$field]' "$receipt") || return 1
    [[ $expected =~ ^[0-9a-f]{64}$ ]] || return 1
    actual=$(sha256sum "$path" | cut -d' ' -f1) || return 1
    [[ $expected == "$actual" ]] || return 1
  done
}

run_once() (
  set -euo pipefail

  local variant=$1
  local run=$2
  local suite=$3
  local destination="$evidence_root/$variant/run-$run"
  local interrupted
  local suffix=interrupted
  local started_at
  local suite_sha256
  local setter_sha256
  local health_sha256
  local database_snapshot_sha256

  if [[ -f $destination/complete.json ]] && complete_run_valid "$destination" "$variant" "$run" "$suite"; then
    echo "=== $variant run $run: already complete ==="
    return 0
  fi

  if [[ -e $destination ]]; then
    if [[ -f $destination/complete.json ]]; then
      suffix=invalid-receipt
    fi
    interrupted="${destination}.${suffix}-$(date -u +%Y%m%dT%H%M%SZ)"
    echo "=== $variant run $run: preserving incomplete attempt as $interrupted ==="
    mv "$destination" "$interrupted"
  fi

  mkdir -p "$destination"
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')

  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$destination/setter.json" record \
    2>&1 | tee "$destination/setter.log"
  capture_health "$variant-run-$run-after-setter" "$started_at" \
    "$destination/health.json"
  capture_snapshot "$destination/database-snapshot.json"

  [[ -n $started_at ]]
  [[ -s $destination/setter.json ]]
  [[ -s $destination/health.json ]]
  [[ -s $destination/database-snapshot.json ]]
  suite_sha256=$(sha256sum "$suite" | cut -d' ' -f1)
  setter_sha256=$(sha256sum "$destination/setter.json" | cut -d' ' -f1)
  health_sha256=$(sha256sum "$destination/health.json" | cut -d' ' -f1)
  database_snapshot_sha256=$(sha256sum "$destination/database-snapshot.json" | cut -d' ' -f1)

  jq -n \
    --arg variant "$variant" \
    --argjson run "$run" \
    --arg started_at "$started_at" \
    --arg suite_sha256 "$suite_sha256" \
    --arg setter_sha256 "$setter_sha256" \
    --arg health_sha256 "$health_sha256" \
    --arg database_snapshot_sha256 "$database_snapshot_sha256" \
    '{format:1, variant:$variant, run:$run, started_at:$started_at,
      suite_sha256:$suite_sha256, setter_sha256:$setter_sha256,
      health_sha256:$health_sha256,
      database_snapshot_sha256:$database_snapshot_sha256}' \
    >"$destination/complete.json.next"
  mv "$destination/complete.json.next" "$destination/complete.json"
)

run_with_retries() {
  local variant=$1
  local run=$2
  local suite=$3
  local attempt

  for attempt in 1 2 3; do
    echo "=== $variant run $run attempt $attempt ==="
    run_once "$variant" "$run" "$suite" &
    local attempt_pid=$!
    if wait "$attempt_pid"; then
      return
    fi

    echo "=== $variant run $run attempt $attempt failed; restarting the full cold cycle ===" >&2
    sleep 3
  done

  echo "failed $variant run $run after three cold-cycle attempts" >&2
  return 1
}

mapfile -t variants < <(jq -r '.variants[].id' "$matrix")
if [[ $# -gt 0 ]]; then
  variants=("$@")
fi

mkdir -p "$evidence_root"
for variant in "${variants[@]}"; do
  suite="$script_dir/suites/generated/hot-cue-setter-seek/hot-cue-setter-seek-$variant.json"
  test -f "$suite"
  run_with_retries "$variant" 1 "$suite"
  run_with_retries "$variant" 2 "$suite"
done

echo "=== Extended Hot Cue seek-descriptor matrix: complete ==="
