# Device predicate direct-reference audit

This generated report inventories direct x86-64 callers of every selected
Pro DJ Link identity, model, capability, and row-compatibility helper that
can plausibly affect Link Export. The JSON companion preserves every call site.

Binary SHA-256: `07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244`.
Targets: 23; validated direct references: 67; database-serving references: 5.

| Helper | Group | Direct refs | DB-serving refs |
| --- | --- | ---: | ---: |
| `receive-link-member-inner` (`0x1003dd5f0`) | identity-ingress | 1 | 0 |
| `detect-link-device-inner` (`0x1003df6d0`) | identity-ingress | 1 | 0 |
| `receive-link-member` (`0x100ca8180`) | identity-ingress | 0 | 0 |
| `add-link-device` (`0x1020581b0`) | identity-ingress | 2 | 0 |
| `get-member-info-inner` (`0x1003e1110`) | identity-accessor | 0 | 0 |
| `get-member-info-proxy` (`0x100e39700`) | identity-accessor | 1 | 0 |
| `get-model-name-inner` (`0x1003dcd70`) | model-accessor | 0 | 0 |
| `get-model-name-inner-buffer` (`0x1003dcdb0`) | model-accessor | 0 | 0 |
| `get-model-name-network` (`0x101db4dd0`) | model-accessor | 1 | 0 |
| `get-model-name-network-buffer` (`0x101db4a40`) | model-accessor | 1 | 0 |
| `get-model-name-interval` (`0x100b76280`) | model-accessor | 1 | 0 |
| `get-model-name-interval-buffer` (`0x100b76310`) | model-accessor | 3 | 0 |
| `get-model-name` (`0x100ca9500`) | model-accessor | 4 | 2 |
| `get-model-names` (`0x100ca93f0`) | model-accessor | 2 | 0 |
| `is-specific-model` (`0x100ca9380`) | model-predicate | 35 | 0 |
| `is-cdj-network` (`0x100ca72b0`) | model-predicate | 5 | 0 |
| `is-aio` (`0x102521e80`) | database-serving-predicate | 1 | 1 |
| `clear-aio-map` (`0x102520860`) | database-serving-lifecycle | 1 | 1 |
| `new-cdj-supported` (`0x102256b20`) | row-compatibility-predicate | 1 | 1 |
| `support-my-setting` (`0x100b76530`) | device-setting-predicate | 2 | 0 |
| `support-duplication-v2` (`0x100b76580`) | device-setting-predicate | 2 | 0 |
| `support-device-setting` (`0x100b765d0`) | device-setting-predicate | 2 | 0 |
| `set-deck-aio` (`0x10019bad0`) | drag-drop-output | 1 | 0 |

## Database-serving references

- `get-model-name` <- `__ZN9PSvDBMain5isAIOEh` at `0x102521f3c` (call).
- `get-model-name` <- `__ZN9PSvDBMain5isAIOEh` at `0x102521f86` (call).
- `is-aio` <- `__ZN14PSvAppSyncDBIF14getDispSongInfEhjj` at `0x1016c0650` (call).
- `clear-aio-map` <- `__ZN9PSvDBMain10DisconnectEh` at `0x102520838` (call).
- `new-cdj-supported` <- `__ZN9PSvDBMain20GetListBufRowContentEhh17ENUM_CATEGORYKINDPvPmbjP18RetListBufParamExt` at `0x100fa0252` (call).

## Caller scopes

- `receive-link-member-inner`: link-plumbing=1. Parses the link-member payload before notifying ProDJLink.
- `detect-link-device-inner`: link-plumbing=1. Notifies the application that a link device is available.
- `receive-link-member`: none. Carries the decoded device type into LinkDeviceManager.
- `add-link-device`: link-plumbing=2. Stores device type and presence state for a discovered peer.
- `get-member-info-inner`: none. Network-layer member timing and flag accessor.
- `get-member-info-proxy`: link-plumbing=1. Proxy member-state accessor used during link-member receipt.
- `get-model-name-inner`: none. Network-layer model-name accessor.
- `get-model-name-inner-buffer`: none. Network-layer buffer model-name accessor.
- `get-model-name-network`: link-plumbing=1. Link-network model-name wrapper.
- `get-model-name-network-buffer`: link-plumbing=1. Link-network buffer model-name wrapper.
- `get-model-name-interval`: link-plumbing=1. Keepalive-state model-name accessor.
- `get-model-name-interval-buffer`: link-plumbing=3. Keepalive-state buffer model-name accessor.
- `get-model-name`: application-ui=2, database-serving=2. Application-facing model-name accessor.
- `get-model-names`: application-ui=2. Enumerates model names for application UI.
- `is-specific-model`: application-ui=35. Compares one player's model name with a literal model.
- `is-cdj-network`: application-ui=5. Reports whether the connected network has a CDJ-class peer.
- `is-aio`: database-serving=1. Caches an XDJ-prefix classification used by Display Song Info.
- `clear-aio-map`: database-serving=1. Clears a player's cached AIO classification on disconnect.
- `new-cdj-supported`: database-serving=1. Computes per-track compatibility state consumed by track rows.
- `support-my-setting`: link-plumbing=2. Gates My Settings network messages.
- `support-duplication-v2`: link-plumbing=2. Gates My Settings duplication version 2.
- `support-device-setting`: link-plumbing=2. Gates device-setting network messages.
- `set-deck-aio`: link-plumbing=1. Serializes the AIO deck form for drag-and-drop play.

## Boundary

This scan proves direct references in the pinned x86-64 text slice. It does
not exclude indirect calls, vtables, function pointers, inlining, cached state
written by another path, or architecture-specific behavior. Audio/HID/MIDI
controller classification and removable-storage classification are separate
subsystems and are excluded from this Link Export peer-identity inventory.
