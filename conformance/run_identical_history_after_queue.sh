#!/usr/bin/env bash
set -euo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly lab=$(cd -- "$script_dir/.." && pwd)
readonly workspace=$(cd -- "$lab/.." && pwd)
readonly vm="$workspace/rekordbox-windows"
readonly queue_unit=${1:-codex-rekordbox-real-oracle-queue-20261002n.service}
readonly queue_receipt=${REKORDBOX_QUEUE_RECEIPT:-"$lab/data/experiments/real-rekordbox-queue-finalization.json"}
readonly queue_scope=${REKORDBOX_QUEUE_SCOPE:-"real Rekordbox 7.2.19 only"}
readonly history_root="$lab/data/experiments/hot-cue-bank/legacy-identical-request-history"
readonly receipt="$history_root/finalization.json"
queue_observed_active=false

while true; do
  if ! state=$(systemctl --user show "$queue_unit" -p ActiveState --value 2>/dev/null); then
    if [[ $queue_observed_active == true && -f $queue_receipt ]]; then
      break
    fi
    echo "$queue_unit disappeared without a finalization receipt" >&2
    exit 1
  fi

  case "$state" in
    active|activating|reloading|deactivating)
      queue_observed_active=true
      sleep 60
      ;;
    inactive|failed) break ;;
    *) echo "unexpected $queue_unit state: $state" >&2; exit 1 ;;
  esac
done

if systemctl --user show "$queue_unit" -p ActiveState --value >/dev/null 2>&1; then
  result=$(systemctl --user show "$queue_unit" -p Result --value)
  status=$(systemctl --user show "$queue_unit" -p ExecMainStatus --value)
  if [[ $result != success || $status != 0 ]]; then
    echo "queue $queue_unit did not finish successfully; history capture remains pending" >&2
    exit 1
  fi
fi
jq -e --arg queue_scope "$queue_scope" '
  .format == 1 and
  .scope == $queue_scope and
  .focused_tests_passed == true and
  .synthetic_identity_units_active == false and
  .isolated_vm_stopped == true
' "$queue_receipt" >/dev/null

"$script_dir/record_hot_cue_legacy_identical_request_history.sh"
"$lab/.venv/bin/python" \
  "$lab/tools/summarize_hot_cue_legacy_identical_request_history.py"

(
  cd "$script_dir"
  "$lab/.venv/bin/python" -m unittest \
    test_hot_cue_legacy_identical_request_history \
    test_hot_cue_legacy_setter_parser \
    test_hot_cue_legacy_setter_parser_summary \
    test_real_rekordbox_phase_boundary \
    test_corpus_documentation
)

if systemctl --user list-units --state=active --plain --no-legend \
  'rekordbox-identity-*' | grep -q .; then
  echo "synthetic rekordbox identity unit remains active" >&2
  exit 1
fi

"$vm/vmctl" isolated-stop

jq -n \
  --arg completed_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg queue_unit "$queue_unit" \
  --arg queue_finalization_sha256 "$(sha256sum "$queue_receipt" | cut -d' ' -f1)" \
  --arg summary_sha256 "$(sha256sum "$history_root/summary.json" | cut -d' ' -f1)" \
  --arg cycle_1_sha256 "$(sha256sum "$history_root/cycle-1/complete.json" | cut -d' ' -f1)" \
  --arg cycle_2_sha256 "$(sha256sum "$history_root/cycle-2/complete.json" | cut -d' ' -f1)" \
  '{format:1, scope:"real Rekordbox 7.2.19 only",
    completed_at:$completed_at, queue_unit:$queue_unit,
    queue_finalization_sha256:$queue_finalization_sha256,
    summary_sha256:$summary_sha256,
    cycle_receipt_sha256:[$cycle_1_sha256,$cycle_2_sha256],
    focused_tests_passed:true, synthetic_identity_units_active:false,
    isolated_vm_stopped:true}' >"$receipt.next"
mv "$receipt.next" "$receipt"

"$lab/.venv/bin/python" "$lab/tools/update_checksums.py"
echo "=== identical-request history validated and isolated VM stopped ==="
