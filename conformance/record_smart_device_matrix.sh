#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/smart-rule-matrix"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly suite="$script_dir/suites/smart-device-cross.json"

readonly identities=(
  "xdj-rx3:xdj-rx3-player-11.json"
  "cdj-3000:cdj-3000-player-1.json"
  "cdj-2000nxs2:cdj-2000nxs2-player-2.json"
  "xdj-xz:xdj-xz-player-3.json"
  "xdj-az:xdj-az-player-4.json"
  "xdj-1000mk2:xdj-1000mk2-player-5.json"
  "unknown-mixer:unknown-mixer-player-6.json"
  "unknown-djm:unknown-djm-player-6.json"
)

cleanup() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap cleanup EXIT

"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"

for entry in "${identities[@]}"; do
  model=${entry%%:*}
  identity=${entry#*:}
  result="$script_dir/goldens/rekordbox-7.2.19/$model/smart-device-cross.json"
  mkdir -p "$(dirname -- "$result")"
  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$script_dir/runs/$identity" \
    "$result" auto
done
