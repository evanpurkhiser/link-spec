# Link Export request vocabulary

This chapter defines the complete command namespace currently known to this
lab and separates four claims that must not be conflated:

1. a player firmware names a command;
2. Rekordbox 7.2.19 dispatches that command;
3. the command reaches a database or filesystem implementation;
4. a real-Rekordbox oracle records its observable response.

The canonical machine-readable ledger is
`data/static-analysis/link-export-request-vocabulary.json`. It contains 185
unique command kinds, including all 173 request/reply names recovered from the
pinned CDJ-3000 application, the physical RX3's `0x0001` client control,
conformance probes, and Rekordbox-only switch arms absent from that client
enum. The generator
joins the firmware vocabulary, the 74-kind live menu corpus, and exact switch
tables decoded from the pinned Rekordbox Mach-O.

## Coverage states

| State | Meaning | Current count |
|---|---|---:|
| `real-rekordbox-menu-oracle` | A declarative suite has recorded the command against Rekordbox 7.2.19; its menu/database behavior is classified | 74 |
| `rekordbox-static-dispatch` | Rekordbox has an exact command arm, but this corpus has not recorded that adjacent command as a live oracle | 54 |
| `rekordbox-static-rejected` | The request reaches an unsupported top-level/low-byte arm or falls outside a bounded handler table | 27 |
| `rekordbox-recognized-log-only` | Rekordbox has an exact switch arm that logs without the recovered payload implementation | 8 |
| `physical-client-control` | A physical player emitted a protocol control outside the recovered ordinary server request tables | 1 |
| `source-vocabulary-only` | A named client request still lacks an exact terminal Rekordbox arm or live result | 0 |
| `reply-vocabulary` | A named client-side reply kind | 21 |

A source-only command would be an open evidence cell, not evidence of support;
none remains in the current namespace.
Likewise, a static dispatch proves the path in Rekordbox 7.2.19 but does not
prove its argument contract, success conditions, reply bytes, or lifecycle.

## Client cancellation command (`0001`)

Dysentery names `0x0001` "invalid data." The RX3 firmware establishes a more
specific meaning: `RecvFromCommTask` constructs a zeroed command, copies the
outstanding request ID, writes kind `0x0001`, and sends it when
`CheckCanceledRequest` reports a GUI cancellation. It is absent from the complete
CDJ-3000 request-name table and from Rekordbox's ordinary `1xxx`, `2xxx`, and
`3xxx` request dispatch. The retained physical RX3 nevertheless emits five
zero-argument `0001` messages, always reusing the transaction ID of the
immediately preceding `2003` artwork request **[CAP, DYS, RX3DEC]**.

The reports arrive 21,098 to 126,329 microseconds after their artwork requests.
Three follow a captured `4002` reply: one status-zero 28,040-byte JPEG and two
status-50 empty replies. The other two have no correlated server reply in the
retained stream. No reply to `0001` itself is captured. Packet order cannot
show whether a captured `4002` had reached the client task before cancellation,
but the firmware rules out artwork-content validation as the command's trigger.
It is a client cancellation control, not a Rekordbox request-handler contract.
The ordered timings are retained in `navigation-transcript.json`.

## Top-level dispatch

`PSvDBMain::OnClientReq` first classifies the request by its high nibble. Lower
bytes have meaning only inside the selected class.

| High nibble | Dispatcher | Secondary key |
|---:|---|---|
| `1` | `PSvDBMain::OnListClientCmd` | low byte `00..17` |
| `2` | `PSvDBMain::OnMAnlzClientCmd` | low byte `01..07` |
| `3` | `PSvDBMain::OnOtherClientCmd` | low byte `00..08` |

Every other high-nibble class is passed directly to
`PSvDBMain::OnUnknownClientCmd`, which returns `0x4003`. This terminal rule
classifies `0x0100`, every `0x5xxx` provider-browser request, and `0x6100` as
unsupported by Rekordbox 7.2.19. The physical `0x0001` report is kept outside
this ordinary request classification because it reuses the completed artwork
transaction and has no captured reply of its own. This ordering is important.
A request ending in `03` is not automatically an
image request. `0x2003` reaches `OnImgCmd`, while `0x3e03` first enters the
`3xxx` tree, reaches `OnOtherCmd`, and is rejected because that handler's
bounded table ends at `0x3d03`.

## List class (`1xxx`)

The low byte selects the menu family. `00` is a second bounded switch over
`0x1000..0x1500`; `09` and `16` are unsupported; `0c` admits the special
`0x130c` path and rejects the remaining forms. The other recognized low bytes
route to their named Genre, Artist, Album, Track, Playlist, BPM, Rating, Year,
Label, Key, Color, Play Count, Prepare, Length, Bitrate, History, File Name,
New Key, My Tag, or Matching handler.

The 74-kind real menu corpus, complete signatures, navigation edges, query
predicates, ordering, row types, and rendering behavior are documented in
`PROTOCOL_REFERENCE.md` and `DATABASE_QUERIES.md`. The per-kind database ledger
is `data/static-analysis/menu-database-query-map.json`.

`0x1011` is Bitrate Root in the current player enum, live oracle, and
Rekordbox handler. The older inline Dysentery `dbserver.clj` description
"request folder menu" conflicts with Dysentery's current `menus.adoc` table
and is treated as a stale comment.

The Year handler has its own exact 11-entry high-byte table. Release Year uses
`0x1008..0x1208`; Date Added uses `0x1708..0x1a08`. The intervening client
names `0x1308..0x1608` for Stock Year/Month all target one invalid-kind branch,
return `-2` to `OnClientReq`, and consequently receive `0x4003` from
`OnUnknownClientCmd` **[DEC]**.

## Analysis class (`2xxx`)

The low-byte dispatch is exact:

| Low byte | Handler | Status |
|---:|---|---|
| `01` | `OnCueBnkCmd` | Hot Cue Bank catalog/getters/setters are extensively live-recorded |
| `02` | `OnSongInfCmd` | Display, Play, Delivery, and recognized no-builder commands are extensively live-recorded |
| `03` | `OnImgCmd` | only `0x2003` and `0x2103` are recognized in 7.2.19 |
| `04` | `OnSongAnlzCmd` | exact bounded table `0x2004..0x2d04` |
| `05` | `OnWriteCmd` | exact ten-kind table `0x2005..0x2905`; seven targets and three log-only arms |
| `06` | unsupported arm | `0x2006`, `0x2106`, and `0x2206` are statically rejected |
| `07` | `OnDbModCmd` | exact `0x2107` Rating and `0x2507` BPM mutation arms |

`XDJ_RR_ADJACENT_COMMANDS.md` joins the old-Key/Cue Track browsers and every
directly reached XDJ-RR write/modification command to these terminal paths.
All 102 request kinds with direct named XDJ-RR callers now have terminal
Rekordbox evidence.

The Song Info kinds `0x2202` through `0x2502` are role-sensitive rather than a
single unsupported family. Rekordbox 7.2.19 recognizes each kind but returns a
kind-specific `0x4003`. In the opposite serving direction, XDJ-RX firmware
builds generic/non-Rekordbox metadata for `0x2202` and a six-row summary for
`0x2302`. Across XDJ-RX, XDJ-RR, XDJ-RX2, XDJ-XZ, and XDJ-RX3, the client
sends `0x2402` track-decode requests and expects `0x4802`, while `0x2502` is a
one-way register track length command. Every one of those five local servers
dispatches the latter two to stubs that log unsupported. The hash-pinned
`data/static-analysis/player-hosted-song-info.json` audit records the exact
arguments, reply contract, and source provenance. CDJ-3000, XDJ-AZ,
OMNIS-DUO, and CDJ-1500X retain `CMD_GET_DECODE_INFO`,
`CMD_REG_TRK_LENGTH`, and format entries for `0x2402`, `0x2502`, and `0x4802`;
whole-tree scans of 26,862 decompiled C sources find every exact literal only
in those name/format files. This is vocabulary continuity with no literal
client or server implementation. Computed or decompiler-omitted paths remain
the explicit boundary
**[SRC, DEC, OBS]**.

The low-byte-`06` result means Dysentery's `0x2006` Folder Menu does not exist
as a working Rekordbox 7.2.19 server path. The newer CDJ-3000 source calls the
same number `CMD_CACHE_FOLDER`; names differ across generations, while the
server rejection is version-specific binary evidence.

### Artwork commands

| Kind | Client name | Rekordbox target | Reply | Success dependency |
|---:|---|---|---:|---|
| `2003` | `CMD_GET_IMAGE` | database interface `+0x190` | `4002` | active AppSync queries `ImagePath` from undeleted `djmdContent` by ID, then `djmdPlaylist`; Master fallback resolves `djmdImage` by image ID |
| `2103` | `CMD_GET_IMAGE2` | database interface `+0x198` | `4002` | AppSync applies the same direct `ImagePath` lookup to the content ID; Master fallback resolves `djmdContent.ImageID` first |

The interface symbols identify these targets as `getDBImgData` and
`getDBImgDataByContentID`, but their database semantics differ by installed
interface. The active Link Export AppSync implementation selects `ImagePath`
directly from undeleted `djmdContent`, falling back to `djmdPlaylist`; its
content-ID entry point is a thin call into that same lookup. The Master
fallback instead calls `DsqlContent_GetImageID` and then `DsqlImg_GetPath`.
Both paths enter a common JPEG loader with a one-MiB ceiling and dimension
validation. A live success fixture therefore needs artwork bytes, but it does
not need playable audio. `ADJACENT_PAYLOAD_SERVICES.md` records the full split.

### Analysis commands

| Kind | Rekordbox target | Reply | Recovered dependency |
|---:|---|---:|---|
| `2004` | `GetWave` | `4402` | analysis path; `MstLoadLoudWave` and `MstLoadDotWave`; fixed 904-byte reply |
| `2104` | `GetUsbCue` | `4702` | database cue rows; no audio decoding visible |
| `2204` | `GetQtzInf` | `4602` | analysis path; beat-grid loaders |
| `2304` | recognized log-only | packed context only | reads the track-type byte, logs, and returns internal `-2` |
| `2404` | recognized log-only | packed context only | reads the track-type byte, logs, and returns internal `-2` |
| `2504` | `GetVbrInf` | `4502` | analysis path; `MstLoadVBR` |
| `2604` | recognized log-only | packed context only | reads the track-type byte, logs, and returns internal `-2` |
| `2704` | recognized log-only | packed context only | reads the track-type byte, logs, and returns internal `-2` |
| `2804` | `GetQtzInf` | `4000` | analysis path; numeric quantize-offset result |
| `2904` | `LoadParWav` | `4a02` | analysis path; detailed waveform data |
| `2a04` | `LoadKeyInf` | `4c02` | analysis path; key-analysis data |
| `2b04` | `GetUsbCueExt` | `4e02` | AppSync cue callback or database cue/cue-option rows; no filesystem read in either recovered builder |
| `2c04` | `GetSpecifiedAtomInfo` | `4f02` | `EXT`/`2EX` atom loader; `PCP2`, `PCPT`, and `PMAI` are explicitly short-circuited to an empty reply |
| `2d04` | `GetSpecifiedAtomInfo` | `4f02` | exact alias of the same target in 7.2.19 |

These paths strengthen the lab's media assumption: menu, metadata, cue, and
configuration coverage does not require audio media. Successful waveform,
beat-grid, VBR, key, or atom probes may require minimal ANLZ artifacts; artwork
success requires minimal image bytes. Those files are protocol fixtures rather
than playable tracks.

The retained physical RX3 session confirms native use of `2003`, `2103`,
`2004`, `2204`, `2504`, `2b04`, `2c04`, and the `2d04` alias. It also fixes the
client's context split: location 8 for artwork and dedicated waveform/cue/VBR/
beat-grid services, location 1 for specified atoms, and location 3 for the
adjacent `3100` selected-track buffer operation. The trace includes successful
`PWV4`, `PWV6`, `PWV5`, preview-waveform, VBR, beat-grid, and JPEG payloads,
plus empty `PSSI`, `PQT2`, and extended-cue replies. See
`PHYSICAL_RX3_SESSION.md` and the hash-preserving
`navigation-transcript.json`. The capture identifies native client vocabulary
and arguments but not its Rekordbox server version **[CAP]**.

## Other class (`3xxx`)

The low byte selects a bounded mutation/control handler:

| Low byte | Handler | Exact accepted kinds in recovered tables |
|---:|---|---|
| `00` | `OnListBuffCmd` | `3000`, `3100` |
| `01` | `OnHistoryCmd` | `3001..3401` in `0x100` steps |
| `02` | `OnPrepareCmd` | `3002..3402` in `0x100` steps |
| `03` | `OnOtherCmd` | `3003..3d03` in `0x100` steps |
| `04` | special arm | `3104` only |
| `05` | unsupported arm | none |
| `06` | `OnUserCmd` | `3006` |
| `07` | `OnFilterCmd` | `3007..3407` in `0x100` steps |
| `08` | `OnOther2Cmd` | `3008` |

The exact terminal arms are:

| Family | Kinds and recovered target names |
|---|---|
| List buffer | `3000` contents (`4001/4101/4201`), `3100` offset (`4000`) |
| History | `3001` insert, `3101` delete, `3201` on-air, `3301` delete-history reply, `3401` delete-history track |
| Prepare/tag list | `3002` add Prepare, `3102` add tag-list playlist, `3202` unlisted arm, `3302` change order, `3402` is-tag-list-playlist |
| Other | `3003` color code, `3103` unlisted arm, `3203` firmware version, `3303` browse type, `3403` unlisted arm, `3503` unplayable info, `3603` hierarchy, `3703`/`3803` unlisted arms, `3903` property table, `3a03` New Key translation, `3b03` play state, `3c03` My Setting flag, `3d03` New Key ID |
| Special | `3104` recognized zero-result case (`4000`) |
| User | `3006` DJ ID (`4d02`) |
| Filter | `3007` enable, `3107` get property, `3207` set property, `3307` set My Tag, `3407` add My Tag item |
| Other2 | `3008` database interface `+0x228` (`4000`) |

The `0x3006` User arm has a complete static contract in
`USER_INFO_DJID_ORACLE.md` and
`data/static-analysis/user-info-djid.json`. Rekordbox returns `0x4d02` with a
160-byte zero-padded blob when a valid `djprofile.nxs` supplied a 32-byte DJ
ID at server startup, or the same reply kind with declared length zero when no
DJ ID is loaded. CDJ-3000 firmware issues this request before Delivery Song
Info after track load; live 7.2.19 serialization and argument boundaries remain
an authority-oracle gap **[DEC, CDJ-DEC]**.

The client enum names several requests outside these bounded Rekordbox tables.
`0x3005`, `0x3501`, `0x3602`, `0x3704`, `0x3804`, `0x3e03`, and `0x3f03` are
therefore classified as statically rejected in 7.2.19. In particular,
Dysentery's tentative `0x3e03` USB-information interpretation and the newer
`CMD_GET_IS_RBM_MOUNT` name describe client vocabulary, not a supported server
arm in this Rekordbox build.

`0x3b03` has a fully recovered scalar contract. It accepts one numeric
ContentID, searches the critical-section-protected Link-played ID array in
`PSvDBMain`, and returns a `0x4000` DWORD value: `2` when present and zero when
absent. `GetListBufRowContent` searches the same array and maps membership to
argument-7 bit `0x100`. XDJ-RR's `dbcl_GetTrackPlayState` fixes location 1,
sends the selected track's ContentID, and retains the reply's low byte for its
Played/Unplayed browse action **[DEC, RR-DEC]**.

## Reproduction and invariants

Regenerate both machine artifacts from the lab root:

```sh
python3 tools/extract_link_export_dispatch_tables.py
python3 tools/generate_link_export_request_vocabulary.py
```

`conformance/test_link_export_request_vocabulary.py` requires:

- byte-identical extraction from the pinned Rekordbox SHA-256;
- byte-identical vocabulary generation;
- unique command kinds;
- exact inclusion of every firmware-enum name, every menu-corpus request, and
  every four-digit static arm;
- exact analysis handlers and known reply kinds;
- explicit rejection of the low-byte-`06` and out-of-range `3xxx` examples;
- terminal `0x4003` classification of every otherwise source-only command;
- the exact Release Year, unsupported Stock Date, and Date Added jump table;
- preservation of `0x1011` as Bitrate Root.

The JSON retains the complete per-command provenance, route, terminal target,
reply kind, dependency, and rejection reason. This chapter summarizes that
ledger; it does not replace it.
