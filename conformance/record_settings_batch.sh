#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <suite>[:<fixture>] [...]" >&2
  exit 2
fi

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly golden_dir="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"

for specification in "$@"; do
  suite_name="${specification%%:*}"
  fixture_name="${specification#*:}"
  if [[ $fixture_name == "$specification" ]]; then
    fixture_name="$suite_name"
  fi

  fixture="$script_dir/fixtures/generated/$fixture_name"
  suite="$script_dir/suites/generated/$suite_name.json"
  if [[ ! -f $suite ]]; then
    suite="$script_dir/suites/$suite_name.json"
  fi
  golden="$golden_dir/$suite_name.json"

  test -f "$fixture/manifest.json"
  test -f "$suite"
  if [[ -e $golden ]]; then
    echo "refusing to overwrite existing golden: $golden" >&2
    exit 1
  fi

  echo "=== $suite_name using $fixture_name: activate ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  echo "=== $suite_name: launch ==="
  "$script_dir/start_oracle_ui.sh"
  echo "=== $suite_name: record and repeat ==="
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$golden"
done
