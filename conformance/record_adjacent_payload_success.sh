#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture=${REKORDBOX_PAYLOAD_FIXTURE:-"$script_dir/fixtures/generated/payload-valid"}
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity=${REKORDBOX_PAYLOAD_IDENTITY:-"$script_dir/runs/xdj-rx3-player-11.json"}
readonly suite=${REKORDBOX_PAYLOAD_SUITE:-"$script_dir/suites/adjacent-payload-success.json"}
readonly golden=${REKORDBOX_PAYLOAD_GOLDEN:-"$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-success.json"}
readonly candidate="$golden.next"
readonly assets=${REKORDBOX_PAYLOAD_ASSETS:-"$script_dir/payload-assets/generated"}
readonly asset_manifest=${REKORDBOX_PAYLOAD_ASSET_MANIFEST:-"$assets/manifest.json"}
readonly evidence=${REKORDBOX_PAYLOAD_EVIDENCE:-"$lab/data/experiments/adjacent-payload/success"}
readonly variant=${REKORDBOX_PAYLOAD_VARIANT:-baseline}
readonly receipt_scope=${REKORDBOX_PAYLOAD_SCOPE:-"real Rekordbox 7.2.19 generated adjacent payload success"}
readonly case_count=${REKORDBOX_PAYLOAD_CASE_COUNT:-15}
readonly service_count=${REKORDBOX_PAYLOAD_SERVICE_COUNT:-10}
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly guest_share='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/share'
readonly guest_artwork_dir="$guest_share/PIONEER/Artwork/000/deterministic"
readonly guest_analysis_dir="$guest_share/PIONEER/USBANLZ/000/deterministic"
staged_by_this_run=false

remove_assets() {
  "$guestctl" powershell \
    "Remove-Item -LiteralPath '$guest_artwork_dir','$guest_analysis_dir' -Recurse -Force -ErrorAction SilentlyContinue; if ((Test-Path -LiteralPath '$guest_artwork_dir') -or (Test-Path -LiteralPath '$guest_analysis_dir')) { throw 'deterministic payload directories remain after cleanup' }; Write-Output 'Deterministic payload assets removed.'"
}

restore() {
  local status=$?
  local cleanup_status=0

  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline" || cleanup_status=$?
  if [[ $staged_by_this_run == true ]]; then
    remove_assets || cleanup_status=$?
  fi
  if (( status != 0 )); then
    exit "$status"
  fi

  exit "$cleanup_status"
}
trap restore EXIT

capture_guest_assets() {
  local output=$1

  "$guestctl" powershell \
    "\$items = @(
      [pscustomobject]@{ path = 'PIONEER/Artwork/000/deterministic/artwork.jpg'; file = '$guest_artwork_dir/artwork.jpg' },
      [pscustomobject]@{ path = 'PIONEER/USBANLZ/000/deterministic/ANLZ0000.2EX'; file = '$guest_analysis_dir/ANLZ0000.2EX' },
      [pscustomobject]@{ path = 'PIONEER/USBANLZ/000/deterministic/ANLZ0000.DAT'; file = '$guest_analysis_dir/ANLZ0000.DAT' },
      [pscustomobject]@{ path = 'PIONEER/USBANLZ/000/deterministic/ANLZ0000.EXT'; file = '$guest_analysis_dir/ANLZ0000.EXT' }
    ); @(
      \$items | ForEach-Object {
        \$entry = Get-Item -LiteralPath \$_.file;
        [pscustomobject]@{ path = \$_.path; size = \$entry.Length; sha256 = (Get-FileHash -LiteralPath \$_.file -Algorithm SHA256).Hash.ToLowerInvariant() }
      }
    ) | ConvertTo-Json -Depth 3" | tr -d '\r' >"$output.next"

  jq -e 'length == 4' "$output.next" >/dev/null
  diff -u \
    <(jq -S '.assets | sort_by(.path)' "$asset_manifest") \
    <(jq -S 'sort_by(.path)' "$output.next")
  mv "$output.next" "$output"
}

stage_assets() {
  "$guestctl" powershell \
    "if ((Test-Path -LiteralPath '$guest_artwork_dir') -or (Test-Path -LiteralPath '$guest_analysis_dir')) { throw 'deterministic payload target already exists' }; New-Item -ItemType Directory -Path '$guest_artwork_dir','$guest_analysis_dir' -Force | Out-Null; Write-Output 'Deterministic payload directories created.'"
  staged_by_this_run=true

  "$guestctl" copy-to \
    "$assets/PIONEER/Artwork/000/deterministic/artwork.jpg" \
    "$guest_artwork_dir/artwork.jpg"
  for extension in 2EX DAT EXT; do
    "$guestctl" copy-to \
      "$assets/PIONEER/USBANLZ/000/deterministic/ANLZ0000.$extension" \
      "$guest_analysis_dir/ANLZ0000.$extension"
  done

  capture_guest_assets "$evidence/staged-assets.json"
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

run_phase() {
  local phase=$1
  local started_at

  echo "=== adjacent payload generated success $variant: $phase reset and restart ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  capture_guest_assets "$evidence/$phase-assets.json"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "adjacent-payload-success-$variant-$phase-before" "$started_at" \
    "$evidence/$phase-health-before.json"

  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$candidate" "$phase"

  capture_health "adjacent-payload-success-$variant-$phase-after" "$started_at" \
    "$evidence/$phase-health-after.json"
}

write_receipt() {
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg scope "$receipt_scope" \
    --arg variant "$variant" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg asset_manifest_sha256 "$(sha256sum "$asset_manifest" | cut -d' ' -f1)" \
    --arg staged_assets_sha256 "$(sha256sum "$evidence/staged-assets.json" | cut -d' ' -f1)" \
    --arg record_assets_sha256 "$(sha256sum "$evidence/record-assets.json" | cut -d' ' -f1)" \
    --arg repeat_assets_sha256 "$(sha256sum "$evidence/repeat-assets.json" | cut -d' ' -f1)" \
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
      asset_manifest_sha256:$asset_manifest_sha256,
      staged_assets_sha256:$staged_assets_sha256,
      record_assets_sha256:$record_assets_sha256,
      repeat_assets_sha256:$repeat_assets_sha256,
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
test -f "$asset_manifest"
mkdir -p "$evidence"

if [[ -f $golden && -f $evidence/receipt.json ]]; then
  echo "=== adjacent payload generated success $variant: canonical golden and receipt exist; skipping ==="
  exit 0
fi

test ! -e "$golden"
test ! -e "$candidate"
test ! -e "$evidence/receipt.json.next"

stage_assets
run_phase record
run_phase repeat

mv "$candidate" "$golden"
write_receipt
echo "=== adjacent payload generated success $variant: promoted ==="
