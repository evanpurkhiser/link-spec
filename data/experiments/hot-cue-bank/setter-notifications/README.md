# Hot Cue Bank setter notification capture

## Established static contract

After a successful legacy or extended Hot Cue Bank setter returns a nonzero
resolved CueID, `PSvDBMain::OnCueBnkCmd` calls
`PSvDBMain::DeliverHCBankUpdate`. The helper invokes the installed delivery
sink with `(class=3, id=CueID, extra=0)` when delivery flag bit 1 is enabled.
The retained disassembly is
`data/static-analysis/hot-cue-bank-notifications.disasm.txt`.

## Protocol boundary

The installed sink is the embedded `UiProDJLink + 0x18` callback. Update class
3 maps to `DatabaseIF::notifyDBUpdated(0x1e, CueID, 0)` inside the Rekordbox
process. The complete installation, virtual dispatch, seven-entry class table,
and terminal application callback are retained in
`data/static-analysis/hot-cue-bank-notification-callback.disasm.txt` and pinned
by `conformance/test_hot_cue_notification_callback.py`.

This callback chain has no Link Export serializer, socket send, or peer
selection. A passive packet capture could observe an absence but could not
establish it; the static call chain closes the server-protocol question. No
capture unit or pcap belongs to the canonical evidence set.
