#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly python="$lab/.venv/bin/python"

run_stage() {
  local name=$1
  local recorder=$2
  local reducer=$3

  echo "=== queue stage: $name ==="
  "$script_dir/$recorder"
  "$python" "$lab/tools/$reducer"
  echo "=== queue stage complete: $name ==="
}

"$python" "$lab/tools/summarize_hot_cue_declared_length_ffffffff_lifecycle.py"
"$python" "$lab/tools/summarize_hot_cue_slot_8_lifecycle.py"

run_stage \
  returned-slots-ffffffff-lifecycle \
  record_hot_cue_returned_slots_ffffffff_lifecycle.sh \
  summarize_hot_cue_returned_slots_ffffffff_lifecycle.py

run_stage \
  extended-setter-parser \
  record_hot_cue_extended_setter_parser_matrix.sh \
  summarize_hot_cue_extended_setter_parser.py
run_stage \
  legacy-setter-parser \
  record_hot_cue_legacy_setter_parser_matrix.sh \
  summarize_hot_cue_legacy_setter_parser.py
run_stage \
  hot-cue-buffer-disconnect \
  record_hot_cue_bank_buffer_disconnect.sh \
  summarize_hot_cue_buffer_disconnect.py
run_stage \
  cdj-2000nexus-status \
  record_cdj_2000nexus_status_matrix.sh \
  summarize_cdj_2000nexus_status_matrix.py
run_stage \
  secondary-columns-legacy \
  record_secondary_legacy_matrix.sh \
  summarize_secondary_legacy.py
run_stage \
  extended-setter-fields \
  record_hot_cue_extended_setter_field_matrix.sh \
  summarize_hot_cue_extended_setter_fields.py
run_stage \
  extended-setter-seek \
  record_hot_cue_extended_setter_seek_matrix.sh \
  summarize_hot_cue_extended_setter_seek.py
run_stage \
  bpm-tolerance-boundaries \
  record_bpm_tolerance_boundaries.sh \
  summarize_bpm_tolerance_boundaries.py

"$script_dir/finalize_real_rekordbox_queue.sh"
