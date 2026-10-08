#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly fixture="$script_dir/fixtures/generated/cloud-sync-zero"
readonly baseline_fixture="$script_dir/fixtures/generated/play-paths"
readonly identity="$script_dir/runs/xdj-rx3-player-1.json"
readonly suite="$script_dir/suites/generated/song-info-cloud-sync-zero.json"
readonly golden="$script_dir/goldens/rekordbox-7.2.19/xdj-rx3/song-info-cloud-sync-zero.json"
readonly candidate="$golden.next"
readonly evidence="$lab/data/experiments/song-info-cloud-sync-zero"
readonly guestctl="$lab/guest-control/guestctl"
readonly guest_settings='C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/rekordbox3.settings'
readonly guest_root='C:/Users/Research/link-export-conformance/cloud-sync-zero'
readonly moved_root='C:/Users/Research/link-export-conformance/moved-from-cloud'
readonly baseline_settings="$evidence/guest-baseline-rekordbox3.settings"
readonly baseline_state="$evidence/guest-baseline-rekordbox3.settings.json"
restored=false

snapshot_settings() {
  local sha256

  "$guestctl" copy-from "$guest_settings" "$baseline_settings"
  sha256=$(sha256sum "$baseline_settings" | cut -d' ' -f1)
  jq -n --arg guest_path "$guest_settings" --arg sha256 "$sha256" \
    '{format:1,guest_path:$guest_path,exists:true,sha256:$sha256}' >"$baseline_state"
}

restore_settings() {
  local expected actual

  expected=$(jq -er .sha256 "$baseline_state")
  [[ $(sha256sum "$baseline_settings" | cut -d' ' -f1) == "$expected" ]]
  "$guestctl" copy-to "$baseline_settings" "$guest_settings"
  actual=$("$guestctl" powershell \
    "(Get-FileHash -Algorithm SHA256 -LiteralPath '$guest_settings').Hash.ToLowerInvariant()" \
    | tr -d '\r[:space:]')
  [[ $actual == "$expected" ]]
}

restore() {
  local status=$?

  trap - EXIT
  set +e
  if [[ $restored != true && -f $baseline_state ]]; then
    "$script_dir/activate_fixture.sh" "$baseline_fixture"
    restore_settings
  fi
  exit "$status"
}
trap restore EXIT

prepare_phase() {
  local phase=$1

  "$script_dir/activate_fixture.sh" "$fixture"
  "$guestctl" copy-to "$baseline_settings" "$guest_settings"
  "$guestctl" powershell \
    "[xml]\$s = Get-Content -Raw -LiteralPath '$guest_settings'; \$sync = @(\$s.PROPERTIES.VALUE | Where-Object { \$_.name -eq 'CLSSyncMethod' }); if (\$sync.Count -ne 1) { throw 'expected one CLSSyncMethod value' }; \$sync[0].val = '0'; \$moved = @(\$s.PROPERTIES.VALUE | Where-Object { \$_.name -eq 'MovedFromCloudDir' }); if (\$moved.Count -eq 0) { \$node = \$s.CreateElement('VALUE'); \$node.SetAttribute('name', 'MovedFromCloudDir'); \$node.SetAttribute('val', '$moved_root'); [void]\$s.PROPERTIES.AppendChild(\$node) } elseif (\$moved.Count -eq 1) { \$moved[0].val = '$moved_root' } else { throw 'multiple MovedFromCloudDir values' }; \$s.Save('$guest_settings')"
  "$guestctl" powershell \
    "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '$guest_root','$moved_root'; New-Item -ItemType Directory -Force -Path '$guest_root/org-existing-dir','$moved_root' | Out-Null; [IO.File]::WriteAllBytes('$guest_root/org-existing.bin',[Text.Encoding]::ASCII.GetBytes('cloud-sync-zero-original')); [IO.File]::WriteAllBytes('$moved_root/moved-existing.bin',[Text.Encoding]::ASCII.GetBytes('cloud-sync-zero-moved')); [IO.File]::WriteAllBytes('$moved_root/moved-service-five.bin',[Text.Encoding]::ASCII.GetBytes('cloud-sync-zero-service-five'))"
  "$guestctl" powershell \
    "[xml]\$s = Get-Content -Raw -LiteralPath '$guest_settings'; @('CLSSyncMethod','MovedFromCloudDir') | ForEach-Object { \$name = \$_; \$node = @(\$s.PROPERTIES.VALUE | Where-Object { \$_.name -eq \$name }); [ordered]@{name=\$name;count=\$node.Count;value=if (\$node.Count -eq 1) {[string]\$node[0].val} else {\$null}} } | ConvertTo-Json" \
    >"$evidence/$phase-settings.json"
  jq -e '
    length == 2 and
    .[0] == {name:"CLSSyncMethod",count:1,value:"0"} and
    .[1].name == "MovedFromCloudDir" and .[1].count == 1 and
    .[1].value == "C:/Users/Research/link-export-conformance/moved-from-cloud"
  ' "$evidence/$phase-settings.json" >/dev/null
}

mkdir -p "$evidence"
test -f "$fixture/manifest.json"
test -f "$suite"
test -f "$identity"
test ! -e "$golden"
test ! -e "$candidate"
test ! -e "$baseline_state"
snapshot_settings

for phase in record repeat; do
  prepare_phase "$phase"
  "$script_dir/start_oracle_ui.sh"
  "$script_dir/oracle_record.sh" \
    "$suite" "$fixture/manifest.json" "$identity" "$candidate" "$phase"
done

mv "$candidate" "$golden"
"$script_dir/activate_fixture.sh" "$baseline_fixture"
restore_settings
restored=true

jq -n \
  --arg recorded_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg golden_sha256 "$(sha256sum "$golden" | cut -d' ' -f1)" \
  --arg suite_sha256 "$(sha256sum "$suite" | cut -d' ' -f1)" \
  --arg fixture_manifest_sha256 "$(sha256sum "$fixture/manifest.json" | cut -d' ' -f1)" \
  --arg baseline_settings_sha256 "$(jq -er .sha256 "$baseline_state")" \
  --arg record_settings_sha256 "$(sha256sum "$evidence/record-settings.json" | cut -d' ' -f1)" \
  --arg repeat_settings_sha256 "$(sha256sum "$evidence/repeat-settings.json" | cut -d' ' -f1)" \
  '{format:1,scope:"real Rekordbox 7.2.19 Play Song Info CLSSyncMethod zero",
    recorded_at:$recorded_at,case_count:10,record_repeat_execution_count:20,
    golden_sha256:$golden_sha256,suite_sha256:$suite_sha256,
    fixture_manifest_sha256:$fixture_manifest_sha256,
    baseline_settings_sha256:$baseline_settings_sha256,
    record_settings_sha256:$record_settings_sha256,
    repeat_settings_sha256:$repeat_settings_sha256,
    original_settings_restored:true}' >"$evidence/receipt.json"

echo "=== Play Song Info CLSSyncMethod=0 golden promoted and guest settings restored ==="
