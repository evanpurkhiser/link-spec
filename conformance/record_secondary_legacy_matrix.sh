#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly identity="$script_dir/runs/xdj-rx3-player-11.json"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly golden_dir="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3"
readonly receipts="$lab/data/experiments/secondary-column-legacy/repeats"
readonly variants=(
  artist album bpm rating genre comment time remixer label original-artist key
  bitrate color play-count date-added
)

restore() {
  local status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

mkdir -p "$receipts"
for variant in "${variants[@]}"; do
  id="secondary-$variant-legacy"
  fixture="$script_dir/fixtures/generated/secondary-$variant"
  suite="$script_dir/suites/generated/$id.json"
  golden="$golden_dir/$id.json"
  candidate="$golden.next"
  receipt="$receipts/$id.json"

  if [[ -f $golden && -f $receipt ]]; then
    echo "=== $id: already complete ==="
    continue
  fi

  test -f "$fixture/manifest.json"
  test -f "$suite"

  if [[ -f $golden ]]; then
    reference="$golden"
    echo "=== $id: golden exists without receipt; re-verifying ==="
  elif [[ -f $candidate ]]; then
    reference="$candidate"
    echo "=== $id: resuming recorded candidate ==="
  else
    echo "=== $id: independent record ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$candidate" record
    reference="$candidate"
  fi

  echo "=== $id: independent fixture-reset repeat ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$reference" repeat

  if [[ $reference == "$candidate" ]]; then
    mv "$candidate" "$golden"
  fi
  jq -n \
    --arg id "$id" \
    --arg verified_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    '{format:1, id:$id, repeat_verified:true, verified_at:$verified_at,
      suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256,
      golden_sha256:$golden_sha256}' >"$receipt.next"
  mv "$receipt.next" "$receipt"
done

echo "=== persisted secondary-column legacy matrix: complete ==="
