#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly suite_root="$script_dir/suites/generated/song-info-location2-malformed-history-timing"
readonly evidence_root="$lab/data/experiments/song-info-status-location2/malformed-history-timing"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'

restore() {
  local status=$?
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
  return 1
}

mkdir -p "$evidence_root"
mapfile -t suites < <(find "$suite_root" -maxdepth 1 -type f -name '*.json' | sort)

for suite in "${suites[@]}"; do
  variant=$(basename "$suite" .json)
  evidence="$evidence_root/$variant"
  mkdir -p "$evidence"

  for observation in 1 2 3 4; do
    output="$evidence/observation-$observation.json"
    receipt="$evidence/observation-$observation.receipt.json"
    health_before="$evidence/observation-$observation-health-before.json"
    health_after="$evidence/observation-$observation-health-after.json"

    if [[ -f $output && -f $receipt ]]; then
      expected=$(jq -er .observation_sha256 "$receipt")
      actual=$(sha256sum "$output" | cut -d' ' -f1)
      [[ $actual == "$expected" ]]
      echo "=== malformed-history timing $variant observation $observation: receipt exists; skipping ==="
      continue
    fi
    if [[ -f $output || -f $receipt || -f $health_before || -f $health_after ]]; then
      echo "$variant observation $observation has incomplete evidence; inspect it before resuming" >&2
      exit 1
    fi

    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
    started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
    capture_health "location2-malformed-history-timing-$variant-$observation-before" \
      "$started_at" "$health_before"
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$output" record
    capture_health "location2-malformed-history-timing-$variant-$observation-after" \
      "$started_at" "$health_after"

    jq -n \
      --arg variant "$variant" \
      --argjson observation "$observation" \
      --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
      --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
      --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
      --arg observation_sha256 "$(sha256sum "$output" | cut -d' ' -f1)" \
      --arg health_before_sha256 "$(sha256sum "$health_before" | cut -d' ' -f1)" \
      --arg health_after_sha256 "$(sha256sum "$health_after" | cut -d' ' -f1)" \
      '{format:1,variant:$variant,observation:$observation,
        suite_sha256:$suite_sha256,
        fixture_manifest_sha256:$fixture_manifest_sha256,
        identity_sha256:$identity_sha256,
        observation_sha256:$observation_sha256,
        health_before_sha256:$health_before_sha256,
        health_after_sha256:$health_after_sha256}' \
      >"$receipt.next"
    mv "$receipt.next" "$receipt"
  done
done

echo "=== location-2 malformed-history timing study: 28 observations complete ==="
