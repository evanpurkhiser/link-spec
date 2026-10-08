#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly declaration="$script_dir/data/xdj-rr-location9-matrix.json"
readonly fixture="$script_dir/fixtures/generated/full"

mapfile -t declarations < <(
  jq -r '.variants[] | [.id, .suite, .identity, .golden, .evidence] | @tsv' \
    "$declaration"
)

for declaration_row in "${declarations[@]}"; do
  IFS=$'\t' read -r variant suite_relative identity_relative golden_relative evidence_relative \
    <<<"$declaration_row"
  suite="$script_dir/$suite_relative"
  identity="$script_dir/$identity_relative"
  golden="$script_dir/$golden_relative"
  evidence="$script_dir/$evidence_relative"
  mkdir -p "$(dirname -- "$golden")" "$evidence"

  REKORDBOX_FILELESS_VARIANT="xdj-rr-location9-$variant" \
  REKORDBOX_FILELESS_SCOPE="real Rekordbox 7.2.19 XDJ-RR source-defined location-9 Delivery matrix" \
  REKORDBOX_FILELESS_FIXTURE="$fixture" \
  REKORDBOX_FILELESS_IDENTITY="$identity" \
  REKORDBOX_FILELESS_SUITE="$suite" \
  REKORDBOX_FILELESS_GOLDEN="$golden" \
  REKORDBOX_FILELESS_EVIDENCE="$evidence" \
  REKORDBOX_FILELESS_CASE_COUNT=6 \
  REKORDBOX_FILELESS_SERVICE_COUNT=1 \
  "$script_dir/record_adjacent_payload_fileless.sh"
done

echo "=== XDJ-RR source-defined location-9 Delivery matrix: complete ==="
