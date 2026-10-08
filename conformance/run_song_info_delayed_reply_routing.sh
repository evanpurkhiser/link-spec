#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly timing="$lab/data/experiments/song-info-status-location2/malformed-history-timing/finalization.json"
readonly evidence="$lab/data/experiments/song-info-status-location2/delayed-reply-routing"
readonly summary="$evidence/summary.json"
readonly rows="$evidence/observations.csv"
readonly declaration="$script_dir/data/song-info-delayed-reply-routing-matrix.json"
readonly static_artifact="$lab/data/static-analysis/song-info-command-lifecycle.disasm.txt"
readonly completion="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly pinned_runner="$script_dir/pinned/link-export-conformance"
readonly pinned_tests="$script_dir/pinned/link-export-conformance-tests"
readonly pinned_manifest="$script_dir/pinned/manifest.json"
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

require_timing_authority() {
  jq -e '
    .format == 1 and
    .scope == "real Rekordbox 7.2.19 RX3 malformed-history timing" and
    .delay_value_count == 7 and .observations_per_delay == 4 and
    .observation_count == 28 and
    .focused_tests_passed == true and .pinned_tests_passed == true and
    .synthetic_identity_units_active == false and .isolated_vm_stopped == true
  ' "$timing" >/dev/null
}

require_pinned_runners() {
  local runner_sha256 test_runner_sha256

  runner_sha256=$(sha256sum "$pinned_runner" | cut -d' ' -f1)
  test_runner_sha256=$(sha256sum "$pinned_tests" | cut -d' ' -f1)
  [[ $runner_sha256 == "$(jq -er .runner.sha256 "$pinned_manifest")" ]]
  [[ $test_runner_sha256 == "$(jq -er .test_runner.sha256 "$pinned_manifest")" ]]
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
    --arg timing_finalization_sha256 "$(sha256sum "$timing" | cut -d' ' -f1)" \
    --arg declaration_sha256 "$(sha256sum "$declaration" | cut -d' ' -f1)" \
    --arg static_artifact_sha256 "$(sha256sum "$static_artifact" | cut -d' ' -f1)" \
    --arg runner_sha256 "$(sha256sum "$pinned_runner" | cut -d' ' -f1)" \
    --arg test_runner_sha256 "$(sha256sum "$pinned_tests" | cut -d' ' -f1)" \
    --arg pinned_manifest_sha256 "$(sha256sum "$pinned_manifest" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg rows_sha256 "$(sha256sum "$rows" | cut -d' ' -f1)" \
    '{format:1,scope:"real Rekordbox 7.2.19 player-routed malformed Song Info reply lifecycle",
      completed_at:$completed_at,baseline_database_sha256:$baseline_database_sha256,
      timing_finalization_sha256:$timing_finalization_sha256,
      declaration_sha256:$declaration_sha256,
      static_artifact_sha256:$static_artifact_sha256,
      runner_sha256:$runner_sha256,test_runner_sha256:$test_runner_sha256,
      pinned_manifest_sha256:$pinned_manifest_sha256,
      summary_sha256:$summary_sha256,rows_sha256:$rows_sha256,
      variant_count:6,observations_per_variant:4,observation_count:24,
      focused_tests_passed:true,pinned_tests_passed:true,
      synthetic_identity_units_active:false,isolated_vm_stopped:true}' \
    >"$completion.next"
  mv "$completion.next" "$completion"
}

require_timing_authority
require_pinned_runners
"$lab/.venv/bin/python" "$script_dir/generate_matrices.py"
(
  cd "$lab"
  "$lab/.venv/bin/python" -m unittest \
    conformance.test_song_info_delayed_reply_routing \
    conformance.test_song_info_command_lifecycle
)

"$vm/vmctl" isolated-start
vm_started=true
"$guestctl" wait 300
"$vm/vmctl" isolation-check
"$script_dir/record_song_info_delayed_reply_routing.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_song_info_delayed_reply_routing.py"
(
  cd "$lab"
  "$lab/.venv/bin/python" -m unittest \
    conformance.test_song_info_delayed_reply_routing \
    conformance.test_song_info_command_lifecycle \
    conformance.test_status_location2_malformed_history_timing \
    conformance.test_real_rekordbox_phase_boundary
  "$pinned_tests"
)

require_clean_baseline
"$vm/vmctl" isolated-stop
vm_started=false
write_receipt
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"
completed=true

echo "=== Song Info delayed-reply routing study validated and isolated VM stopped ==="
