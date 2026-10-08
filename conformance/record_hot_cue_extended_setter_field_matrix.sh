#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly root=$(cd -- "$lab/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/hot-cue-bank-mutation-duplicate-slot"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-11-status.json"
readonly matrix="$script_dir/data/hot-cue-setter-field-matrix.json"
readonly evidence_root="$lab/data/experiments/hot-cue-bank/extended-setter-fields/repeats"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_database='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox/master.db'
readonly options='/mnt/documents/multimedia/djing/rekordbox/options.json'
readonly python="$root/rekordbox-windows/.venv/bin/python"

restore() {
  local status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

copy_optional() {
  local guest_path=$1
  local host_path=$2

  if [[ $("$guestctl" powershell "[bool](Test-Path '$guest_path')" | tr -d '\r') == True ]]; then
    "$guestctl" copy-from "$guest_path" "$host_path"
  fi
}

capture_database_snapshot() (
  local output=$1
  local temporary

  temporary=$(mktemp -d)
  trap 'rm -rf "$temporary"' EXIT
  "$guestctl" copy-from "$guest_database" "$temporary/master.db"
  copy_optional "${guest_database}-wal" "$temporary/master.db-wal"
  copy_optional "${guest_database}-shm" "$temporary/master.db-shm"
  "$python" "$lab/tools/snapshot_hot_cue_mutation.py" \
    "$temporary/master.db" "$options" "$output"
)

write_receipt() {
  local variant=$1
  local suite=$2
  local golden=$3
  local evidence=$4

  jq -n \
    --arg variant "$variant" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --arg record_snapshot_sha256 "$(sha256sum "$evidence/record-snapshot.json" | cut -d' ' -f1)" \
    --arg repeat_snapshot_sha256 "$(sha256sum "$evidence/repeat-snapshot.json" | cut -d' ' -f1)" \
    '{format:1, variant:$variant, backend:"rekordbox", backend_version:"7.2.19",
      suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      identity_sha256:$identity_sha256,
      golden_sha256:$golden_sha256,
      record_snapshot_sha256:$record_snapshot_sha256,
      repeat_snapshot_sha256:$repeat_snapshot_sha256}' \
    >"$evidence/receipt.json.next"
  mv "$evidence/receipt.json.next" "$evidence/receipt.json"
}

mapfile -t variants < <(jq -r '.variants[].id' "$matrix")
if [[ $# -gt 0 ]]; then
  variants=("$@")
fi

for variant in "${variants[@]}"; do
  suite="$script_dir/suites/generated/hot-cue-setter-fields/hot-cue-setter-field-$variant.json"
  golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3-status/hot-cue-setter-field-$variant.json"
  candidate="$golden.next"
  evidence="$evidence_root/$variant"
  recorded=false

  test -f "$suite"
  if [[ -f $golden && -f $evidence/receipt.json ]]; then
    echo "=== $variant: canonical golden and database receipt already exist; skipping ==="
    continue
  fi
  mkdir -p "$evidence"

  if [[ -f $golden ]]; then
    echo "=== $variant: backfill record database proof ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$golden" repeat
    capture_database_snapshot "$evidence/record-snapshot.json"

    echo "=== $variant: backfill repeat database proof ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"
    "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$golden" repeat
    capture_database_snapshot "$evidence/repeat-snapshot.json"
    write_receipt "$variant" "$suite" "$golden" "$evidence"
    continue
  fi

  if [[ -f $candidate && ! -f $evidence/record-snapshot.json ]]; then
    echo "=== $variant: discarding candidate without its record database proof ==="
    rm -f "$candidate" "$golden.actual.json"
  fi
  if [[ ! -f $candidate && -f $evidence/record-snapshot.json ]]; then
    echo "=== $variant: discarding record database proof without its candidate ==="
    rm -f "$evidence/record-snapshot.json"
  fi

  if [[ -f $candidate && -f $evidence/record-snapshot.json ]]; then
    echo "=== $variant: resuming recorded candidate and database proof ==="
    recorded=true
  else
    test ! -e "$candidate"
    test ! -e "$evidence/record-snapshot.json"
    for attempt in 1 2 3; do
      echo "=== $variant: record attempt $attempt ==="
      "$script_dir/activate_fixture.sh" "$fixture"
      "$script_dir/start_oracle_ui.sh"

      if "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
        "$identity" "$candidate" record; then
        capture_database_snapshot "$evidence/record-snapshot.json"
        recorded=true
        break
      fi

      rm -f "$candidate" "$golden.actual.json"
    done
  fi
  [[ $recorded == true ]]

  echo "=== $variant: independent fixture-reset repeat ==="
  "$script_dir/activate_fixture.sh" "$fixture"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
    "$identity" "$candidate" repeat
  capture_database_snapshot "$evidence/repeat-snapshot.json"

  mv "$candidate" "$golden"
  write_receipt "$variant" "$suite" "$golden" "$evidence"
  echo "=== $variant: promoted ==="
done

echo "=== Extended Hot Cue mutable-field matrix: complete ==="
