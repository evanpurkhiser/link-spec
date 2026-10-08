#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/../.." && pwd)
readonly python="$root/rekordbox-windows/.venv/bin/python"
readonly source_database="$root/rekordbox-windows/shared/library/master.db"
readonly options='/mnt/documents/multimedia/djing/rekordbox/options.json'

usage() {
  echo "usage: $0 --all | <settings-variant> [...]" >&2
  exit 2
}

if [[ $# -eq 0 ]]; then
  usage
fi

if [[ $1 == --all ]]; then
  [[ $# -eq 1 ]] || usage
  mapfile -t variants < <(
    find "$script_dir/settings/generated" -maxdepth 1 -type f -name '*.json' \
      -printf '%f\n' | sed 's/\.json$//' | sort
  )
  variants+=(category-special-bits custom-colors hidden-selected-comment)
else
  variants=("$@")
fi

for variant in "${variants[@]}"; do
  fixture="$script_dir/fixtures/generated/$variant"
  if [[ -d $fixture ]]; then
    echo "fixture already exists: $variant"
    continue
  fi

  settings="$script_dir/settings/generated/$variant.json"
  if [[ ! -f $settings ]]; then
    settings="$script_dir/settings/$variant.json"
  fi
  if [[ ! -f $settings ]]; then
    echo "settings variant does not exist: $variant" >&2
    exit 1
  fi

  "$python" "$script_dir/build_fixture.py" settings \
    "$source_database" "$options" "$fixture" --settings-file "$settings"
done
