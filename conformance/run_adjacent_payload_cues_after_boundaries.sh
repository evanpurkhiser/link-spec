#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly predecessor_unit=${REKORDBOX_PAYLOAD_BOUNDARY_UNIT:-codex-rekordbox-adjacent-boundaries-20261003ab18.service}
readonly predecessor_receipt="$lab/data/experiments/adjacent-payload/boundaries/finalization.json"
readonly declaration="$script_dir/data/adjacent-payload-cue-matrix.json"
readonly evidence="$lab/data/experiments/adjacent-payload/cues"
readonly summary="$evidence/summary.json"
readonly matrix="$evidence/matrix.csv"
readonly completion_receipt="$evidence/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
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

if [[ ! -x $conformance_test_runner ]]; then
  echo "pinned conformance test executable is absent or not executable: $conformance_test_runner" >&2
  exit 1
fi
expected_test_runner_sha256=$(jq -er .test_runner.sha256 "$pinned_manifest")
conformance_test_runner_sha256=$(sha256sum "$conformance_test_runner" | cut -d' ' -f1)
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
    .scope == "real Rekordbox 7.2.19 adjacent payload parser boundaries" and
    .variant_count == 30 and .case_count == 57 and
    .focused_tests_passed == true and .rust_tests_passed == true and
    .synthetic_identity_units_active == false and
    .deterministic_guest_assets_removed == true and
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

variant_receipts() {
  local variant

  while IFS= read -r variant; do
    jq -n \
      --arg variant "$variant" \
      --arg sha256 "$(sha256sum "$evidence/variants/$variant/receipt.json" | cut -d' ' -f1)" \
      '{variant:$variant,sha256:$sha256}'
  done < <(jq -r '.variants[].variant' "$declaration") | jq -s .
}

write_receipt() {
  local expected_database receipts

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  receipts=$(variant_receipts)
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg baseline_database_sha256 "$expected_database" \
    --arg predecessor_receipt_sha256 "$(sha256sum "$predecessor_receipt" | cut -d' ' -f1)" \
    --arg declaration_sha256 "$(sha256sum "$declaration" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$script_dir/fixtures/generated/adjacent-payload-cues/manifest.json" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$summary" | cut -d' ' -f1)" \
    --arg matrix_sha256 "$(sha256sum "$matrix" | cut -d' ' -f1)" \
    --arg conformance_test_runner_sha256 "$conformance_test_runner_sha256" \
    --arg pinned_manifest_sha256 "$pinned_manifest_sha256" \
    --argjson variant_receipts "$receipts" \
    '{format:1, scope:"real Rekordbox 7.2.19 adjacent cue payload matrix",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      predecessor_receipt_sha256:$predecessor_receipt_sha256,
      declaration_sha256:$declaration_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      summary_sha256:$summary_sha256,
      matrix_sha256:$matrix_sha256,
      conformance_test_runner_sha256:$conformance_test_runner_sha256,
      pinned_manifest_sha256:$pinned_manifest_sha256,
      variant_receipts:$variant_receipts,
      variant_count:8, case_count:114,
      focused_tests_passed:true, rust_tests_passed:true,
      synthetic_identity_units_active:false,
      isolated_vm_stopped:true}' \
    >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

wait_for_predecessor
require_successful_predecessor

"$vm/vmctl" isolated-start
vm_started=true
"$guestctl" wait 300
"$vm/vmctl" isolation-check

"$script_dir/record_adjacent_payload_cue_matrix.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_adjacent_payload_cues.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_adjacent_payload_cues \
    test_payload_assets \
    test_adjacent_payload_services \
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

echo "=== adjacent cue payload matrix validated and isolated VM stopped ==="
