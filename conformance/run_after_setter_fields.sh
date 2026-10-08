#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly predecessor_unit=${REKORDBOX_SETTER_FIELDS_UNIT:-codex-rekordbox-setter-fields-20261002r.service}
readonly matrix="$script_dir/data/hot-cue-setter-field-matrix.json"
readonly evidence_root="$lab/data/experiments/hot-cue-bank/extended-setter-fields/repeats"
readonly active_manifest="$vm/shared/link-export-conformance/active-guest-manifest.json"
readonly baseline_manifest="$script_dir/fixtures/generated/play-paths/manifest.json"
predecessor_observed_active=false

setter_fields_complete() {
  local variant suite golden evidence

  while IFS= read -r variant; do
    suite=$(jq -er --arg id "$variant" '.variants[] | select(.id == $id) | .suite' "$matrix")
    golden=$(jq -er --arg id "$variant" '.variants[] | select(.id == $id) | .golden' "$matrix")
    evidence="$evidence_root/$variant"

    [[ -f $script_dir/$suite ]]
    [[ -f $script_dir/$golden ]]
    [[ ! -e $script_dir/$golden.next ]]
    [[ -f $evidence/record-snapshot.json ]]
    [[ -f $evidence/repeat-snapshot.json ]]
    [[ -f $evidence/receipt.json ]]
    [[ ! -e $evidence/receipt.json.next ]]
  done < <(jq -er '.variants[].id' "$matrix")
}

wait_for_predecessor() {
  local state

  while true; do
    if ! state=$(systemctl --user show "$predecessor_unit" -p ActiveState --value 2>/dev/null); then
      if [[ $predecessor_observed_active == true ]] && setter_fields_complete; then
        return
      fi

      echo "$predecessor_unit disappeared without complete setter-field evidence" >&2
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
  local active_state result exit_status expected_database active_database

  [[ $predecessor_observed_active == true ]]
  if active_state=$(systemctl --user show "$predecessor_unit" -p ActiveState --value 2>/dev/null); then
    result=$(systemctl --user show "$predecessor_unit" -p Result --value)
    exit_status=$(systemctl --user show "$predecessor_unit" -p ExecMainStatus --value)

    [[ $active_state == inactive ]]
    [[ $result == success ]]
    [[ $exit_status == 0 ]]
  fi

  setter_fields_complete
  "$lab/.venv/bin/python" "$lab/tools/summarize_hot_cue_extended_setter_fields.py"

  expected_database=$(jq -er .database_sha256 "$baseline_manifest")
  active_database=$(jq -er .database_sha256 "$active_manifest")
  [[ $active_database == "$expected_database" ]]

  if systemctl --user list-units --state=active --plain --no-legend \
    'rekordbox-identity-*' | grep -q .; then
    echo "synthetic rekordbox identity unit remains active" >&2
    exit 1
  fi
}

wait_for_predecessor
require_successful_predecessor

(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_hot_cue_extended_setter_fields \
    test_real_rekordbox_phase_boundary
)

"$script_dir/record_hot_cue_extended_setter_seek_matrix.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_hot_cue_extended_setter_seek.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_hot_cue_extended_setter_seek \
    test_real_rekordbox_phase_boundary
)

"$script_dir/record_bpm_tolerance_boundaries.sh"
"$lab/.venv/bin/python" "$lab/tools/summarize_bpm_tolerance_boundaries.py"
(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_bpm_tolerance_boundaries \
    test_bpm_tolerance_static_analysis \
    test_real_rekordbox_phase_boundary
)

"$script_dir/finalize_real_rekordbox_queue.sh"

echo "=== setter-field handoff, seek/BPM capture, and queue finalization complete ==="
