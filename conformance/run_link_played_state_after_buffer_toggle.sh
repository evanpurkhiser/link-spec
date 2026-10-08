#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_BUFFER_TOGGLE_UNIT:-codex-rekordbox-hot-cue-buffer-link-toggle-20261003ag18.service}
readonly predecessor_receipt="$lab/data/experiments/hot-cue-bank/buffer-link-toggle/finalization.json"
readonly evidence="$lab/data/experiments/played-track-state/transition-reset"
readonly capture_receipt="$evidence/receipt.json"
readonly summary="$evidence/summary.json"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly fixture_manifest="$script_dir/fixtures/generated/full/manifest.json"
readonly suite="$script_dir/suites/link-played-state.json"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly recorder="$script_dir/record_link_played_state.sh"
readonly reducer="$lab/tools/summarize_link_played_state.py"
readonly conformance_test_runner="$script_dir/pinned/link-export-conformance-tests"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
predecessor_observed_active=false
completed=false
vm_started=false

expected_test_runner_sha256=$(jq -er .test_runner.sha256 "$pinned_manifest")
conformance_test_runner_sha256=$(sha256sum "$conformance_test_runner" | cut -d' ' -f1)
[[ -x $conformance_test_runner ]]
[[ $conformance_test_runner_sha256 == "$expected_test_runner_sha256" ]]
pinned_manifest_sha256=$(sha256sum "$pinned_manifest" | cut -d' ' -f1)

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
    .scope == "real Rekordbox 7.2.19 Hot Cue buffer LINK-toggle lifecycle" and
    .mode_count == 2 and .run_count == 4 and .suite_execution_count == 8 and
    .focused_tests_passed == true and .pinned_tests_passed == true and
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
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture_manifest" | cut -d' ' -f1)" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg recorder_sha256 "$(sha256sum "$recorder" | cut -d' ' -f1)" \
    --arg reducer_sha256 "$(sha256sum "$reducer" | cut -d' ' -f1)" \
    --arg capture_receipt_sha256 "$(sha256sum "$capture_receipt" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg conformance_test_runner_sha256 "$conformance_test_runner_sha256" \
    --arg pinned_manifest_sha256 "$pinned_manifest_sha256" \
    '{format:1,
      scope:"real Rekordbox 7.2.19 Link-played transition under reset options",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      suite_sha256:$suite_sha256,identity_sha256:$identity_sha256,
      recorder_sha256:$recorder_sha256,reducer_sha256:$reducer_sha256,
      capture_receipt_sha256:$capture_receipt_sha256,
      summary_sha256:$summary_sha256,
      conformance_test_runner_sha256:$conformance_test_runner_sha256,
      pinned_manifest_sha256:$pinned_manifest_sha256,
      case_count:19,process_count:2,record_repeat_verified:true,
      guest_state_restored:true,focused_tests_passed:true,
      pinned_tests_passed:true,synthetic_identity_units_active:false,
      isolated_vm_stopped:true}' >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

wait_for_predecessor
require_successful_predecessor

"$vm/vmctl" isolated-start
vm_started=true
"$guestctl" wait 300
"$vm/vmctl" isolation-check

"$recorder"
"$lab/.venv/bin/python" "$reducer"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_played_track_state \
    test_corpus_documentation \
    test_menu_database_query_map \
    test_link_export_request_vocabulary \
    test_history_lifecycle_documentation
  "$conformance_test_runner"
)

require_clean_baseline
"$vm/vmctl" isolated-stop
vm_started=false
write_receipt
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"
completed=true

echo "=== Link-played transition validated, guest restored, and isolated VM stopped ==="
