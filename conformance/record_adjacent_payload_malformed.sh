#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly matrix="$script_dir/data/adjacent-payload-malformed-matrix.json"
readonly evidence_root="$lab/data/experiments/adjacent-payload/malformed/repeats"
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
  local suite=$2
  local candidate=$3
  local evidence=$4
  local phase=$5
  local started_at

  echo "=== $id: $phase fixture reset and cold process ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "$id-$phase-before" "$started_at" "$evidence/$phase-health-before.json"
  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$candidate" "$phase"
  capture_health "$id-$phase-after" "$started_at" "$evidence/$phase-health-after.json"
}

archive_failed_phase() {
  local id=$1
  local candidate=$2
  local evidence=$3
  local phase=$4
  local attempt=$5
  local archive="$evidence/$phase.interrupted-$(date -u +%Y%m%dT%H%M%SZ)-attempt-$attempt"
  local path

  mkdir -p "$archive"
  for path in "$evidence/$phase-health-before.json" "$evidence/$phase-health-after.json"; do
    if [[ -f $path ]]; then
      mv "$path" "$archive/$(basename -- "$path")"
    fi
  done
  if [[ $phase == record && -f $candidate ]]; then
    mv "$candidate" "$archive/candidate.json"
  fi
  echo "=== $id: quarantined failed $phase attempt $attempt at $archive ==="
}

run_phase_with_retry() {
  local id=$1
  local suite=$2
  local candidate=$3
  local evidence=$4
  local phase=$5
  local attempt pid status

  for attempt in 1 2 3; do
    (set -euo pipefail; run_phase "$id" "$suite" "$candidate" "$evidence" "$phase") &
    pid=$!
    if wait "$pid"; then
      return
    else
      status=$?
    fi
    archive_failed_phase "$id" "$candidate" "$evidence" "$phase" "$attempt"
  done
  return "$status"
}

write_receipt() {
  local id=$1
  local suite=$2
  local golden=$3
  local evidence=$4

  jq -n \
    --arg id "$id" \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --arg record_health_before_sha256 "$(sha256sum "$evidence/record-health-before.json" | cut -d' ' -f1)" \
    --arg record_health_after_sha256 "$(sha256sum "$evidence/record-health-after.json" | cut -d' ' -f1)" \
    --arg repeat_health_before_sha256 "$(sha256sum "$evidence/repeat-health-before.json" | cut -d' ' -f1)" \
    --arg repeat_health_after_sha256 "$(sha256sum "$evidence/repeat-health-after.json" | cut -d' ' -f1)" \
    '{format:1, scope:"real Rekordbox 7.2.19 malformed adjacent payload case",
      id:$id, completed_at:$completed_at,
      suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256,
      golden_sha256:$golden_sha256,
      record_health_before_sha256:$record_health_before_sha256,
      record_health_after_sha256:$record_health_after_sha256,
      repeat_health_before_sha256:$repeat_health_before_sha256,
      repeat_health_after_sha256:$repeat_health_after_sha256,
      case_count:1, exact_repeat:true}' \
    >"$evidence/receipt.json.next"
  mv "$evidence/receipt.json.next" "$evidence/receipt.json"
}

mapfile -t declarations < <(
  jq -r '.cases[] | [.id, .suite, .golden] | @tsv' "$matrix"
)

for declaration in "${declarations[@]}"; do
  IFS=$'\t' read -r id suite_relative golden_relative <<<"$declaration"
  suite="$script_dir/$suite_relative"
  golden="$script_dir/$golden_relative"
  candidate="$golden.next"
  evidence="$evidence_root/$id"

  test -f "$suite"
  mkdir -p "$(dirname -- "$golden")" "$evidence"
  if [[ -f $golden && -f $evidence/receipt.json ]]; then
    echo "=== $id: canonical golden and receipt exist; skipping ==="
    continue
  fi
  if [[ -f $golden || -f $evidence/receipt.json || -f $evidence/receipt.json.next ]]; then
    echo "$id has incomplete promoted evidence; inspect it before resuming" >&2
    exit 1
  fi

  if [[ -f $candidate && -f $evidence/record-health-before.json && -f $evidence/record-health-after.json ]]; then
    echo "=== $id: resuming complete record-side candidate ==="
  else
    if [[ -f $candidate || -f $evidence/record-health-before.json || -f $evidence/record-health-after.json ]]; then
      echo "$id has incomplete record-side evidence; inspect it before resuming" >&2
      exit 1
    fi
    run_phase_with_retry "$id" "$suite" "$candidate" "$evidence" record
  fi

  if [[ -f $evidence/repeat-health-before.json || -f $evidence/repeat-health-after.json ]]; then
    archive_failed_phase "$id" "$candidate" "$evidence" repeat 0
  fi
  run_phase_with_retry "$id" "$suite" "$candidate" "$evidence" repeat
  mv "$candidate" "$golden"
  write_receipt "$id" "$suite" "$golden" "$evidence"
  echo "=== $id: promoted ==="
done

echo "=== malformed adjacent payload matrix: complete ==="
