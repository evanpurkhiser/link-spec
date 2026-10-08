#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/../.." && pwd)
readonly python="$root/rekordbox-windows/.venv/bin/python"
readonly source_database="$root/rekordbox-windows/shared/library/master.db"
readonly options='/mnt/documents/multimedia/djing/rekordbox/options.json'

mapfile -t variants < <(
  find "$script_dir/settings/generated" -maxdepth 1 -type f \
    \( -name 'secondary-*.json' -o -name 'no-secondary-selection.json' \
       -o -name 'multiple-secondary-selections.json' \) \
    -printf '%f\n' | sed 's/\.json$//' | sort
)

for variant in "${variants[@]}"; do
  fixture="$script_dir/fixtures/generated/smart-$variant"
  if [[ -d $fixture ]]; then
    echo "fixture already exists: smart-$variant"
    continue
  fi

  "$python" "$script_dir/build_fixture.py" smart-settings \
    "$source_database" "$options" "$fixture" \
    --settings-file "$script_dir/settings/generated/$variant.json"
done
