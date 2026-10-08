#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_MALFORMED_PAYLOAD_UNIT:-codex-rekordbox-adjacent-malformed-20261003u9.service}
readonly predecessor_receipt="$lab/data/experiments/adjacent-payload/malformed/finalization.json"
readonly evidence="$lab/data/experiments/sort-secondary-render-6"
readonly capture_receipt="$evidence/receipt.json"
readonly summary="$evidence/summary.json"
readonly matrix="$evidence/rows.csv"
readonly physical_requests="$evidence/physical-rx3-requests.json"
readonly physical_pcap="$evidence/source-rx3-rekordbox-working-ap-20260927.pcap"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/sort-secondary-render-6.json"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly conformance_test_runner="$script_dir/pinned/link-export-conformance-tests"
readonly standalone=${REKORDBOX_SORT_STANDALONE:-false}
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
      inactive|failed) return ;;
      *) echo "unexpected $predecessor_unit state: $state" >&2; exit 1 ;;
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
    .scope == "real Rekordbox 7.2.19 malformed adjacent payload matrix" and
    .case_count == 96 and .service_count == 16 and
    .focused_tests_passed == true and
    .synthetic_identity_units_active == false and
    .isolated_vm_stopped == true
  ' "$predecessor_receipt" >/dev/null
}

require_clean_baseline() {
  local expected_database active_database

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  active_database=$(jq -er .database_sha256 "$active_manifest")
  [[ $active_database == "$expected_database" ]]
  if systemctl --user list-units --state=active --plain --no-legend \
    'rekordbox-identity-*' | grep -q .; then
    echo "synthetic rekordbox identity unit remains active" >&2
    exit 1
  fi
}

write_receipt() {
  local expected_database predecessor_receipt_sha256

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  predecessor_receipt_sha256=''
  if [[ -f $predecessor_receipt ]]; then
    predecessor_receipt_sha256=$(sha256sum "$predecessor_receipt" | cut -d' ' -f1)
  fi
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg baseline_database_sha256 "$expected_database" \
    --arg predecessor_receipt_sha256 "$predecessor_receipt_sha256" \
    --argjson standalone "$standalone" \
    --arg capture_receipt_sha256 "$(sha256sum "$capture_receipt" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg matrix_sha256 "$(sha256sum "$matrix" | cut -d' ' -f1)" \
    --arg physical_requests_sha256 "$(sha256sum "$physical_requests" | cut -d' ' -f1)" \
    --arg physical_pcap_sha256 "$(sha256sum "$physical_pcap" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    '{format:1, scope:"real Rekordbox 7.2.19 RX3 sort and six-argument render cross",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256, standalone:$standalone,
      predecessor_receipt_sha256:(if $predecessor_receipt_sha256 == "" then null else $predecessor_receipt_sha256 end),
      capture_receipt_sha256:$capture_receipt_sha256,
      summary_sha256:$summary_sha256,
      matrix_sha256:$matrix_sha256,
      physical_requests_sha256:$physical_requests_sha256,
      physical_pcap_sha256:$physical_pcap_sha256,
      golden_sha256:$golden_sha256,
      case_count:11, row_count:88, record_repeat_execution_count:22,
      focused_tests_passed:true, rust_tests_passed:true,
      synthetic_identity_units_active:false,
      isolated_vm_stopped:true}' >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

if [[ $standalone != true ]]; then
  wait_for_predecessor
  require_successful_predecessor
fi

"$lab/tools/extract_dbserver_pcap.py" \
  "$physical_pcap" \
  --source 10.0.0.143 --destination 10.0.0.119 \
  --kind 0x1004 --kind 0x3000 --output "$physical_requests"

"$vm/vmctl" isolated-start
"$guestctl" wait 300
"$vm/vmctl" isolation-check

"$script_dir/record_sort_secondary_render_6.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_sort_secondary_render_6.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_sort_secondary_render_6 \
    test_corpus_documentation \
    test_real_rekordbox_phase_boundary
  "$conformance_test_runner"
)

require_clean_baseline
"$vm/vmctl" isolated-stop
write_receipt
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"

echo "=== RX3 sort/six-argument-render oracle validated and isolated VM stopped ==="
