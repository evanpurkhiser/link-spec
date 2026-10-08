#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly matrix="$script_dir/data/song-info-location2-malformed-history-matrix.json"
readonly suite_root="$script_dir/suites/generated/song-info-location2-malformed-history"
readonly golden_root="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3-status/song-info-location2-malformed-history-lifecycle"
readonly receipt_root="$lab/data/experiments/song-info-status-location2/malformed-history-lifecycle/repeats"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'

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
  return 1
}

run_phase() {
  local pair=$1
  local phase=$2
  local suite=$3
  local target=$4
  local evidence=$5
  local started_at

  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "location2-malformed-history-$pair-$phase-before" "$started_at" \
    "$evidence/$phase-health-before.json"
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$target" "$phase"
  capture_health "location2-malformed-history-$pair-$phase-after" "$started_at" \
    "$evidence/$phase-health-after.json"
}

mkdir -p "$golden_root" "$receipt_root"
mapfile -t pairs < <(jq -r '.pairs[].id' "$matrix")
if [[ $# -gt 0 ]]; then
  pairs=("$@")
fi

for pair in "${pairs[@]}"; do
  suite="$suite_root/$pair.json"
  golden="$golden_root/$pair.json"
  candidate="$golden.next"
  evidence="$receipt_root/$pair"
  receipt="$evidence/receipt.json"

  test -f "$suite"
  mkdir -p "$evidence"
  if [[ -f $golden && -f $receipt ]]; then
    expected=$(jq -er .golden_sha256 "$receipt")
    actual=$(sha256sum "$golden" | cut -d' ' -f1)
    [[ $actual == "$expected" ]]
    echo "=== malformed history $pair: canonical repeat receipt exists; skipping ==="
    continue
  fi

  if [[ -f $golden || -f $receipt || -f $receipt.next ]]; then
    echo "malformed history $pair has incomplete promoted evidence; inspect it before resuming" >&2
    exit 1
  fi

  if [[ -f $candidate && -f $evidence/record-health-before.json && -f $evidence/record-health-after.json ]]; then
    echo "=== malformed history $pair: resuming complete record-side candidate ==="
  else
    if [[ -f $candidate || -f $evidence/record-health-before.json || -f $evidence/record-health-after.json ]]; then
      echo "malformed history $pair has incomplete record-side evidence; inspect it before resuming" >&2
      exit 1
    fi
    echo "=== malformed history $pair: independent record ==="
    run_phase "$pair" record "$suite" "$candidate" "$evidence"
  fi

  echo "=== malformed history $pair: fixture-reset cold-process repeat ==="
  run_phase "$pair" repeat "$suite" "$candidate" "$evidence"
  mv "$candidate" "$golden"

  jq -n \
    --arg pair "$pair" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --arg record_health_before_sha256 "$(sha256sum "$evidence/record-health-before.json" | cut -d' ' -f1)" \
    --arg record_health_after_sha256 "$(sha256sum "$evidence/record-health-after.json" | cut -d' ' -f1)" \
    --arg repeat_health_before_sha256 "$(sha256sum "$evidence/repeat-health-before.json" | cut -d' ' -f1)" \
    --arg repeat_health_after_sha256 "$(sha256sum "$evidence/repeat-health-after.json" | cut -d' ' -f1)" \
    '{format:1, pair:$pair, suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256, golden_sha256:$golden_sha256,
      record_health_before_sha256:$record_health_before_sha256,
      record_health_after_sha256:$record_health_after_sha256,
      repeat_health_before_sha256:$repeat_health_before_sha256,
      repeat_health_after_sha256:$repeat_health_after_sha256,
      independently_repeated:true}' \
    >"$receipt.next"
  mv "$receipt.next" "$receipt"
  echo "=== malformed history $pair: promoted ==="
done

echo "=== location-2 malformed-history ordered-pair matrix: complete ==="
