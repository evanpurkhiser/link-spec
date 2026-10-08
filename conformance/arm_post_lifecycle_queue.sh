#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly lifecycle_unit=${REKORDBOX_LIFECYCLE_UNIT:-codex-rekordbox-song-info-malformed-history-lifecycle-20261004z27.service}
readonly receipt="$lab/data/experiments/post-lifecycle-queue-arming.json"
readonly mode=${1:-arm}

if [[ $mode != arm && $mode != record-active ]]; then
  echo "usage: $0 [arm|record-active]" >&2
  exit 2
fi

if [[ $(systemctl --user show "$lifecycle_unit" -p ActiveState --value) != active ]]; then
  echo "$lifecycle_unit is not active" >&2
  exit 1
fi

readonly stages=$(cat <<'EOF'
codex-rekordbox-adjacent-success-status-20261003aa18.service|144h|run_adjacent_payload_success_status_after_history.sh|adjacent payload status/setup authority
codex-rekordbox-adjacent-boundaries-20261003ab18.service|192h|run_adjacent_payload_boundaries_after_status.sh|adjacent payload parser boundaries
codex-rekordbox-adjacent-cues-20261003ac18.service|216h|run_adjacent_payload_cues_after_boundaries.sh|adjacent cue payload authority
codex-rekordbox-xdj-rr-location9-20261003ad18.service|240h|run_xdj_rr_location9_after_cues.sh|XDJ-RR location-9 authority
codex-rekordbox-xdj-rr-old-key-20261003ae18.service|264h|run_xdj_rr_old_key_after_location9.sh|XDJ-RR old-Key and CueTrack authority
codex-rekordbox-xdj-xz-corroborating-20261003af18.service|288h|run_xdj_xz_corroborating_status_after_old_key.sh|corroborating XDJ-XZ status matrix
codex-rekordbox-hot-cue-buffer-link-toggle-20261003ag18.service|336h|run_hot_cue_buffer_link_toggle_after_xdj_xz.sh|Hot Cue buffer LINK-toggle lifecycle
codex-rekordbox-link-played-state-20261003ah18.service|360h|run_link_played_state_after_buffer_toggle.sh|Link-played transition authority
codex-rekordbox-link-played-persistence-20261003ai18.service|384h|run_link_played_persistence_after_transition.sh|Link-played restart persistence
codex-rekordbox-link-played-link-toggle-20261003aj18.service|408h|run_link_played_link_toggle_after_persistence.sh|Link-played LINK-toggle refresh
codex-rekordbox-link-played-multiplayer-20261003ak18.service|432h|run_link_played_multiplayer_after_link_toggle.sh|two-player Link-played ownership
codex-rekordbox-sort-secondary-render-5-20261003al18.service|456h|run_sort_secondary_render_5_after_multiplayer.sh|five-argument active-sort rendering
codex-rekordbox-sort-secondary-render-7-20261003am18.service|480h|run_sort_secondary_render_7_after_render_5.sh|seven-argument active-sort rendering
codex-rekordbox-render-arity-boundaries-20261003an18.service|504h|run_render_arity_boundaries_after_render_7.sh|track render arity boundaries
codex-rekordbox-render-arity-underflow-20261003ao18.service|528h|run_render_arity_underflow_after_boundaries.sh|track render arity underflow
codex-rekordbox-render-argument-types-20261003ap18.service|552h|run_render_argument_type_matrix_after_underflow.sh|track render argument types
codex-rekordbox-render-numeric-fields-20261003aq18.service|576h|run_render_numeric_fields_after_argument_types.sh|track render numeric fields
codex-rekordbox-render-override-controls-20261003ar18.service|600h|run_render_override_controls_after_numeric_fields.sh|track render override controls
EOF
)

while IFS='|' read -r unit runtime script description; do
  if [[ $mode == arm ]]; then
    if [[ $(systemctl --user show "$unit" -p LoadState --value 2>/dev/null) != not-found ]]; then
      echo "$unit already exists" >&2
      exit 1
    fi

    systemd-run --user --collect \
      --unit="$unit" \
      --description="Rekordbox research: $description" \
      --working-directory="$lab" \
      --property="RuntimeMaxSec=$runtime" \
      --setenv="REKORDBOX_MALFORMED_HISTORY_UNIT=$lifecycle_unit" \
      "$script_dir/$script"
  fi

  if [[ $(systemctl --user show "$unit" -p ActiveState --value) != active ]]; then
    echo "$unit did not become active" >&2
    exit 1
  fi
done <<<"$stages"

stage_state=$(
  while IFS='|' read -r unit runtime script description; do
    jq -n \
      --arg unit "$unit" \
      --arg runtime "$runtime" \
      --arg script "conformance/$script" \
      --arg description "$description" \
      --arg invocation_id "$(systemctl --user show "$unit" -p InvocationID --value)" \
      '{unit:$unit,runtime_max:$runtime,script:$script,description:$description,
        invocation_id:$invocation_id,active:true}'
  done <<<"$stages" | jq -s .
)

mkdir -p "$(dirname -- "$receipt")"
jq -n \
  --arg recorded_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg lifecycle_unit "$lifecycle_unit" \
  --arg lifecycle_invocation_id "$(systemctl --user show "$lifecycle_unit" -p InvocationID --value)" \
  --arg launcher_sha256 "$(sha256sum "${BASH_SOURCE[0]}" | cut -d' ' -f1)" \
  --argjson stages "$stage_state" \
  '{format:1,scope:"post-lifecycle real-Rekordbox authority queue arming",
    recorded_at:$recorded_at,lifecycle_unit:$lifecycle_unit,
    lifecycle_invocation_id:$lifecycle_invocation_id,
    launcher_sha256:$launcher_sha256,stage_count:18,all_active:true,stages:$stages}' \
  >"$receipt.next"
mv "$receipt.next" "$receipt"

echo "=== post-lifecycle Rekordbox authority queue armed ==="
