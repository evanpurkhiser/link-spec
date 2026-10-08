#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly root=$(cd -- "$script_dir/../.." && pwd)
readonly guestctl="$root/rekordbox-link-export-research/guest-control/guestctl"
readonly guest_dir='C:/Users/Research/link-export-conformance'
readonly guest_script="$guest_dir/start-oracle-ui.ps1"
readonly marker="$guest_dir/link-ready.json"

"$guestctl" powershell \
  "New-Item -ItemType Directory -Force -Path '$guest_dir' | Out-Null"
"$guestctl" copy-to "$script_dir/start-oracle-ui.ps1" "$guest_script"
"$guestctl" powershell \
  "Remove-Item -Force -ErrorAction SilentlyContinue '$marker'; \$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File \"$guest_script\"'; \$principal = New-ScheduledTaskPrincipal -UserId 'Research' -LogonType Interactive -RunLevel Limited; Register-ScheduledTask -TaskName 'RekordboxOracleLaunch' -Action \$action -Principal \$principal -Force | Out-Null; Start-ScheduledTask -TaskName 'RekordboxOracleLaunch'; \$deadline = (Get-Date).AddSeconds(120); \$status = \$null; while (\$null -eq \$status -and (Get-Date) -lt \$deadline) { if (Test-Path '$marker') { try { \$candidate = Get-Content -Raw '$marker' | ConvertFrom-Json; if (\$null -ne \$candidate -and \$null -ne \$candidate.success) { \$status = \$candidate } } catch {} }; if (\$null -eq \$status) { Start-Sleep -Milliseconds 500 } }; if (\$null -eq \$status) { throw 'Timed out waiting for a complete interactive rekordbox LINK marker.' }; if (-not \$status.success) { throw \$status.error }; \$status | ConvertTo-Json"

echo 'rekordbox interactive window is ready'
