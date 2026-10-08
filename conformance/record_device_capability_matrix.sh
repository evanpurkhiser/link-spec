#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
guestctl="$script_dir/../guest-control/guestctl"

identities=(
  'xdj-rx3-player-11.json:xdj-rx3'
  'cdj-3000-player-1.json:cdj-3000'
  'cdj-2000nxs2-player-2.json:cdj-2000nxs2'
  'xdj-xz-player-3.json:xdj-xz'
  'xdj-az-player-4.json:xdj-az'
  'xdj-1000mk2-player-5.json:xdj-1000mk2'
  'unknown-mixer-player-6.json:unknown-mixer'
  'unknown-djm-player-6.json:unknown-djm'
)

for entry in "${identities[@]}"; do
  identity=${entry%%:*}
  model=${entry#*:}
  golden="$script_dir/goldens/rekordbox-7.2.19/$model/device-capabilities.json"
  if [[ -f $golden ]]; then
    echo "device capability golden already exists for $model; skipping"
    continue
  fi

  echo "recording device capability cross for $model"
  recorded=false
  for attempt in 1 2 3; do
    echo "attempt $attempt for $model"
    "$guestctl" powershell \
      'Get-Process rekordbox -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep -Seconds 2'
    "$script_dir/start_oracle_ui.sh"
    if "$script_dir/record_device_model.sh" \
      "$script_dir/runs/$identity" "$model" device-capabilities; then
      recorded=true
      break
    fi
  done

  if [[ $recorded != true ]]; then
    echo "failed to record device capability cross for $model" >&2
    exit 1
  fi
done
