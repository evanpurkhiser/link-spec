# Rekordbox UI automation evidence

These screenshots record the UI states used to make real-Rekordbox oracle
activation deterministic. They contain only the isolated Windows guest and
synthetic fixtures.

The noVNC browser screenshot is 1,280 pixels wide. Its 925-pixel guest canvas
begins at screenshot x=178, while noVNC's internal RFB pointer API accepts
guest framebuffer coordinates directly. The visible LINK tile center at
screenshot `(203, 495)` is therefore guest coordinate `(25, 495)`.

`conformance/oracle_record.sh` imports `/app/ui.js` and sends button events
through `UI.rfb._sendMouse`. This avoids browser-to-canvas scaling and offset
errors. The same helper dismisses the Mobile Library Sync dialog using guest
coordinates before clicking LINK. When that dialog is absent, its dismissal
points land in inert track-table cells.

| Screenshot | Evidence |
| --- | --- |
| `link-before-click.png` | Earlier compact LINK source state |
| `link-after-click.png` | Earlier successful activation state |
| `link-loop-live.png` | LINK retry-loop diagnostic |
| `rekordbox-mobile-connect-modal-current.png` | Mobile-device dialog intercepting browser-relative clicks |
| `rekordbox-sync-manager-expanded-current.png` | Expanded Sync Manager changes the apparent source-strip layout |
| `rekordbox-link-tile-guest-coordinate.png` | Current LINK tile used to derive guest coordinate `(25, 495)` |
| `rekordbox-link-rfb-cleanup-race.png` | Expected desktop after the failed batch's EXIT trap stopped Rekordbox |
