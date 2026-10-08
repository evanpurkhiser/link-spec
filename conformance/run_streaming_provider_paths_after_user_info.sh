#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_USER_INFO_UNIT:-codex-rekordbox-user-info-djid-20261004as18.service}
readonly predecessor_receipt="$lab/data/experiments/user-info-djid/finalization.json"
readonly evidence="$lab/data/experiments/streaming-provider-paths"
readonly capture_receipt="$evidence/receipt.json"
readonly summary="$evidence/summary.json"
readonly matrix="$evidence/matrix.csv"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/streaming-provider-paths.json"
readonly suite="$script_dir/suites/generated/streaming-provider-paths.json"
readonly fixture_manifest="$script_dir/fixtures/generated/streaming-provider-paths/manifest.json"
readonly static_audit="$lab/data/static-analysis/streaming-provider-registry.json"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly conformance_test_runner="$script_dir/pinned/link-export-conformance-tests"
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
      if [[ $predecessor_observed_active == true && -f $predecessor_receipt ]]; then return; fi
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
    [[ $active_state == inactive && $result == success && $exit_status == 0 ]]
  fi
  jq -e '
    .format == 1 and
    .scope == "real Rekordbox 7.2.19 user-info/DJ-ID authority" and
    .execution_count == 10 and .case_count == 142 and
    .record_repeat_execution_count == 284 and
    .focused_tests_passed == true and .pinned_tests_passed == true and
    .original_profile_restored == true and
    .synthetic_identity_units_active == false and .isolated_vm_stopped == true
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
    --arg capture_receipt_sha256 "$(sha256sum "$capture_receipt" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg matrix_sha256 "$(sha256sum "$matrix" | cut -d' ' -f1)" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture_manifest" | cut -d' ' -f1)" \
    --arg static_audit_sha256 "$(sha256sum "$static_audit" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --argjson static_prediction_conflict_count "$(jq '.static_prediction_conflicts | length' "$summary")" \
    '{format:1,scope:"real Rekordbox 7.2.19 production-shaped streaming provider paths",
      completed_at:$completed_at,baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      capture_receipt_sha256:$capture_receipt_sha256,
      summary_sha256:$summary_sha256,matrix_sha256:$matrix_sha256,
      suite_sha256:$suite_sha256,fixture_manifest_sha256:$fixture_manifest_sha256,
      static_audit_sha256:$static_audit_sha256,golden_sha256:$golden_sha256,
      case_count:7,record_repeat_execution_count:14,
      static_prediction_conflict_count:$static_prediction_conflict_count,
      focused_tests_passed:true,pinned_tests_passed:true,
      synthetic_identity_units_active:false,isolated_vm_stopped:true}' \
    >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

wait_for_predecessor
require_successful_predecessor
"$vm/vmctl" isolated-start
vm_started=true
"$guestctl" wait 300
"$vm/vmctl" isolation-check
"$script_dir/record_streaming_provider_paths.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_streaming_provider_paths.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_streaming_provider_registry test_streaming_provider_paths \
    test_link_export_request_vocabulary test_corpus_documentation \
    test_real_rekordbox_phase_boundary
  "$conformance_test_runner"
)
require_clean_baseline
"$vm/vmctl" isolated-stop
vm_started=false
write_receipt
completed=true
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"

echo "=== Streaming-provider path oracle validated and isolated VM stopped ==="
