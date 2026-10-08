#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 || ($1 != probe && $1 != golden) || (${2:-} != '' && ${2:-} != --resume) ]]; then
  echo "usage: $0 probe|golden [--resume]" >&2
  exit 2
fi

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly mode=$1
readonly resume=${2:-}

mapfile -t variants < <(
  find "$script_dir/settings/generated" -maxdepth 1 -type f \
    \( -name 'secondary-*.json' -o -name 'no-secondary-selection.json' \
       -o -name 'multiple-secondary-selections.json' \) \
    -printf '%f\n' | sed 's/\.json$//' | sort
)

cleanup() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap cleanup EXIT

for variant in "${variants[@]}"; do
  name="smart-$variant"
  fixture="$script_dir/fixtures/generated/$name"
  suite="$script_dir/suites/generated/$name.json"
  if [[ $mode == probe ]]; then
    result="$lab/data/experiments/smart-secondary-columns/probe/$name.json"
  else
    result="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/$name.json"
  fi

  test -f "$fixture/manifest.json"
  test -f "$suite"
  if [[ -e $result ]]; then
    if [[ $mode == probe || $resume == --resume ]]; then
      echo "=== $name: existing recorded-and-repeated result retained ==="
      continue
    fi
    echo "refusing to overwrite existing result: $result" >&2
    exit 1
  fi

  mkdir -p "$(dirname -- "$result")"
  echo "=== $name: activate, launch, record, repeat ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$result" auto
done
