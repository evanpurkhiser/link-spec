#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly index="$script_dir/data/adjacent-payload-cue-matrix.json"
readonly fixture="$script_dir/fixtures/generated/adjacent-payload-cues"
readonly golden_root="$script_dir/goldens/rekordbox-7.2.19"
readonly evidence_root="$lab/data/experiments/adjacent-payload/cues/variants"

record_variant() {
  local variant=$1
  local suite_relative=$2
  local model=$3
  local golden_name=$4
  local identity_relative=$5
  local case_count=$6
  local service_count=$7
  local suite="$script_dir/$suite_relative"
  local identity="$script_dir/$identity_relative"
  local golden="$golden_root/$model/$golden_name"
  local evidence="$evidence_root/$variant"

  mkdir -p "$(dirname -- "$golden")" "$evidence"
  REKORDBOX_FILELESS_VARIANT="cue-$variant" \
  REKORDBOX_FILELESS_SCOPE="real Rekordbox 7.2.19 adjacent cue payload matrix" \
  REKORDBOX_FILELESS_FIXTURE="$fixture" \
  REKORDBOX_FILELESS_IDENTITY="$identity" \
  REKORDBOX_FILELESS_SUITE="$suite" \
  REKORDBOX_FILELESS_GOLDEN="$golden" \
  REKORDBOX_FILELESS_EVIDENCE="$evidence" \
  REKORDBOX_FILELESS_CASE_COUNT="$case_count" \
  REKORDBOX_FILELESS_SERVICE_COUNT="$service_count" \
    "$script_dir/record_adjacent_payload_fileless.sh"
}

mapfile -t declarations < <(
  jq -r '.variants[] | [.variant, .suite, .golden_model, .golden, .identity, .case_count, .service_count] | @tsv' "$index"
)

for declaration in "${declarations[@]}"; do
  IFS=$'\t' read -r variant suite model golden identity case_count service_count \
    <<<"$declaration"
  record_variant "$variant" "$suite" "$model" "$golden" "$identity" "$case_count" "$service_count"
done

echo "=== adjacent cue payload matrix: complete ==="
