#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <int32-max|high-bit|uint32-max>" >&2
  exit 2
fi

readonly probe=$1
case "$probe" in
  int32-max|high-bit|uint32-max) ;;
  *)
    echo "unknown probe: $probe" >&2
    exit 2
    ;;
esac

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-banks"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly suite="$script_dir/suites/hot-cue-bank-count-$probe.json"
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-count-$probe.json"
readonly candidate="$golden.next"
readonly evidence="$lab/data/experiments/hot-cue-bank/count-hazards/$probe"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'

restore() {
  status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

capture_health() {
  local label=$1
  local since=$2
  local output=$3
  local attempt

  for attempt in 1 2 3 4 5; do
    if "$guestctl" powershell \
      "& '$guest_health' -Label '$label' -SinceUtc ([DateTime]::Parse('$since').ToUniversalTime())" \
      >"$output"; then
      return
    fi

    sleep 3
  done

  echo "failed to capture guest health after five attempts" >&2
  return 1
}

run_phase() {
  local phase=$1
  local started_at

  echo "=== Hot Cue Bank count $probe: $phase reset and restart ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "$probe-$phase-before" "$started_at" "$evidence/$phase-before.json"

  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$candidate" "$phase"

  capture_health "$probe-$phase-after" "$started_at" "$evidence/$phase-after.json"
}

test -f "$fixture/manifest.json"
test -f "$identity"
test -f "$suite"
test ! -e "$golden"
test ! -e "$candidate"
mkdir -p "$evidence"

run_phase record
run_phase repeat

mv "$candidate" "$golden"
echo "=== Hot Cue Bank count $probe: promoted ==="
