# Device predicate direct-reference audit

This generated report inventories direct ARM64 callers of every selected
Pro DJ Link identity, model, capability, and row-compatibility helper that
can plausibly affect Link Export. The JSON companion preserves every call site.

Binary SHA-256: `07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244`.
Targets: 23; validated direct references: 68; database-serving references: 6.

| Helper | Group | Direct refs | DB-serving refs |
| --- | --- | ---: | ---: |
| `receive-link-member-inner` (`0x10039063c`) | identity-ingress | 1 | 0 |
| `detect-link-device-inner` (`0x100392390`) | identity-ingress | 1 | 0 |
| `receive-link-member` (`0x100bbbcd4`) | identity-ingress | 0 | 0 |
| `add-link-device` (`0x101e0c4e4`) | identity-ingress | 2 | 0 |
| `get-member-info-inner` (`0x100393d50`) | identity-accessor | 0 | 0 |
| `get-member-info-proxy` (`0x100d34d98`) | identity-accessor | 1 | 0 |
| `get-model-name-inner` (`0x10038fdac`) | model-accessor | 0 | 0 |
| `get-model-name-inner-buffer` (`0x10038fdfc`) | model-accessor | 0 | 0 |
| `get-model-name-network` (`0x101b8c5e8`) | model-accessor | 1 | 0 |
| `get-model-name-network-buffer` (`0x101b8c254`) | model-accessor | 1 | 0 |
| `get-model-name-interval` (`0x100aa27d8`) | model-accessor | 1 | 0 |
| `get-model-name-interval-buffer` (`0x100aa286c`) | model-accessor | 3 | 0 |
| `get-model-name` (`0x100bbd058`) | model-accessor | 4 | 2 |
| `get-model-names` (`0x100bbcf48`) | model-accessor | 2 | 0 |
| `is-specific-model` (`0x100bbcecc`) | model-predicate | 35 | 0 |
| `is-cdj-network` (`0x100bbadfc`) | model-predicate | 5 | 0 |
| `is-aio` (`0x10227953c`) | database-serving-predicate | 1 | 1 |
| `clear-aio-map` (`0x102277d14`) | database-serving-lifecycle | 1 | 1 |
| `new-cdj-supported` (`0x101fe5e60`) | row-compatibility-predicate | 2 | 2 |
| `support-my-setting` (`0x100aa2a98`) | device-setting-predicate | 2 | 0 |
| `support-duplication-v2` (`0x100aa2ac0`) | device-setting-predicate | 2 | 0 |
| `support-device-setting` (`0x100aa2ae8`) | device-setting-predicate | 2 | 0 |
| `set-deck-aio` (`0x100179038`) | drag-drop-output | 1 | 0 |

## Database-serving references

- `get-model-name` <- `__ZN9PSvDBMain5isAIOEh` at `0x102279620` (bl).
- `get-model-name` <- `__ZN9PSvDBMain5isAIOEh` at `0x102279660` (bl).
- `is-aio` <- `__ZN14PSvAppSyncDBIF14getDispSongInfEhjj` at `0x101514b74` (bl).
- `clear-aio-map` <- `__ZN9PSvDBMain10DisconnectEh` at `0x102277cfc` (bl).
- `new-cdj-supported` <- `__ZN9PSvDBMain20GetListBufRowContentEhh17ENUM_CATEGORYKINDPvPmbjP18RetListBufParamExt` at `0x100e84900` (bl).
- `new-cdj-supported` <- `__ZN9PSvDBMain20GetListBufRowContentEhh17ENUM_CATEGORYKINDPvPmbjP18RetListBufParamExt` at `0x100e8491c` (bl).

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
- `new-cdj-supported`: database-serving=2. Computes per-track compatibility state consumed by track rows.
- `support-my-setting`: link-plumbing=2. Gates My Settings network messages.
- `support-duplication-v2`: link-plumbing=2. Gates My Settings duplication version 2.
- `support-device-setting`: link-plumbing=2. Gates device-setting network messages.
- `set-deck-aio`: link-plumbing=1. Serializes the AIO deck form for drag-and-drop play.

## Boundary

This scan proves direct references in the pinned ARM64 text slice. It does
not exclude indirect calls, vtables, function pointers, inlining, cached state
written by another path, or architecture-specific behavior. Audio/HID/MIDI
controller classification and removable-storage classification are separate
subsystems and are excluded from this Link Export peer-identity inventory.
