#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 1 || (${1:-} != '' && ${1:-} != --resume) ]]; then
  echo "usage: $0 [--resume]" >&2
  exit 2
fi

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly baseline_fixture="$script_dir/fixtures/generated/play-paths"
readonly key_fixture="$script_dir/fixtures/generated/key-notation"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly settings="$lab/data/experiments/key-notation/device-settings"
readonly guest_setting='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/DEVSETTING.DAT'
readonly resume=${1:-}

states=(classic alphanumeric)

restore() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline_fixture"
  "$lab/guest-control/guestctl" copy-to \
    "$settings/baseline/DEVSETTING.DAT" "$guest_setting"
  exit "$status"
}
trap restore EXIT

for state in "${states[@]}"; do
  name="key-device-setting-$state"
  setting="$settings/generated/$state.DAT"
  suite="$script_dir/suites/generated/$name.json"
  result="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/$name.json"

  test -f "$setting"
  test -f "$suite"
  if [[ -e $result ]]; then
    if [[ $resume == --resume ]]; then
      echo "=== $name: existing recorded-and-repeated result retained ==="
      continue
    fi
    echo "refusing to overwrite existing result: $result" >&2
    exit 1
  fi

  echo "=== $name: activate, set local device style, launch, record, repeat ==="
  "$script_dir/activate_fixture.sh" "$key_fixture"
  "$lab/guest-control/guestctl" copy-to "$setting" "$guest_setting"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" \
    "$suite" "$key_fixture/manifest.json" "$identity" "$result" record

  "$script_dir/activate_fixture.sh" "$key_fixture"
  "$lab/guest-control/guestctl" copy-to "$setting" "$guest_setting"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" \
    "$suite" "$key_fixture/manifest.json" "$identity" "$result" repeat
done

for name in \
  device-key-style-alphanumeric-secondary-bpm \
  device-key-style-alphanumeric-smart-secondary-bpm; do
  if [[ $name == *-smart-* ]]; then
    bpm_fixture="$script_dir/fixtures/generated/smart-secondary-bpm"
  else
    bpm_fixture="$script_dir/fixtures/generated/secondary-bpm"
  fi
  suite="$script_dir/suites/generated/$name.json"
  result="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/$name.json"

  if [[ -e $result ]]; then
    if [[ $resume == --resume ]]; then
      echo "=== $name: existing recorded-and-repeated result retained ==="
      continue
    fi
    echo "refusing to overwrite existing result: $result" >&2
    exit 1
  fi

  echo "=== $name: activate persisted BPM, set Alphanumeric, record, repeat ==="
  "$script_dir/activate_fixture.sh" "$bpm_fixture"
  "$lab/guest-control/guestctl" copy-to \
    "$settings/generated/alphanumeric.DAT" "$guest_setting"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" \
    "$suite" "$bpm_fixture/manifest.json" "$identity" "$result" record

  "$script_dir/activate_fixture.sh" "$bpm_fixture"
  "$lab/guest-control/guestctl" copy-to \
    "$settings/generated/alphanumeric.DAT" "$guest_setting"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" \
    "$suite" "$bpm_fixture/manifest.json" "$identity" "$result" repeat
done
