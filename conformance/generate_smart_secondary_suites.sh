#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/../.." && pwd)
readonly python="$root/rekordbox-windows/.venv/bin/python"

if [[ $# -gt 1 || ($# -eq 1 && $1 != --from-probes) ]]; then
  echo "usage: $0 [--from-probes]" >&2
  exit 2
fi

mapfile -t variants < <(
  find "$script_dir/settings/generated" -maxdepth 1 -type f \
    \( -name 'secondary-*.json' -o -name 'no-secondary-selection.json' \
       -o -name 'multiple-secondary-selections.json' \) \
    -printf '%f\n' | sed 's/\.json$//' | sort
)

for variant in "${variants[@]}"; do
  arguments=(
    "$script_dir/generate_smart_secondary_suite.py" "$variant"
    --output "$script_dir/suites/generated/smart-$variant.json"
  )
  if [[ ${1:-} == --from-probes ]]; then
    arguments+=(
      --oracle "$script_dir/../data/experiments/smart-secondary-columns/probe/smart-$variant.json"
    )
  fi
  "$python" "${arguments[@]}"
done
