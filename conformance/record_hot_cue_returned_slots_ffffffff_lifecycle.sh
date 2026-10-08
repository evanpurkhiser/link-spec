#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec "$script_dir/record_hot_cue_slot_8_lifecycle.sh" returned-slots-ffffffff
