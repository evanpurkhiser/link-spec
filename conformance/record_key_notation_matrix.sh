#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 1 || (${1:-} != '' && ${1:-} != --resume) ]]; then
  echo "usage: $0 [--resume]" >&2
  exit 2
fi

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly baseline_fixture="$script_dir/fixtures/generated/play-paths"
readonly fixture="$script_dir/fixtures/generated/key-notation"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly preferences="$lab/data/experiments/key-notation/preferences"
readonly guest_settings='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/rekordbox3.settings'
readonly resume=${1:-}

states=(
  classic-normalized
  classic-database
  alphanumeric-normalized
  alphanumeric-database
)

restore() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline_fixture"
  "$lab/guest-control/guestctl" copy-to \
    "$preferences/baseline/rekordbox3.settings" "$guest_settings"
  exit "$status"
}
trap restore EXIT

for state in "${states[@]}"; do
  name="key-notation-$state"
  settings="$preferences/generated/$state.settings"
  suite="$script_dir/suites/generated/$name.json"
  result="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/$name.json"

  test -f "$settings"
  test -f "$suite"
  if [[ -e $result ]]; then
    if [[ $resume == --resume ]]; then
      echo "=== $name: existing recorded-and-repeated result retained ==="
      continue
    fi
    echo "refusing to overwrite existing result: $result" >&2
    exit 1
  fi

  echo "=== $name: activate, set preference, launch, record, repeat ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$lab/guest-control/guestctl" copy-to "$settings" "$guest_settings"
  "$lab/guest-control/guestctl" powershell \
    "[xml]\$s = Get-Content -Raw '$guest_settings'; \$names = 'KeyStringSetting','ShowOriginalKey'; \$s.PROPERTIES.VALUE | Where-Object { \$_.name -in \$names } | Select-Object name,val | ConvertTo-Json"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$result" record

  "$script_dir/activate_fixture.sh" "$fixture"
  "$lab/guest-control/guestctl" copy-to "$settings" "$guest_settings"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$result" repeat
done
