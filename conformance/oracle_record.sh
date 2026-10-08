#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 5 ]]; then
  echo "usage: $0 <suite.json> <manifest.json> <identity.json> <golden.json> [auto|record|repeat]" >&2
  exit 2
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
conformance="$root/rekordbox-link-export-research/conformance"
vm="$root/rekordbox-windows"
runner=${LINK_EXPORT_CONFORMANCE_BIN:-$conformance/pinned/link-export-conformance}
suite=$(realpath "$1")
manifest=$(realpath "$2")
identity=$(realpath "$3")
golden=$(realpath -m "$4")
phase=${5:-auto}
max_attempts=${REKORDBOX_LINK_MAX_ATTEMPTS:-10}
unit="rekordbox-identity-$(date +%s)"
active_manifest="$root/rekordbox-windows/shared/link-export-conformance/active-guest-manifest.json"
record_log=''

if [[ ! -x $runner ]]; then
  echo "conformance runner is absent or not executable: $runner" >&2
  echo "build it before starting the isolated recording batch" >&2
  exit 1
fi
runner_sha256=$(sha256sum "$runner" | cut -d' ' -f1)
echo "Using conformance runner $runner (SHA-256 $runner_sha256)"

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
repeat_strategy=$(jq -r '.repeat_strategy // "immediate"' "$suite")
expected_database=$(jq -er .database_sha256 "$manifest")
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
test -f "$active_manifest" || {
  echo "guest fixture activation marker is absent: $active_manifest" >&2
  exit 1
}
active_database=$(jq -er .database_sha256 "$active_manifest")
if [[ $active_database != "$expected_database" ]]; then
  echo "active guest fixture is $active_database, expected $expected_database" >&2
  exit 1
fi
if [[ $phase != auto && $phase != record && $phase != repeat ]]; then
  echo "unknown phase: $phase" >&2
  exit 2
fi
if [[ ! $max_attempts =~ ^[1-9][0-9]*$ ]]; then
  echo "REKORDBOX_LINK_MAX_ATTEMPTS must be a positive integer: $max_attempts" >&2
  exit 2
fi
if [[ $phase == auto && $repeat_strategy != immediate ]]; then
  echo "suite requires $repeat_strategy; run phase 'record', reset/restart, then phase 'repeat'" >&2
  exit 2
fi

"$vm/vmctl" isolation-check

close_browser() {
  agent-browser --session rekordbox-windows close >/dev/null 2>&1 || true
}

stop_identity() {
  systemctl --user stop "$unit.service" >/dev/null 2>&1 || true
  close_browser
  if [[ -n $record_log ]]; then
    rm -f "$record_log"
  fi
}
trap stop_identity EXIT

systemd-run --user --collect --unit="$unit" \
  --description="rekordbox synthetic Link Export identity" \
  --working-directory="$conformance" \
  --property=RuntimeMaxSec=15m \
  python "$conformance/identity_adapter.py" \
    --model "$model" --player "$player" --device-type "$device_type" \
    --generation "$generation" --mac "$mac" --address "$address" \
    --broadcast "$broadcast" --source-port "$source_port" --peers "$peers" \
    --presence "$presence" --model-code "$model_code" \
    --status-port "$status_port" "${status_args[@]}" \
    "${peer_args[@]}"

sleep 15

click_link() {
  local console_url='https://18006.prk.network/'
  local current_url

  current_url=$(agent-browser --session rekordbox-windows get url 2>/dev/null || true)
  if [[ $current_url != "$console_url" ]]; then
    agent-browser --session rekordbox-windows open "$console_url" >/dev/null
    agent-browser --session rekordbox-windows wait --load domcontentloaded >/dev/null
    agent-browser --session rekordbox-windows wait 3000 >/dev/null
  fi
  agent-browser --session rekordbox-windows wait 1000 >/dev/null

  rfb_click() {
    local x=$1
    local y=$2
    local attempt

    for attempt in 1 2 3; do
      if agent-browser --session rekordbox-windows eval \
        "(async()=>{const {default:UI}=await import('/app/ui.js'); const r=UI.rfb; r._sendMouse($x,$y,0); r._sendMouse($x,$y,1); await new Promise(done=>setTimeout(done,150)); r._sendMouse($x,$y,0);})()" \
        >/dev/null; then
        return
      fi

      if (( attempt >= 3 )); then
        echo "RFB click at ($x,$y) failed after $attempt attempts" >&2
      fi
      ((attempt < 3)) || return 1
      agent-browser --session rekordbox-windows open "$console_url" >/dev/null
      agent-browser --session rekordbox-windows wait --load domcontentloaded >/dev/null
      agent-browser --session rekordbox-windows wait 2000 >/dev/null
    done
  }

  # Rekordbox Agent can leave an elevated terminal over the main window after
  # its legacy wmic probe fails on Windows 11. This is inert top chrome when
  # the terminal is absent.
  rfb_click 824 52
  agent-browser --session rekordbox-windows wait 500 >/dev/null

  # A first-run Mobile Library Sync prompt intercepts LINK until acknowledged.
  # These points are ordinary track-table cells when the prompt is absent.
  rfb_click 221 419
  rfb_click 462 419
  # Rekordbox 7.2.19 can place the same dialog slightly higher after a relaunch.
  rfb_click 497 389
  agent-browser --session rekordbox-windows wait 500 >/dev/null
  # The noVNC canvas begins 178 screenshot pixels from the left. Sending the
  # event through RFB keeps this coordinate in guest framebuffer space.
  rfb_click 25 495
  agent-browser --session rekordbox-windows wait 8000 >/dev/null
  close_browser
}

activate_link() {
  local attempt

  for attempt in 1 2 3 4 5; do
    if click_link; then
      return
    fi

    echo "LINK UI activation failed; retrying complete browser flow ($attempt/5)." >&2
    close_browser
    ((attempt < 5)) || return 1
    sleep 3
  done
}

record() {
  "$runner" record \
    --host 172.31.96.96 --suite "$suite" --manifest "$manifest" \
    --identity "$identity" --backend rekordbox --backend-version 7.2.19 \
    --golden "$golden"
}

link_is_unavailable() {
  local log=$1

  grep -Eq \
    'Link Export is disabled|port query .* timed out|port query .* failed: Resource temporarily unavailable|dbserver connection .* failed: connection timed out' \
    "$log"
}

activate_link

if [[ $phase == auto || $phase == record ]]; then
  record_log=$(mktemp)
  attempt=1
  while ! record 2>&1 | tee "$record_log"; do
    if ! link_is_unavailable "$record_log"; then
      exit 1
    fi
    if (( attempt >= max_attempts )); then
      echo "LINK remained unavailable after $max_attempts activation attempts." >&2
      exit 1
    fi

    attempt=$((attempt + 1))
    echo "LINK is not ready; retrying activation ($attempt/$max_attempts)." >&2
    sleep 5
    activate_link
  done
  rm -f "$record_log"
  record_log=''
fi

if [[ $phase == auto || $phase == repeat ]]; then
  verify() {
    "$runner" verify \
      --host 172.31.96.96 --suite "$suite" --manifest "$manifest" \
      --identity "$identity" --backend rekordbox-repeat --backend-version 7.2.19 \
      --golden "$golden"
  }

  record_log=$(mktemp)
  attempt=1
  while ! verify 2>&1 | tee "$record_log"; do
    if ! link_is_unavailable "$record_log"; then
      exit 1
    fi
    if (( attempt >= max_attempts )); then
      echo "LINK remained unavailable after $max_attempts verification attempts." >&2
      exit 1
    fi

    attempt=$((attempt + 1))
    echo "LINK is not ready for verification; retrying activation ($attempt/$max_attempts)." >&2
    sleep 5
    activate_link
  done
  rm -f "$record_log"
  record_log=''
fi
