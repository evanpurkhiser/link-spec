#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)

REKORDBOX_FILELESS_VARIANT=render-arity-boundaries \
REKORDBOX_FILELESS_SCOPE="real Rekordbox 7.2.19 track render arity boundaries" \
REKORDBOX_FILELESS_FIXTURE="$script_dir/fixtures/generated/full" \
REKORDBOX_FILELESS_IDENTITY="$script_dir/runs/xdj-rx3-player-11.json" \
REKORDBOX_FILELESS_SUITE="$script_dir/suites/generated/render-arity-boundaries.json" \
REKORDBOX_FILELESS_GOLDEN="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/render-arity-boundaries.json" \
REKORDBOX_FILELESS_EVIDENCE="$lab/data/experiments/render-arity-boundaries" \
REKORDBOX_FILELESS_CASE_COUNT=70 \
REKORDBOX_FILELESS_SERVICE_COUNT=1 \
"$script_dir/record_adjacent_payload_fileless.sh"
