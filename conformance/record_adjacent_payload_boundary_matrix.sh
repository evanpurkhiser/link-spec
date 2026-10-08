#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly matrix="$script_dir/data/adjacent-payload-boundary-matrix.json"
readonly assets_root="$script_dir/payload-assets/boundaries"
readonly suites_root="$script_dir/suites/generated/adjacent-payload-boundaries"
readonly golden_root="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-boundaries"
readonly evidence_root="$lab/data/experiments/adjacent-payload/boundaries/variants"

record_variant() {
  local variant=$1
  local case_count=$2
  local service_count=$3
  local assets="$assets_root/$variant"
  local suite="$suites_root/$variant.json"
  local golden="$golden_root/$variant.json"
  local evidence="$evidence_root/$variant"

  mkdir -p "$golden_root" "$evidence"
  REKORDBOX_PAYLOAD_VARIANT="$variant" \
  REKORDBOX_PAYLOAD_SCOPE="real Rekordbox 7.2.19 adjacent payload parser boundaries" \
  REKORDBOX_PAYLOAD_ASSETS="$assets" \
  REKORDBOX_PAYLOAD_ASSET_MANIFEST="$assets/manifest.json" \
  REKORDBOX_PAYLOAD_SUITE="$suite" \
  REKORDBOX_PAYLOAD_GOLDEN="$golden" \
  REKORDBOX_PAYLOAD_EVIDENCE="$evidence" \
  REKORDBOX_PAYLOAD_CASE_COUNT="$case_count" \
  REKORDBOX_PAYLOAD_SERVICE_COUNT="$service_count" \
    "$script_dir/record_adjacent_payload_success.sh"
}

mapfile -t declarations < <(
  jq -r '.variants[] | [.name, .case_count, .service_count] | @tsv' "$matrix"
)

for declaration in "${declarations[@]}"; do
  IFS=$'\t' read -r variant case_count service_count <<<"$declaration"
  record_variant "$variant" "$case_count" "$service_count"
done

echo "=== adjacent payload parser boundary matrix: complete ==="
