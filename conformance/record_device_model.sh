#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <identity.json> <golden-model-directory> [suite ...]" >&2
  exit 2
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
conformance="$root/rekordbox-link-export-research/conformance"
vm="$root/rekordbox-windows"
identity=$(realpath "$1")
model_directory=$2
shift 2
suites=("$@")
if [[ ${#suites[@]} == 0 ]]; then
  suites=(full legacy)
fi
fixture_profile=${FIXTURE_PROFILE:-full}
manifest="$conformance/fixtures/generated/$fixture_profile/manifest.json"
golden_directory="$conformance/goldens/rekordbox-7.2.19/$model_directory"
active_manifest="$root/rekordbox-windows/shared/link-export-conformance/active-guest-manifest.json"
unit="rekordbox-identity-$(date +%s)"

model=$(jq -er .model "$identity")
player=$(jq -er .player "$identity")
device_type=$(jq -er .device_type "$identity")
generation=$(jq -er .generation "$identity")
mac=$(jq -er .mac "$identity")
address=$(jq -er .address "$identity")
broadcast=$(jq -er .broadcast "$identity")
peer_address=$(jq -r '.peer_address // empty' "$identity")
source_port=$(jq -r '.source_port // 0' "$identity")
status_port=$(jq -r '.status_port // 50002' "$identity")
status_template=$(jq -r '.status_template // "none"' "$identity")
status_packet_hex=$(jq -r '.status_packet_hex_path // empty' "$identity")
peers=$(jq -r '.peers // 0' "$identity")
presence=$(jq -r '.presence // 1' "$identity")
model_code=$(jq -r '.model_code // 100' "$identity")
peer_args=()
if [[ -n $peer_address ]]; then
  peer_args=(--peer-address "$peer_address")
fi
status_args=(--status-template "$status_template")
if [[ -n $status_packet_hex ]]; then
  if [[ $status_packet_hex != /* ]]; then
    status_packet_hex="$conformance/$status_packet_hex"
  fi
  test -f "$status_packet_hex"
  status_args=(--status-packet-hex "$status_packet_hex")
fi

"$vm/vmctl" isolation-check
test -f "$active_manifest"
test "$(jq -er .database_sha256 "$active_manifest")" = \
  "$(jq -er .database_sha256 "$manifest")"
mkdir -p "$golden_directory"

stop_identity() {
  systemctl --user stop "$unit.service" >/dev/null 2>&1 || true
}
trap stop_identity EXIT

systemd-run --user --collect --unit="$unit" \
  --description="rekordbox synthetic device-matrix identity" \
  --working-directory="$conformance" \
  --property=RuntimeMaxSec=20m \
  python "$conformance/identity_adapter.py" \
    --model "$model" --player "$player" --device-type "$device_type" \
    --generation "$generation" --mac "$mac" --address "$address" \
    --broadcast "$broadcast" --source-port "$source_port" --peers "$peers" \
    --presence "$presence" --model-code "$model_code" \
    --status-port "$status_port" "${status_args[@]}" "${peer_args[@]}"

sleep 8
agent-browser --session rekordbox-windows mouse move 205 500 >/dev/null
agent-browser --session rekordbox-windows mouse down >/dev/null
agent-browser --session rekordbox-windows mouse up >/dev/null
agent-browser --session rekordbox-windows wait 3000 >/dev/null

for suite in "${suites[@]}"; do
  suite_path="$conformance/suites/$suite.json"
  golden="$golden_directory/$suite.json"

  python3 "$conformance/protocol_runner.py" record \
    --host 172.31.96.96 --suite "$suite_path" --manifest "$manifest" \
    --identity "$identity" --backend rekordbox --backend-version 7.2.19 \
    --golden "$golden"

  python3 "$conformance/protocol_runner.py" verify \
    --host 172.31.96.96 --suite "$suite_path" --manifest "$manifest" \
    --identity "$identity" --backend rekordbox-repeat \
    --backend-version 7.2.19 --golden "$golden"
done
