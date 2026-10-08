#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly evidence="$lab/data/experiments/song-info-status-location2/malformed-history-timing"
readonly summary="$evidence/summary.json"
readonly matrix="$evidence/observations.csv"
readonly conflict_record="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3-status/song-info-location2-malformed-history/play-extra-argument__then__delivery-blob-content.json.next"
readonly conflict_repeat="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3-status/song-info-location2-malformed-history/play-extra-argument__then__delivery-blob-content.json.actual.json"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly conformance_test_runner="$script_dir/pinned/link-export-conformance-tests"
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
    --arg conflict_record_sha256 "$(sha256sum "$conflict_record" | cut -d' ' -f1)" \
    --arg conflict_repeat_sha256 "$(sha256sum "$conflict_repeat" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg matrix_sha256 "$(sha256sum "$matrix" | cut -d' ' -f1)" \
    '{format:1,scope:"real Rekordbox 7.2.19 RX3 malformed-history timing",
      completed_at:$completed_at,baseline_database_sha256:$baseline_database_sha256,
      conflict_record_sha256:$conflict_record_sha256,
      conflict_repeat_sha256:$conflict_repeat_sha256,
      delay_value_count:7,observations_per_delay:4,observation_count:28,
      summary_sha256:$summary_sha256,matrix_sha256:$matrix_sha256,
      focused_tests_passed:true,pinned_tests_passed:true,
      synthetic_identity_units_active:false,isolated_vm_stopped:true}' \
    >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

test -f "$conflict_record"
test -f "$conflict_repeat"
"$vm/vmctl" isolated-start
vm_started=true
"$guestctl" wait 300
"$vm/vmctl" isolation-check
"$script_dir/record_status_location2_malformed_history_timing.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_status_location2_malformed_history_timing.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_status_location2_malformed_history_timing \
    test_status_location2_malformed_history \
    test_real_rekordbox_phase_boundary
  "$conformance_test_runner"
)
require_clean_baseline
"$vm/vmctl" isolated-stop
vm_started=false
write_receipt
completed=true

echo "=== Location-2 malformed-history timing study validated and isolated VM stopped ==="
