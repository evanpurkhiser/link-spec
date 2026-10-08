#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/.." && pwd)
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly output="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"
categories=("$@")
if (( ${#categories[@]} == 0 )); then
  categories=(02 03 04 21)
fi
current_unit=''

stop_identity() {
  if [[ -n $current_unit ]]; then
    systemctl --user stop "$current_unit.service" >/dev/null 2>&1 || true
    current_unit=''
  fi
}
trap stop_identity EXIT

record() {
  local fixture=$1
  local golden=$2

  python3 "$script_dir/protocol_runner.py" record \
    --host 172.31.96.96 --suite "$suite" --manifest "$fixture/manifest.json" \
    --identity "$identity" --backend rekordbox --backend-version 7.2.19 \
    --golden "$golden"
}

for category in "${categories[@]}"; do
  profile="category-${category}-disabled"
  fixture="$script_dir/fixtures/generated/$profile"
  suite="$script_dir/suites/generated/search-$profile.json"
  current_unit="rekordbox-identity-search-category-$category"

  systemd-run --user --collect --unit="$current_unit" \
    --description="rekordbox synthetic Search identity" \
    --working-directory="$script_dir" \
    --property=RuntimeMaxSec=15m \
    python "$script_dir/identity_adapter.py" \
      --model XDJ-RX3 --player 11 --device-type type7 --generation 3 \
      --mac 02:00:00:60:00:50 --address 172.31.96.50 \
      --broadcast 172.31.96.255 --peer-address 172.31.96.96 \
      --source-port 0 --peers 1 --presence 2 --model-code 0 \
      --status-port 50002 --status-template none

  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  agent-browser --session rekordbox-windows mouse move 205 507 >/dev/null
  agent-browser --session rekordbox-windows mouse down >/dev/null
  agent-browser --session rekordbox-windows mouse up >/dev/null
  agent-browser --session rekordbox-windows wait 5000 >/dev/null

  golden="$output/search-$profile.json"
  for attempt in 1 2 3; do
    record_log=$(mktemp)
    if record "$fixture" "$golden" 2>&1 | tee "$record_log"; then
      rm -f "$record_log"
      break
    fi

    if (( attempt == 3 )); then
      rm -f "$record_log"
      exit 1
    fi
    if grep -q 'Link Export is disabled' "$record_log"; then
      agent-browser --session rekordbox-windows mouse move 205 507 >/dev/null
      agent-browser --session rekordbox-windows mouse down >/dev/null
      agent-browser --session rekordbox-windows mouse up >/dev/null
    elif ! grep -Eq 'port query .* timed out' "$record_log"; then
      rm -f "$record_log"
      exit 1
    fi
    rm -f "$record_log"
    agent-browser --session rekordbox-windows wait 5000 >/dev/null
  done
  python3 "$script_dir/protocol_runner.py" verify \
    --host 172.31.96.96 --suite "$suite" --manifest "$fixture/manifest.json" \
    --identity "$identity" --backend rekordbox-repeat --backend-version 7.2.19 \
    --golden "$golden"

  stop_identity
done
