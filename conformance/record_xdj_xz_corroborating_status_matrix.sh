#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly matrix="$script_dir/data/xdj-xz-corroborating-status-matrix.json"
readonly identity="$script_dir/runs/xdj-xz-player-1-corroborating-status.json"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly evidence="$lab/data/experiments/device-status/xdj-xz-corroborating/repeats"
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
  local id=$1
  local phase=$2
  local fixture=$3
  local suite=$4
  local target=$5
  local evidence_dir=$6
  local started_at

  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "xdj-xz-$id-$phase-before" "$started_at" \
    "$evidence_dir/$phase-health-before.json"
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$target" "$phase"
  capture_health "xdj-xz-$id-$phase-after" "$started_at" \
    "$evidence_dir/$phase-health-after.json"
}

write_receipt() {
  local id=$1
  local fixture=$2
  local suite=$3
  local golden=$4
  local evidence_dir=$5
  local receipt="$evidence_dir/receipt.json"

  jq -n \
    --arg id "$id" \
    --arg verified_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --arg record_health_before_sha256 "$(sha256sum "$evidence_dir/record-health-before.json" | cut -d' ' -f1)" \
    --arg record_health_after_sha256 "$(sha256sum "$evidence_dir/record-health-after.json" | cut -d' ' -f1)" \
    --arg repeat_health_before_sha256 "$(sha256sum "$evidence_dir/repeat-health-before.json" | cut -d' ' -f1)" \
    --arg repeat_health_after_sha256 "$(sha256sum "$evidence_dir/repeat-health-after.json" | cut -d' ' -f1)" \
    '{format:1, scope:"real Rekordbox 7.2.19 corroborating XDJ-XZ status case",
      id:$id, status_provenance:"corroborating-fixture",
      repeat_verified:true, verified_at:$verified_at,
      suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256,
      golden_sha256:$golden_sha256,
      record_health_before_sha256:$record_health_before_sha256,
      record_health_after_sha256:$record_health_after_sha256,
      repeat_health_before_sha256:$repeat_health_before_sha256,
      repeat_health_after_sha256:$repeat_health_after_sha256}' >"$receipt.next"
  mv "$receipt.next" "$receipt"
}

mapfile -t declarations < <(
  jq -r '.variants[] | [.id, .fixture, .suite, .golden] | @tsv' "$matrix"
)
mkdir -p "$evidence"
for declaration in "${declarations[@]}"; do
  IFS=$'\t' read -r id fixture_name suite_name golden_name <<<"$declaration"
  fixture="$script_dir/fixtures/generated/$fixture_name"
  suite="$script_dir/$suite_name"
  golden="$script_dir/$golden_name"
  candidate="$golden.next"
  evidence_dir="$evidence/$id"
  receipt="$evidence_dir/receipt.json"

  test -f "$fixture/manifest.json"
  test -f "$suite"
  mkdir -p "$(dirname -- "$golden")" "$evidence_dir"

  if [[ -f $golden && -f $receipt ]]; then
    expected=$(jq -er .golden_sha256 "$receipt")
    actual=$(sha256sum "$golden" | cut -d' ' -f1)
    [[ $actual == "$expected" ]]
    echo "=== $id: canonical golden and receipt exist; skipping ==="
    continue
  fi
  if [[ -f $golden || -f $receipt || -f $receipt.next ]]; then
    echo "$id has incomplete promoted evidence; inspect it before resuming" >&2
    exit 1
  fi

  if [[ -f $candidate && -f $evidence_dir/record-health-before.json && -f $evidence_dir/record-health-after.json ]]; then
    echo "=== $id: resuming complete record-side candidate ==="
  else
    if [[ -f $candidate || -f $evidence_dir/record-health-before.json || -f $evidence_dir/record-health-after.json ]]; then
      echo "$id has incomplete record-side evidence; inspect it before resuming" >&2
      exit 1
    fi
    echo "=== $id: independent record ==="
    run_phase "$id" record "$fixture" "$suite" "$candidate" "$evidence_dir"
  fi

  if [[ -f $evidence_dir/repeat-health-before.json || -f $evidence_dir/repeat-health-after.json ]]; then
    echo "$id has incomplete repeat-side evidence; inspect it before resuming" >&2
    exit 1
  fi
  echo "=== $id: fixture-reset cold-process repeat ==="
  run_phase "$id" repeat "$fixture" "$suite" "$candidate" "$evidence_dir"
  mv "$candidate" "$golden"
  write_receipt "$id" "$fixture" "$suite" "$golden" "$evidence_dir"
  echo "=== $id: promoted ==="
done

echo "=== corroborating XDJ-XZ status matrix: complete ==="
