# Device predicate audit

This chapter inventories the device identity and capability predicates in both
slices of the pinned rekordbox 7.2.19 universal executable and traces their
direct callers. It
answers a narrower question than the dynamic device matrix: which recovered
model, device-class, or capability decisions can reach Link Export serving
code, and which belong only to the application UI or adjacent Pro DJ Link
features?

The x86-64 machine-readable result is
`data/static-analysis/device-predicate-audit.json`; the ARM64 result is
`data/static-analysis/device-predicate-audit-arm64.json`. Their generated
Markdown companions use the same basenames. All four are recreated by
`tools/audit_device_predicates.py` and are pinned to executable SHA-256
`07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244`.

## Result

Both slices contain the same 23 identity ingress functions, member/model
accessors, model predicates, capability predicates, lifecycle helpers, and
output selectors. The x86-64 audit validates 67 direct `rel32` call or jump
sites, five of them owned by database-serving code. ARM64 validates 68 direct
`B` or `BL` sites, six of them database-owned. Both reach the same three
behavioral decisions **[DEC]**:

| Decision | Direct database-serving caller | Effect |
| --- | --- | --- |
| `PSvDBMain::isAIO(player)` | `PSvAppSyncDBIF::getDispSongInf` | Reorders Comment relative to Key, Rating, Color, Genre, and Stock Date in Display Song Info |
| `PSvDBMain::clearAIOMap(player)` | `PSvDBMain::Disconnect` | Invalidates the cached Display Song Info classification |
| `DsqlContent_GetNewCDJSupported(content_id)` | `PSvDBMain::GetListBufRowContent` | Supplies track compatibility state used by the rendered track row |

In both slices, two database-owned sites are the model-name reads inside
`isAIO`; they are inputs to the first decision, not additional menu branches.
ARM64's sole extra site is a second call to
`DsqlContent_GetNewCDJSupported` from the same `GetListBufRowContent` owner.
It duplicates the content-only compatibility decision rather than introducing
another device-classification branch.

No direct database-serving caller reaches `isSpecificModel`, `isCDJNetwork`,
`getModelNames`, the device-setting support bits, or the drag-and-drop deck
serializer. The named model comparisons discovered through those functions
therefore do not justify adding model-specific root, category, sort, filter,
pagination, or row-layout branches to a Link Export implementation **[DEC]**.

## Discovery identity path

The recovered discovery path preserves several fields that must remain
separate test dimensions:

1. `InnerLinkAPI::receiveLinkMember` parses a membership message.
2. The application callback reaches `ProDJLink::receiveLinkMember` through a
   virtual dispatch; this edge is intentionally absent from a direct-call
   scan.
3. `ProDJLink::receiveLinkMember(id, device_type, present)` reads timing and
   flags through `LinkProxy::getMemberInfo`, then calls
   `LinkDeviceManager::addLinkDevice`.
4. `LinkDeviceManager` stores device type, presence, timing, address, and
   version state. It performs an immediate model lookup for a `DJS-1000`
   special case, but membership does not itself populate the model buffer.
5. `PSvLinkNormalInterval::messageReceived` maps raw packet kind `0x0a` to
   `PSvLinkPlayerLinkInfo::setData`, stores a separate `0xb8`-byte per-player
   status record, and emits message type `0x6e` when the record's 20-byte model
   string changes.
6. The `linkProc` jump table dispatches `0x6e` to
   `noticeModelNameUpdate(player)`. Model accessors read the status record
   directly; `PSvDBMain::isAIO` lazily converts it into a distinct cached
   boolean.

Device class, model text, player number, presence, generation-shaped packet
fields, and query context are consequently correlated in real packets but are
not interchangeable. The dynamic oracle already varies those fields
independently where the wire encoder permits it.

`ProDJLink::receiveLinkMember` has zero direct references in the generated
report because the upstream notification is virtual. This is an observed
boundary of the scanner, not evidence that the function is unreachable.

The complete ingress-to-cache proof is retained in
`data/static-analysis/model-name-state-path.disasm.txt`. Its contract test also
resolves the `linkProc` jump table from the executable: membership type `0x04`
lands at `receiveLinkMember`, while model-change type `0x6e` lands at
`noticeModelNameUpdate` **[DEC]**.

## Three different classifications

The executable uses the word AIO in more than one path, but the predicates are
not equivalent.

### Display Song Info AIO

`PSvDBMain::isAIO(player)` obtains the model name and tests `startsWith("XDJ")`.
It also performs a second, logically redundant `startsWith("XDJ-AZ")` test,
ORs the results, and caches the boolean by player number. Its sole direct
behavioral caller is `PSvAppSyncDBIF::getDispSongInf` **[DEC]**.

The status-backed XDJ-RX3 and CDJ-3000 captures prove both output orders. A
keepalive-only XDJ identity does not populate the status-backed lookup needed
by this path, so model text in a discovery packet alone is insufficient
**[OBS]**.

The installed Windows PE independently follows the same boundary. Its `0x2002`
dispatcher reaches the RTTI-derived `PSvAppSyncDBIF` vtable slot `+0x168` and
active formatter `0x142361f30`. That formatter calls Windows `isAIO` at
`0x1423815c0`; the helper obtains the model and performs the same XDJ-prefix
classification. The retained disassembly and vtable proof live under
`data/static-analysis/windows/` **[DEC]**.

Key notation is a local setting dimension rather than a peer-model predicate.
The same Windows formatter calls the local `DEVSETTING.DAT` style predicate
through `exchangeKeyNameIfNeed`. Classic/Alphanumeric output changes under an
unchanged XDJ-RX3 identity, while the XDJ-prefix branch remains unchanged
**[OBS, DEC]**.

### Windows PE evidence boundary

The real authority recordings execute the Windows 7.2.19 build whose SHA-256
is `c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37`.
The PE is stripped, so its static predicate coverage is narrower than the
symbol-rich universal Mach-O **[DEC]**:

| Decision | Windows static evidence | Windows runtime evidence |
| --- | --- | --- |
| Display Song Info XDJ-prefix classification | Exact `0x2002` dispatcher, RTTI-derived AppSync vtable slot, formatter `0x142361f30`, and `isAIO` `0x1423815c0` | Authentic RX3 status produces AIO order; the matched CDJ control produces ordinary order |
| Disconnect-time AIO-cache invalidation | Disconnect `0x142380930` contains the player-keyed erase of the `0x790` AIO map under its `0x7a0` lock; the separately emitted map-only helper `0x142381700` has zero direct callers | RX3 rejoin and RX3-to-CDJ replacement lifecycles independently prove cache invalidation |
| Track compatibility | AppSync `GetListBufRowContent` `0x14238c720` inlines the FileType/SampleRate predicate; its Master-interface branch calls the standalone copy `0x14227e200` once | The complete 382-row Windows oracle proves the same byte/rate predicate and BitDepth invariance |
| Absence of other peer-model menu branches | Whole-image semantic audit over all 174,813 runtime-function records; the compatibility signature occurs exactly twice, and the bare `XDJ` prefix literal has one direct reference | Eight ordinary identities and the status-backed RX3/CDJ menu, Play, Delivery, and Hot Cue crosses constrain the tested surfaces |

The Windows audit pins six direct calls targeting the five recovered functions:
one Display `isAIO` call, one call to Disconnect, one call to the standalone
compatibility predicate, and three calls to `GetListBufRowContent`. Disconnect
and the active AppSync row path each contain their relevant decision inline, a
platform-specific call-graph difference retained in narrow disassembly slices.
The dual-slice direct-call negative result remains the broader symbol-derived
inventory. No Mach-O address or call count is transferred to the PE **[DEC]**.

`data/static-analysis/windows/device-semantic-audit.json` adds two independent
whole-image searches. The normalized FileType/SampleRate sequence appears
exactly twice: once in the standalone path at `0x14227e2d2..0x14227e2f4` and
once in the AppSync row builder at `0x14238cb54..0x14238cb74`. The scan includes
all 174,813 PE runtime-function records and permits the standalone sequence to
cross its chained `.pdata` boundary. It therefore finds no third semantic copy
of the known compatibility predicate **[DEC]**.

The same artifact inventories every exact ASCII `XDJ` and `XDJ-AZ` occurrence
and every direct RIP-relative `LEA` reference. Thirty-seven references exist;
the sole reference to the bare `XDJ` prefix literal is at `0x142381659` inside
the known `isAIO` helper. The other 36 reference exact `XDJ-AZ` literals and do
not duplicate the general XDJ-prefix classification. Dynamically constructed
model strings and classifiers with a different instruction shape remain an
explicit boundary **[DEC]**.

The symbol-rich x86-64 slice supplies the subsystem ownership that stripped
Windows addresses cannot. The generated
`data/static-analysis/model-literal-owner-audit.json` finds 30 direct exact-
literal references: 19 audio-device, 6 controller-mapping, 2 application-UI,
1 anonymous deck-helper, and exactly 2 database-serving references. The two
database references are the bare `XDJ` and redundant `XDJ-AZ` loads in the
same `PSvDBMain::isAIO(unsigned char)` body. This classifies every direct
exact-literal use in that slice without importing macOS addresses into the
Windows call graph **[DEC]**.

### Exact model UI predicates

`ProDJLink::isSpecificModel(player, literal)` copies at most 20 model bytes and
performs an exact C-string comparison. Its 35 direct call sites belong to UI,
layout, switch mapping, link-panel, remote-control, or remote-settings
functions. The recovered literals are:

| Literal | Direct-use surfaces |
| --- | --- |
| `XDJ-XZ` | Link panels, layout, device display, common-message handling, remote settings |
| `XDJ-AZ` | Link panels, layout, device display, common-message handling, remote settings |
| `XDJ-RR` | Switch mapping, remote settings |
| `XDJ-RX2` | Switch mapping, remote settings |
| `OPUS-QUAD` | Device display, switch mapping, UI commands, remote settings |

`ProDJLink::isCDJNetwork()` returns a cached byte from the link-device manager.
Its five direct callers are also UI or remote-settings code. These branches
explain visible application controls without implying dbserver menu changes
**[DEC, OBS]**.

### Drag-and-drop AIO deck form

`PSvLinkNetworkAccess::instPlayMusic` compares the destination's model name
exactly with `OPUS-QUAD`. Equality selects
`PSvLinkDDIndicationInfo::setDeckAIO`; every other model selects `setDeck`.
This decision affects the drag-and-drop play indication packet, not database
menu construction or Display Song Info. An `XDJ*` prefix is not used here
**[DEC]**.

These three classifiers must retain separate names in tests and
implementations:

- `display_song_info_xdj_prefix`;
- `exact_model_ui_behavior`;
- `opus_quad_drag_drop_deck_form`.

Collapsing them into one `is_aio` capability would predict behavior the binary
does not implement.

## Capability bits

`PSvLinkNormalInterval` exposes three per-player predicates over a stored
capability byte **[DEC]**:

| Predicate | Bit | Direct consumers |
| --- | ---: | --- |
| `isSupportMysetting` | 3 (`0x08`) | My Settings data and read-response messages |
| `isSupportDuplicationv2` | 2 (`0x04`) | My Settings data and read-response messages |
| `isSupportDeviceSetting` | 7 (`0x80`) | Device-setting read-response and renewal messages |

Players 9 through 12 use the alternate record bank selected by the same three
helpers. None of their six direct consumers is a database-menu builder. These
bits belong in the broader Pro DJ Link/device-settings map, but they are not
evidence for Link Export navigation differences.

## Track compatibility is not peer identity

`DsqlContent_GetNewCDJSupported(content_id)` has a device-sounding name but
accepts only a content ID. It reads content metadata and is called from the
track row builder. Its result changes the compatibility bit in the row for all
clients using that request path; the current function does not receive the
requesting player's model, class, generation, or capability mask **[DEC]**.

The complete body reads `FileType` column `0x0e` as a signed byte. Raw bytes 5
and 6 return false; bytes 11 and 12 read `SampleRate` column `0x21` and return
true only for 44100 or 48000; all other bytes return true. No BitDepth column
is read. This is a content-only byte/rate predicate rather than a codec-name,
peer-generation, or bit-depth capability table **[DEC]**.

The eight-track compatibility oracle independently confirms supported and
failure cases without media files **[OBS]**. The completed 382-row
extended/legacy oracle exhausts the FileType byte domain, integer narrowing
controls, SampleRate boundaries, and BitDepth invariance. Both setup widths
return all 382 rows and repeat exactly: 298 are supported and 84 unsupported,
and every 12-field legacy row is the exact prefix of its 16-field extended row
**[OBS, DB]**. Device identity and track compatibility remain separate axes
even when a client uses the row bit to decide whether it can load a track.

## Negative result and boundary

Across both pinned slices, direct-reference evidence finds no explicit model
predicate in:

- root and sort menu construction;
- category query dispatch and database filtering;
- pagination and list serialization;
- secondary-column selection and formatting;
- Play Song Info and Delivery Info builders;
- adjacent artwork, waveform, beat-grid, VBR, segmented-key, and arbitrary-atom
  payload builders;
- setup width or root capability-mask handling.

This agrees with the eight-identity ordinary-menu oracle and the genuine
RX3/CDJ status-backed Play and Delivery crosses **[DEC, OBS]**. For adjacent
payloads, the exact dispatcher and loader audit independently identifies
packed track type, identifiers, atom tag, extension, database path, and file
bytes as inputs; the successful matched-status cross remains pending. The
Windows full-image audit also finds zero absolute pointer references to the
five recovered Display, disconnect/cache, compatibility, and row-builder
functions, excluding ordinary pointer-table and vtable storage for those exact
addresses. Its semantic companion exhausts the known compatibility sequence
and direct bare-XDJ literal use. This remains a bounded negative result:
computed function pointers, dynamically constructed model strings, cached
state written elsewhere, and architecture-specific behavior outside these
signatures remain outside the scan. Status packet shape can
also change whether a request
reaches a builder at all; the malformed Play/Delivery dispatch observations
remain a separate dynamic surface.

Audio/HID/MIDI controller classification (`djplay::DeviceDefs`), removable
storage classification, audio device types, and rendering backends are
different subsystems. They are explicitly excluded from the generated peer
identity inventory so similarly named `is*Device` functions do not inflate the
Link Export matrix.

## Reproduction

From `/home/evan/workspace/rx3-research/rekordbox-link-export-research`:

```sh
BIN=../artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox

.venv/bin/python tools/audit_device_predicates.py "$BIN" \
  --json data/static-analysis/device-predicate-audit.json \
  --markdown data/static-analysis/device-predicate-audit.md

.venv/bin/python tools/audit_device_predicates.py "$BIN" \
  --architecture arm64 \
  --json data/static-analysis/device-predicate-audit-arm64.json \
  --markdown data/static-analysis/device-predicate-audit-arm64.md

.venv/bin/python tools/disassemble_symbols.py "$BIN" \
  'ProDJLink(12isCDJNetwork|15isSpecificModel|12getModelName|13getModelNames)|PSvDBMain(5isAIO|11clearAIOMap)|PSvLinkNormalInterval(18isSupportMysetting|22isSupportDuplicationv2|22isSupportDeviceSetting)|DsqlContent_GetNewCDJSupported' \
  --output data/static-analysis/device-predicate-bodies.disasm.txt

.venv/bin/python tools/disassemble_symbols.py "$BIN" \
  'WidgetProDJLink14displayDevices|WidgetLinkMixer10setVisible|DJSystemRemoteComponent6update|WidgetLinkPlayer7resized|UiProDJLink19handleCommonMessage|RemoteSettingController9updateAll|UiProDJLink23convertLinkIDtoSwitchID|UiProDJLink17handleSwitchEvent|UiProDJLink7perform' \
  --output data/static-analysis/device-model-callers.disasm.txt

.venv/bin/python tools/audit_model_literal_owners.py "$BIN" \
  data/static-analysis/windows/device-semantic-audit.json \
  --output data/static-analysis/model-literal-owner-audit.json
```

The audit exits if the executable hash differs or any selected symbol is
missing. Regenerating to temporary paths and comparing bytes verifies that the
JSON and Markdown outputs are deterministic. The generator resolves the binary
argument before serializing provenance, so the documented relative invocation
and an absolute invocation produce identical artifacts.

`conformance/test_device_predicate_audit.py` regenerates all four files through
the documented relative path and compares them byte for byte with the
checked-in artifacts. It also pins both inventories at 23 targets: x86-64 has
67 validated direct references and five database-serving references, while
ARM64 has 68 and six. The test requires the compatibility helper's duplicate
ARM64 call to be the only per-target count difference.
