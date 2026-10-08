#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_MALFORMED_HISTORY_UNIT:-codex-rekordbox-song-info-malformed-history-lifecycle-20261004z27.service}
readonly predecessor_receipt="$lab/data/experiments/song-info-status-location2/malformed-history-lifecycle/finalization.json"
readonly evidence="$lab/data/experiments/adjacent-payload/success-status"
readonly summary="$evidence/summary.json"
readonly matrix="$evidence/matrix.csv"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly asset_manifest="$script_dir/payload-assets/generated/manifest.json"
readonly guest_artwork_dir='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/share/PIONEER/Artwork/000/deterministic'
readonly guest_analysis_dir='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/share/PIONEER/USBANLZ/000/deterministic'
readonly variants=(
  cdj-3000-player-1-extended
  cdj-3000-player-1-legacy
  xdj-rx3-player-11-extended
  xdj-rx3-player-11-legacy
)
predecessor_observed_active=false
completed=false
vm_started=false

cleanup() {
  local status=$?
  trap - EXIT
  if [[ $completed != true && $vm_started == true ]]; then
    set +e
    "$script_dir/activate_fixture.sh" "$script_dir/fixtures/generated/play-paths"
    "$vm/vmctl" isolated-stop
  fi
  exit "$status"
}
trap cleanup EXIT

wait_for_predecessor() {
  local state

  while true; do
    if ! state=$(systemctl --user show "$predecessor_unit" -p ActiveState --value 2>/dev/null); then
      if [[ $predecessor_observed_active == true && -f $predecessor_receipt ]]; then
        return
      fi

      echo "$predecessor_unit disappeared without a finalization receipt" >&2
      exit 1
    fi

    case "$state" in
      active|activating|reloading|deactivating)
        predecessor_observed_active=true
        sleep 30
        ;;
      inactive|failed)
        return
        ;;
      *)
        echo "unexpected $predecessor_unit state: $state" >&2
        exit 1
        ;;
    esac
  done
}

require_successful_predecessor() {
  local active_state result exit_status

  [[ $predecessor_observed_active == true ]]
  if active_state=$(systemctl --user show "$predecessor_unit" -p ActiveState --value 2>/dev/null); then
    result=$(systemctl --user show "$predecessor_unit" -p Result --value)
    exit_status=$(systemctl --user show "$predecessor_unit" -p ExecMainStatus --value)
    [[ $active_state == inactive ]]
    [[ $result == success ]]
    [[ $exit_status == 0 ]]
  fi

  jq -e '
    .format == 1 and
    .scope == "real Rekordbox 7.2.19 RX3 location-2 malformed-history lifecycle" and
    .ordered_pairs == 256 and .independently_repeated_pairs == 256 and
    .focused_tests_passed == true and
    .synthetic_identity_units_active == false and
    .isolated_vm_stopped == true
  ' "$predecessor_receipt" >/dev/null
}

require_clean_baseline() {
  local expected_database active_database guest_state

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  active_database=$(jq -er .database_sha256 "$active_manifest")
  [[ $active_database == "$expected_database" ]]

  guest_state=$("$guestctl" powershell \
    "[pscustomobject]@{ artwork = [bool](Test-Path -LiteralPath '$guest_artwork_dir'); analysis = [bool](Test-Path -LiteralPath '$guest_analysis_dir') } | ConvertTo-Json -Compress" | tr -d '\r')
  [[ $(jq -r '.artwork or .analysis' <<<"$guest_state") == false ]]

  if systemctl --user list-units --state=active --plain --no-legend \
    'rekordbox-identity-*' | grep -q .; then
    echo "synthetic rekordbox identity unit remains active" >&2
    exit 1
  fi
}

variant_receipts() {
  local variant

  for variant in "${variants[@]}"; do
    jq -n \
      --arg variant "$variant" \
      --arg sha256 "$(sha256sum "$evidence/$variant/receipt.json" | cut -d' ' -f1)" \
      '{variant:$variant,sha256:$sha256}'
  done | jq -s .
}

write_receipt() {
  local expected_database receipts

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  receipts=$(variant_receipts)
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg baseline_database_sha256 "$expected_database" \
    --arg predecessor_receipt_sha256 "$(sha256sum "$predecessor_receipt" | cut -d' ' -f1)" \
    --arg asset_manifest_sha256 "$(sha256sum "$asset_manifest" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg matrix_sha256 "$(sha256sum "$matrix" | cut -d' ' -f1)" \
    --argjson variant_receipts "$receipts" \
    '{format:1, scope:"real Rekordbox 7.2.19 adjacent payload status/setup success cross",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      asset_manifest_sha256:$asset_manifest_sha256,
      summary_sha256:$summary_sha256,
      matrix_sha256:$matrix_sha256,
      variant_receipts:$variant_receipts,
      variant_count:4, case_count:60,
      focused_tests_passed:true,
      synthetic_identity_units_active:false,
      deterministic_guest_assets_removed:true,
      isolated_vm_stopped:true}' \
    >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

wait_for_predecessor
require_successful_predecessor

"$vm/vmctl" isolated-start
vm_started=true
"$guestctl" wait 300
"$vm/vmctl" isolation-check

"$script_dir/record_adjacent_payload_success_status_cross.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_adjacent_payload_success_status.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_payload_assets \
    test_adjacent_payload_services \
    test_device_status_source_inventory \
    test_public_status_source_audit \
    test_corpus_documentation \
    test_real_rekordbox_phase_boundary
)

require_clean_baseline
"$vm/vmctl" isolated-stop
vm_started=false
write_receipt
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"
completed=true

echo "=== adjacent payload status/setup success cross validated and isolated VM stopped ==="
