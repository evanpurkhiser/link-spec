#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly matrix="$script_dir/data/cdj-2000nexus-status-matrix.json"
readonly identity="$script_dir/runs/cdj-2000nexus-player-1-genuine-status.json"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly evidence="$script_dir/../data/experiments/device-status/cdj-2000nexus/repeats"

restore() {
  local status=$?
  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline"
  exit "$status"
}
trap restore EXIT

mapfile -t variants < <(jq -c '.variants[]' "$matrix")
mkdir -p "$evidence"
for variant in "${variants[@]}"; do
  id=$(jq -r .id <<<"$variant")
  fixture_name=$(jq -r .fixture <<<"$variant")
  suite_name=$(jq -r .suite <<<"$variant")
  golden_name=$(jq -r .golden <<<"$variant")
  fixture="$script_dir/fixtures/generated/$fixture_name"
  suite="$script_dir/$suite_name"
  golden="$script_dir/$golden_name"
  candidate="$golden.next"
  receipt="$evidence/$id.json"

  if [[ -f $golden && -f $receipt ]]; then
    echo "=== $id: already complete ==="
    continue
  fi

  test -f "$fixture/manifest.json"
  test -f "$suite"
  mkdir -p "$(dirname -- "$golden")"

  if [[ -f $golden ]]; then
    reference="$golden"
    echo "=== $id: golden exists without repeat receipt; re-verifying ==="
  elif [[ -f $candidate ]]; then
    reference="$candidate"
    echo "=== $id: resuming recorded candidate ==="
  else
    recorded=false
    for attempt in 1 2 3; do
      echo "=== $id: record attempt $attempt ==="
      "$script_dir/activate_fixture.sh" "$fixture"
      "$script_dir/start_oracle_ui.sh"

      if "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
        "$identity" "$candidate" record; then
        recorded=true
        break
      fi

      rm -f "$candidate" "$golden.actual.json"
    done
    [[ $recorded == true ]]
    reference="$candidate"
  fi

  repeated=false
  for attempt in 1 2 3; do
    echo "=== $id: independent repeat attempt $attempt ==="
    "$script_dir/activate_fixture.sh" "$fixture"
    "$script_dir/start_oracle_ui.sh"

    if "$script_dir/oracle_record.sh" "$suite" "$fixture/manifest.json" \
      "$identity" "$reference" repeat; then
      repeated=true
      break
    fi

    rm -f "$reference.actual.json"
  done
  [[ $repeated == true ]]

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
  echo "=== $id: promoted ==="
done

echo "=== genuine CDJ-2000nexus status matrix: complete ==="
