#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly guestctl="$lab/guest-control/guestctl"
readonly history_unit=${REKORDBOX_HISTORY_UNIT:-codex-rekordbox-identical-history-20261002d.service}
readonly history_receipt="$lab/data/experiments/hot-cue-bank/legacy-identical-request-history/finalization.json"
readonly compatibility_summary="$lab/data/experiments/track-compatibility-exhaustive/summary.json"
readonly completion_receipt="$lab/data/experiments/track-compatibility-exhaustive/finalization.json"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
history_observed_active=false

wait_for_history() {
  local state

  while true; do
    if ! state=$(systemctl --user show "$history_unit" -p ActiveState --value 2>/dev/null); then
      if [[ $history_observed_active == true && -f $history_receipt ]]; then
        return
      fi

      echo "$history_unit disappeared without a finalization receipt" >&2
      exit 1
    fi

    case "$state" in
      active|activating|reloading|deactivating)
        history_observed_active=true
        sleep 30
        ;;
      inactive|failed)
        return
        ;;
      *)
        echo "unexpected $history_unit state: $state" >&2
        exit 1
        ;;
    esac
  done
}

require_successful_history() {
  local active_state result exit_status

  [[ $history_observed_active == true || -f $history_receipt ]]
  if active_state=$(systemctl --user show "$history_unit" -p ActiveState --value 2>/dev/null); then
    result=$(systemctl --user show "$history_unit" -p Result --value)
    exit_status=$(systemctl --user show "$history_unit" -p ExecMainStatus --value)

    [[ $active_state == inactive ]]
    [[ $result == success ]]
    [[ $exit_status == 0 ]]
  fi

  jq -e '
    .format == 1 and
    .scope == "real Rekordbox 7.2.19 only" and
    (.cycle_receipt_sha256 | length == 2) and
    .focused_tests_passed == true and
    .synthetic_identity_units_active == false and
    .isolated_vm_stopped == true
  ' "$history_receipt" >/dev/null
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
  mkdir -p "$(dirname -- "$completion_receipt")"
  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg baseline_database_sha256 "$expected_database" \
    --arg history_receipt_sha256 "$(sha256sum "$history_receipt" | cut -d' ' -f1)" \
    --arg summary_sha256 "$(sha256sum "$compatibility_summary" | cut -d' ' -f1)" \
    --arg extended_golden_sha256 "$(sha256sum "$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/track-compatibility-exhaustive-extended.json" | cut -d' ' -f1)" \
    --arg legacy_golden_sha256 "$(sha256sum "$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/track-compatibility-exhaustive-legacy.json" | cut -d' ' -f1)" \
    --arg extended_receipt_sha256 "$(sha256sum "$lab/data/experiments/track-compatibility-exhaustive/setups/extended/receipt.json" | cut -d' ' -f1)" \
    --arg legacy_receipt_sha256 "$(sha256sum "$lab/data/experiments/track-compatibility-exhaustive/setups/legacy/receipt.json" | cut -d' ' -f1)" \
    '{format:1, scope:"real Rekordbox 7.2.19 track compatibility only",
      completed_at:$completed_at,
      baseline_database_sha256:$baseline_database_sha256,
      history_receipt_sha256:$history_receipt_sha256,
      compatibility_summary_sha256:$summary_sha256,
      extended_golden_sha256:$extended_golden_sha256,
      legacy_golden_sha256:$legacy_golden_sha256,
      extended_receipt_sha256:$extended_receipt_sha256,
      legacy_receipt_sha256:$legacy_receipt_sha256,
      focused_tests_passed:true,
      synthetic_identity_units_active:false,
      isolated_vm_stopped:true}' \
    >"$completion_receipt.next"
  mv "$completion_receipt.next" "$completion_receipt"
}

wait_for_history
require_successful_history

"$vm/vmctl" isolated-start
"$guestctl" wait 300
"$vm/vmctl" isolation-check

"$script_dir/record_track_compatibility_exhaustive.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_track_compatibility_exhaustive.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_track_compatibility_exhaustive \
    test_corpus_documentation \
    test_history_lifecycle_documentation \
    test_public_status_source_audit \
    test_menu_database_query_map \
    test_source_library_count_audit \
    test_real_rekordbox_phase_boundary
)

require_clean_baseline
"$vm/vmctl" isolated-stop
write_receipt
"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"

echo "=== exhaustive track compatibility validated and isolated VM stopped ==="
