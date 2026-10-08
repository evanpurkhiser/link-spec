#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
readonly receipt="$lab/data/experiments/real-rekordbox-queue-finalization.json"
readonly conformance_runner="$script_dir/pinned/link-export-conformance"
readonly conformance_test_runner="$script_dir/pinned/link-export-conformance-tests"
readonly pinned_manifest="$script_dir/pinned/manifest.json"

for executable in "$conformance_runner" "$conformance_test_runner"; do
  if [[ ! -x $executable ]]; then
    echo "pinned conformance executable is absent or not executable: $executable" >&2
    exit 1
  fi
done

conformance_runner_sha256=$(sha256sum "$conformance_runner" | cut -d' ' -f1)
conformance_test_runner_sha256=$(sha256sum "$conformance_test_runner" | cut -d' ' -f1)
expected_runner_sha256=$(jq -er .runner.sha256 "$pinned_manifest")
expected_test_runner_sha256=$(jq -er .test_runner.sha256 "$pinned_manifest")
[[ $conformance_runner_sha256 == "$expected_runner_sha256" ]]
[[ $conformance_test_runner_sha256 == "$expected_test_runner_sha256" ]]
pinned_manifest_sha256=$(sha256sum "$pinned_manifest" | cut -d' ' -f1)

python3 "$lab/tools/summarize_hot_cue_declared_length_ffffffff_lifecycle.py"
python3 "$lab/tools/summarize_hot_cue_slot_8_lifecycle.py"
python3 "$lab/tools/summarize_hot_cue_returned_slots_ffffffff_lifecycle.py"
python3 "$lab/tools/summarize_hot_cue_extended_setter_parser.py"
python3 "$lab/tools/summarize_hot_cue_legacy_setter_parser.py"
python3 "$lab/tools/summarize_hot_cue_buffer_disconnect.py"
python3 "$lab/tools/summarize_cdj_2000nexus_status_matrix.py"
python3 "$lab/tools/summarize_secondary_legacy.py"
python3 "$lab/tools/summarize_bpm_tolerance_boundaries.py"
python3 "$lab/tools/summarize_hot_cue_extended_setter_fields.py"
python3 "$lab/tools/summarize_hot_cue_extended_setter_seek.py"

(
  cd "$script_dir"
  python3 -m unittest \
    test_hot_cue_declared_length_ffffffff_lifecycle \
    test_hot_cue_declared_length_ffffffff_lifecycle_summary \
    test_hot_cue_slot_8_lifecycle \
    test_hot_cue_slot_8_static_analysis \
    test_hot_cue_returned_slots_ffffffff_lifecycle \
    test_hot_cue_setter_reply_target_audit \
    test_hot_cue_extended_setter_parser \
    test_hot_cue_legacy_setter_parser \
    test_hot_cue_legacy_setter_summary \
    test_hot_cue_buffer_disconnect \
    test_cdj_2000nexus_status_matrix \
    test_secondary_legacy_matrix \
    test_hot_cue_extended_setter_fields \
    test_hot_cue_extended_setter_seek \
    test_device_status_source_inventory \
    test_public_status_source_audit \
    test_menu_database_query_map \
    test_link_export_request_vocabulary \
    test_adjacent_payload_services \
    test_payload_assets \
    test_db_interface_selection_audit \
    test_category_configuration_semantics \
    test_corpus_documentation \
    test_history_lifecycle_documentation \
    test_reference_hierarchy_claims \
    test_source_library_count_audit \
    test_bpm_tolerance_boundaries \
    test_bpm_tolerance_static_analysis \
    test_track_compatibility_exhaustive \
    test_update_checksums \
    test_real_rekordbox_phase_boundary
  "$conformance_test_runner"
)

expected_database=$(jq -er .database_sha256 "$baseline_manifest")
active_database=$(jq -er .database_sha256 "$active_manifest")
[[ $active_database == "$expected_database" ]]

if systemctl --user list-units --state=active --plain --no-legend \
  'rekordbox-identity-*' | grep -q .; then
  echo "synthetic rekordbox identity unit remains active" >&2
  exit 1
fi

"$vm/vmctl" isolated-stop

jq -n \
  --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg baseline_database_sha256 "$expected_database" \
  --arg conformance_runner_sha256 "$conformance_runner_sha256" \
  --arg conformance_test_runner_sha256 "$conformance_test_runner_sha256" \
  --arg pinned_manifest_sha256 "$pinned_manifest_sha256" \
  --arg lifecycle_summary_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/extended-setter-parser/declared-length-ffffffff-lifecycle/summary.json" | cut -d' ' -f1)" \
  --arg slot8_lifecycle_summary_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/extended-setter-parser/slot-00000008-lifecycle/summary.json" | cut -d' ' -f1)" \
  --arg returned_slots_lifecycle_summary_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/extended-setter-parser/returned-slots-ffffffff-lifecycle/summary.json" | cut -d' ' -f1)" \
  --arg extended_summary_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/extended-setter-parser/summary.json" | cut -d' ' -f1)" \
  --arg legacy_summary_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/legacy-setter-parser/summary.json" | cut -d' ' -f1)" \
  --arg legacy_matrix_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/legacy-setter-parser/matrix.csv" | cut -d' ' -f1)" \
  --arg buffer_summary_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/buffer-disconnect/summary.json" | cut -d' ' -f1)" \
  --arg cdj2000nexus_summary_sha256 "$(sha256sum "$lab/data/experiments/device-status/cdj-2000nexus/summary.json" | cut -d' ' -f1)" \
  --arg secondary_legacy_summary_sha256 "$(sha256sum "$lab/data/experiments/secondary-column-legacy/summary.json" | cut -d' ' -f1)" \
  --arg bpm_tolerance_summary_sha256 "$(sha256sum "$lab/data/experiments/bpm-tolerance-boundaries/summary.json" | cut -d' ' -f1)" \
  --arg setter_fields_summary_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/extended-setter-fields/summary.json" | cut -d' ' -f1)" \
  --arg setter_seek_summary_sha256 "$(sha256sum "$lab/data/experiments/hot-cue-bank/extended-setter-seek/summary.json" | cut -d' ' -f1)" \
  '{format:1, scope:"real Rekordbox 7.2.19 only",
    completed_at:$completed_at,
    baseline_database_sha256:$baseline_database_sha256,
    conformance_runner_sha256:$conformance_runner_sha256,
    conformance_test_runner_sha256:$conformance_test_runner_sha256,
    pinned_manifest_sha256:$pinned_manifest_sha256,
    lifecycle_summary_sha256:$lifecycle_summary_sha256,
    slot8_lifecycle_summary_sha256:$slot8_lifecycle_summary_sha256,
    returned_slots_lifecycle_summary_sha256:$returned_slots_lifecycle_summary_sha256,
    extended_summary_sha256:$extended_summary_sha256,
    legacy_summary_sha256:$legacy_summary_sha256,
    legacy_matrix_sha256:$legacy_matrix_sha256,
    buffer_summary_sha256:$buffer_summary_sha256,
    cdj2000nexus_summary_sha256:$cdj2000nexus_summary_sha256,
    secondary_legacy_summary_sha256:$secondary_legacy_summary_sha256,
    bpm_tolerance_summary_sha256:$bpm_tolerance_summary_sha256,
    setter_fields_summary_sha256:$setter_fields_summary_sha256,
    setter_seek_summary_sha256:$setter_seek_summary_sha256,
    focused_tests_passed:true, rust_tests_passed:true,
    synthetic_identity_units_active:false, isolated_vm_stopped:true}' \
  >"$receipt.next"
mv "$receipt.next" "$receipt"
python3 "$lab/tools/update_checksums.py"

echo "=== real Rekordbox queue validated and isolated VM stopped ==="
