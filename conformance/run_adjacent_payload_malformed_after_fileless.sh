#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_PAYLOAD_UNIT:-codex-rekordbox-adjacent-payload-20261002t.service}
readonly predecessor_receipt="$lab/data/experiments/adjacent-payload/fileless/finalization.json"
readonly evidence="$lab/data/experiments/adjacent-payload/malformed"
readonly summary="$evidence/summary.json"
readonly matrix="$evidence/matrix.csv"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
predecessor_observed_active=false

wait_for_predecessor() {
  local state
  while true; do
    if ! state=$(systemctl --user show "$predecessor_unit" -p ActiveState --value 2>/dev/null); then
      if [[ -f $predecessor_receipt ]]; then
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
    [[ $predecessor_observed_active == true || -f $predecessor_receipt ]]
    result=$(systemctl --user show "$predecessor_unit" -p Result --value)
    exit_status=$(systemctl --user show "$predecessor_unit" -p ExecMainStatus --value)
    [[ $active_state == inactive ]]
    [[ $result == success ]]
    [[ $exit_status == 0 ]]
  else
    [[ -f $predecessor_receipt ]]
  fi
  jq -e '
    .format == 1 and
    .scope == "real Rekordbox 7.2.19 fileless adjacent payload services" and
    .case_count == 196 and .service_count == 16 and
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
  local expected_database
  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg baseline_database_sha256 "$expected_database" \
    --arg predecessor_receipt_sha256 "$(sha256sum "$predecessor_receipt" | cut -d' ' -f1)" \
    --arg declaration_sha256 "$(sha256sum "$script_dir/data/adjacent-payload-malformed-matrix.json" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg matrix_sha256 "$(sha256sum "$matrix" | cut -d' ' -f1)" \
    '{format:1, scope:"real Rekordbox 7.2.19 malformed adjacent payload matrix",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      declaration_sha256:$declaration_sha256,
      summary_sha256:$summary_sha256,
      matrix_sha256:$matrix_sha256,
      case_count:96, service_count:16,
      focused_tests_passed:true,
      synthetic_identity_units_active:false,
      isolated_vm_stopped:true}' \
    >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

wait_for_predecessor
require_successful_predecessor

"$vm/vmctl" isolated-start
"$guestctl" wait 300
"$vm/vmctl" isolation-check

"$script_dir/record_adjacent_payload_malformed.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_adjacent_payload_malformed.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
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

echo "=== malformed adjacent payload oracle validated and isolated VM stopped ==="
