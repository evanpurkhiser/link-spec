#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly golden_dir="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"
category_ids=(1 2 3 4 5 6 7 8 9 10 11 12 15 17 18 19 20 21 22 23 26)

if [[ $# -gt 0 ]]; then
  category_ids=("$@")
fi

for category_id in "${category_ids[@]}"; do
  printf -v name 'category-%02d-disabled' "$category_id"
  fixture="$script_dir/fixtures/generated/$name"
  suite="$script_dir/suites/generated/$name.json"
  golden="$golden_dir/$name.json"
  candidate="$golden.next"

  test -f "$fixture/manifest.json"
  test -f "$suite"
  test -f "$golden"
  test ! -e "$candidate"

  echo "=== $name: activate ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  echo "=== $name: launch ==="
  "$script_dir/start_oracle_ui.sh"
  echo "=== $name: record and repeat ==="
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$candidate"

  if ! diff -u \
    <(jq -S '.behavior.cases[] | select(.id == "root")' "$golden") \
    <(jq -S '.behavior.cases[] | select(.id == "root")' "$candidate"); then
    echo "root behavior changed; retained candidate for inspection: $candidate" >&2
    exit 1
  fi

  mv "$candidate" "$golden"
  echo "=== $name: promoted ==="
done
