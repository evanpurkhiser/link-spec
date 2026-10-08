#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_RENDER_CONTROLS_UNIT:-codex-rekordbox-render-override-controls-20261003ar18.service}
readonly predecessor_receipt="$lab/data/experiments/render-override-controls/finalization.json"
readonly evidence="$lab/data/experiments/user-info-djid"
readonly summary="$evidence/summary.json"
readonly readable_matrix="$evidence/matrix.csv"
readonly execution_matrix="$script_dir/data/user-info-djid-matrix.json"
readonly profile_manifest="$script_dir/user-info-djid-profiles/manifest.json"
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
    .scope == "real Rekordbox 7.2.19 track render override controls" and
    .case_count == 17 and .record_repeat_execution_count == 34 and
    .focused_tests_passed == true and .pinned_tests_passed == true and
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
  jq -e '
    all(.entries[] | select(.role | endswith("backup")); .exists == false)
  ' "$evidence/restored-profile-state.json" >/dev/null
}

write_receipt() {
  local expected_database executions

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  executions=$(
    jq -c '.executions[]' "$execution_matrix" | while IFS= read -r execution; do
      id=$(jq -r .id <<<"$execution")
      golden_rel=$(jq -r .golden <<<"$execution")
      jq -n \
        --arg id "$id" \
        --arg golden_sha256 "$(sha256sum "$script_dir/$golden_rel" | cut -d' ' -f1)" \
        --arg receipt_sha256 "$(sha256sum "$evidence/$id/receipt.json" | cut -d' ' -f1)" \
        '{id:$id,golden_sha256:$golden_sha256,receipt_sha256:$receipt_sha256}'
    done | jq -s .
  )
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg baseline_database_sha256 "$expected_database" \
    --arg predecessor_receipt_sha256 "$(sha256sum "$predecessor_receipt" | cut -d' ' -f1)" \
    --arg execution_matrix_sha256 "$(sha256sum "$execution_matrix" | cut -d' ' -f1)" \
    --arg profile_manifest_sha256 "$(sha256sum "$profile_manifest" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg readable_matrix_sha256 "$(sha256sum "$readable_matrix" | cut -d' ' -f1)" \
    --arg original_profile_state_sha256 "$(sha256sum "$evidence/original-profile-state.json" | cut -d' ' -f1)" \
    --arg restored_profile_state_sha256 "$(sha256sum "$evidence/restored-profile-state.json" | cut -d' ' -f1)" \
    --argjson static_prediction_conflict_count "$(jq '.static_prediction_conflicts | length' "$summary")" \
    --argjson executions "$executions" \
    '{format:1,scope:"real Rekordbox 7.2.19 user-info/DJ-ID authority",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      execution_matrix_sha256:$execution_matrix_sha256,
      profile_manifest_sha256:$profile_manifest_sha256,
      summary_sha256:$summary_sha256,
      readable_matrix_sha256:$readable_matrix_sha256,
      original_profile_state_sha256:$original_profile_state_sha256,
      restored_profile_state_sha256:$restored_profile_state_sha256,
      execution_count:10,case_count:142,record_repeat_execution_count:284,
      static_prediction_conflict_count:$static_prediction_conflict_count,
      executions:$executions,
      focused_tests_passed:true,pinned_tests_passed:true,
      original_profile_restored:true,
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
"$script_dir/record_user_info_djid_matrix.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_user_info_djid_matrix.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_user_info_djid test_user_info_djid_live \
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

echo "=== User-info/DJ-ID authority oracle validated and isolated VM stopped ==="
