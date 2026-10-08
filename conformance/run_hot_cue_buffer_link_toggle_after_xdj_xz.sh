#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_XDJ_XZ_UNIT:-codex-rekordbox-xdj-xz-corroborating-20261003af18.service}
readonly predecessor_receipt="$lab/data/experiments/device-status/xdj-xz-corroborating/finalization.json"
readonly evidence="$lab/data/experiments/hot-cue-bank/buffer-link-toggle"
readonly summary="$evidence/summary.json"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly fixture_manifest="$script_dir/fixtures/generated/hot-cue-banks/manifest.json"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly warmup_suite="$script_dir/suites/hot-cue-bank-buffer-disconnect-warmup.json"
readonly post_suite="$script_dir/suites/hot-cue-bank-buffer-disconnect-post.json"
readonly recorder="$script_dir/record_hot_cue_bank_buffer_link_toggle.sh"
readonly reducer="$lab/tools/summarize_hot_cue_buffer_link_toggle.py"
readonly conformance_test_runner="$script_dir/pinned/link-export-conformance-tests"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
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

expected_test_runner_sha256=$(jq -er .test_runner.sha256 "$pinned_manifest")
conformance_test_runner_sha256=$(sha256sum "$conformance_test_runner" | cut -d' ' -f1)
[[ -x $conformance_test_runner ]]
[[ $conformance_test_runner_sha256 == "$expected_test_runner_sha256" ]]
pinned_manifest_sha256=$(sha256sum "$pinned_manifest" | cut -d' ' -f1)

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
    .scope == "real Rekordbox 7.2.19 corroborating XDJ-XZ status matrix" and
    .status_provenance == "corroborating-fixture" and
    .variant_count == 13 and .case_count == 249 and
    .record_repeat_execution_count == 498 and
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

run_receipts() {
  local mode run path

  for mode in control toggle; do
    for run in 1 2; do
      path="$evidence/repeats/$mode-run-$run/receipt.json"
      jq -n \
        --arg id "$mode-run-$run" \
        --arg sha256 "$(sha256sum "$path" | cut -d' ' -f1)" \
        '{id:$id,sha256:$sha256}'
    done
  done | jq -s .
}

write_receipt() {
  local expected_database receipts

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  receipts=$(run_receipts)
  mkdir -p "$evidence"
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg baseline_database_sha256 "$expected_database" \
    --arg predecessor_receipt_sha256 "$(sha256sum "$predecessor_receipt" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture_manifest" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg warmup_suite_sha256 "$(sha256sum "$warmup_suite" | cut -d' ' -f1)" \
    --arg post_suite_sha256 "$(sha256sum "$post_suite" | cut -d' ' -f1)" \
    --arg recorder_sha256 "$(sha256sum "$recorder" | cut -d' ' -f1)" \
    --arg reducer_sha256 "$(sha256sum "$reducer" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg conformance_test_runner_sha256 "$conformance_test_runner_sha256" \
    --arg pinned_manifest_sha256 "$pinned_manifest_sha256" \
    --argjson run_receipts "$receipts" \
    '{format:1,
      scope:"real Rekordbox 7.2.19 Hot Cue buffer LINK-toggle lifecycle",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256,
      warmup_suite_sha256:$warmup_suite_sha256,
      post_suite_sha256:$post_suite_sha256,
      recorder_sha256:$recorder_sha256,reducer_sha256:$reducer_sha256,
      summary_sha256:$summary_sha256,
      conformance_test_runner_sha256:$conformance_test_runner_sha256,
      pinned_manifest_sha256:$pinned_manifest_sha256,
      run_receipts:$run_receipts,
      mode_count:2,run_count:4,suite_execution_count:8,
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

"$recorder"
"$lab/.venv/bin/python" "$reducer"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_hot_cue_buffer_link_toggle \
    test_hot_cue_buffer_disconnect \
    test_hot_cue_buffer_disconnect_summary \
    test_hot_cue_notification_callback \
    test_corpus_documentation \
    test_real_rekordbox_phase_boundary
  "$conformance_test_runner"
)

require_clean_baseline
"$vm/vmctl" isolated-stop
vm_started=false
write_receipt
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"
completed=true

echo "=== Hot Cue buffer LINK-toggle lifecycle validated and isolated VM stopped ==="
