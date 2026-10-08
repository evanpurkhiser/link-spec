# Packed context oracle

This chapter defines the four-byte context carried by ordinary Link Export menu
queries and render requests. It combines exhaustive real-rekordbox recordings
with the corresponding rekordbox 7.2.19 control flow. The current phase tests
only real rekordbox; the canonical suite is retained for a later backend replay.

## Byte layout

The context is transmitted as one 32-bit number:

```text
0xPP_LL_SS_TT
```

| Byte | Role | Established behavior |
| --- | --- | --- |
| `PP` | requester/player | Ordinary Track returns for `0x01`; tested values `0x02..0x06` time out |
| `LL` | menu location | Tested generic values `0x01..0x08` select independent process-wide list buffers; XDJ-RR fixes Delivery `2602` to source-defined `0x09`, whose live matrix is queued |
| `SS` | media slot | Tested values `0x00..0x04` return the ordinary Track menu |
| `TT` | track type | Exhaustively recorded over `0x00..0xff`; exact results below |

The experiments hold the first three bytes at `0x01_01_03` and vary `TT`.
Every case uses a fresh TCP connection. The ordinary Track domain exhausts all
256 byte values. Three family crosses then use `0x00..0x06` over 47 list
requests, seven Song Info requests, and three Hot Cue Bank shapes. The
fixtures need no media files.

`XDJ_RR_CLIENT_NAVIGATION.md` adds the player-side context domain. Its generated
inventory proves direct named XDJ-RR callers at every literal location 1-8 and
associates locations 4-8 with concrete loaded-track, sort/Song Info,
Prepare/Tag List, category-reload, and payload workflows. The location-9
Delivery wrapper has no direct named XDJ-RR caller, so the queued live matrix
tests it as a source-defined specialized context rather than extending the
ordinary Track claim **[RR-DEC]**.

## Track-type domain

Dysentery assigns these client-side names:

| Value | Client meaning | Rekordbox 7.2.19 result |
| ---: | --- | --- |
| `0x00` | no track | Eight-row menu; argument 10 is zero |
| `0x01` | rekordbox track | Eight-row menu; argument 10 is `0x00000100` |
| `0x02` | unanalyzed track | Eight-row menu; argument 10 is zero |
| `0x03` | unassigned here | No header before the read deadline |
| `0x04` | unassigned here | No header before the read deadline |
| `0x05` | audio CD track | Eight-row menu; argument 10 is zero |
| `0x06` | streaming track | Eight-row menu; argument 10 is zero |
| `0x07..0xff` | unassigned here | Eight-row menu; argument 10 is zero |

Thus 254 values return a normal `4000` header with total 8 and all eight rows.
Exactly `0x03` and `0x04` time out before any header with transport error kind
`WouldBlock`. The two values are reported as measured routing boundaries; the
available evidence does not assign them semantic names.

All 253 successful values other than `0x01` produce field-identical rows.
Comparing those rows with `0x01`, argument 10 is the only changing field:

```text
TT = 0x01: row argument 10 = 0x00000100
other successful TT:           0x00000000
```

Both clean-process recordings agree exactly. In each pass the same rekordbox
process was responsive before and after all 256 cases, and the Windows
Application event query returned no new events.

## Static explanation

`PSvDBMain::OnTrackListCmd` at `0x101d2c6c0` passes the complete packed context
through database-interface virtual slot `+0x48`. The active
`PSvAppSyncDBIF::getTrack_Root` implementation at `0x1016bc8e0` uses the complete
value when it clears and populates the list buffer. Its ordinary membership
query does not branch on the low track-type byte.

`PSvDBMain::GetListBufContents` at `0x100fa1110` extracts the media slot from the
context byte above `TT` and passes the low byte separately to
`PSvDBMain::GetListBufRowContent` at `0x100f9fe40`. The row renderer admits its
cache and `HotCueAutoLoad` enrichment path only when `TT == 1`. This exactly
explains the argument-10 `0x100` bit observed for `0x01` and its absence from all
other successful values.

`PSvDBMain::OnClientReq` at `0x102521340` supplies the exact routing boundary.
It first computes `request_kind >> 12`. For class `1`, the `0x1xxx` list
family, it reads `TT`, subtracts three, and intercepts the request when the
result is zero or one. Thus exactly `TT = 0x03` and `0x04` enter an internal
observer/notification path and never call `PSvDBMain::OnListClientCmd`; no
`0x4000` header can be produced. Every other low byte enters normal list
dispatch. Class `2`, including Song Info and Hot Cue Bank requests, follows
`OnMAnlzClientCmd` and bypasses this gate.

The static branch explains the timeout set but does not give `0x03` or `0x04`
a semantic name. They remain unnamed measured client values.

## List-family cross

The 329-case `context-track-type-families` suite crosses `TT = 0x00..0x06`
with all 47 requests in the canonical `full` navigation suite. The results are
exact across two clean processes:

- `0x03` and `0x04` time out before a header for every `0x1xxx` request.
- `0x00`, `0x01`, `0x02`, `0x05`, and `0x06` reach normal list dispatch. Each
  produces 46 menus and the existing `0x1018` Hot Cue Bank legacy-request
  error.
- Root `0x1000` and Search `0x1300` are populated only for `0x01`. The other
  successful types receive normal zero-row menus. Direct Track, category,
  hierarchy, and filter leaves remain queryable for those types.
- Seven track-producing hierarchy/playlist leaves copy `TT << 24` into row
  argument 7: Genre, Artist, Album, Label, Original Artist, Remixer, and
  Playlist. This affects 25 rows per nonzero successful type. Direct Track and
  scalar-filter leaves do not copy it.
- Only `0x01` adds argument-10 bit `0x100`. The effect covers 60 track rows
  across 17 families; all other successful types leave that bit clear.

Apart from the Root/Search shape change and row arguments 7 and 10 just
described, the successful responses are field-identical.

## Song Info cross

The 49-case `context-analysis-track-types` suite crosses the seven known client
values with `0x2002`, `0x2102`, `0x2202..0x2502`, and `0x2602`. Every request,
including types `0x03` and `0x04`, receives a header, confirming that the
list-only dispatcher gate does not apply.

For Display `0x2002`, Play `0x2102`, and Delivery `0x2602`, only `TT = 0x01`
returns rows: 16, 7, and 13 respectively. Every other type returns `0x4000`
with total `0xffffffff` and no render. Requests `0x2202..0x2502` return
`0x4003` for every type.

## Hot Cue Bank cross

The 21-case `context-hot-cue-track-types` suite crosses the same values with
Hot Cue Bank `0x2001` for the tree root, a populated bank, and an empty bank.
Only `TT = 0x01` behaves normally, returning totals 3, 8, and 0. Every other
type returns `0x4000` with total 50, accepts a render request for 32 rows, then
sends no render messages before the `WouldBlock` deadline. This is a
post-header render timeout, distinct from both the `0x1xxx` pre-header gate and
the Song Info `0xffffffff` error result.

## Device and setup interaction

Two compact 16-case suites cross packed type with all eight ordinary discovery
identities under both extended and legacy setup. The identity set covers six
named players, both unknown mixer/DJM controls, XDJ/CDJ/non-player prefixes,
all four keepalive classes, generations 0/2/3, and player numbers 1-6 and 11.
Each setup/identity golden was immediately repeated.

Every extended behavior envelope is byte-identical after provenance removal,
with SHA-256
`bea74aa6bfd2ce82f6bc423e30cfee7f2b523e76a83e4d519c0ebbe841e55d90`.
Every legacy envelope is likewise identical, with SHA-256
`6fe895b6474d5231d4ac1241c6b4426e072377e1753f1d88e3dc170b92911cc1`.
The cross verifies:

- Track types `0x03` and `0x04` time out before a header for every identity and
  both setup widths.
- Root and Search populate only for type `0x01` in every cell.
- Ordinary Track argument 10 and hierarchy argument 7 retain the same
  type-derived values in every cell.
- Legacy rows are exactly the first 12 arguments of the corresponding
  16-argument extended rows. Setup width does not change routing, membership,
  totals, ordering, or the retained flag fields.

This adds 16 goldens and 256 real-Rekordbox case executions, each immediately
repeated. The machine summary and bounded service journal are under
`data/experiments/packed-context/device-setup-cross/`.

## Status-derived AIO interaction

Six additional Display Song Info goldens cross types `0x00..0x06`, extended
and legacy setup, authentic XDJ-RX3 player-11 status, an
RX3-template-derived CDJ-3000 player-1 control, and an
RX3-status/requester-1 mismatch control. Each was immediately
repeated.

The admission rule is invariant: only type `0x01` returns the 16 Display rows.
Types `0x00` and `0x02..0x06` return `0x4000`, total `0xffffffff`, and no rows.
Legacy rows remain exact 12-argument prefixes of extended rows.

For admitted type `0x01`, the first context byte selects the player passed to
`isAIO`:

- context player 11 plus RX3 player-11 status uses AIO order, moving Comment
  from position 11 to position 6;
- context player 1 plus CDJ-3000 player-1 status uses ordinary order;
- context player 1 while RX3 player-11 status is present also uses ordinary
  order.

Thus an XDJ status packet elsewhere in the process does not globally enable
AIO ordering. Classification is looked up for the requester/player encoded in
the query context. Setup width changes serialization width only.

## Status-backed Play interaction

Four Play Song Info goldens cross types `0x00..0x06`, extended and legacy
setup, genuine XDJ-RX3 player-11 status with requester 11, and genuine
CDJ-3000 player-1 status with requester 1. Each capture was immediately
repeated.

Only type `0x01` returns the seven Play rows. Types `0x00` and `0x02..0x06`
return `0x4000`, total `0xffffffff`, and no rows. After normalizing the
requester byte in the request and render contexts, the complete response
envelopes are identical between RX3 and CDJ-3000 within each setup. The
extended behavior hash is
`3a425319ea4322b578efd2c559984fc028e27c4c00b272c69d41c20b3ae0d0f0`;
the legacy behavior hash is
`f205fd2bd1c4d143ed4be574d89cfec4c61d38d02481bde63c3fb7544d949f33`.
Legacy rows are exact 12-argument prefixes of the extended rows.

This distinguishes Play from Display: the same genuine identities exercise
requester-keyed AIO ordering in Display, while Play has no observed
model-classification branch for any packed type or setup width in this cross.

## Remaining class-2 status interaction

Four further goldens cross types `0x00..0x06`, both setup widths, and the same
matched RX3/CDJ status identities over Delivery `0x2602` and recognized kinds
`0x2202..0x2502`. Each 35-case capture was immediately repeated.

Delivery retains the established admission rule: type `0x01` returns all 13
rows; the other six types return `0x4000`, total `0xffffffff`, and no rows.
Every recognized no-builder kind returns `0x4003` with its request kind as the
sole argument for every packed type. It does not construct a menu or emit a
total.

After requester-byte normalization, the complete RX3 and CDJ-3000 envelopes
are identical within each setup. The extended behavior hash is
`2eff175f6049a229665d0df46aa00cddc2e4749f3b1358bb1b380f52e8053da6`;
the legacy behavior hash is
`12a5195f55ead8d8f83021bac8cc278029796ad5ba0a2e3e5816cdde5b792d58`.
Legacy Delivery rows are exact 12-argument prefixes of extended rows. Together
with the Display and Play matrices, this completes the known Song Info request
kinds x packed types x matched RX3/CDJ status x setup-width cross.

## Hot Cue direct-getter interaction

Four 28-case goldens cross the legacy `0x2101` and extended `0x2301` Hot Cue
Bank getters over types `0x00..0x06`, populated and empty selectors, genuine
RX3/CDJ status, and both setup modes. Every capture was immediately repeated.

Only type `0x01` reaches the database. Its legacy getter returns the expected
`0x4702` populated or empty cue envelope, and its extended getter returns the
expected `0x4e02` populated or empty record envelope. Every other type returns
the same direct response kind, status `50`, empty blobs, and zero records.
These are well-formed direct error replies, distinct from the list-family
pre-header timeouts, Song Info `0x4000` menus, and Hot Cue catalog render
timeouts.

All six rejected types are byte-identical within a getter/selector family.
After request removal, all 28 decoded replies are identical across RX3 and
CDJ-3000 and across extended and legacy setup. Their shared normalized behavior
hash is `820ec23cde0fa1d817f42ff8812fe1abca175d1a9885cb7c36279b01e2f06c6f`.

## Hot Cue catalog interaction

Four 21-case goldens cross `0x2001` over the tree root, populated Alpha Bank,
and valid Empty Bank; types `0x00..0x06`; authentic RX3 and derived CDJ-3000
status controls; and both setup modes. Every capture was immediately repeated
after fixture reset and process
restart.

Type `0x01` returns the fixture totals 3, 8, and 0. Types `0x00` and
`0x02..0x06` return a successful total-50 header, emit no rows for the requested
32-row render, and finish as `WouldBlock`. After requester-context
normalization, RX3 and CDJ-3000 behavior is identical within setup. Legacy rows
are exact 12-field prefixes of extended rows. The normalized behavior hashes
are `3a1559bf7881415f56bf9db4b44a252de043bbbdf8bbf6b0d9c0800aa0ccc0ce`
for extended setup and
`bfbea6623b0f3cdd0ea5d712412cb12772d36c7a7ae622734d9e1523064db514`
for legacy setup.

## Extended Hot Cue setter interaction

Four 14-case goldens cross extended setter `0x2401` over the same seven packed
types, matched RX3/CDJ status, and both setup modes. Each rejected setter is
followed by a fresh type-1 getter, and type 1 runs last with its own getter.
Every suite was independently repeated after fixture reset and process restart.

Type `0x01` returns status zero with the canonical 124-byte record, mutates the
membership, and is byte-identical to the following getter. Types `0x00` and
`0x02..0x06` return `4e02 [2401, 50, 0, empty_blob, 0]`. All 24 following
getter controls return the shared pristine record, proving the rejected paths
do not change the database view. The complete decoded response sequence is
identity- and setup-invariant; its shared signature is
`93cb7f88f8289a00ad3c4350421360ae830aad7ab2be1ada03f52a8e9b1b72e3`.

## Legacy Hot Cue setter interaction

Four more 14-case goldens apply the same matrix to legacy change operation
`0x2201`. A type-1 extended getter over slots 1–6 follows every request so a
plausible track-cue acknowledgement cannot be mistaken for a database write.

Type `0x01` returns the canonical two-cue `0x4702`, changes only slot 4 to the
expected 56-byte record, and leaves slots 5 and 6 byte-identical. Types `0x00`
and `0x02..0x06` return
`4702 [2201, 50, 0, empty_blob, 36, 0, 0, 0, empty_blob]`; all 24 following
getters return the same pristine 372-byte record set. The complete decoded
response sequence is identity- and setup-invariant, with shared signature
`fa283bebdfd95dcd54c234e1cb6e01a3dccff7f91de80c2e9ab6e07cc3260558`.

## Process-wide buffer identity

The complete 32-bit context is the list-buffer key. A query clears and replaces
only rows carrying that exact value. A render selects rows using the same key.
Consequently, changing any context byte creates a distinct stored menu identity,
and an initialized context remains readable from a later TCP connection until
rekordbox replaces or clears it. The Hot Cue Bank location-state experiments
demonstrate this process-wide persistence directly.

## Reproduction and provenance

The checked-in components are:

- `conformance/generate_context_track_type_suite.py`: deterministic generator.
- `conformance/suites/context-track-types.json`: all 256 declarations.
- `conformance/record_context_track_types.sh`: isolated recording workflow.
- `conformance/goldens/rekordbox-7.2.19/xdj-rx3/context-track-types.json`:
  canonical real-rekordbox result.
- `data/experiments/packed-context/track-types/`: record/repeat health evidence
  and the machine-validated summary.
- `data/static-analysis/context-track-type.disasm.txt`: focused static evidence.
- `data/static-analysis/context-track-type-routing.disasm.txt`: top-level
  request-class and `0x03`/`0x04` routing gate.
- `tools/summarize_context_track_types.py`: invariant checker and summary writer.
- `conformance/suites/context-track-type-families.json`,
  `context-analysis-track-types.json`, and `context-hot-cue-track-types.json`:
  the 329-, 49-, and 21-case cross-family declarations and goldens.
- `data/experiments/packed-context/{family-cross,analysis-cross,hot-cue-cross}/`:
  health evidence and machine-validated summaries for both clean processes.
- `conformance/suites/context-device-setup-{extended,legacy}.json`, 16 model
  goldens, and `data/experiments/packed-context/device-setup-cross/`: the
  complete ordinary-identity/setup interaction cross and validator.
- `conformance/suites/context-display-status*.json`, six status/mismatch
  goldens, and `data/experiments/packed-context/display-status-cross/`: the
  status-backed, requester-keying, setup-width, and exact-repeat evidence.
- `conformance/suites/context-play-status*.json`, four status-backed goldens,
  and `data/experiments/packed-context/play-status-cross/`: the Play packed
  type, identity, setup-width, and exact-repeat evidence.
- `conformance/suites/context-class2-status*.json`, four status-backed
  goldens, and `data/experiments/packed-context/class2-status-cross/`: the
  Delivery/no-builder packed type, identity, setup-width, and repeat evidence.
- `conformance/suites/context-hot-cue-getter-status*.json`, four
  status-backed goldens, and
  `data/experiments/packed-context/hot-cue-getter-status-cross/`: the direct
  getter packed-type, identity, setup, and repeat evidence.
- `conformance/suites/context-hot-cue-setter-status*.json`, four
  status-backed goldens, and
  `data/experiments/packed-context/hot-cue-setter-status-cross/`: the extended
  setter gate, post-rejection database reads, accepted mutation, and repeat
  evidence.
- `conformance/suites/context-hot-cue-legacy-setter-status*.json`, four
  status-backed goldens, and
  `data/experiments/packed-context/hot-cue-legacy-setter-status-cross/`: the
  legacy setter gate, six-slot post-request reads, accepted slot-4 mutation,
  and repeat evidence.
- `conformance/suites/context-hot-cue-catalog-status*.json`, four
  status-backed goldens, and
  `data/experiments/packed-context/hot-cue-catalog-status-cross/`: the catalog
  root/populated/empty packed-type, identity, setup, and repeat evidence.

Run the machine validator from this directory:

```bash
python tools/summarize_context_track_types.py
python tools/summarize_context_track_type_families.py
python tools/summarize_context_analysis_track_types.py
python tools/summarize_context_hot_cue_track_types.py
python tools/summarize_context_device_setup.py
python tools/summarize_context_display_status.py
python tools/summarize_context_play_status.py
python tools/summarize_context_class2_status.py
python tools/summarize_context_hot_cue_getter_status.py
python tools/summarize_context_hot_cue_setter_status.py
python tools/summarize_context_hot_cue_legacy_setter_status.py
python tools/summarize_context_hot_cue_catalog_status.py
```

The summary pins these identities:

| Artifact | SHA-256 |
| --- | --- |
| Generator | `6d2a2b4a5e336bcc6847772415dad29c48d5c208846d25d1f446bfa7a57a9a12` |
| Suite | `e3f5d29139f717634099fd6d4746c063f8f44a96d3272dcd7d90dbb629e99e49` |
| Golden | `a020a12838ff23ee931225d81e09dfa38a26d37f95afef9c25d7c87b1105bd54` |
| Static evidence | `6fdc36560135ba42923c92f6d8897ec6e0383db951aca391c1cb2ea49c8a62b8` |
| Routing evidence | `6dde2e506bb52f84a121c19bcc527193076c98d006bd5211f61b7836bbff2f1e` |
| Fixture fingerprint | `c7b0b834a1a1320faaa3526c4792f0d31430c617ea9b8b6008521c514b67853c` |

The cross-family golden hashes are `09995fec3f849020c86a79d035edf1f75483210c2e904db55aec420dac53782c`,
`9b8c6ed36da66cd81c38d36bdd8ebdf8ccf36c8ae50c271ec6820e9cab84b2ed`,
and `1427ad163a5635e391e49ff78e2055cd9e8622f9c55c020f83335a3aec4a198f`
for list families, Song Info, and Hot Cue Bank respectively.

The recorder installs the fixture only in the isolated Windows guest, starts a
clean rekordbox process for each pass, records before/after health, and restores
the `play-paths` baseline. The physical-LAN VM remains inactive. The suite is in
the deferred replay set and has not been run against rbxport.

## Remaining crosses

- Capture native status shapes beyond the authentic RX3 and derived CDJ-3000
  controls.
- Test buffer invalidation beyond clean process restart and explicit replacement.
