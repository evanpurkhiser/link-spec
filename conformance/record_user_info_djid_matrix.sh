#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/full"
readonly baseline="$script_dir/fixtures/generated/play-paths"
readonly matrix="$script_dir/data/user-info-djid-matrix.json"
readonly profiles="$script_dir/user-info-djid-profiles"
readonly profile_manifest="$profiles/manifest.json"
readonly evidence_root="$lab/data/experiments/user-info-djid"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_health='C:/Users/Research/link-export-conformance/capture-rekordbox-health.ps1'
readonly guest_dir='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6'
readonly guest_nxs="$guest_dir/djprofile.nxs"
readonly guest_alt="$guest_dir/djprofile.bin"
readonly guest_nxs_backup="$guest_dir/djprofile.nxs.link-export-oracle-backup"
readonly guest_alt_backup="$guest_dir/djprofile.bin.link-export-oracle-backup"
original_prepared=false
original_restored=false

capture_profile_state() {
  local label=$1
  local output=$2

  "$guestctl" powershell \
    "\$paths = @(
      [pscustomobject]@{ role = 'nxs'; path = '$guest_nxs' },
      [pscustomobject]@{ role = 'alternate'; path = '$guest_alt' },
      [pscustomobject]@{ role = 'nxs-backup'; path = '$guest_nxs_backup' },
      [pscustomobject]@{ role = 'alternate-backup'; path = '$guest_alt_backup' }
    ); [pscustomobject]@{
      label = '$label';
      entries = @(\$paths | ForEach-Object {
        \$item = Get-Item -LiteralPath \$_.path -Force -ErrorAction SilentlyContinue;
        if (\$null -eq \$item) {
          [pscustomobject]@{ role = \$_.role; exists = \$false; kind = \$null; size = \$null; sha256 = \$null }
        } elseif (\$item.PSIsContainer) {
          [pscustomobject]@{ role = \$_.role; exists = \$true; kind = 'directory'; size = \$null; sha256 = \$null }
        } else {
          [pscustomobject]@{ role = \$_.role; exists = \$true; kind = 'file'; size = \$item.Length; sha256 = (Get-FileHash -LiteralPath \$item.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
        }
      })
    } | ConvertTo-Json -Depth 4" | tr -d '\r' >"$output.next"
  jq -e '.entries | length == 4' "$output.next" >/dev/null
  mv "$output.next" "$output"
}

remove_oracle_paths() {
  "$guestctl" powershell \
    "Remove-Item -LiteralPath '$guest_nxs','$guest_alt' -Recurse -Force -ErrorAction SilentlyContinue; if ((Test-Path -LiteralPath '$guest_nxs') -or (Test-Path -LiteralPath '$guest_alt')) { throw 'DJ-ID oracle profile path remains' }"
}

restore_original_profiles() {
  local current

  remove_oracle_paths
  "$guestctl" powershell \
    "if (Test-Path -LiteralPath '$guest_nxs_backup') { Move-Item -LiteralPath '$guest_nxs_backup' -Destination '$guest_nxs' }; if (Test-Path -LiteralPath '$guest_alt_backup') { Move-Item -LiteralPath '$guest_alt_backup' -Destination '$guest_alt' }; if ((Test-Path -LiteralPath '$guest_nxs_backup') -or (Test-Path -LiteralPath '$guest_alt_backup')) { throw 'DJ-ID backup path remains after restoration' }"
  capture_profile_state restored "$evidence_root/restored-profile-state.json"
  current="$evidence_root/restored-profile-state.json"
  diff -u \
    <(jq -S '[.entries[] | select(.role == "nxs" or .role == "alternate")]' "$evidence_root/original-profile-state.json") \
    <(jq -S '[.entries[] | select(.role == "nxs" or .role == "alternate")]' "$current")
  original_restored=true
}

restore() {
  local status=$?
  local cleanup_status=0

  trap - EXIT
  set +e
  "$script_dir/activate_fixture.sh" "$baseline" || cleanup_status=$?
  if [[ $original_prepared == true && $original_restored != true ]]; then
    restore_original_profiles || cleanup_status=$?
  fi
  if (( status != 0 )); then
    exit "$status"
  fi
  exit "$cleanup_status"
}
trap restore EXIT

prepare_original_profiles() {
  "$script_dir/activate_fixture.sh" "$fixture"
  capture_profile_state original "$evidence_root/original-profile-state.json"
  jq -e '
    all(.entries[] | select(.role | endswith("backup")); .exists == false)
  ' "$evidence_root/original-profile-state.json" >/dev/null
  "$guestctl" powershell \
    "if (Test-Path -LiteralPath '$guest_nxs') { Move-Item -LiteralPath '$guest_nxs' -Destination '$guest_nxs_backup' }; if (Test-Path -LiteralPath '$guest_alt') { Move-Item -LiteralPath '$guest_alt' -Destination '$guest_alt_backup' }"
  original_prepared=true
  capture_profile_state backed-up "$evidence_root/backed-up-profile-state.json"
  jq -e '
    all(.entries[] | select(.role == "nxs" or .role == "alternate"); .exists == false)
  ' "$evidence_root/backed-up-profile-state.json" >/dev/null
}

stage_profile() {
  local profile=$1
  local output=$2
  local filename target expected

  remove_oracle_paths
  case "$profile" in
    absent)
      ;;
    directory-at-target)
      "$guestctl" powershell \
        "New-Item -ItemType Directory -Path '$guest_nxs' -Force | Out-Null"
      ;;
    *)
      filename=$(jq -er --arg profile "$profile" \
        '.profiles[] | select(.id == $profile) | .filename' "$profile_manifest")
      target=$(jq -er --arg profile "$profile" \
        '.profiles[] | select(.id == $profile) | .guest_target' "$profile_manifest")
      if [[ $target == djprofile.nxs ]]; then
        "$guestctl" copy-to "$profiles/$filename" "$guest_nxs"
      else
        [[ $target == djprofile.bin ]]
        "$guestctl" copy-to "$profiles/$filename" "$guest_alt"
      fi
      ;;
  esac

  capture_profile_state "$profile" "$output"
  case "$profile" in
    absent)
      jq -e 'all(.entries[] | select(.role == "nxs" or .role == "alternate"); .exists == false)' "$output" >/dev/null
      ;;
    directory-at-target)
      jq -e '(.entries[] | select(.role == "nxs")) | .kind == "directory"' "$output" >/dev/null
      ;;
    *)
      expected=$(jq -er --arg profile "$profile" \
        '.profiles[] | select(.id == $profile) | .sha256' "$profile_manifest")
      target=$(jq -er --arg profile "$profile" \
        '.profiles[] | select(.id == $profile) | if .guest_target == "djprofile.nxs" then "nxs" else "alternate" end' "$profile_manifest")
      jq -e --arg role "$target" --arg expected "$expected" \
        '(.entries[] | select(.role == $role)) | .kind == "file" and .sha256 == $expected' "$output" >/dev/null
      ;;
  esac
}

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

run_phase() {
  local execution=$1
  local profile=$2
  local suite=$3
  local identity=$4
  local candidate=$5
  local phase=$6
  local evidence=$7
  local started_at

  "$script_dir/activate_fixture.sh" "$fixture"
  stage_profile "$profile" "$evidence/$phase-profile-before.json"
  "$script_dir/start_oracle_ui.sh"
  "$guestctl" copy-to "$script_dir/capture_rekordbox_health.ps1" "$guest_health"
  started_at=$("$guestctl" powershell '[DateTime]::UtcNow.ToString("o")' | tr -d '\r')
  capture_health "user-info-djid-$execution-$phase-before" "$started_at" \
    "$evidence/$phase-health-before.json"
  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$candidate" "$phase"
  capture_health "user-info-djid-$execution-$phase-after" "$started_at" \
    "$evidence/$phase-health-after.json"
  capture_profile_state "$profile-post-$phase" "$evidence/$phase-profile-after.json"
}

write_receipt() {
  local execution=$1
  local profile=$2
  local suite=$3
  local identity=$4
  local golden=$5
  local evidence=$6

  jq -n \
    --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg execution "$execution" \
    --arg profile "$profile" \
    --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
    --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
    --arg profile_manifest_sha256 "$(sha256sum "$profile_manifest" | cut -d' ' -f1)" \
    --arg identity_sha256 "$(sha256sum "$identity" | cut -d' ' -f1)" \
    --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
    --arg record_profile_before_sha256 "$(sha256sum "$evidence/record-profile-before.json" | cut -d' ' -f1)" \
    --arg record_profile_after_sha256 "$(sha256sum "$evidence/record-profile-after.json" | cut -d' ' -f1)" \
    --arg repeat_profile_before_sha256 "$(sha256sum "$evidence/repeat-profile-before.json" | cut -d' ' -f1)" \
    --arg repeat_profile_after_sha256 "$(sha256sum "$evidence/repeat-profile-after.json" | cut -d' ' -f1)" \
    --arg record_health_before_sha256 "$(sha256sum "$evidence/record-health-before.json" | cut -d' ' -f1)" \
    --arg record_health_after_sha256 "$(sha256sum "$evidence/record-health-after.json" | cut -d' ' -f1)" \
    --arg repeat_health_before_sha256 "$(sha256sum "$evidence/repeat-health-before.json" | cut -d' ' -f1)" \
    --arg repeat_health_after_sha256 "$(sha256sum "$evidence/repeat-health-after.json" | cut -d' ' -f1)" \
    '{format:1,scope:"real Rekordbox 7.2.19 user-info/DJ-ID authority",
      completed_at:$completed_at,execution:$execution,profile:$profile,
      suite_sha256:$suite_sha256,
      fixture_manifest_sha256:$fixture_manifest_sha256,
      profile_manifest_sha256:$profile_manifest_sha256,
      identity_sha256:$identity_sha256,golden_sha256:$golden_sha256,
      record_profile_before_sha256:$record_profile_before_sha256,
      record_profile_after_sha256:$record_profile_after_sha256,
      repeat_profile_before_sha256:$repeat_profile_before_sha256,
      repeat_profile_after_sha256:$repeat_profile_after_sha256,
      record_health_before_sha256:$record_health_before_sha256,
      record_health_after_sha256:$record_health_after_sha256,
      repeat_health_before_sha256:$repeat_health_before_sha256,
      repeat_health_after_sha256:$repeat_health_after_sha256,
      exact_repeat:true}' >"$evidence/receipt.json.next"
  mv "$evidence/receipt.json.next" "$evidence/receipt.json"
}

test -f "$matrix"
test -f "$profile_manifest"
mkdir -p "$evidence_root"
prepare_original_profiles

while IFS= read -r encoded; do
  execution=$(printf '%s' "$encoded" | base64 -d | jq -r .id)
  profile=$(printf '%s' "$encoded" | base64 -d | jq -r .profile)
  suite_rel=$(printf '%s' "$encoded" | base64 -d | jq -r .suite)
  identity_rel=$(printf '%s' "$encoded" | base64 -d | jq -r .identity)
  golden_rel=$(printf '%s' "$encoded" | base64 -d | jq -r .golden)
  suite="$script_dir/$suite_rel"
  identity="$script_dir/$identity_rel"
  golden="$script_dir/$golden_rel"
  candidate="$golden.next"
  evidence="$evidence_root/$execution"
  receipt="$evidence/receipt.json"

  test -f "$suite"
  test -f "$identity"
  mkdir -p "$evidence" "$(dirname -- "$golden")"
  if [[ -f $golden && -f $receipt ]]; then
    [[ $(jq -er .golden_sha256 "$receipt") == "$(sha256sum "$golden" | cut -d' ' -f1)" ]]
    echo "=== user info $execution: canonical repeat receipt exists; skipping ==="
    continue
  fi
  if [[ -e $golden || -e $candidate || -e $receipt || -e $receipt.next ]]; then
    echo "user info $execution has incomplete evidence; preserve and inspect it before resuming" >&2
    exit 1
  fi

  echo "=== user info $execution: independent record ==="
  run_phase "$execution" "$profile" "$suite" "$identity" "$candidate" record "$evidence"
  echo "=== user info $execution: fresh-fixture/process repeat ==="
  run_phase "$execution" "$profile" "$suite" "$identity" "$candidate" repeat "$evidence"
  mv "$candidate" "$golden"
  write_receipt "$execution" "$profile" "$suite" "$identity" "$golden" "$evidence"
done < <(jq -r '.executions[] | @base64' "$matrix")

restore_original_profiles
echo "=== real-Rekordbox user-info/DJ-ID matrix recorded and original profile restored ==="
