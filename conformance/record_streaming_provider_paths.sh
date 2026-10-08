#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)

REKORDBOX_FILELESS_VARIANT=streaming-provider-paths \
REKORDBOX_FILELESS_SCOPE="real Rekordbox 7.2.19 production-shaped streaming provider paths" \
REKORDBOX_FILELESS_FIXTURE="$script_dir/fixtures/generated/streaming-provider-paths" \
REKORDBOX_FILELESS_IDENTITY="$script_dir/runs/xdj-rx3-player-1.json" \
REKORDBOX_FILELESS_SUITE="$script_dir/suites/generated/streaming-provider-paths.json" \
REKORDBOX_FILELESS_GOLDEN="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/streaming-provider-paths.json" \
REKORDBOX_FILELESS_EVIDENCE="$lab/data/experiments/streaming-provider-paths" \
REKORDBOX_FILELESS_CASE_COUNT=7 \
REKORDBOX_FILELESS_SERVICE_COUNT=1 \
"$script_dir/record_adjacent_payload_fileless.sh"
