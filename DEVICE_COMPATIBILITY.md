# Client and device compatibility

Link Export behavior is influenced by three independently visible inputs:
protocol setup shape, request-supplied capabilities, and the discovered player
identity. They should not be collapsed into one model-name switch.

## Evidence levels

| Behavior | Evidence | Confidence |
| --- | --- | --- |
| One setup argument gets `4000 [0, 0x11]` and 12-field rows | Repeated isolated oracle | Established for RX3 and CDJ identities |
| Two setup arguments get `0000 [0x11, 0x14]` and 16-field rows | Repeated isolated oracle | Established for RX3 and CDJ identities |
| Root mask controls category admission | Executable plus captured request | Exact predicate recovered |
| Model names beginning `XDJ` classify as AIO | Executable | Exact helper behavior recovered |
| AIO classification changes Display Song Info item order | Executable plus repeated status-backed oracle | Exact branch and complete 16-row order confirmed |
| Model/AIO classification changes stable Play or Delivery Song Info | Genuine RX3/CDJ status oracle plus executable | No difference after requester-context normalization; no classifier appears in either recovered builder |
| Model/AIO classification changes packed Play Song Info admission or rows | Genuine RX3/CDJ status x types `0x00..0x06` x both setup widths | No difference after requester-context normalization; type `0x01` alone succeeds |
| Model/AIO classification changes packed Delivery/no-builder dispatch | Genuine RX3/CDJ status x five request kinds x seven types x both setup widths | No difference after requester normalization; Delivery admits type `0x01`, while recognized no-builders always return `0x4003` |
| Model/AIO classification changes packed Hot Cue direct getters | Genuine RX3/CDJ status x `2101`/`2301` x populated/empty x seven types x both setup widths | No difference; type `0x01` serves data and all other types return direct status 50 |
| Model/AIO classification changes packed Hot Cue extended setter | Genuine RX3/CDJ status x `2401` x seven types x both setup widths | No difference in reply or database state; type `0x01` mutates and all other types return status 50 with pristine readback |
| Model/AIO classification changes packed Hot Cue legacy setter | Genuine RX3/CDJ status x `2201` x seven types x both setup widths | No difference in reply or database state; type `0x01` mutates slot 4 and all other types return status 50 with pristine D/E/F readback |
| Model/AIO classification changes adjacent artwork/analysis payload builders | Complete dual-slice 23-target device-predicate audit plus exact payload dispatcher/loader bodies | No direct model, class, generation, or capability predicate reaches these builders in either slice; packed track type and request arguments remain independent inputs, while matched-status live success crosses remain pending |
| Status presence changes malformed Play/Delivery dispatch | Genuine RX3/CDJ status oracle | Argumentless Delivery returns an empty Play-kind header under status but times out under the ordinary identity |
| XDJ-RX3 versus CDJ-3000 changes Link-panel controls | Live isolated oracle | Established for the tested identities |
| XDJ-RX3 versus CDJ-3000 changes the 47-case full menu corpus | Live isolated oracle | No change for extended setup, mask `0x05cfffff`, five-argument render |
| Model/AIO/class/generation changes the fixed-envelope root/list corpus | Eight-identity repeated oracle | No change across every named model and all four keepalive classes |
| File/sample-rate/new-CDJ checks affect row compatibility data | Exact executable predicate plus repeated eight-row and exhaustive 382-row compatibility fixtures | `FileType` bytes 5/6 fail; 11/12 require 44.1 or 48 kHz; every other byte passes; `BitDepth` is not read; both setup widths repeat exactly |

## Setup shape and row width

The observed setup command is message kind `0000`:

- `fffffffe:0000 [1]` receives `fffffffe:4000 [0, 0x11]` and selects
  12 arguments per `4101` row.
- `fffffffe:0000 [1, 0x14]` receives
  `fffffffe:0000 [0x11, 0x14]` and selects 16 arguments per `4101` row.

The first 12 extended arguments and the legacy row agree. Secondary text and
the composite item type are constructed before truncation. The four fields
omitted from legacy serialization are arguments 12-15: an auxiliary ID,
tertiary-string byte length, tertiary text, and BPM x100 for captured track
rows.

The setup argument count is currently the strongest observed discriminator.
The captures do not prove that rekordbox derives it from model name; the client
chooses the setup shape on the wire.

Both setup forms were recorded and independently repeated under eight identity
controls covering every named model, all four keepalive classes, generations
0/2/3, and discovery players 1-6 and 11. The extended behavior hash is
`d8c262a03cb6d38a486bd096be3e2a196773d4c60fb407ebbc2d689f470404b5`;
the legacy behavior hash is
`d9c5ccd1fefb28c14b40e6aee23d8519ff1947b56164c00db9d24fab4c74f181`.
Within each setup form all eight envelopes are byte-for-byte identical after
canonical key ordering. `DEVICE_MATRIX_ORACLE.md` gives the command and full
identity table.

## Root capability mask

The final `1000` argument is consumed directly by `GetRootMenu`. Each configured
category must pass both its database visibility state and its required mask
bit. The exact bit map, Date Added special case, Folder suppression, and legacy
Hot Cue Bank synthesis are in `CONFIGURATION.md`.

This is a client-advertised capability path: two clients can request different
root trees without changing the database. The controlled extended-client
matrix sends `0x05cfffff`; the retained physical RX3 sent `0x05fdffff`; and
Dysentery documents `0x00ffffff` for older clients. Rekordbox has an explicit
compatibility branch only for the exact latter value. The physical request also
establishes query player 11 and context `0x0b010401` **[CAP]**.

The live 31-case mask sweep confirmed the predicate for the controlled mask:
single configured bits
produce one row, zero produces none, the legacy mask produces 19 rows without
Matching, and the captured/all-bit masks produce 20. Items without a visible
category remain absent even when their capability bit is set **[OBS]**.

## Model-name classification

### Status-owned model state

Discovery membership and model availability are separate state transitions in
this build. Internal membership message type `0x04` reaches
`InnerLinkAPI::receiveLinkMember`, and `ProDJLink::receiveLinkMember` calls
`LinkDeviceManager::addLinkDevice` with device type, presence, timing, address,
and version fields. `addLinkDevice` asks `LinkProxy::getModelName` for one
special `DJS-1000` check, but it does not populate the model buffer.

The model buffer belongs to `PSvLinkNormalInterval`'s per-player status record.
Its packet-kind jump table maps raw kind `0x0a` to the branch where
`messageReceived` parses player status through
`PSvLinkPlayerLinkInfo::setData`, selects player slots 1-8 or 9-12, and stores a
`0xb8`-byte record. The 20-byte model string begins at record offset `0x0b`.
Before replacing a record, the parser copies the prior model, compares it with
the newly parsed model, and emits internal message type `0x6e` only when they
differ. The `InnerLinkAPI::linkProc` jump table maps `0x6e` exactly to the arm
that calls `noticeModelNameUpdate(player)`.

`PSvLinkNormalInterval::getModelName` reads the same record and offset;
`PSvLinkNetworkAccess`, `InnerLinkAPI`, `LinkProxy`, and `ProDJLink` are
delegating accessors. The update callback continues through vtable slot
`+0x158` to `UiProDJLink::notifyModelNameUpdate`, which posts application
message `0x1234`, category `0x0a`, command `0x13`. The Display builder does not
consume that UI notification. `PSvDBMain::isAIO` lazily calls the accessor on
its first request for a player and stores a separate boolean cache.

This ownership explains the dynamic boundary without extrapolation: a
keepalive-only identity can become a Link member while its status-owned model
record remains empty. A successfully admitted player-status packet supplies
the model read by `isAIO`. The trace proves the parser, storage, notification,
getter, and cache chain. It does not prove that every synthetic status shape
will pass all earlier admission checks **[DEC, OBS]**.

`PSvDBMain::isAIO(player_number)` performs these steps:

1. Check a cache keyed by player number.
2. Obtain the peer model through `ProDJLink::getModelName(player_number)`.
3. Test whether the model starts with `XDJ`.
4. Separately test whether it starts with `XDJ-AZ`.
5. OR the results, cache the boolean, and return it.

The second test is logically contained by the first in this build, but both
calls exist in the machine code. Cache entries are cleared through
`clearAIOMap` as player state changes.

A validated direct-call scan finds one caller:
`PSvAppSyncDBIF::getDispSongInf(player, ...)`. The AIO branch emits the Comment
display item before Key, Rating, Color, Genre, and Stock Date. The non-AIO
branch emits the same six items with Comment after Stock Date. Both paths then
rejoin for the remaining display fields.

The repeated `0x2002` oracle confirms this model-dependent ordering difference:
status-backed XDJ-RX3/player-11 places Comment sixth, while the matched
CDJ-3000/player-1 status control places it eleventh after Stock Date. A
keepalive-only identity does not populate this model cache. The complete rows,
packet hashes, and lifecycle control are in `DISPLAY_SONG_INFO_ORACLE.md`
**[OBS, DEC]**.

Mutating the captured RX3 status shape to XDJ-XZ, XDJ-AZ, or XDJ-1000MK2 at
player 11 causes all four Display Song Info probes to time out. Mutating it to
the unknown-model control at player 1 returns ordinary menus. This is evidence
that accepted live classification depends on more than an `XDJ` model prefix;
it is not evidence for the native packet shape or menu behavior of those three
products **[OBS]**.

This result does not establish that XDJ/RX3 clients receive different root-menu
membership, sort menus, query results, or `4001/4101/4201` row layouts. Those
surfaces remain explicit oracle comparisons.

Broadened direct-call and function-body inspection found no model-name read or
`isAIO` call in `GetRootMenu`, `GetSortMenu`, the list-buffer insertors,
`GetListBufRowContent`, or `GetListBufContents` **[DEC]**. Ordinary Link Export
menu differences are therefore currently attributable to the inputs those
paths consume: setup width, root capability mask, packed context, render
arguments, persisted database settings, and per-track metadata. This is a
bounded negative result for the pinned functions, not proof that no indirect
model-dependent state can ever reach them.

The generated 23-target audit strengthens this boundary. It validates 67
x86-64 and 68 ARM64 direct references: every `isSpecificModel` and
`isCDJNetwork` caller is UI or
remote-settings code, while dbserver reaches only the Display `isAIO` branch,
its disconnect cache clear, and the content-only track compatibility helper.
The exact UI literals are XDJ-XZ, XDJ-AZ, XDJ-RR, XDJ-RX2, and OPUS-QUAD.
Drag-and-drop play uses a separate exact OPUS-QUAD decision for its AIO deck
packet, so it must not be conflated with Display's `XDJ*` classifier.
`DEVICE_PREDICATE_AUDIT.md` gives the full caller table **[DEC]**.

`data/device-behavior-matrix.json` joins that static boundary to the canonical
runtime evidence. It retains all eight ordinary identities and their four
byte-identical behavior hashes, then separately indexes the status-backed
Display, Play, Delivery/no-builder, Hot Cue catalog, and Hot Cue getter
crosses. Display is the only recorded identity-dependent serving surface in
that joined matrix. The file preserves source hashes and provenance tiers, so
the derived CDJ-3000 control cannot be mistaken for a captured native packet.

The stripped Windows PE independently recovers all three serving decisions.
Display calls `isAIO` at `0x1423815c0`; Disconnect `0x142380930` contains the
player-keyed AIO-map erase inline; and AppSync `GetListBufRowContent`
`0x14238c720` contains the FileType/SampleRate predicate inline. Its alternate
Master-interface branch calls the standalone predicate at `0x14227e200`.
These addresses come from the exact Windows authority executable, while the
382-row runtime oracle independently validates the compatibility truth table
**[DEC, OBS]**.

The `0x2102` Play and `0x2602` Delivery sibling suites currently use an
XDJ-RX3/player-1 keepalive identity. Static inspection of their active AppSync
builders recovered database and path selection but no direct `isAIO` call.
Their complete ordinary and legacy rows are established; status-backed RX3,
CDJ-3000, and native other-model crosses remain explicit matrix dimensions in
`SONG_INFO_SIBLINGS_ORACLE.md` **[OBS, DEC]**.

## Live identity comparison

The same encrypted `full` fixture and `full.json` suite were recorded through
two discovery identities on September 30, 2026:

| Field | XDJ-RX3 run | CDJ-3000 run |
| --- | --- | --- |
| Model string | `XDJ-RX3` | `CDJ-3000` |
| Discovery player | 11 | 1 |
| Keepalive device type | 7 | 1 (`cdj`) |
| Presence byte | 2 | 1 |
| Model-code byte | 0 | 100 |
| Query setup device/context high byte | 1 / 1 | 1 / 1 |
| Setup | Extended and legacy | Extended and legacy |
| Root mask | `0x05cfffff` | `0x05cfffff` |
| Default render arity | 5 | 5 |
| Extended cases recorded and repeated | 47 | 47 |
| Legacy cases recorded and repeated | 2 | 2 |

Both discoveries caused the same `LINK` source to appear. After enabling it,
the CDJ-3000 identity added a `MASTER` indicator and 120.00 BPM control beside
player 1; the XDJ-RX3 identity showed player 1 and `LINK` without those controls
**[OBS]**. The screenshots are
`data/rekordbox-cdj-3000-link-enabled.png` and
`data/rekordbox-xdj-rx3-link-enabled.png`.

The canonical `.behavior` objects for all 47 extended cases are byte-for-byte
identical across all eight controls after sorted JSON serialization, with
SHA-256
`d8c262a03cb6d38a486bd096be3e2a196773d4c60fb407ebbc2d689f470404b5`
**[OBS]**. This covers the configured root, track and lookup menus, hierarchy
drilldowns, filters, Matching, search, playlist navigation, rendered row fields,
and the suite's error-tolerant History/Hot Cue cases. It proves menu invariance
for this exact request configuration, not for alternate setup widths, root
masks, render arguments, codec compatibility fixtures, or the separately
recorded Display, Play, and Delivery Song Info APIs.

The two-case legacy suite is also identical across all eight controls, with
SHA-256
`d9c5ccd1fefb28c14b40e6aee23d8519ff1947b56164c00db9d24fab4c74f181`.
It proves the reply shape, 12-field track truncation, and exact-mask Hot Cue
Bank root branch for this controlled query device. Discovery player and TCP
query player remain separate matrix dimensions.

In both Mach-O slices, `PSvDBMain::Disconnect(player_number)` directly calls
`clearAIOMap`. Windows Disconnect `0x142380930` inlines the same keyed tree
erase instead. Reconnect and identity-change tests verify that the cached
classification does not leak into the next session **[DEC, OBS]**.

## Per-track compatibility checks

The macOS row builder calls `DsqlContent_GetNewCDJSupported`; the active Windows
AppSync row builder inlines its FileType/SampleRate logic, while its alternate
Master-interface branch calls the standalone Windows copy at `0x14227e200`.
Both paths also read `HotCueAutoLoad` and have old/new musical-key conversion
paths. The repeated metadata-only compatibility fixture assigns extended row
argument 10: `0x100` is supported and `0x101` sets compatibility-failure bit 0
**[OBS, DEC]**.

The predicate loads `FileType` as a signed byte. Raw bytes 5 and 6 return false.
Raw bytes 11 and 12 load `SampleRate` and return true only for decimal 44100
(`0xac44`) or 48000 (`0xbb80`). Every other file-type byte returns true without
consulting sample rate. Neither the Windows inline query nor either standalone
implementation loads `BitDepth`; depth cannot affect this compatibility bit on
the recovered paths **[DEC]**.

The packed track-type byte independently gates the `HotCueAutoLoad` half of this
word. With identical content metadata, type `0x01` preserves bit `0x100`, while
all 253 other successful final-byte values clear it. The compatibility low bit
and the track-type gate are separate inputs to the same argument. See
`PACKED_CONTEXT_ORACLE.md` **[OBS, DEC]**.

Track type is also independent of advertised device model. Across the canonical
list families, type `0x01` alone populates Root/Search and enables
`HotCueAutoLoad`; seven hierarchy/playlist leaves copy `TT << 24` into argument
7. The top-level dispatcher intercepts types `0x03` and `0x04` only for
`0x1xxx` requests. Song Info and Hot Cue Bank reach class-2 dispatch for every
type but produce normal local-library results only for `0x01`. The ordinary
identity/setup interaction is complete: all eight identities are field-identical
within each setup, and legacy responses are exact 12-field prefixes of the
extended responses. The status-backed cross closes the Display interaction:
the context requester byte selects the cached player classification. RX3
player-11 status yields AIO order for requester 11 but ordinary order for
requester 1; matched CDJ-3000 player-1 status yields ordinary order. Track type
`0x01` is the sole admitted type in every cell, and setup width changes only
the row suffix. The equivalent matched-status Play cross is also identical
between RX3 player 11 and CDJ-3000 player 1 after context normalization for
all seven types and both setup widths. Play therefore does not reproduce
Display's AIO ordering branch on this surface. The 140-case Delivery and
recognized-no-builder matrix is likewise identical between matched RX3 and
CDJ-3000 status identities after normalization. For the known Song Info kinds,
Display remains the only stable response surface with a model-classification
difference.

The legacy and extended Hot Cue Bank direct getters follow the same identity
boundary. Across matched RX3/CDJ status and both setup modes, their decoded
responses are identical: type `0x01` serves the fixture, while every other
type returns the getter's ordinary direct reply kind with status `50` and no
records. Setup width has no effect because these are direct blob replies, not
`0x4101` menu rows.

The supported rows are FileType 1 MP3 at 44.1/48 kHz, FileType 4 M4A at
44.1 kHz, and FileType 11 WAV at 44.1 kHz. FileType 5 FLAC at 48/96 kHz,
FileType 11 WAV at 88.2 kHz, and FileType 12 AIFF at 96 kHz set the failure
bit. Bit depth was 16 for the supported rows and 24 for the failing high-rate
or FLAC/AIFF rows, so this fixture does not independently assign a bit-depth
predicate. Both Track and File Name menus returned all eight records without
media files; membership is independent of this displayed compatibility bit for
the tested path. `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md` contains the complete
table and fixture fingerprints.

The eight-row fixture also crosses its sampled metadata across all eight
ordinary model identities, and those behavior envelopes are identical. The
exhaustive fixture separates the predicate's true inputs from codec labels:
all 256 file-type bytes, 14 wide integer narrowing controls, 56 sample-rate
boundaries over types 5/6/11/12, and 56 bit-depth invariance rows under
supported and rejected branches **[OBS, DB, DEC]**.

Both cold-process record/repeat runs return all 382 rows with one responsive
Rekordbox process and no new Application events. Extended rows have 16
arguments; legacy rows have 12, and every legacy row is the exact 12-argument
prefix of its extended counterpart. The complete observed predicate is:

- FileType bytes 5 and 6 return `0x101` for every tested sample rate and depth.
- FileType bytes 11 and 12 return `0x100` only at exactly 44100 or 48000 Hz.
- Every other byte in `0x00..0xff` returns `0x100` at the controlled 44100 Hz.
- Wide FileType values narrow to their low byte: 261/262 reject as 5/6, while
  267/268 enter the 11/12 rate branch and pass at 44100 Hz.
- Changing BitDepth across signed/unsigned extrema and ordinary audio depths
  never changes the result under a supported type, always-rejected type 5, or
  rate-rejected type 11 at 48001 Hz.

The matrix therefore contains 298 supported and 84 unsupported rows. Its
partition totals are 254/2 for the byte sweep, 12/2 for wide FileType values,
4/52 for SampleRate, and 28/28 for the deliberately balanced BitDepth controls.
The canonical goldens, two setup receipts, strict summary, and finalization
receipt are under `data/experiments/track-compatibility-exhaustive/`.

Delivery Song Info ordering was also crossed with device lifecycle. Six RX3
calls followed by discovery expiry and either the same RX3 identity or a
CDJ-3000 replacement resume as calls seven through fourteen. Complete row
payloads are identical across both lifecycle modes and repeats. XDJ/CDJ
keepalive classification does not alter this builder's rows or process-scoped
ordering for the tested request envelope **[OBS]**.

## Adjacent payload identity boundary

The artwork and analysis services are direct-response commands rather than
list-buffer menus. Their recovered handlers construct fixed reply families
`0x4002`, `0x4402`, `0x4502`, `0x4602`, `0x4a02`, `0x4c02`, and `0x4f02`, or the
scalar `0x4000` reply. They do not enter the 12-field/16-field `0x4101` row
serializer, so setup width is not a row-layout dimension for these responses
**[DEC]**.

The generated device-predicate audit validates all 67 x86-64 and 68 ARM64
direct references to its 23 identity, model, class, and capability targets.
Five x86-64 and six ARM64 references belong to database-serving code: two
model-name reads inside `isAIO`, the Display Song Info call to `isAIO`,
disconnect-time `clearAIOMap`, and the content-only compatibility predicate in
the track-row builder. ARM64 calls that last predicate twice from the same
owner. No artwork or analysis payload handler calls any audited peer predicate
**[DEC]**.

This does not collapse payload admission into device identity. Each request
still carries a packed context whose track-type byte is consumed by dispatch,
and `0x2003`/`0x2103` have explicit type-dependent image errors. Content ID,
image ID, menu location, atom tag, and analysis extension remain request axes.
The 196-case fileless declaration covers packed types `0x00..0x06` across all
16 adjacent kinds; the generated-success declaration supplies valid bytes for
all ten filesystem-backed kinds **[OBS plan, DEC]**.

The bounded negative static result establishes that a peer-model branch is not
present in the recovered direct-call graph of either slice. It does not prove
that status-backed
session state can never affect dispatch before those handlers, nor that setup
negotiation can never affect admission. A matched genuine RX3/CDJ status cross
over successful payloads is therefore retained as a dynamic follow-up rather
than inferred from the ordinary-identity capture.

## Command dispatch

`PSvDBMain::OnListClientCmd` dispatches list requests into dedicated handlers
for Genre, Artist, Album, Track, Playlist, BPM, Rating, Year, Label, Key, Color,
Play Count, Prepare, Length, Bitrate, History, File Name, New Key, My Tag,
Matching, and Other. Unknown commands receive `4003` while preserving the
transaction ID.

The dispatch breadth explains why a root entry is not the complete capability
surface. Date Added, play count, My Tag, New Key, and prepare paths can exist in
the implementation even when the current database/root mask does not advertise
them.

## Client cache and menu location

The packed context selects a menu location. The server stores the current list
buffer for that location, and a later `3000` render request supplies offset and
count. Clients must serialize menu creation and rendering per location; a new
query can replace the list that an earlier render expected.

In the isolated XDJ-RX3-shaped session, requester byte 1 was accepted and bytes
2-6 timed out. Menu locations 1-8 and slot candidates 0-4 were accepted. These
are context-word request rules, separate from the discovery model and player
number used to expose LINK **[OBS]**.

That sweep advertised only player 1, so it does not establish that requester 2
is rejected when a player-2 discovery entry exists. The generated two-player
Link-played sequence advertises ordinary RX3 players 1 and 2 from distinct
addresses and uses setup device/context pairs `(1, 0x01010301)` and
`(2, 0x02010301)`. Player-2 response expectations remain open: admission,
timeout, or disconnect is retained as real-Rekordbox evidence, while every
player-2 mutation begins on a fresh connection. Generation `ak18` therefore
tests both requester admission and shared-versus-partitioned Link-played state
without overriding the earlier single-identity result **[OBS plan]**.

`GetListBufContents` also reads optional render arguments:

- With at least six arguments, argument 6 is converted by
  `DBCommon_GetCateKind` and passed to the row renderer.
- With at least eight arguments, an additional boolean and integer are passed
  to the row renderer.

The observed eight-argument render shape is documented in
`PROTOCOL_REFERENCE.md`. These render-time fields are another possible client
capability channel and should not be inferred solely from model identity.

## Device comparison experiment

A rigorous comparison holds library state constant and records, for each
synthetic identity/setup combination:

1. Discovery model name and player number.
2. Setup argument count and values.
3. Root mask and returned category IDs/types/order.
4. Sort-menu rows.
5. Render request arity and optional arguments.
6. Extended/legacy track fields for a fixed codec fixture set.
7. New Key, My Tag, Prepare, Date Added, play-count, and Hot Cue Bank catalog
   behavior, including `0x2001` modes/count and specialized menu locations.
8. Hot Cue Bank `0x2101` direct-response behavior. RX3 and RR model strings,
   with and without captured player status, return payload-identical populated
   and empty `0x4702` replies for equivalent selectors.
9. Session cache behavior after reconnect and identity change.
10. Display-song-info item order, including the Comment position around the AIO
   boundary.

The test must run on an isolated L2 network. The physical RX3 is explicitly
outside the experiment topology.
