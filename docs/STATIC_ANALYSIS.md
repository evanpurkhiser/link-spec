# Static-analysis provenance

This chapter makes the rekordbox executable findings reproducible and bounds
what they prove.

## macOS target

| Property | Value |
| --- | --- |
| Product | rekordbox 7.2.19 |
| File | `artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox` |
| Size | 301,587,792 bytes |
| SHA-256 | `07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244` |
| Container | Universal Mach-O |
| Analyzed slice | x86-64 |
| Other slice | arm64 |

The binary retains a large symbol table. Symbol names are implementation
evidence, while disassembly establishes control flow, constants, calls, and
literal references. Neither substitutes for a wire capture when serialization
or runtime state can alter behavior.

## Windows target

| Property | Value |
| --- | --- |
| Product | rekordbox 7.2.19.0 |
| Guest file | `C:\Program Files\rekordbox\rekordbox 7.2.19\rekordbox.exe` |
| Size | 103,540,656 bytes |
| SHA-256 | `c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37` |
| Container | PE32+ |
| Architecture | x86-64 |

The Windows executable is the exact file used by the live oracle. It is
stripped of the useful function symbols retained by the macOS build.
`tools/analyze_windows_pe.py` recovers function bounds from `.pdata`, validates
decoded immediate references, annotates selected functions, and resolves MSVC
class vtables through RTTI type descriptors and complete-object locators.

The full PE is extracted to temporary host storage from the retained exact
installer at `../rekordbox-windows/shared/Install_rekordbox_x64_7_2_19.exe`;
copying the installed guest path is a hash-equivalent fallback. The lab retains
hash-pinned metadata and focused derived disassembly under
`data/static-analysis/windows/` without duplicating the 103 MB executable.

## Local toolchain

The project-local `.venv` contains `lief 0.17.1` and `capstone 5.0.6`.
`tools/disassemble_symbols.py`:

1. Selects the x86-64 slice.
2. Indexes symbols by virtual address.
3. Selects functions by regular expression.
4. Bounds each function at the next symbol address.
5. Annotates direct calls/jumps and printable RIP-relative strings.
6. Marks matching data/unmapped symbols rather than treating them as code.

`tools/find_direct_xrefs.py` scans the text for direct x86-64 `rel32` call/jump
references to one or more virtual addresses. Candidate opcodes are validated by
linear disassembly from their owning symbol. A zero result does not exclude
function pointers, vtables, computed branches, inlining, or references from
another architecture.
`tools/list_symbols.py` inventories address-bearing symbols by regular
expression for either architecture before a focused disassembly is generated.
`tools/find_immediate_references.py` first locates plausible little-endian
immediates in executable ranges, groups them by owning symbol, and disassembles
only those owners. This makes request-kind searches over the 301 MB binary
reproducible without treating raw data matches as code.

`tools/analyze_windows_pe.py` provides the corresponding stripped-PE workflow.
It treats `.pdata` runtime entries as authoritative function bounds and uses
MSVC RTTI to bind indirect virtual dispatch to concrete functions. It also
supports multi-immediate and memory-displacement signatures, fast validated
direct control-transfer references, absolute-pointer searches, and explicit
code ranges spanning split unwind entries. This avoids assigning macOS symbol
names to Windows addresses merely because their code is similar.

## Generated evidence

`data/static-analysis/` contains:

| File | Scope |
| --- | --- |
| `root-sort-menu.disasm.txt` | Root and sort menu builders |
| `settings-and-menu.disasm.txt` | Settings tables, initialization, and menu reads |
| `subcolumn-mutators.disasm.txt` | Selection-bit setters/clearers |
| `subcolumn-sql.disasm.txt` | Selected-secondary SQL and row-builder context |
| `subcolumn-controller-paths.disasm.txt` | Dev, AppSync, and desktop-controller secondary-column readers and writers, including exact AppSync SQL and dispatch |
| `client-and-render.disasm.txt` | List dispatch and row serialization |
| `predicates-and-mapping.disasm.txt` | Category/sort predicates, icon and secondary mapping |
| `menu-query-functions.disasm.txt` | All `djeplGet*` menu family functions |
| `sql-literal-index.json` | Generated exact SQL literal/fragment index over every retained disassembly artifact, including hashes, addresses, function ownership, platform, and duplicate provenance |
| `rowset-builders.disasm.txt` | Shared entity/track rowset builders and filters |
| `device-and-dispatch.disasm.txt` | Client dispatch, unknown response, AIO classifier |
| `adjacent-link-export-dispatch.disasm.txt` | Analysis/image/other request dispatch and adjacent payload loaders |
| `adjacent-payload-loaders.disasm.txt` | AppSync/Master artwork paths plus detailed waveform, segmented-key, and extended-cue builders |
| `adjacent-payload-services.json` | Generated image/analysis request, reply, database, filesystem, and response-shape contract |
| `other-client-dispatch.disasm.txt` | Complete `3xxx` low-byte router and list-buffer, History, Prepare, Other, User, Filter, and Other2 handlers |
| `link-export-dispatch-tables.json` | Exact SHA-verified decoding of ten list, Year, analysis, history, prepare, other, and filter switch tables plus the top-level default route |
| `link-export-request-vocabulary.json` | Complete joined client/server command ledger with live, static, rejected, log-only, source-only, and reply states |
| `control-mutation-command-map.json` | Generated 54-command join across every `0x2x05`, `0x2x07`, and `0x3xxx` request, Rekordbox route/effect, and 97 direct XDJ-RR caller sites |
| `year-list-handler.disasm.txt` | Complete Release Year, rejected Stock Date, and Date Added switch implementation |
| `source-only-client-handlers.disasm.txt` | XDJ-RR old-Key/Cue Track routing, complete `OnWriteCmd` and `OnDbModCmd` switches, named write targets, and reply constructors |
| `source-only-client-db-effects.disasm.txt` | AppSync old-Key builders, Rating/BPM mutations, analysis-path lookup, and quantize-offset flag mutation |
| `device-symbols.txt` | Device, model, player, compatibility, and AIO symbol inventory |
| `device-direct-xrefs.txt` | Validated direct callers of six device/compatibility functions |
| `device-identity-paths.disasm.txt` | Device discovery, AIO use, compatibility, and identity call paths |
| `device-predicate-audit.{json,md}` and `device-predicate-audit-arm64.{json,md}` | Generated dual-slice identity/capability audit: the same 23 targets, 67 x86-64 and 68 ARM64 direct references, and caller-scope classification |
| `device-predicate-bodies.disasm.txt` | Model, AIO, settings-capability, and track-compatibility predicate bodies |
| `model-name-state-path.disasm.txt` | Player-status model storage, model-change message `0x6e`, membership path, accessor chain, UI notification, and Display AIO cache |
| `device-model-callers.disasm.txt` | All direct exact-model/UI callers and their literal-model construction |
| `db-interface-selection.{json,md}` | Complete x86-64 RIP-relative vtable-selection audit for AppSync and Master database interfaces |
| `db-interface-selection.disasm.txt` | Shared-interface installation plus all FilterSettingManager/TrackFilter AppSync-versus-Master branches |
| `unobserved-list-handlers.disasm.txt` | Play Count, Prepare, New Key, My Tag, and Date Added list dispatchers |
| `mytag-prepare-queries.disasm.txt` | My Tag and Prepare database query implementations |
| `listbuf-layout.disasm.txt` | Materialized list-buffer schemas, insertion record packing, and shared row builders |
| `list-buffer-location.disasm.txt` | Packed-context key storage, selective clear, render predicate, and process-wide `djmdLeftBuf` access |
| `context-track-type.disasm.txt` | Track request dispatch, active AppSync Track root, final-byte extraction, and type-one render enrichment gate |
| `context-track-type-routing.disasm.txt` | Top-level request-class dispatch and exact list-family interception of context types `0x03` and `0x04` |
| `bpm-tolerance-boundaries.disasm.txt` | Track selector 6 integer bound construction, zero-tolerance whole-BPM special case, and inclusive predicate |
| `listbuf-insert.disasm.txt` | Track-row construction and configured right-column insertion |
| `right-column-precompute.disasm.txt` | Right-column selection, mapping arrays, numeric keys, and table-string formatting |
| `played-track-cache-member-xrefs.txt` | Exhaustive `PSvDBMain` references to the Link-played array and its critical section |
| `played-track-cache.disasm.txt` | Played-state settings persistence, controller bits, ID extraction, dbserver handoff, and atomic cache replacement |
| `played-track-producers.disasm.txt` | Desktop and Link-history played-state producers, per-track and global clearers, UI callbacks, and DB-server refresh notification |
| `hot-cue-bank.disasm.txt` | `0x2001` catalog plus `0x2101` cue dispatch, membership-to-`djmdCue` getters, AppSync alternative, and `0x4702` serializer |
| `hot-cue-bank-membership-resolver.disasm.txt` | Exact AppSync bank/slot-to-CueID resolver used by setters, including its one-row rejection branch |
| `hot-cue-bank-legacy-setter.disasm.txt` | AppSync fixed-record setter and `GetUsbCue` response source for `0x2201` |
| `dbserver-command-parser.disasm.txt` | Complete `DBCFmt_GetCmdPrmFmt`, `PostServerMessage`, and `OnClientReq`; `0x2401` is declared as six fields tagged number, number, number, number, blob, number |
| `dbserver-connection-send.disasm.txt` | Complete `PSvDBConnection` receive/send path; blob lengths must be `1..0x4fffff`, an oversized blob leaves a partial command for dispatch, and Drop/Listen/destructor paths emit the `0xfffffffe/0x0100` close sentinel |
| `song-info-command-lifecycle.disasm.txt` | Synchronous `PSvDBMain` request execution, player-keyed asynchronous response queue, disconnect cleanup, and socket-drop routing that explains the observed malformed Song Info orphan reply |
| `player-hosted-song-info.json` | Twenty-three-source role audit for `0x2202..0x2502`: successful XDJ-RX player-hosted generic/summary builders; five-generation decode-info `0x4802` and one-way track-length client contracts whose local server arms are stubs; plus hash-bound whole-tree scans of 26,862 newer-generation C sources proving all exact `0x2402`/`0x2502`/`0x4802` literals remain confined to name/format tables |
| `user-info-djid.disasm.txt` | `0x3006` dispatch and `0x4d02` construction, DJ-ID ownership, profile path/validation, and server-start forwarding |
| `user-info-djid.json` | Generated SHA-bound Rekordbox 7.2.19 and CDJ-3000 audit for `djprofile.nxs`, the 32/160-byte payload split, post-load request chain, and live-evidence boundary |
| `dbserver-command-free.disasm.txt` | Complete `DBCCmd_Free`; every materialized string/blob/array argument pointer is freed according to the command-format tag table |
| `hot-cue-reply-routing.disasm.txt` | `RetNewCueToClient` and `RequestToSendData`; correlated `0x4e02` replies retain the transaction but enter the shared DB communications queue keyed by player/device byte rather than an originating socket |
| `hot-cue-setter-reply-target.json` | Reproducible AppSync vtable resolution proving that setter reply slot `+0x288` is `getHCBnkCuePointExt`, with database-update and returned-slot call ordering |
| `cue-time-conversion.disasm.txt` | Complete millisecond-to-150-fps cue/loop conversion, including loop-end decrement |
| `hot-cue-seek-fault.disasm.txt` | AppSync extended getter plus both advancing unsigned parsers, proving the inbound/outbound interior-pointer frees |
| `display-song-info-dispatch.disasm.txt` | `0x2002` dispatch, AppSync/Master builders, database reads, and AIO branch |
| `display-song-info-direct-xrefs.txt` | Validated dispatch, builder, and model-update caller chain |
| `category-configuration-fields.disasm.txt` | Exact root-serving category columns versus settings-editor `InfoOrder`; proves enabled empty categories remain visible and `InfoOrder` has no recovered root/Display wire effect |
| `request-1500-immediates.txt` | Every validated x86-64 owner containing immediate request kind `0x1500` |
| `request-1500.disasm.txt` | Formatter, dispatch, and cache owners selected from the immediate scan |
| `search-result-implementation.disasm.txt` | Complete ordinary/new-command search implementation bodies |
| `playlist-queries.disasm.txt` | Playlist Link Export wrappers and lower-level list, track, data, and count getters |
| `smart-playlist-paths.disasm.txt` | `getRowset_Playlist`, desktop smart-list track getters, and related evaluator entry points |
| `smart-condition-evaluator.disasm.txt` | Smart condition XML parsing, fixed/relative date conversion, string comparison, and track-condition evaluation |
| `smart-xml-parser.disasm.txt` | SmartList document loader and direct-child node parser, including logic fallback and condition admission |
| `smart-date-conversion.disasm.txt` | Complete fixed-date and relative day/month conversion helpers |
| `smart-collation.disasm.txt` | Complete ICU-backed text equality, contains, starts-with, ends-with, and constructor bodies |
| `windows/rekordbox-metadata.json` | Exact Windows PE identity, sections, entrypoint, and recovered function count |
| `windows/manifest.json` | Hash-bound source identity, analyzer identity, exact invocation, and artifact hash for every retained Windows static extract |
| `windows/request-1112-immediates.json` | Both validated `0x1112` immediate owners |
| `windows/request-1112-dispatch.disasm.txt` | History root/track dispatch and virtual slots `+0x228`/`+0x230` |
| `windows/appsync-history-vtable.json` | RTTI-derived `PSvAppSyncDBIF` vtable slice binding `+0x230` to `0x14236c690` |
| `windows/appsync-history.disasm.txt` | Active Windows History query and row-construction implementation |
| `windows/request-2002-immediates.json` | Validated Windows `0x2002` dispatcher owner |
| `windows/song-info-dispatch.disasm.txt` | Windows Display Song Info dispatch to the database interface |
| `windows/display-song-info-wrapper.disasm.txt` | Wrapper call through virtual slot `+0x168` |
| `windows/appsync-display-vtable.json` | RTTI-derived slot binding to the active AppSync formatter |
| `windows/appsync-display-song-info.disasm.txt` | Active Windows content query, field construction, AIO branch, and Key call |
| `windows/is-aio.disasm.txt` | Windows cached XDJ-prefix model classifier |
| `windows/device-predicate-audit.json` / `.md` | Exact Windows Display, disconnect/cache, row-compatibility ownership and direct-call counts |
| `windows/device-semantic-audit.json` | Whole-image Windows compatibility-signature and exact XDJ/XDJ-AZ literal-reference audit |
| `model-literal-owner-audit.json` | Symbol-rich subsystem ownership for every direct exact-XDJ literal reference, bound to the Windows companion counts |
| `windows/disconnect-aio-cache.disasm.txt` | Windows Disconnect with the player-keyed AIO-map erase inlined |
| `windows/clear-aio-map.disasm.txt` | Separately emitted map-only AIO clear helper with zero direct calls |
| `windows/content-compatibility.disasm.txt` | Complete standalone Windows FileType/SampleRate predicate |
| `windows/get-list-row-content-compatibility.disasm.txt` | Active AppSync inline predicate and alternate Master-interface standalone call |
| `DEVICE_PREDICATE_AUDIT.md` Windows PE evidence boundary | Separates exact Windows inline/call ownership from the broader symbol-derived Mach-O inventory and runtime authority |
| `windows/exchange-key-name.disasm.txt` | Windows local-device Classic/Alphanumeric Key conversion |
| `windows/local-key-style.disasm.txt` | Windows `DEVSETTING.DAT` key-style predicate |
| `../experiments/link-visibility/windows-history-summary.json` | Machine-checked PE identity, virtual dispatch, SQL, field absence, macOS xrefs, and artifact hashes |

These files are generated artifacts, not edited decompilation. Each address
applies only to the platform and pinned binary hash named by its provenance.

Regenerate the user-info/DJ-ID evidence from the lab root with:

```sh
.venv/bin/python tools/disassemble_symbols.py \
  ../artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox \
  '(__ZN6common12PropertyPathEv|__ZN11KuvoService7isValidERKN4juce4FileE|__ZN11KuvoService7nxsFileEv|__ZN11PSvDBServer5StartEPKhPKNS_12SharedDBInfoE|__ZN9PSvDBMain9OnUserCmdEP16_struct_dbsm_msg|__ZN9PSvDBMain5StartEPKh|__ZN9PSvDBMain7GetDJIDEPh)' \
  --max-bytes 0x10000 \
  --output data/static-analysis/user-info-djid.disasm.txt
.venv/bin/python tools/audit_user_info_djid.py \
  --output data/static-analysis/user-info-djid.json
```

Regenerate the played-state evidence from the lab root with:

```sh
.venv/bin/python tools/find_member_offset_references.py \
  ../artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox \
  0x698 0x6d8 0x6e4 --symbol-pattern PSvDBMain \
  --output data/static-analysis/played-track-cache-member-xrefs.txt
.venv/bin/python tools/disassemble_symbols.py \
  ../artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox \
  'PSvDB(Main26NotifyLibraryUpdatedPlayed|Server26NotifyLibraryUpdatedPlayed)|Database(IF16getAllLinkPlayed|Mediator16getAllLinkPlayed)|rekordboxDBController(19getAllLinkPlayedIDs|18updatePlayedStatus|24clearAllLinkPlayedStatus|22setInitialPlayedStatus)|PlayedSettingFile(20get_prop_file_option|15getPlayedTracks|16savePlayedTracks)|SettingIF(22getCurrentPlayedOption|26getCurrentLinkPlayedOption)' \
  --max-bytes 0x10000 \
  --output data/static-analysis/played-track-cache.disasm.txt
.venv/bin/python tools/disassemble_symbols.py \
  ../artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox \
  'DatabaseMediator(21addTrackToPlayHistory|22notifyDBUpdatedHistory|17deleteLinkHistory|15notifyDBUpdated|16notifyToDBServer|D2Ev)|DatabaseIF(15notifyDBUpdated|17deleteLinkHistory|21addTrackToPlayHistory|24clearAllLinkPlayedStatus)|UiProDJLink(18ReceiveUpdateEvent|23ReceiveDeleteHisotryCmd)|PlayHistoryManager13timerCallback|ViewBrowsePlayedColorComponent13buttonClicked' \
  --max-bytes 0x10000 \
  --output data/static-analysis/played-track-producers.disasm.txt
```

`tools/extract_link_export_dispatch_tables.py` uses only Python's standard
library to select the x86-64 universal-binary slice, parse `LC_SEGMENT_64`, map
virtual addresses, and decode signed relative offsets. The complete routing
interpretation and its client-enum boundary are in
`LINK_EXPORT_REQUEST_VOCABULARY.md`; the corresponding conformance test
requires byte-identical extraction and vocabulary generation.

The Year-handler body is retained separately because its jump table closes the
last four client-enum requests that previously lacked terminal server
evidence. Regenerate it with:

```sh
.venv/bin/python tools/disassemble_symbols.py \
  ../artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox \
  'OnYearListCmd' \
  --output data/static-analysis/year-list-handler.disasm.txt
```

## Shared database interface selection

The two database interfaces have equal `0x328`-byte vtables, but their
construction sites give them different roles. The generated audit validates
six RIP-relative LEA references into `PSvAppSyncDBIF` and three into
`PSvMasterDBIF` across the complete pinned x86-64 `__text` section **[DEC]**.

`PSvDBMain::SetSharedDBInfo` is the only `PSvDBMain` selection site. It
allocates `0x28` bytes, writes `PSvAppSyncDBIF`'s object vptr, stores the object
at `PSvDBMain + 0x690`, and sets or constructs `FilterSettingManager` with
database index `3`. `PSvDBMain` initializes the same field to null and destroys
it through its virtual destructor slot **[DEC]**.

All three Master references occur in exactly these functions:

- `FilterSettingManager` constructor;
- `FilterSettingManager::setDBIndex`;
- `TrackFilter` constructor.

Each function branches on `RbDBIndex == 3`: the equal arm constructs a
40-byte AppSync object, including its extra two-vector state, and the unequal
arm constructs a 16-byte Master wrapper. The three paired branches account for
every Master selection site found by the audit. AppSync has one additional
constructor in `SetSharedDBInfo` and two exact `vtable + 0x10` destructor
resets. Thus the active shared Link Export backend is AppSync; Master supports
non-index-3 desktop/filter operations rather than a second selected
Link Export server backend **[DEC]**.

The audit's negative boundary is explicit: it covers validated RIP-relative
LEA references in the x86-64 text slice. It does not exclude computed
addresses, references outside text, dynamically loaded construction, or
arm64-only behavior.

## Windows History platform boundary

The stripped Windows `0x1112` dispatcher at `0x142385970` calls virtual slot
`+0x230`. MSVC RTTI identifies the live database interface as
`PSvAppSyncDBIF`; its slot target is `0x14236c690`. That function reads
`TrackNo` and `ContentID` from the history rowset, selects the corresponding
live content row, formats the configured secondary value, and inserts it. It
does not read `FolderPath` or call an explicit streaming-visibility predicate.

The pinned macOS `djeplGetTrack_History` implementation differs: its two loops
call `dsqlIsLinkExportVisibleTrack` at `0x1010c5e12` and `0x1010c5f20` before
insertion. The real Windows oracle returning all fourteen controlled rows is
therefore explained by a concrete platform-specific query pipeline **[OBS,
DEC]**.

## Windows Display and key-style paths

The exact installed Windows 7.2.19 PE has SHA-256
`c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37`.
The stripped `0x2002` dispatcher at `0x142386ad0` calls wrapper
`0x14238e3e0`, which dispatches through database-interface vtable slot
`+0x168`. MSVC RTTI identifies the live object as `PSvAppSyncDBIF`; that slot
targets `0x142361f30` **[DEC]**.

The active formatter queries live `djmdContent` by ID, extracts the packed
context's high byte, and calls Windows `isAIO` at `0x1423815c0`. That helper
caches the result per player and tests the peer model for an `XDJ` prefix. Its
additional `XDJ-AZ` prefix check is a redundant subset. The true branch inserts
Comment immediately after the first five fields; the false branch inserts it
after Stock Date. This matches the symbolized macOS implementation and the live
RX3/CDJ ordering oracle.

The same formatter calls `0x14235e5e0` for Key text. This is the stripped
counterpart of `exchangeKeyNameIfNeed`; it calls `0x141c5f780`, the counterpart
of `DeviceSettingFile::isLocalKeyCatDispStyleNormal`, maps the result to Classic
or Alphanumeric notation, normalizes the input to one of 24 harmonic positions,
and selects the corresponding label table. The two-state `DEVSETTING.DAT`
oracle independently confirms every resulting string and UTF-16 length
**[OBS, DEC]**.

## Windows cache and compatibility ownership

Windows Disconnect at `0x142380930` acquires the lock at object offset `0x7a0`,
finds and erases the requesting player from the AIO-classification map at
offset `0x790`, then continues the remaining per-player disconnect cleanup.
The separately emitted map-only helper at `0x142381700` performs the same keyed
erase but has zero direct `call rel32` or `jmp rel32` references. This differs
from both Mach-O slices, where Disconnect calls `clearAIOMap` out of line
**[DEC]**.

Windows `GetListBufRowContent` at `0x14238c720` has two database-interface
branches. The active AppSync branch queries `FileType` and `SampleRate` and
inlines the complete compatibility truth table. The alternate Master branch
calls the standalone predicate at `0x14227e200` exactly once. The standalone
body selects `djmdContent` through `idxMasContent`, reads columns `0x0e` and
`0x21`, and implements the same byte/rate decisions. Neither Windows path reads
BitDepth **[DEC]**.

The generated Windows audit validates one direct call each to `isAIO`,
Disconnect, and the standalone compatibility predicate, plus three direct
calls to `GetListBufRowContent`; the map-only helper has none. These counts are
exhaustive for direct relative control transfers to the five recovered
functions. Indirect calls and other duplicated inline predicates remain a
separate bounded search surface.

## Malformed Song Info reply routing

`PSvDBMain::run` takes inbound commands from its queue and calls `OnClientReq`
synchronously. Correlated replies take a different path: `OnSongInfCmd` calls
`RequestToSendData`, which posts to `PSvDBComm` with a player byte and no
originating socket. `PSvDBMain::Disconnect(player)` clears filter and AIO state
and requests the socket drop, while the connection listener independently
constructs transaction `0xfffffffe`, kind `0x0100`, as its close sentinel
**[RB-DEC]**.

Malformed Delivery reads the low 32 bits of a blob allocation pointer as its
ContentID. The lookup misses, the builder returns zero, and the wrapper queues
the ordinary transaction-1 `0x4000 [0x2602, 0]` response. The close sentinel
can reach the originating socket first. When an immediate replacement socket
registers the same player, all four cold-process observations receive that
identical late frame after setup and before sending another request. Waiting
50 or 100 ms before replacement yields no frame in eight observations; twelve
matched valid-extra-argument controls also yield none. Draining the orphan is
sufficient for the same socket and a later fresh socket to return the correct
13-row Delivery result in all 24 observations **[OBS]**.

The static player-keyed queue plus the exact live frame establishes cross-
socket response routing. The absence at tested delays is consistent with the
reply being discarded when no player socket is registered, but the exact
discard instruction has not been isolated **[RB-DEC, OBS inference]**.

## Extended-setter overflow lifecycle

`DBCFmt_GetCmdPrmFmt` maps request `0x2401` to six argument tags at
`0x10049d80a`: number, number, number, number, blob, number. The command
receiver stores each argument in an eight-byte slot. Its blob case at
`0x10143b8a8` reads the preceding numeric slot as the allocation and receive
length. Values from 1 through `0x4fffff` allocate and receive that many bytes;
zero and values at or above `0x500000` branch to the argument-loop exit.

The exit is permissive. The oversized-value branch does not mark the command
invalid, free it, or synthesize a protocol error. `ReceiveCommand` returns the
zero-initialized command with its first four numeric values populated and its
blob pointer and final record-count value still zero. The active
`PSvAppSyncDBIF::setHCBnkCuePointExt` null-pointer/count guards consequently
return status 50 without reading a blob or mutating the database.

The connection event is separate. `PSvDBConnection` destructor, `Drop`, and
`Listen` error paths build a command with transaction `0xfffffffe` and kind
`0x0100`, send it, and drop the EDB agent. Live no-send observations then see
EOF on that socket, proving the frame is the close sentinel rather than a
correlated response. `RetNewCueToClient` retains transaction 1 for the actual
status-50 `0x4e02` and calls `RequestToSendData` with a player/device byte.
That function posts to the shared DB-communications queue without carrying the
originating socket. This establishes the mechanism by which the delayed reply
can reach a replacement connection registered for the same player identity.
The lifecycle timing matrix supplies the runtime bounds for that behavior
**[RB-DEC, OBS]**.

## Extended-setter slot-8 lifecycle

The active AppSync setter extracts the slot word at `0x1016d3fbd`, computes
`slot - 9`, compares the 16-bit result with `-8`, and takes the unsigned-below
branch at `0x1016d3fc9`. This wraparound predicate admits exactly slots 1
through 8. Slot 0 and every value from 9 through `0xffff` take the status-50
exit **[RB-DEC]**.

An admitted slot is passed unchanged to `HCBnkSong_GetCueID`. That resolver's
query returned zero rows for fixture bank 9060, slot 8. Its branch at
`0x1016d2e11..0x1016d2e23` rejects exactly `size() == 1`; zero and sizes above
one proceed to `var::operator[](0)`. The setter therefore reaches a row-zero
access on an empty query result **[DB, RB-DEC]**.

Three independent cold-process observations establish the runtime boundary.
The slot-8 setter and a fresh-socket immediate getter both timed out in every
run. Rekordbox remained alive and responsive, Windows recorded no new
Application errors, and logical snapshots showed the membership and cue rows
pristine. Restarting Rekordbox against the same database restored the getter:
all three runs returned the same status-zero, one-record, 124-byte baseline
reply, with the database still pristine **[OBS, DB]**.

The static empty-row access is consistent with this repeat-verified serving
stall. The artifacts establish correlation rather than a debugger-level causal
trace, so the exact internal blocking mechanism remains an inference
**[RB-DEC, OBS]**.

## Legacy-setter flag decoding

`DBCFmt_GetCmdPrmFmt` maps `0x2201` to seven tags, including packed context:
number, number, number, number, blob, number, blob. The two blob sizes are
therefore the numeric arguments immediately before the 36-byte cue record and
eight-byte millisecond extension. `ReceiveCommand` allocates exactly the
preceding numeric value for each blob when it is in `1..0x4fffff`, stores that
pointer in the command, and passes both the pointer and size by address to the
imported `_edb_comm_bytes` primitive. `DBCCmd_Free` later walks the same tag
table and frees every tag-1-through-3 pointer **[RB-DEC]**.

This localizes the declared-length-one/seven heap-corruption observations to
the command materialization and disposal lifetime, before `OnCueBnkCmd` sees
the record. The live requests carry eight extension bytes but allocate one or
seven. Both produce the same Windows heap-corruption exception. The imported
receive primitive is not present in the pinned binary, so whether it overruns
the declared allocation, records an inconsistent length, or damages allocator
metadata through another path remains an evidence-backed hypothesis rather
than a decompiled fact **[RB-DEC, OBS]**.

Declared length eight does not identify the later Link Export outage. Its wire
request is byte-for-byte identical across seven nominal cells. Eight earlier
cold-process observations accepted that request and served the immediate
getter; six later observations accepted the same request and then lost the
port-query listener until process restart. The
reducer now fingerprints the request independently of axis labels and exposes
this cross-variant lifecycle conflict. An interleaved history control is
required before assigning the outage to process history, crash recovery, or
another external state dimension **[OBS]**.

`PSvDBMain::OnCueBnkCmd` admits legacy mutation when the complete flag word is
in inclusive range `0x00040000..0x0006ffff`; its upper word consequently
selects ordinals 4, 5, and 6. Inside `PSvAppSyncDBIF::setHCBnkCuePoint`,
`0x1016d2954..0x1016d29aa` independently compares cue byte 0 with 1. Equality
loads extension dword 1 into `OutMsec`; every other byte value supplies
`0xffffffff`. Live flags `0x00040000`, `0x00040001`, and `0x00040100` confirm
the split: all target membership 94201, but only the low-byte-one form stores
the extension sentinel `0x88888888` **[RB-DEC, OBS, DB]**.

The same setter maps its 36-byte `cue_data` record without an intermediate
schema translation. Word 1 at `+0x04` becomes the decimal-string `ContentID`;
word 2 at `+0x08` is never loaded; and words 3 through 8 at offsets
`+0x0c,+0x10,+0x14,+0x18,+0x1c,+0x20` become `InFrame`, `OutFrame`,
`InMpegFrame`, `OutMpegFrame`, `InMpegAbs`, and `OutMpegAbs`, respectively.
The extension's first dword supplies `InMsec` when its pointer is usable, with
an `InFrame` conversion fallback, while the flag-byte rule above controls the
second dword's use as `OutMsec`. `Color` is always written as `-1`. No load from
word 2 occurs anywhere in `PSvAppSyncDBIF::setHCBnkCuePoint`. The complete
zero/`UINT32_MAX` live pairs change the request fingerprint while preserving
the setter response, semantic membership row, listener lifecycle, and restart
getter payload. They distinguish this static non-use from a value that is read
and then normalized away **[RB-DEC, OBS, DB]**.

## Extended-setter reply target and ordering

The generated `hot-cue-setter-reply-target.json` resolves the pinned x86-64
AppSync vtable rather than inferring its target from a nearby symbol. The
object vptr begins 16 bytes into `__ZTV14PSvAppSyncDBIF`; entry `+0x288` at
`0x105656fc8` contains little-endian pointer `0x1016d2f20`, exactly
`PSvAppSyncDBIF::getHCBnkCuePointExt` **[RB-DEC]**.

Both extended-setter exits call this slot. The rejection path loads the
requested return count at `0x1016d4068` and calls it at `0x1016d4074`. The
successful path completes its last database update at `0x1016d4c18`, then
loads the bank ID at `0x1016d4c76`, loads the return count at `0x1016d4c79`,
and calls the getter at `0x1016d4c85`. Reply generation is therefore a getter
operation after durable mutation, which accounts for the repeat-verified
returned-slot `UINT32_MAX` result: the mutation persists even though setter
reply and immediate getter both stall **[RB-DEC, OBS, DB]**.

## Extended-getter seek-info fault

`PSvAppSyncDBIF::getHCBnkCuePointExt` converts a nonempty
`InPointSeekInfo` database string to a newly allocated UTF-16 buffer. It stores
the base in a local cursor slot, then passes the slot by address to
`getUInt64Value` twice and `getUInt32Value` once. Each helper both returns one
unsigned decimal component and advances the cursor past digits and one
separator **[DEC]**.

At `0x1016d3664`, the getter reloads the now-advanced cursor and calls
`djrfree` with it at `0x1016d366d`. This is an interior pointer, not the
allocation base. The third return value has already overwritten the register
that held that base. The outbound branch repeats the same defect at
`0x1016d3842..0x1016d384b`; inbound validity gates that branch, and the inbound
invalid free occurs first. Empty inbound text avoids allocation, and
outbound-only text is never parsed **[DEC]**.

The isolated Windows oracle independently observes the predicted boundary:
outbound-only state returns a normal record, while inbound `1,2,3` times out
and leaves no Rekordbox process. The disassembly therefore localizes the live
process exit to the invalid free rather than the SQL query, decimal value, or
record serializer **[OBS, DEC]**.

## Key recovered functions

| Address | Symbol | Established behavior |
| ---: | --- | --- |
| `0x1004b23f0` | `PSvDBMain::GetRootMenu` | Category iteration, Folder suppression, Hot Cue compatibility insertion |
| `0x1004b2610` | `PSvDBMain::GetSortMenu` | Sort iteration and row construction |
| `0x1004b2760` | `PSvDBMain::GetHCBnkList` | Alternate master-database Hot Cue Bank tree/track branch, unsigned `max(count,3)`, and three full-width candidate allocations |
| `0x1016d1c60` | `PSvAppSyncDBIF::getHCBnkList` | Active local-library Hot Cue Bank SQL path; unsigned minimum-three calculation followed by a signed loop-limit comparison, making bit 31 the empty-result boundary without count-sized arrays |
| `0x101d2e730` | `PSvDBMain::OnCueBnkCmd` | Hot Cue Bank dispatch; `0x2201` mutation only for flag range `0x00040000..0x0006ffff`, followed by ContentID-based `GetUsbCue` even outside that gate |
| `0x102524860` | `PSvMasterDBIF::getHCBnkList` | Serialized Hot Cue Bank database wrapper |
| `0x101aba880` | `PSvDBMain::GetHCBnkCuePoint` | Membership cue-number to `CueID` to `djmdCue` resolution |
| `0x1016d2600` | `PSvAppSyncDBIF::getHCBnkCuePoint` | Direct membership timing-column alternative |
| `0x1025217f0` | `PSvDBMain::RetCueToClient` | Builds the direct `0x4702` cue-data response |
| `0x1016d2f20` | `PSvAppSyncDBIF::getHCBnkCuePointExt` | Active `0x2301` membership query and variable-record builder |
| `0x101abab00` | `PSvDBMain::GetHCBnkCuePointExt` | Master-DB `CueID`/option-table alternative for `0x2301` |
| `0x1016d28f0` | `PSvAppSyncDBIF::setHCBnkCuePoint` | Legacy `0x2201` membership update; consumes its ordinal without the master path's minus-three adjustment |
| `0x1016d3ef0` | `PSvAppSyncDBIF::setHCBnkCuePointExt` | AppSync extended mutation and canonical getter reply path |
| `0x10143b430` | `PSvDBConnection::ReceiveCommand` | Parses command tags and values; blob tag `0x03` takes its byte count from the preceding numeric argument, admits only `1..0x4fffff`, and returns an otherwise valid partial command when that bound fails |
| `0x10143bb60` | `PSvDBConnection::SendCommand` | Serializes replies and bounds blob arguments to at most `0x4fffff` bytes |
| `0x1016d2d70` | `HCBnkSong_GetCueID` | AppSync bank/slot resolver; rejects exactly one result, otherwise reads row zero |
| `0x101abb210` | `PSvDBMain::SetHCBnkCuePointExt` | Master-DB extended mutation path |
| `0x102521010` | `PSvDBMain::DeliverHCBankUpdate` | Gated delivery-sink callback `(class=3, CueID, 0)` after successful legacy or extended mutation |
| `0x1017b3000` | `djplay::UiProDJLink::notifyLinkConnect` | Installs the embedded `PSvDBServerCallback` subobject during database-server initialization |
| `0x1017b4e30` | `djplay::UiProDJLink::ReceiveUpdateEvent` | Maps callback class 3 to internal database-update type `0x1e` and calls `DatabaseIF::notifyDBUpdated(0x1e, CueID, 0)` |
| `0x1009b1f80` | `getUInt64Value` | Decimal UTF-16 seek component parser |
| `0x1009b1ff0` | `getUInt32Value` | Final decimal UTF-16 seek component parser |
| `0x100a05250` | `DsqlHCBnkSong_GetContentID` | Ordered bank-membership content/position resolution |
| `0x101011090` | `WhereCategory_Enable` | Disable special cases and capability-bit predicate |
| `0x101137870` | `WhereSort_Enable` | Bit-0 visibility predicate |
| `0x100f9fe40` | `GetListBufRowContent` | Track/entity field construction |
| `0x100fa1110` | `GetListBufContents` | Paging and `4001/4101/4201` serialization |
| `0x101d2c6c0` | `OnTrackListCmd` | Passes the complete packed context through the Track database-interface call |
| `0x1016bc8e0` | `PSvAppSyncDBIF::getTrack_Root` | Active ordinary-Track membership and context-keyed list-buffer construction |
| `0x1006eb3f0` | `WhereListBuf_Condition` | Exact equality between render context and `djmdLeftBuf` column zero |
| `0x10249cd50` | `DsqlListBuf_Insert` | Insert-record to 14-column `djmdLeftBuf` mapping and 255-code-unit caps |
| `0x10249cf40` | `DsqlListBuf_Clear` | Deletes rows for one packed context and preserves other context buffers |
| `0x10249cfc0` | `DsqlListBuf_InsEnd` | Restores list-buffer transaction state through `DsqlCmn_ChangeAutoCommitStat`; argument one commits, enables autocommit, and ensures the context index is open |
| `0x1016bf5b0` | `insertLeftBuf_Track` | Track primary/right fields, streaming exclusion, and precomputed formatter text |
| `0x101f3ed50`, `0x101f3edf0` | `dsqlIsLinkExportVisibleTrack` overloads | Invert the common streaming classifier for an ID or row |
| `0x101f3efd0` | `_isStreamingTrack` | Fetch content column 1 (`FolderPath`) and classify its protocol |
| `0x1030d8820` | `streaming::isStreamingProtocol` | Dispatch through active provider protocol handlers |
| `0x101614df0` | `dsqlGetRightListInfo_DB` | `MenuItemID` to field/type/formatter static maps |
| `0x1016bc730` | `getRightTrackKey` | Precomputed numeric value and sentinel rules |
| `0x1016b7bc0` | `Get_SubCategoryValue` | Secondary-column jump table and values |
| `0x1004dbb90` | `ReturnIconID` | Sort/category-to-type lookup table |
| `0x101d2bb80` | `OnListClientCmd` | Request-family dispatch |
| `0x102521340` | `OnClientReq` | Top-level request-class dispatch; diverts list requests with context low byte `0x03` or `0x04` before `OnListClientCmd` |
| `0x102521500` | `OnUnknownClientCmd` | `4003` unknown-command reply |
| `0x102521e80` | `isAIO` | Cached XDJ-prefix classification |
| `0x142386ad0` | Windows `0x2002` dispatcher | Display wrapper dispatch in the installed PE |
| `0x142361f30` | Windows AppSync Display formatter | Active content query, AIO order branch, and Key formatter call |
| `0x1423815c0` | Windows `isAIO` | Cached XDJ-prefix classification matching macOS |
| `0x142380930` | Windows Disconnect | Per-player cleanup with inlined AIO-map erase |
| `0x142381700` | Windows map-only AIO clear | Separately emitted keyed erase; zero direct calls |
| `0x14238c720` | Windows `GetListBufRowContent` | Active AppSync inline compatibility predicate and Master fallback |
| `0x14227e200` | Windows standalone content compatibility | Master-interface FileType/SampleRate predicate |
| `0x14235e5e0` | Windows `exchangeKeyNameIfNeed` | Local-device Classic/Alphanumeric conversion |
| `0x141c5f780` | Windows local Key-style predicate | Loads the `DEVSETTING.DAT` category style |
| `0x1016c01b0` | `PSvAppSyncDBIF::getDispSongInf` | AIO-dependent display-item ordering |
| `0x101d2edc0` | `PSvDBMain::OnSongInfCmd` | `0x2002` through `0x2602` song-information dispatch |
| `0x101ab8190` | `PSvDBMain::GetDispSongInf` | Database-interface dispatch for Display Song Info |
| `0x101ab7b90` | `PSvDBMain::GetDispSongInfDB` | Master-database content/category lookup path |
| `0x102523c40` | `PSvMasterDBIF::getDispSongInf` | Locked Master-database wrapper |
| `0x101ab8f70` | `PSvDBMain::GetPlaySongInf` | Active Play Song Info database-interface dispatch |
| `0x1016c14e0` | `PSvAppSyncDBIF::getPlaySongInf` | Seven-row live-content, file-path, and Hot Cue metadata builder |
| `0x1016b9b60` | `convertToRealPath` | Unified path conversion and conditional AppSync drive replacement |
| `0x101ab8320` | `PSvDBMain::GetPlaySongInfDB` | Static fallback Play Song Info builder |
| `0x101ab8f10` | `PSvDBMain::GetDeliveryInf` | Active Delivery Info database-interface dispatch |
| `0x1016cdc00` | `PSvAppSyncDBIF::getDeliveryInf` | Thirteen-row Delivery metadata and lookup builder |
| `0x101ab8700` | `PSvDBMain::GetDeliveryInfDB` | Static fallback Delivery Info builder with 19 insertion sites |
| `0x10049d4a5` | `DBCFmt_GetCmdPrmFmt` `0x1500` case | Four arguments tagged number, number, number, string |
| `0x10252237e` | `PSvDBMain::getListCmdCacheResult` `0x1500` case | Search Track cache lookup branch |
| `0x1025224ed`, `0x10252270a` | `PSvDBMain::setListCmdCacheResult` `0x1500` cases | Search Track cache insertion branches |
| `PSvDBMain::OnOtherListCmd` jump-table case | Search Track dispatch | Signed low-byte sort ID, 5,000 budget, and new-command flag |
| `PSvAppSyncDBIF::getNewSearchResult` | Shared Search backend | Common ordinary/Search Track search interface |
| `PSvAppSyncDBIF::getNewSearchResultForNewCommand_Content` | Search Track content implementation | New-command content scan and configured sort path |
| `0x1004b3d20` `djepl_getPlaylistTracks` | Playlist track wrapper | Context/sort setup, rowset acquisition, visibility checks, and row construction |
| `0x100489470` `getRowset_Playlist` | Playlist rowset builder | Membership/track selection and sorting path used by Link Export |
| `0x101ba9720` `db::dsqlGetPlaylistTrack` | Lower-level playlist membership getter | Table key 9 selection by playlist ID, TrackNo sort, and ContentID extraction |
| `0x1019c3d90` `rekordboxDBController::getSmartPlaylistTrack` | Desktop smart-list getter | Calls `getSmartlistContentData`, distinct from the simple membership getter |
| `0x102334b00` `db::getSmartlistContentData` | SmartList content loader | Parses the stored XML with JUCE, requires a document element, obtains a node, then evaluates the collection |
| `0x102335130` `db::getSmartlistNode` | Smart node parser | Requires `NODE`, collects only direct `CONDITION` children, rejects zero conditions, and defaults logic outside 1/2 to all-of |
| `0x1023354a0` `db::operate` | Track-condition evaluator | Rejects invalid date conversions; property type `0x40` accepts only My Tag operators 8/9 and scans the tag array/count at track offsets `0x440`/`0x44c` |
| `0x102335b20` `db::dateToDay` | Fixed-date parser | Requires length 10, consumes positions 0-3/5-6/8-9 without digit checks, ignores positions 4/7, normalizes through the C time runtime, and returns zero for nonpositive conversions |
| `0x1023359e0` `db::operateString` | String-condition evaluator | Applies property-specific string operators |
| `0x102333de0` `db::CollationRule::equals` | Collation equality | Serializes access to the shared ICU search object and performs boundary-aware primary-collation equality |
| `0x102334110` `db::CollationRule::contains` | Collation containment | Performs ICU search while advancing on Unicode code-point boundaries |
| `0x102334430` `db::CollationRule::startsWith` | Collation prefix | Requires the collation match at the start boundary |
| `0x102334720` `db::CollationRule::endsWith` | Collation suffix | Requires the collation match to reach the final boundary |
| `0x102335310` `db::CollationRule::CollationRule` | Collation initialization | Constructs ICU 51 `StringSearch` with the US locale and sets collator strength to zero (primary) |
| `0x102335ca0` `db::getSmartlistCondition` | Smart XML condition parser | Parses properties/operators/values; the `myTag` branch at `0x102336623` uses JUCE signed `getIntAttribute` and assigns type `0x40`; singular case-insensitive `month` uses `pastMonthToDay`, every other relative unit uses `pastDayToDay` |
| `0x102336ba0` `db::pastMonthToDay` | Relative calendar-month boundary | Converts current local time, subtracts the normalized month count, and returns the resulting day number |
| `0x102336c60` `db::pastDayToDay` | Relative day boundary | Converts current local time to a day number and subtracts the normalized count |
| dispatcher symbols in `unobserved-list-handlers.disasm.txt` | Play Count, Prepare, New Key, My Tag | Accepted request kinds, arities, selector widths, and called getters |
| query symbols in `mytag-prepare-queries.disasm.txt` | `Dsql_GetPrepareList`, `Dsql_GetMyTag`, `Dsql_GetMyTagOnTrack` | Ordered Prepare membership and both My Tag query directions |
| `song-info-siblings.disasm.txt` | Play/Delivery wrappers, AppSync and fallback builders | Dispatch, vtable offsets, SQL, field sources, and row construction for `0x2102`/`0x2602` |
| `play-song-info-cloud-paths.{json,disasm.txt}` | Play cloud-path setting and helper audit | Raw `CLSSyncMethod` default, complete x86-64 direct-call inventory, exact zero/nonzero branch, filesystem predicates, share/download helper domains, and remaining live equivalence class |
| `link-export-visibility.disasm.txt` | Both visibility overloads, common streaming helper, and protocol dispatcher | Exact `FolderPath` predicate and runtime provider dispatch |
| `streaming-provider-registry.{json,disasm.txt}` | Hash-pinned manager construction, generic path dispatch, login dispatch, Beatport vtable predicate, and Beatsource null/constant-false path | Provider slot ownership and exact Beatport `/v4/catalog/tracks/` substring semantics |
| `link-export-visibility-xrefs.txt` | Nine validated direct calls in seven containing functions | Playlist, flex sort, Search, History, shared insertion, and SmartList coverage |
| `play-path-conversion.disasm.txt` | Complete `convertToRealPath` helper | Null handling, drive-info gate, unified-path conversion, replacement, allocation, and return codes |

## BPM tolerance predicate

`djeplGetTrack_BPMRange` passes selector 6, the selected BPM, and the requested
tolerance into `getRowset_Track`. The selector-6 branch at
`0x100487d70..0x100487dc2` computes nonzero bounds as signed integer
`(100 - p) * BPM / 100` and `(100 + p) * BPM / 100`; the compiler's magic-number
division sequence truncates toward zero. Tolerance zero follows the separate
branch at `0x1004880fb..0x10048812e`, rounds the selected value to a whole BPM,
and constructs `[rounded - 50, rounded + 49]`.

Both values reach `wherefuncGetRowset_Vals` in comparison mode 1. Its
`setle` pair at `0x100489356..0x100489363` admits the row only when
`lower <= BPM && BPM <= upper`, proving both endpoints inclusive. The focused
artifact is `data/static-analysis/bpm-tolerance-boundaries.disasm.txt` **[DEC]**.
The paired 43-track Windows AppSync matrix confirms every endpoint and
immediate outside neighbor in independent fresh-fixture/process runs.
Tolerance zero returns precisely 119.50 through 120.49 around selected 120.00;
each nonzero tolerance includes both integer-truncated bounds. All seven result
sets are nested **[OBS, DB]**.

## Device-classification boundary

The validated direct-reference scan finds one ordinary caller of `isAIO`:
`PSvAppSyncDBIF::getDispSongInf`. Its XDJ/non-XDJ branch changes the placement
of Comment inside the display-song-info field list. Inspection of
`GetRootMenu`, `GetSortMenu`, the entity/track list-buffer insertors,
`GetListBufRowContent`, and `GetListBufContents` finds no direct model-name read
or `isAIO` call **[DEC]**.

For the pinned x86-64 build, the evidence therefore separates two surfaces:

- Display Song Info has a statically and live-proven XDJ-prefix classifier;
- ordinary menu serialization consumes setup width, request masks/context,
  render arguments, database settings, and row metadata without a recovered
  direct model classifier.

This is a bounded result. Direct-reference scanning does not exclude a vtable,
function pointer, inlined test, cached state written elsewhere, or an
architecture-specific difference. The controlled XDJ-RX3/CDJ-3000 oracle
comparison supplies independent runtime evidence for the tested menu surface.

### Model-state ingress and cache

The generated `model-name-state-path.disasm.txt` closes the ownership gap
between discovery, status reception, and `isAIO`:

1. `InnerLinkAPI::linkProc` dispatches internal membership message type `0x04`
   to `receiveLinkMember`.
2. `ProDJLink::receiveLinkMember` sends device type, presence, member timing,
   address, and version data to `LinkDeviceManager::addLinkDevice`. The manager
   performs a model lookup for its exact `DJS-1000` exclusion, but does not
   write the model string.
3. `PSvLinkNormalInterval::messageReceived` maps raw packet kind `0x0a` to the
   player-status branch, calls `PSvLinkPlayerLinkInfo::setData`, and stores a
   `0xb8`-byte record for players 1-8 or 9-12. Model text begins at record
   offset `0x0b`.
4. The parser compares the previous and incoming model strings after updating
   the record. A change appends internal message type `0x6e` with the player
   number.
5. The same `linkProc` jump table maps `0x6e` to
   `noticeModelNameUpdate(player)`. The callback reaches the UI listener through
   vtable slot `+0x158`.
6. `PSvLinkNormalInterval::getModelName` reads the status record at the same
   offset. The NetworkAccess, InnerLinkAPI, LinkProxy, and ProDJLink layers
   delegate this value to `PSvDBMain::isAIO`, which maintains its own boolean
   map until `clearAIOMap(player)`.

The contract test resolves the raw-kind `0x0a` parser entry and both internal
message jump-table entries from the binary rather than assigning names by
source order. It also regenerates all 3,331 trace lines byte-for-byte. Static
evidence therefore proves why membership can exist while the model getter is
empty. Dynamic evidence independently observes that state for keepalive-only
identities and sees the model after admitted status traffic **[DEC, OBS]**.

## Packed track-type path

`OnClientReq` computes `request_kind >> 12`. For class 1 it reads the low
context byte and checks `(TT - 3) <= 1`, so exactly `0x03` and `0x04` are sent
to an internal observer/notification path instead of `OnListClientCmd`. This
explains the pre-header timeout across all 47 `0x1xxx` list families. Class 2
goes to `OnMAnlzClientCmd` and bypasses the gate, matching the live Song Info
and Hot Cue Bank crosses.

`OnTrackListCmd` passes the complete context to the active AppSync Track-root
implementation. That function uses the full value for list-buffer ownership but
does not branch its ordinary membership query on the low byte.
`GetListBufContents` extracts the low byte and passes it as the track-type
argument to `GetListBufRowContent`. The row renderer enters its cache and
`HotCueAutoLoad` enrichment path only when the value equals one. This matches
the exhaustive live result: only type `0x01` carries row argument-10 bit
`0x100`; every other successful type clears it. Seven hierarchy/playlist
track-producing paths additionally copy `TT << 24` into row argument 7. See
`PACKED_CONTEXT_ORACLE.md` **[OBS, DEC]**.

The broader generated audit covers 23 identity ingress functions, member/model
accessors, model predicates, capability helpers, lifecycle functions, and
output selectors. Among 67 validated direct references, the only
database-serving decisions are Display Song Info `isAIO`, its disconnect cache
clear, and the content-metadata `DsqlContent_GetNewCDJSupported` track-row
predicate. All 35 `isSpecificModel` references and all five `isCDJNetwork`
references are UI or remote-settings code. `DEVICE_PREDICATE_AUDIT.md` records
the exact literals and explains why Display's `XDJ*`, UI exact-model, and
OPUS-QUAD drag-and-drop AIO decisions are separate classifiers **[DEC]**.

`DsqlContent_GetNewCDJSupported` at `0x102256b20` is itself exact. It selects
one `djmdContent` row, reads `FileType` column `0x0e` as a signed byte and
`SampleRate` column `0x21` only for raw file-type bytes 11 or 12. Bytes 5 and 6
return false unconditionally; bytes 11 and 12 return true only when the
32-bit rate equals `0xac44` (44100) or `0xbb80` (48000); every other byte
returns true. No `BitDepth` column is read **[DEC]**. The completed 382-row
extended/legacy Windows oracle confirms the complete byte domain, wide-value
narrowing, exact rate boundaries, and depth invariance. It returns 298
supported and 84 unsupported rows in both setup widths, with exact independent
repeat and exact 12-field legacy prefixes **[OBS, DB]**.

The Windows PE expresses this decision twice. AppSync row construction inlines
the predicate in `0x14238c720`; the Master-interface branch calls the
standalone equivalent at `0x14227e200`. The retained audit binds the exact
query strings, constants, direct-reference counts, and narrow disassembly
slices to the Windows executable hash. A full-image search finds zero 64-bit
absolute pointers to those functions or the recovered Display/AIO and
disconnect/cache functions, excluding ordinary PE pointer-table and vtable
storage for all five exact addresses **[DEC]**.

## Reproduction

From `/home/evan/workspace/rx3-research`:

```sh
BIN=artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox
PY=rekordbox-link-export-research/.venv/bin/python

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'Where(Category|Sort)_Enable|DBCommon_GetCateKind|ReturnIconID|Get_SubCategoryValue' \
  --output rekordbox-link-export-research/data/static-analysis/predicates-and-mapping.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" '^__Z[0-9]+djeplGet' \
  --output rekordbox-link-export-research/data/static-analysis/menu-query-functions.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" '(__Z15getRowset_Track9RbDBIndexajiiii|__Z23wherefuncGetRowset_ValsPvS_)' \
  --output rekordbox-link-export-research/data/static-analysis/bpm-tolerance-boundaries.disasm.txt

"$PY" rekordbox-link-export-research/tools/find_immediate_references.py \
  "$BIN" 0x1500 \
  --output rekordbox-link-export-research/data/static-analysis/request-1500-immediates.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'dsqlGetPlaylist(Item|Track|Data)|dsqlGetSongPlaylistCount|djepl.*Playlist|GetPlaylistList|GetPlaylistTrack' \
  --output rekordbox-link-export-research/data/static-analysis/playlist-queries.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'getRowset_Playlist|dsql.*Smart|GetSmartPlaylistTrack|getSmartPlaylistTrack' \
  --output rekordbox-link-export-research/data/static-analysis/smart-playlist-paths.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'getSmartlistContentData|SmartlistCondition|SmartlistNode|Smartlist' \
  --output rekordbox-link-export-research/data/static-analysis/smart-xml-parser.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'dateToDay|pastDayToDay|pastMonthToDay' \
  --output rekordbox-link-export-research/data/static-analysis/smart-date-conversion.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'CollationRule' \
  --output rekordbox-link-export-research/data/static-analysis/smart-collation.disasm.txt

"$PY" rekordbox-link-export-research/tools/list_symbols.py \
  "$BIN" '(prodjlink|ProDJLink|InnerLinkAPI).*(ModelName|Device|Player|KeepAlive)|PSvDBMain.*(isAIO|clearAIOMap|Client)|setDeckAIO|NewCDJSupported' \
  --output rekordbox-link-export-research/data/static-analysis/device-symbols.txt

"$PY" rekordbox-link-export-research/tools/find_direct_xrefs.py "$BIN" \
  0x102521e80 0x102520860 0x10019bad0 0x102256b20 \
  0x100ca9500 0x1020581b0 \
  > rekordbox-link-export-research/data/static-analysis/device-direct-xrefs.txt

"$PY" rekordbox-link-export-research/tools/audit_device_predicates.py "$BIN" \
  --json rekordbox-link-export-research/data/static-analysis/device-predicate-audit.json \
  --markdown rekordbox-link-export-research/data/static-analysis/device-predicate-audit.md

"$PY" rekordbox-link-export-research/tools/audit_db_interface_selection.py "$BIN" \
  --json rekordbox-link-export-research/data/static-analysis/db-interface-selection.json \
  --markdown rekordbox-link-export-research/data/static-analysis/db-interface-selection.md

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py "$BIN" \
  'FilterSettingManager(C2|10setDBIndex)|TrackFilterC2|PSvDBMain15SetSharedDBInfo' \
  --output rekordbox-link-export-research/data/static-analysis/db-interface-selection.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py "$BIN" \
  'getUInt(32|64)Value|PSvAppSyncDBIF19getHCBnkCuePointExt' \
  --output rekordbox-link-export-research/data/static-analysis/hot-cue-seek-fault.disasm.txt

"$PY" rekordbox-link-export-research/tools/audit_hot_cue_setter_reply_target.py \
  "$BIN" \
  --output rekordbox-link-export-research/data/static-analysis/hot-cue-setter-reply-target.json

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py "$BIN" \
  'ProDJLink(12isCDJNetwork|15isSpecificModel|12getModelName|13getModelNames)|PSvDBMain(5isAIO|11clearAIOMap)|PSvLinkNormalInterval(18isSupportMysetting|22isSupportDuplicationv2|22isSupportDeviceSetting)|DsqlContent_GetNewCDJSupported' \
  --output rekordbox-link-export-research/data/static-analysis/device-predicate-bodies.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py "$BIN" \
  '(__ZN12InnerLinkAPI(8linkProcEv|12getModelNameEj|12getModelNameEjPcj|21noticeModelNameUpdateEh|17receiveLinkMemberEjPKv)|__ZN20PSvLinkNetworkAccess12getModelNameEj|__ZN20PSvLinkNetworkAccess12getModelNameEjPcj|__ZN21PSvLinkNormalInterval(12getModelNameEj|12getModelNameEjPcj|15messageReceivedEPKhRKN4juce11MemoryBlockE)|__ZN9prodjlink9ProDJLink(17receiveLinkMemberEjN13PSvLinkCommon17PSvLinkDeviceTypeEb|12getModelNameEi|21noticeModelNameUpdateEh)|__ZN9prodjlink9LinkProxy12getModelNameEjPcj|__ZN9prodjlink17LinkDeviceManager13addLinkDevice|__ZN6djplay11UiProDJLink21notifyModelNameUpdateEh|__ZN9PSvDBMain(5isAIOEh|11clearAIOMapEh))' \
  --output rekordbox-link-export-research/data/static-analysis/model-name-state-path.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'getDispSongInf|receiveLinkMember|addNotFoundLinkDevice|GetListBufRowContent|handleCommonMessage|instPlayMusic|handleSwitchEvent|PSvDBMain10Disconnect|PSvDBMain5isAIO' \
  --output rekordbox-link-export-research/data/static-analysis/device-identity-paths.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'DsqlListBuf_Insert|getRowset_Track|insertLeftBuf_(Track|Artist|Album|Genre|Label)' \
  --output rekordbox-link-export-research/data/static-analysis/listbuf-layout.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'DsqlListBuf_(Clear|Insert)|WhereListBuf_Condition|GetListBufContents' \
  --output rekordbox-link-export-research/data/static-analysis/list-buffer-location.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'OnTrackListCmd|PSvAppSyncDBIF13getTrack_Root|GetListBuf(RowContent|Contents)' \
  --output rekordbox-link-export-research/data/static-analysis/context-track-type.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'PSvDBMain11OnClientReq' \
  --output rekordbox-link-export-research/data/static-analysis/context-track-type-routing.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'OnYearListCmd' \
  --output rekordbox-link-export-research/data/static-analysis/year-list-handler.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'insertLeftBuf_Track|Dsql_getRightDispCategory|dsqlGetRightListInfo_DB|getRightTrackKey|Get_TableString' \
  --output rekordbox-link-export-research/data/static-analysis/listbuf-insert.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'wherefuncGet_TableString|Dsql_getRightDispCategory|dsqlGetRightListInfo_DB|Get_TableString|getRightDispCategory|getRightTrackKey' \
  --output rekordbox-link-export-research/data/static-analysis/right-column-precompute.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'OnCueBnkCmd|GetHCBnkList|getHCBnkList|DsqlHCBnk' \
  --output rekordbox-link-export-research/data/static-analysis/hot-cue-bank.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'DBCFmt_GetCmdPrmFmt|OnClientReq|PostServerMessage' \
  --output rekordbox-link-export-research/data/static-analysis/dbserver-command-parser.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'DBCCmd_Free' \
  --output rekordbox-link-export-research/data/static-analysis/dbserver-command-free.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'PSvDBMain(17RequestToSendData|17RetNewCueToClient)' \
  --output rekordbox-link-export-research/data/static-analysis/hot-cue-reply-routing.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'PSvDBMain(16DeliverCueUpdate|20DeliverTagListUpdate|19DeliverHCBankUpdate|21DeliverPlaylistUpdate|19DeliverRatingUpdate|16DeliverBpmUpdate|21DeliverGetHotCueEvent)' \
  --output rekordbox-link-export-research/data/static-analysis/hot-cue-bank-notifications.disasm.txt

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'OnMAnlzClientCmd|OnSongInfCmd|GetDispSongInf|getDispSongInf|isAIO|linkProc' \
  --output rekordbox-link-export-research/data/static-analysis/display-song-info-dispatch.disasm.txt

"$PY" rekordbox-link-export-research/tools/find_direct_xrefs.py "$BIN" \
  0x101d2edc0 0x101ab8190 0x102521e80 0x1003dce20 \
  > rekordbox-link-export-research/data/static-analysis/display-song-info-direct-xrefs.txt
```

For the Windows cross-check, extract the exact executable from the retained
7.2.19 NSIS installer without starting the VM, then regenerate the retained
artifacts. The extracted member must hash to
`c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37`:

```sh
LAB=rekordbox-link-export-research
PE=/tmp/rekordbox-7.2.19-windows.exe
PY="$LAB/.venv/bin/python"
INSTALLER=rekordbox-windows/shared/Install_rekordbox_x64_7_2_19.exe

mkdir -p /tmp/rekordbox-7.2.19-extract
7z e -y -o/tmp/rekordbox-7.2.19-extract "$INSTALLER" rekordbox.exe
mv /tmp/rekordbox-7.2.19-extract/rekordbox.exe "$PE"
sha256sum "$PE"
mkdir -p "$LAB/data/static-analysis/windows"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" metadata \
  > "$LAB/data/static-analysis/windows/rekordbox-metadata.json"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" immediate 0x1112 \
  > "$LAB/data/static-analysis/windows/request-1112-immediates.json"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" \
  vtable PSvAppSyncDBIF --start 0x200 --end 0x248 \
  > "$LAB/data/static-analysis/windows/appsync-history-vtable.json"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" function 0x142385970 \
  > "$LAB/data/static-analysis/windows/request-1112-dispatch.disasm.txt"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" function 0x14236c690 \
  > "$LAB/data/static-analysis/windows/appsync-history.disasm.txt"
"$PY" "$LAB/tools/summarize_windows_history.py"

"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" immediate 0x2002 \
  > "$LAB/data/static-analysis/windows/request-2002-immediates.json"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" function 0x142386ad0 \
  > "$LAB/data/static-analysis/windows/song-info-dispatch.disasm.txt"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" function 0x14238e3e0 \
  > "$LAB/data/static-analysis/windows/display-song-info-wrapper.disasm.txt"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" \
  vtable PSvAppSyncDBIF --start 0x140 --end 0x190 \
  > "$LAB/data/static-analysis/windows/appsync-display-vtable.json"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" function 0x142361f30 \
  > "$LAB/data/static-analysis/windows/appsync-display-song-info.disasm.txt"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" function 0x1423815c0 \
  > "$LAB/data/static-analysis/windows/is-aio.disasm.txt"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" function 0x14235e5e0 \
  > "$LAB/data/static-analysis/windows/exchange-key-name.disasm.txt"
"$PY" "$LAB/tools/analyze_windows_pe.py" "$PE" function 0x141c5f780 \
  > "$LAB/data/static-analysis/windows/local-key-style.disasm.txt"
"$PY" "$LAB/tools/generate_windows_device_predicate_audit.py" "$PE"
"$PY" "$LAB/tools/audit_windows_device_semantics.py" "$PE" \
  --output "$LAB/data/static-analysis/windows/device-semantic-audit.json"
"$PY" "$LAB/tools/generate_windows_static_manifest.py"
```

Copying the same path from the installed guest remains a hash-equivalent
fallback, but it is no longer required for static regeneration. The checked-in
files contain those outputs. `windows/manifest.json` binds all
20 retained extracts to their producer and arguments, the three producer hashes,
the executable identity, and the retained installer/member identity. The
temporary host executable and extraction directory are disposable after
verification.

The encrypted configuration export uses the dependency environment already
kept with the Windows lab:

```sh
rekordbox-windows/.venv/bin/python \
  rekordbox-link-export-research/tools/export_link_config.py \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  rekordbox-link-export-research/data/database
```

The options file is read only to derive the SQLCipher key in memory. The
generated CSV/JSON files contain no key, password, path relocation data, track
metadata, or personal library rows.

`tools/generate_database_field_reference.py` opens the deterministic encrypted
`full` fixture through the same memory-only key path and emits
`DATABASE_FIELD_REFERENCE.md` plus
`data/database/link-export-schema.json`. The result classifies all 25
table-like names in the request map, enumerates 389 columns across the 22
physical AppSync tables, joins table and semantic-field evidence to all 95
classified request kinds, and keeps `SELECT *` retrieval distinct from proven
downstream field use. The readable artifact includes the inverse 95-row
request-kind index with an explicit family-level evidence boundary.
`conformance/test_database_field_reference.py` verifies
the table and request domains, required content fields, nonphysical
classifications, secret exclusion, and byte-identical regeneration.

## Confidence rules

- A branch and constants recovered from the pinned function are **DEC** for
  that build and architecture.
- A symbol name without inspected control flow is supporting evidence, not a
  complete contract.
- A database row proves current configuration, not every UI state.
- A packet capture proves runtime serialization for that session.
- A confirmed model-dependent branch proves only the behavior inside its caller;
  it does not imply that every menu or serializer uses the same distinction.
- Differences between static and live evidence remain explicit until a
  controlled experiment explains the boundary.
