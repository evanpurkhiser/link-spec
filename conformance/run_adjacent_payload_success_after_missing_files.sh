#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_MISSING_PAYLOAD_UNIT:-codex-rekordbox-adjacent-missing-20261002v.service}
readonly predecessor_receipt="$lab/data/experiments/adjacent-payload/missing-files/finalization.json"
readonly evidence="$lab/data/experiments/adjacent-payload/success"
readonly capture_receipt="$evidence/receipt.json"
readonly summary="$evidence/summary.json"
readonly matrix="$evidence/matrix.csv"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-success.json"
readonly asset_manifest="$script_dir/payload-assets/generated/manifest.json"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly guest_artwork_dir='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/share/PIONEER/Artwork/000/deterministic'
readonly guest_analysis_dir='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/share/PIONEER/USBANLZ/000/deterministic'
predecessor_observed_active=false

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

  if active_state=$(systemctl --user show "$predecessor_unit" -p ActiveState --value 2>/dev/null); then
    result=$(systemctl --user show "$predecessor_unit" -p Result --value)
    exit_status=$(systemctl --user show "$predecessor_unit" -p ExecMainStatus --value)
    [[ $active_state == inactive ]]
    [[ $result == success ]]
    [[ $exit_status == 0 ]]
  fi

  jq -e '
    .format == 1 and
    .scope == "real Rekordbox 7.2.19 adjacent payload missing files" and
    .case_count == 31 and .service_count == 10 and
    .focused_tests_passed == true and
    .synthetic_identity_units_active == false and
    .isolated_vm_stopped == true
  ' "$predecessor_receipt" >/dev/null
}

capture_is_complete() {
  [[ -f $capture_receipt && -f $golden ]] || return 1

  jq -e \
    --arg suite_sha256 "$(sha256sum "$script_dir/suites/adjacent-payload-success.json" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$script_dir/fixtures/generated/payload-valid/manifest.json" | cut -d' ' -f1)" \
    --arg asset_manifest_sha256 "$(sha256sum "$asset_manifest" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$script_dir/runs/xdj-rx3-player-11.json" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" '
      .format == 1 and
      .scope == "real Rekordbox 7.2.19 generated adjacent payload success" and
      .variant == "baseline" and
      .suite_sha256 == $suite_sha256 and
      .fixture_manifest_sha256 == $fixture_manifest_sha256 and
      .asset_manifest_sha256 == $asset_manifest_sha256 and
      .identity_sha256 == $identity_sha256 and
      .golden_sha256 == $golden_sha256 and
      .case_count == 15 and .service_count == 10 and
      .exact_repeat == true
    ' "$capture_receipt" >/dev/null
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

write_receipt() {
  local expected_database

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg baseline_database_sha256 "$expected_database" \
    --arg predecessor_receipt_sha256 "$(sha256sum "$predecessor_receipt" | cut -d' ' -f1)" \
    --arg capture_receipt_sha256 "$(sha256sum "$capture_receipt" | cut -d' ' -f1)" \
    --arg asset_manifest_sha256 "$(sha256sum "$asset_manifest" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg matrix_sha256 "$(sha256sum "$matrix" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    '{format:1, scope:"real Rekordbox 7.2.19 generated adjacent payload success",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      capture_receipt_sha256:$capture_receipt_sha256,
      asset_manifest_sha256:$asset_manifest_sha256,
      summary_sha256:$summary_sha256,
      matrix_sha256:$matrix_sha256,
      golden_sha256:$golden_sha256,
      case_count:15, service_count:10,
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
"$guestctl" wait 300
"$vm/vmctl" isolation-check

if capture_is_complete; then
  echo "Resuming complete adjacent-payload success capture at reduction"
else
  "$script_dir/record_adjacent_payload_success.sh"
fi
"$lab/.venv/bin/python" "$lab/tools/summarize_adjacent_payload_success.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_payload_assets \
    test_adjacent_payload_services \
    test_link_export_request_vocabulary \
    test_menu_database_query_map \
    test_corpus_documentation \
    test_real_rekordbox_phase_boundary
)

require_clean_baseline
"$vm/vmctl" isolated-stop
write_receipt
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"

echo "=== adjacent payload generated-success oracle validated and isolated VM stopped ==="
