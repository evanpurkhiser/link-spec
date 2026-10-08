#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_COMPATIBILITY_UNIT:-codex-rekordbox-track-compatibility-20261002d.service}
readonly predecessor_receipt="$lab/data/experiments/track-compatibility-exhaustive/finalization.json"
readonly matrix="$script_dir/data/song-info-location2-malformed-history-matrix.json"
readonly summary_root="$lab/data/experiments/song-info-status-location2/malformed-history-lifecycle"
readonly golden_root="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3-status/song-info-location2-malformed-history-lifecycle"
readonly receipt_root="$summary_root/repeats"
readonly completion_receipt="$summary_root/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly conformance_runner="$script_dir/pinned/link-export-conformance"
readonly conformance_test_runner="$script_dir/pinned/link-export-conformance-tests"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
predecessor_observed_active=false

if [[ ! -x $conformance_runner || ! -x $conformance_test_runner ]]; then
  echo "pinned conformance executables are absent or not executable" >&2
  exit 1
fi
expected_runner_sha256=$(jq -er .runner.sha256 "$pinned_manifest")
expected_test_runner_sha256=$(jq -er .test_runner.sha256 "$pinned_manifest")
conformance_runner_sha256=$(sha256sum "$conformance_runner" | cut -d' ' -f1)
conformance_test_runner_sha256=$(sha256sum "$conformance_test_runner" | cut -d' ' -f1)
[[ $conformance_runner_sha256 == "$expected_runner_sha256" ]]
[[ $conformance_test_runner_sha256 == "$expected_test_runner_sha256" ]]
pinned_manifest_sha256=$(sha256sum "$pinned_manifest" | cut -d' ' -f1)

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

  [[ $predecessor_observed_active == true || -f $predecessor_receipt ]]
  if active_state=$(systemctl --user show "$predecessor_unit" -p ActiveState --value 2>/dev/null); then
    result=$(systemctl --user show "$predecessor_unit" -p Result --value)
    exit_status=$(systemctl --user show "$predecessor_unit" -p ExecMainStatus --value)

    [[ $active_state == inactive ]]
    [[ $result == success ]]
    [[ $exit_status == 0 ]]
  fi

  jq -e '
    .format == 1 and
    .scope == "real Rekordbox 7.2.19 track compatibility only" and
    .focused_tests_passed == true and
    .synthetic_identity_units_active == false and
    .isolated_vm_stopped == true
  ' "$predecessor_receipt" >/dev/null
}

start_isolated_vm() {
  "$vm/vmctl" isolated-start
  "$guestctl" wait 300
  "$vm/vmctl" isolation-check
}

batch_is_complete() {
  local pair golden receipt expected actual

  for pair in "$@"; do
    golden="$golden_root/$pair.json"
    receipt="$receipt_root/$pair/receipt.json"
    [[ -f $golden && -f $receipt ]] || return 1

    expected=$(jq -er .golden_sha256 "$receipt") || return 1
    actual=$(sha256sum "$golden" | cut -d' ' -f1)
    [[ $actual == "$expected" ]] || return 1
  done
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
    --arg matrix_sha256 "$(sha256sum "$matrix" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary_root/summary.json" | cut -d' ' -f1)" \
    --arg readable_matrix_sha256 "$(sha256sum "$summary_root/matrix.csv" | cut -d' ' -f1)" \
    --arg conformance_runner_sha256 "$conformance_runner_sha256" \
    --arg conformance_test_runner_sha256 "$conformance_test_runner_sha256" \
    --arg pinned_manifest_sha256 "$pinned_manifest_sha256" \
    '{format:1, scope:"real Rekordbox 7.2.19 RX3 location-2 malformed-history lifecycle",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      matrix_sha256:$matrix_sha256,
      summary_sha256:$summary_sha256,
      readable_matrix_sha256:$readable_matrix_sha256,
      conformance_runner_sha256:$conformance_runner_sha256,
      conformance_test_runner_sha256:$conformance_test_runner_sha256,
      pinned_manifest_sha256:$pinned_manifest_sha256,
      ordered_pairs:256, independently_repeated_pairs:256,
      focused_tests_passed:true,
      synthetic_identity_units_active:false,
      isolated_vm_stopped:true}' \
    >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

wait_for_predecessor
require_successful_predecessor

mapfile -t pairs < <(jq -r '.pairs[].id' "$matrix")
readonly batch_size=64
vm_running=false
for ((offset = 0; offset < ${#pairs[@]}; offset += batch_size)); do
  batch=("${pairs[@]:offset:batch_size}")
  if batch_is_complete "${batch[@]}"; then
    echo "=== malformed history batch $offset: canonical receipts verified; skipping VM ==="
    continue
  fi

  if [[ $vm_running == true ]]; then
    "$vm/vmctl" isolated-stop
  fi
  start_isolated_vm
  vm_running=true
  "$script_dir/record_status_location2_malformed_history_matrix.sh" \
    "${batch[@]}"
done

"$lab/.venv/bin/python" "$lab/tools/summarize_status_location2_malformed_history.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_status_location2_malformed_history \
    test_corpus_documentation \
    test_history_lifecycle_documentation \
    test_public_status_source_audit \
    test_menu_database_query_map \
    test_source_library_count_audit \
    test_real_rekordbox_phase_boundary
  "$conformance_test_runner"
)

require_clean_baseline
"$vm/vmctl" isolated-stop
write_receipt
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"

echo "=== location-2 malformed-history matrix validated and isolated VM stopped ==="
