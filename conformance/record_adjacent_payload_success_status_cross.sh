#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly suite_root="$script_dir/suites/generated/adjacent-payload-success-status"
readonly golden_root="$script_dir/goldens/rekordbox-7.2.19"
readonly evidence_root="$lab/data/experiments/adjacent-payload/success-status"

record_variant() {
  local variant=$1
  local model=$2
  local player=$3
  local setup=$4
  local identity

  case "$player" in
    1) identity="$script_dir/runs/cdj-3000-player-1-status.json" ;;
    11) identity="$script_dir/runs/xdj-rx3-player-11-status.json" ;;
    *) echo "unsupported status player: $player" >&2; return 1 ;;
  esac

  mkdir -p "$golden_root/$model" "$evidence_root/$variant"
  REKORDBOX_PAYLOAD_VARIANT="$variant" \
  REKORDBOX_PAYLOAD_SCOPE="real Rekordbox 7.2.19 adjacent payload status/setup success" \
  REKORDBOX_PAYLOAD_IDENTITY="$identity" \
  REKORDBOX_PAYLOAD_SUITE="$suite_root/player-$player-$setup.json" \
  REKORDBOX_PAYLOAD_GOLDEN="$golden_root/$model/adjacent-payload-success-$setup.json" \
  REKORDBOX_PAYLOAD_EVIDENCE="$evidence_root/$variant" \
    "$script_dir/record_adjacent_payload_success.sh"
}

record_variant cdj-3000-player-1-extended cdj-3000-status 1 extended
record_variant cdj-3000-player-1-legacy cdj-3000-status 1 legacy
record_variant xdj-rx3-player-11-extended xdj-rx3-status 11 extended
record_variant xdj-rx3-player-11-legacy xdj-rx3-status 11 legacy

echo "=== adjacent payload successful status/setup cross: complete ==="
