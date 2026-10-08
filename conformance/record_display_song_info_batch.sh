#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly golden_dir="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"
suites=(
  display-song-info-render
  display-song-info-pagination
  display-song-info-errors
  display-song-info-legacy
)

if [[ $# -gt 0 ]]; then
  suites=("$@")
fi

for name in "${suites[@]}"; do
  case "$name" in
    display-song-info-boundaries)
      fixture="$script_dir/fixtures/generated/boundaries"
      ;;
    display-song-info-unicode-boundaries)
      fixture="$script_dir/fixtures/generated/unicode-boundaries"
      ;;
    display-song-info-invalid)
      fixture="$script_dir/fixtures/generated/invalid"
      ;;
    display-song-info-strings-254)
      fixture="$script_dir/fixtures/generated/display-strings-254"
      ;;
    display-song-info-strings-255)
      fixture="$script_dir/fixtures/generated/display-strings-255"
      ;;
    display-song-info-strings-256)
      fixture="$script_dir/fixtures/generated/display-strings-256"
      ;;
    display-song-info-strings-unicode-256)
      fixture="$script_dir/fixtures/generated/display-strings-unicode-256"
      ;;
    *)
      fixture="$script_dir/fixtures/generated/full"
      ;;
  esac
  suite="$script_dir/suites/generated/$name.json"
  golden="$golden_dir/$name.json"
  candidate="$golden.next"

  test -f "$fixture/manifest.json"
  test -f "$suite"
  test ! -e "$golden"
  test ! -e "$candidate"

  echo "=== $name: activate ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  echo "=== $name: launch ==="
  "$script_dir/start_oracle_ui.sh"
  echo "=== $name: record and repeat ==="
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$candidate"

  mv "$candidate" "$golden"
  echo "=== $name: promoted ==="
done
