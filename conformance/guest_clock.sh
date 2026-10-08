#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly guestctl="$script_dir/../guest-control/guestctl"

usage() {
  echo "usage: $0 {show|set YYYY-MM-DDTHH:MM:SS|restore}" >&2
  exit 2
}

case "${1:-}" in
  show)
    "$guestctl" powershell "Get-Date -Format o; (Get-TimeZone).Id"
    ;;
  set)
    [[ $# -eq 2 && $2 =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]] || usage
    "$guestctl" powershell \
      "Stop-Service W32Time -Force; Set-Date -Date ([datetime]'$2') | Out-Null; Get-Date -Format o; (Get-TimeZone).Id"
    ;;
  restore)
    [[ $# -eq 1 ]] || usage
    host_time=$(date '+%Y-%m-%dT%H:%M:%S')
    "$guestctl" powershell \
      "Set-Date -Date ([datetime]'$host_time') | Out-Null; Start-Service W32Time; Get-Date -Format o; (Get-TimeZone).Id"
    ;;
  *)
    usage
    ;;
esac
