#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/compatibility-exhaustive"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly golden_root="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"
readonly evidence_root="$lab/data/experiments/track-compatibility-exhaustive/setups"
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
  local setup=$1
  local phase=$2
  local suite=$3
  local target=$4
  local evidence=$5
  local started_at

  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "track-compatibility-exhaustive-$setup-$phase-before" "$started_at" \
    "$evidence/$phase-health-before.json"
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$target" "$phase"
  capture_health "track-compatibility-exhaustive-$setup-$phase-after" "$started_at" \
    "$evidence/$phase-health-after.json"
}

for setup in extended legacy; do
  suite="$script_dir/suites/generated/track-compatibility-exhaustive/track-compatibility-exhaustive-$setup.json"
  golden="$golden_root/track-compatibility-exhaustive-$setup.json"
  candidate="$golden.next"
  evidence="$evidence_root/$setup"
  receipt="$evidence/receipt.json"
  mkdir -p "$evidence"

  if [[ -f $golden && -f $receipt ]]; then
    [[ $(jq -er .golden_sha256 "$receipt") == $(sha256sum "$golden" | cut -d' ' -f1) ]]
    echo "=== compatibility exhaustive $setup: canonical golden and receipt exist; skipping ==="
    continue
  fi

  if [[ -f $golden || -f $receipt || -f $receipt.next ]]; then
    echo "compatibility exhaustive $setup has incomplete promoted evidence; inspect it before resuming" >&2
    exit 1
  fi

  if [[ -f $candidate && -f $evidence/record-health-before.json && -f $evidence/record-health-after.json ]]; then
    echo "=== compatibility exhaustive $setup: resuming complete record-side candidate ==="
  else
    if [[ -f $candidate || -f $evidence/record-health-before.json || -f $evidence/record-health-after.json ]]; then
      echo "compatibility exhaustive $setup has incomplete record-side evidence; inspect it before resuming" >&2
      exit 1
    fi
    echo "=== compatibility exhaustive $setup: independent record ==="
    run_phase "$setup" record "$suite" "$candidate" "$evidence"
  fi

  echo "=== compatibility exhaustive $setup: fixture-reset repeat ==="
  run_phase "$setup" repeat "$suite" "$candidate" "$evidence"
  mv "$candidate" "$golden"
  jq -n \
    --arg setup "$setup" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --arg record_health_before_sha256 "$(sha256sum "$evidence/record-health-before.json" | cut -d' ' -f1)" \
    --arg record_health_after_sha256 "$(sha256sum "$evidence/record-health-after.json" | cut -d' ' -f1)" \
    --arg repeat_health_before_sha256 "$(sha256sum "$evidence/repeat-health-before.json" | cut -d' ' -f1)" \
    --arg repeat_health_after_sha256 "$(sha256sum "$evidence/repeat-health-after.json" | cut -d' ' -f1)" \
    '{format:1, scope:"real Rekordbox 7.2.19 exhaustive track compatibility",
      setup:$setup, suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256, golden_sha256:$golden_sha256,
      record_health_before_sha256:$record_health_before_sha256,
      record_health_after_sha256:$record_health_after_sha256,
      repeat_health_before_sha256:$repeat_health_before_sha256,
      repeat_health_after_sha256:$repeat_health_after_sha256,
      independently_repeated:true}' \
    >"$receipt.next"
  mv "$receipt.next" "$receipt"
  echo "=== compatibility exhaustive $setup: promoted ==="
done

echo "=== exhaustive track compatibility matrix: complete ==="
