#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture=${REKORDBOX_FILELESS_FIXTURE:-"$script_dir/fixtures/generated/full"}
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity=${REKORDBOX_FILELESS_IDENTITY:-"$script_dir/runs/xdj-rx3-player-11.json"}
readonly suite=${REKORDBOX_FILELESS_SUITE:-"$script_dir/suites/adjacent-payload-fileless.json"}
readonly golden=${REKORDBOX_FILELESS_GOLDEN:-"$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-fileless.json"}
readonly candidate="$golden.next"
readonly evidence=${REKORDBOX_FILELESS_EVIDENCE:-"$lab/data/experiments/adjacent-payload/fileless"}
readonly variant=${REKORDBOX_FILELESS_VARIANT:-fileless}
readonly receipt_scope=${REKORDBOX_FILELESS_SCOPE:-"real Rekordbox 7.2.19 fileless adjacent payload services"}
readonly case_count=${REKORDBOX_FILELESS_CASE_COUNT:-196}
readonly service_count=${REKORDBOX_FILELESS_SERVICE_COUNT:-16}
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

  echo "failed to capture guest health after five attempts" >&2
  return 1
}

run_phase() {
  local phase=$1
  local started_at

  echo "=== adjacent payload $variant: $phase reset and restart ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "adjacent-payload-$variant-$phase-before" "$started_at" \
    "$evidence/$phase-health-before.json"

  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$candidate" "$phase"

  capture_health "adjacent-payload-$variant-$phase-after" "$started_at" \
    "$evidence/$phase-health-after.json"
}

write_receipt() {
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg scope "$receipt_scope" \
    --arg variant "$variant" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --arg record_health_before_sha256 "$(sha256sum "$evidence/record-health-before.json" | cut -d' ' -f1)" \
    --arg record_health_after_sha256 "$(sha256sum "$evidence/record-health-after.json" | cut -d' ' -f1)" \
    --arg repeat_health_before_sha256 "$(sha256sum "$evidence/repeat-health-before.json" | cut -d' ' -f1)" \
    --arg repeat_health_after_sha256 "$(sha256sum "$evidence/repeat-health-after.json" | cut -d' ' -f1)" \
    --argjson case_count "$case_count" \
    --argjson service_count "$service_count" \
    '{format:1, scope:$scope, variant:$variant,
      completed_at:$completed_at,
      suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256,
      golden_sha256:$golden_sha256,
      record_health_before_sha256:$record_health_before_sha256,
      record_health_after_sha256:$record_health_after_sha256,
      repeat_health_before_sha256:$repeat_health_before_sha256,
      repeat_health_after_sha256:$repeat_health_after_sha256,
      case_count:$case_count, service_count:$service_count, exact_repeat:true}' \
    >"$evidence/receipt.json.next"
  mv "$evidence/receipt.json.next" "$evidence/receipt.json"
}

test -f "$fixture/manifest.json"
test -f "$identity"
test -f "$suite"
mkdir -p "$evidence"

if [[ -f $golden && -f $evidence/receipt.json ]]; then
  echo "=== adjacent payload $variant: canonical golden and receipt exist; skipping ==="
  exit 0
fi

test ! -e "$golden"
test ! -e "$candidate"
test ! -e "$evidence/receipt.json.next"

run_phase record
run_phase repeat

mv "$candidate" "$golden"
write_receipt
echo "=== adjacent payload $variant: promoted ==="
