#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 1 || (${1:-} != '' && ${1:-} != --resume) ]]; then
  echo "usage: $0 [--resume]" >&2
  exit 2
fi

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly fixture="$script_dir/fixtures/generated/link-visibility"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly suite="$script_dir/suites/generated/link-visibility.json"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/link-visibility.json"
readonly resume=${1:-}

restore() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

if [[ -e $golden ]]; then
  if [[ $resume == --resume ]]; then
    echo "=== link-visibility: existing recorded-and-repeated result retained ==="
    exit 0
  fi
  echo "refusing to overwrite existing result: $golden" >&2
  exit 1
fi

echo "=== link-visibility: activate, launch, record ==="
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
"$script_dir/oracle_record.sh" \
  "$suite" "$fixture/manifest.json" "$identity" "$golden" record

echo "=== link-visibility: reset, relaunch, repeat ==="
"$script_dir/activate_fixture.sh" "$fixture"
"$script_dir/start_oracle_ui.sh"
"$script_dir/oracle_record.sh" \
  "$suite" "$fixture/manifest.json" "$identity" "$golden" repeat
