# Link Export row construction

This chapter follows one track from the rowset returned by a menu query through
`djmdLeftBuf` and into a `4101` menu-item message. It documents the intermediate
representations because several wire fields cannot be understood from the final
serializer alone. Unless marked otherwise, the implementation details below are
from the pinned rekordbox 7.2.19 macOS x86-64 binary **[DEC]**.

## Construction stages

A normal track row passes through four distinct stages:

1. The menu-family getter creates a content rowset and applies the requested
   sort.
2. `insertLeftBuf_Track` chooses the configured right-column kind, obtains its
   numeric key and formatted string, and creates an `_st_listbuf_record`.
3. `DsqlListBuf_Insert` packs that record into the 14-column materialized
   `djmdLeftBuf` table.
4. `GetListBufRowContent` reads one materialized row, reconciles the requested
   render-time secondary selector with the precomputed right column, adds
   compatibility and key metadata, and emits either 12 or 16 arguments.

The configured right column is therefore computed when the list buffer is
built. The renderer only regenerates it when the render request asks for a
different selector.

Display, Play, and Delivery Song Info use fixed heterogeneous row builders
rather than an ordinary track rowset. Display and Delivery still construct a
composite Title/secondary row; Play ignores the tested secondary controls.
Their exact row sources and serialization matrices are documented in
`DISPLAY_SONG_INFO_ORACLE.md` and `SONG_INFO_SIBLINGS_ORACLE.md`.

## Insert record

`DsqlListBuf_Insert` consumes the following record. Names describe the proven
track-row use; other item types reuse fields according to their own layouts.

| Record offset | Width | Track-row value | `djmdLeftBuf` column | Wire result |
| ---: | ---: | --- | ---: | --- |
| `0x00` | 4 | Primary/content ID | 2 | argument 1 |
| `0x04` | 4 | Right-column numeric key | 5 | argument 0 |
| `0x08` | 4 | Repeated/content ID | 13 | argument 8 |
| `0x10` | 8 | Primary UTF-16 string pointer | 3 | argument 3 |
| `0x18` | 8 | Right-column UTF-16 string pointer | 6 | argument 5 |
| `0x20` | 4 | Position or track number | 7 | argument 9 |
| `0x24` | 1 | Low item type | 1 | argument 6 low byte |
| `0x25` | 1 | High/right item type | 4 | argument 6 high byte |
| `0x26` | 1 | High flag nibble source | 12 | argument 7 metadata |
| `0x27` | 1 | Low flag nibble source | 12 | argument 7 metadata |
| `0x28` | 8 | First internal sort string | 8 | not serialized directly |
| `0x30` | 8 | Second internal sort string | 10 | not serialized directly |
| `0x38` | 4 | Sequence/order value | 9 | not serialized directly |

The two bytes at offsets `0x26` and `0x27` are packed as
`(offset_0x26 << 4) | offset_0x27` before insertion. The materialized table also
contains constant/empty working columns used by its sort machinery.

`DsqlListBuf_Insert` checks each of the primary, right, and two internal sort
strings. At a UTF-16 length of 255 or greater it writes a NUL at code-unit index
255. The stored visible prefix is therefore at most 255 UTF-16 code units. This
is an in-place mutation of the supplied buffer and is a separate limit from the
127/255 JUCE-character limits in `Get_SubCategoryValue`.

## Track precomputation

`insertLeftBuf_Track` obtains the configured secondary `MenuItemID` through
`getRightDispCategory`. That helper scans live `djmdSort` rows for
`Disable & 2`, has no `ORDER BY`, and returns the first selected row it
encounters. `dsqlGetRightListInfo_DB` maps the menu item to an internal content
field selector, high item-type byte, and table-string formatter:

| Menu item | Display | Internal selector | High type | Table-string ID |
| ---: | --- | ---: | ---: | ---: |
| 1 | Genre | 7 | `06` | 6 |
| 2 | Artist | 5 | `07` | 7 |
| 3 | Album | 6 | `02` | 8 |
| 4 | unused | -1 | `00` | 0 |
| 5 | BPM | 8 | `0d` | 21 |
| 6 | Rating | 15 | `0a` | 0 |
| 7 | unused | -1 | `00` | 0 |
| 8 | Remixer | 17 | `29` | 7 |
| 9 | Label | 18 | `0e` | 9 |
| 10 | Original Artist | 19 | `28` | 7 |
| 11 | Key | 20 | `0f` | 22 |
| 12 | unused | -1 | `00` | 0 |
| 13 | Color | 22 | `13` | 11 |
| 14 | Time | 9 | `0b` | 0 |
| 15 | Bitrate | 11 | `10` | 0 |
| 16-20 | unused | -1 | `00` | 0 |
| 21 | Comment | 0 | `23` | 4 |
| 22 | Date Added | 0 | `2e` | 5 |
| 23 | DJ Play Count | 23 | `2a` | 0 |

`getRightTrackKey` reads the selected numeric content field. Selector 0 reads
the content ID, which is why Comment and Date Added place the content ID in
argument 0. A zero BPM becomes sentinel `0x7fffffff` in this precompute path.
Color IDs outside 1 through 8 likewise become `0x7fffffff`; a valid color also
increments the high type from base `0x13` to `0x14` through `0x1b`.

The visible right string comes from a row-provided `rightStr` when present.
Otherwise `Get_TableString` formats or looks up the selected value and caches
the result back into `rightStr`. The list buffer therefore carries
server-authored presentation text, not necessarily a literal database field.
This explains captures in which a Comment-typed row contains a key/BPM summary.

Rows whose `FolderPath` is recognized by an active streaming-provider handler
are rejected before insertion. The classification is case-sensitive in the
controlled runtime and the provider's exact path predicate: SoundCloud, Tidal,
Spotify, and Apple Music filter; Beatport searches for
`/v4/catalog/tracks/`, so the tested `beatport:tracks:` form does not; and
Beatsource has no constructed service in this build.
Windows AppSync persisted History is an exception to the ordinary-list
behavior: its platform-specific builder bypasses this insertion path and never
reads `FolderPath`. The pinned macOS History function does apply the helper.
This is independent of soft deletion and later per-track compatibility flags;
the complete cross is in `LINK_EXPORT_VISIBILITY_ORACLE.md`.

## Render reconciliation

The normal `0x3000` prefix is `[context, offset, count, seek, total]`.
`GetListBufContents` reads the low 16 bits of `seek` as a normalized first-row
character seek key. It does not read the client-reported total. A sixth field
is a low-word category ID passed through the sparse `DBCommon_GetCateKind`
table before row serialization. These fields control row selection and layout;
the eight-argument gate/selector pair separately controls secondary-column
reconciliation **[DEC]**.

The list request materializes both primary ordering and a right-column value in
`djmdLeftBuf`. Default sort uses the persisted Column selection. Alphabet uses
Title, and the other visible RX3 sorts materialize their own Artist, Album,
BPM, Rating, Genre, Label, Key, Date Added, or DJ Play Count role. A
six-argument render preserves that value. Its final argument remained `12` in
all 11 real-Rekordbox cases and did not force Key **[OBS]**.

The analogous five-argument active-sort matrix is declared but not yet
recorded. Existing Default-only evidence is insufficient to decide whether
omitting the final value preserves, clears, or recomputes each non-default
materialized role. The queued reducer records the complete row and compares it
with the six-argument counterpart without asserting equivalence **[OBS plan]**.

The seven-argument declaration supplies a nominal gate value without a
selector. Static decoding ignores that value because both fields are loaded
only at eight arguments. Its 33-case oracle varies zero, one, and
`UINT32_MAX` across every visible sort to test both the arity boundary and the
predicted preservation of the materialized row **[DEC, OBS plan]**.

The eight-argument render supplies an override gate and optional selector as
documented in `SECONDARY_COLUMNS.md`. Selector zero with an enabled gate reads
the persisted database selection. When the effective selector maps to the same
high type already present in `djmdLeftBuf`, rekordbox preserves the precomputed
numeric key and formatted `rightStr`. When it differs, rekordbox clears both
values, strips the old high byte, and invokes `Get_SubCategoryValue` for the
requested selector.

This distinction is observable:

- Database-selected rendering can return the cached formatter output and the
  precompute sentinels described above when it matches the materialized type.
- Six-argument rendering exposes the active sort's cached right-column value,
  including Key/BPM and BPM/Key composites.
- A render override can return the raw extractor's numeric value and string.
- The high item type still describes the requested display role, even when the
  retained string is a richer server-authored summary.

## Wire arguments

The extended `4101` row has 16 arguments. A legacy row is exactly the first 12
arguments of the same logical row.

| Index | Track-row meaning |
| ---: | --- |
| 0 | Effective right-column numeric key: lookup ID, numeric value, or content ID for Comment/Date Added |
| 1 | `djmdContent.ID` |
| 2 | UTF-16 byte length of argument 3, including NUL |
| 3 | `Title`, or `FileNameL` in File Name browsing |
| 4 | UTF-16 byte length of argument 5, including NUL |
| 5 | Effective right-column display string |
| 6 | `(right_type << 8) | 0x04` |
| 7 | Scope/state flags |
| 8 | `djmdContent.ID`, repeated |
| 9 | Scope-specific position or track number |
| 10 | Compatibility and hot-cue-auto-load flags |
| 11 | Converted/new-key ID on the New Key/Key-category path; zero where that path does not populate it |
| 12 | Original `djmdContent.KeyID`, independent of the selected right column |
| 13 | UTF-16 byte length of argument 14, including NUL |
| 14 | Key display string after the configured key-name exchange |
| 15 | Raw stored `djmdContent.BPM`, already scaled by 100 |

Arguments 12-15 live in the extension structure beginning at offset `0x78` in
the internal return buffer. Argument 12 is the original KeyID for content track
rows. Other item types can assign different meanings to the same wire positions
and must be modeled by item type.

Argument 6 is a numeric field even though ordinary track rows construct it from
two one-byte components. The reproducible
`data/static-analysis/item-type-domain.json` audit finds 51,148 represented
`0x4101` rows and 85 distinct argument-6 values across all 281 row-bearing
canonical Rekordbox 7.2.19 golden files. Every observed value has clear upper
16 bits; the maximum is `0x00002e04`. Consumers should retain the full wire
integer: this versioned corpus result does not establish that the upper 16 bits
are reserved or always zero for other server or client generations.
`ITEM_TYPE_REFERENCE.md` expands that numeric audit into the complete readable
85-type catalog, including class, documented meaning, producing request kinds,
representative real-Rekordbox text, occurrence counts, and per-source
provenance in `data/item-type-reference.json`.

## Flag words

Argument 7 begins at zero. The following mutations are established:

| Mask | Source | Meaning/status |
| ---: | --- | --- |
| `0x00000001` | `djmdSongTagList` lookup, or equivalent cloud query | Track has at least one matching row; the UI feature represented by this table remains a live-test target |
| `0x00000100` | Link-played content-ID cache | Content ID is present in the `PSvDBMain` Link-played snapshot |
| `0x0f000000` | Materialized column 12 low nibble shifted left 20 bits | Packed list/scope metadata |
| `TT << 24` | Packed context track type | Added by Genre, Artist, Album, Label, Original Artist, Remixer, and Playlist track leaves |

The 329-case family cross separates two high-byte sources. The seven named
hierarchy/playlist leaves copy the packed context's `TT` into argument 7 for 25
fixture rows per nonzero successful type. Playlist rows use base state zero;
the other paths preserve their low state bits. Direct Track and scalar-filter
leaves do not copy `TT`. Other observed high-byte scope values still require
path-specific interpretation.

The bit-8 owner is exact in the pinned executable. `PSvDBMain` stores a
thread-safe Link-played ID snapshot at offsets `+0x6d8..+0x6e4`, guarded by the
critical section at `+0x698`. `UiProDJLink` obtains the IDs through
`DatabaseIF::getAllLinkPlayed`; the main database controller includes a track
when `RowDataTrack +0x3f8` has bit `0x10`, then copies its ContentID.
`PSvDBServer::NotifyLibraryUpdatedPlayed` atomically swaps that array into
`PSvDBMain`. Both `GetListBufRowContent` and request `0x3b03`
`CMD_GET_PLAYSTATE` search the same array. The row renderer ORs bit `0x100`
into argument 7 on a match; `0x3b03` returns scalar value `2` on a match and
zero otherwise **[DEC, RR-DEC]**.

The underlying played state belongs to the desktop library/controller layer,
not `master.db` menu membership. Initial state can be restored through the
`AnotherHistories` properties file, gated by the ordinary and Link played-track
options; runtime history notifications update the `RowDataTrack` bits. The
protocol actuator is declared without an inferred result: the focused suite
crosses baseline rows and `0x3b03` replies with `0x3001` insertion, `0x3401`
per-track removal, and `0x3101` whole-history deletion. A controlled
real-Windows record and repeat remain required to establish the precise
transition and refresh timing **[DEC]**.

A separate physical observation corroborates the presentation layer without
closing that Windows experiment. Rekordbox 7.2.11 serving a CDJ-3000 emitted
bit `0x100` on exactly the 854 captured track rows whose tracks the deck had
loaded, consistently across artist, playlist, all-track, metadata, and Link
history views. The adjacent source file and its hash are pinned in
`SOURCES.md` **[EXT-OBS]**.

Argument 10 also begins at zero:

| Mask | Condition |
| ---: | --- |
| `0x00000001` | `DsqlContent_GetNewCDJSupported(contentID)` is false, or the file-type/sample-rate compatibility path rejects the content |
| `0x00000100` | `HotCueAutoLoad` is nonempty and the packed track-type byte is `0x01` |

An exhaustive ordinary-Track sweep over all 256 final context-byte values makes
the second condition observable. All eight fixture rows have nonempty
`HotCueAutoLoad`. Track type `0x01` produces `0x100` for every row; all 253 other
successful types produce zero, and every other row field remains identical.
The remaining two types, `0x03` and `0x04`, time out before a menu header.
`GetListBufContents` extracts the low context byte and
`GetListBufRowContent` explicitly admits the enrichment path only when it is
one. See `PACKED_CONTEXT_ORACLE.md` **[OBS, DEC]**.

Across the full list-family cross, type `0x01` sets argument-10 bit `0x100` on
60 track rows in 17 request families. The effect is therefore a shared track
renderer rule rather than an ordinary-Track-only property.

The decoded compatibility branch marks file types 5 and 6 unsupported. File
types 11 and 12 require a sample rate of 44,100 or 48,000 Hz on that path. Other
types bypass this sample-rate restriction. The 382-row Windows oracle proves
the complete byte domain, wide-value narrowing, exact rate boundaries, and
BitDepth invariance under both setup widths; every legacy result is the exact
12-field prefix of its extended partner. The sampled eight-identity matrix and
the predicate signatures independently establish that peer model, class,
generation, and capability masks are not inputs to this bit **[OBS, DEC]**.

## Evidence

The principal generated evidence is:

- `data/static-analysis/listbuf-insert.disasm.txt`: track record construction.
- `data/static-analysis/listbuf-layout.disasm.txt`: insertion layout and other
  list-buffer builders.
- `data/static-analysis/right-column-precompute.disasm.txt`: configured-column
  selection, mapping arrays, numeric-key extraction, and string formatting.
- `data/static-analysis/client-and-render.disasm.txt`: row reconstruction,
  extension fields, flags, compatibility checks, and serialization.
- `data/static-analysis/context-track-type.disasm.txt`: Track dispatch,
  AppSync query path, context-byte extraction, and the type-one render gate.

Packet and database correlations remain in `PROTOCOL_REFERENCE.md`; controlled
oracle requirements remain in `CONFORMANCE_COVERAGE.md`.
