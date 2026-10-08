# Track secondary columns

Track-list rows carry a primary title and a configurable secondary value. This
chapter separates the database selection, value extraction, wire type, and
display formatting stages.

## Selection

Exactly one active `djmdSort` row normally has `Disable & 2`. This is the
persisted Rekordbox **Column** selection, not the active track sort. The track
builder uses it for Default sort, while a non-default `0x1004` sort selects the
right-column role stored in the list buffer. The eight-argument renderer can
independently read the persisted selection again. The builder resolves a
`MenuItemID`; the renderer resolves a sort `ID`. Neither value is a wire item
type. In the copied database:

```text
sort ID 12 -> menu item 11 (Key) -> Disable 2
```

The renderer executes the following query without `ORDER BY`:

```sql
SELECT ID
FROM djmdSort
WHERE rb_local_deleted = 0 AND (Disable & 2) = 2;
```

It accepts any nonempty result and reads row zero. Exactly one selected row is
therefore a database invariant rather than a constraint enforced by this read
path. Zero selected rows produce title-only `0x0004` rows. The fixture selecting
both Comment and Key reproducibly chooses Comment, but the query's missing
`ORDER BY` makes that an observation of the current database layout rather than
a precedence contract. Both states have repeat-verified oracle goldens.

The list-buffer builder performs the analogous live-row scan and returns the
first selected row's `MenuItemID`. It maps that value to an internal content
field, high type byte, and string formatter before inserting any track rows.
The complete intermediate map is in `ROW_LAYOUT.md`.

Track rows use a composite item type:

```text
(secondary_type << 8) | 0x04
```

`0x04` is the low-byte title/track type. The captured Key selection therefore
produces `0x0f04`.

## Complete selector map

`Get_SubCategoryValue` has a 16-entry jump table covering sort IDs 2 through
17. Sort ID 14 falls through without a dedicated extractor. The table below
also includes sort IDs 0 and 1, whose normal primary ordering does not define a
distinct secondary field.

| Sort ID | Menu item | Secondary | Type byte | Content field | Lookup/format source |
| ---: | ---: | --- | ---: | --- | --- |
| 0 | 25 | Default | `04` fallback | `Title` | Context order |
| 1 | 26 | Alphabet | `04` fallback | `Title` | Alphabetic title |
| 2 | 2 | Artist | `07` | `ArtistID` | `djmdArtist.Name` |
| 3 | 3 | Album | `02` | `AlbumID` | `djmdAlbum.Name` |
| 4 | 5 | BPM | `0d` | `BPM` | Numeric formatter |
| 5 | 6 | Rating | `0a` | `Rating` | Player star renderer/numeric value |
| 6 | 1 | Genre | `06` | `GenreID` | `djmdGenre.Name` |
| 7 | 21 | Comments | `23` | `Commnt` | Direct string |
| 8 | 14 | Time | `0b` | `Length` | Numeric duration formatter |
| 9 | 8 | Remixer | `29` | `RemixerID` | `djmdArtist.Name` |
| 10 | 9 | Label | `0e` | `LabelID` | `djmdLabel.Name` |
| 11 | 10 | Original Artist | `28` | `OrgArtistID` | `djmdArtist.Name` |
| 12 | 11 | Key | `0f` | `KeyID` | `djmdKey` plus key-name exchange |
| 13 | 15 | Bitrate | `10` | `BitRate` | Numeric formatter |
| 14 | none | Reserved/hole | fallback | none | No jump-table case |
| 15 | 13 | Color | `13` or `0x13 + ColorID` | `ColorID` | `djmdColor.Commnt` |
| 16 | 23 | DJ Play Count | `2a` | `DJPlayCount` | Numeric formatter |
| 17 | 22 | Date Added | `2e` | `StockDate` | Direct date string |

`ReturnIconID` independently contains the same sequence, including Comment
`0x23`, Remixer `0x29`, Original Artist `0x28`, DJ Play Count `0x2a`, and Date
Added `0x2e`. This provides a second static check on the jump-table decoding.

## Value extraction

Lookup-backed fields read the foreign-key ID from the materialized content row,
then fetch a display string from the named lookup table. A zero lookup ID yields
no lookup value. Artist, album, genre, remixer, label, original artist, and key
all take this path.

The lookup helper constructs this logical query against the local database:

```sql
SELECT <display-column>
FROM <lookup-table>
WHERE rb_local_deleted = 0 AND ID = <foreign-key>;
```

The display column is `Name` for Artist, Album, Genre, Remixer, Label, and
Original Artist; `ScaleName` for Key; and `Commnt` for Color. Soft-deleted or
dangling lookup rows therefore produce an empty secondary string even though
the composite type still identifies the selected column.

Numeric fields place the value in the row's auxiliary numeric output:

- BPM reads `BPM`.
- Rating reads `Rating`.
- Time reads `Length`.
- Bitrate reads `BitRate`.
- DJ Play Count reads `DJPlayCount`.

Comment copies the content row's `ID` to the auxiliary numeric output and
`Commnt` to the string output. Date Added likewise copies `ID` to the numeric
output and `StockDate` to the string output. This differs from the numeric
columns, whose auxiliary output is the displayed value itself.

Color reads `ColorID`, looks up its configured comment, and derives the type
byte as follows:

```text
ColorID == 0 or 255 -> type 0x13
otherwise           -> type 0x13 + low_byte(ColorID)
```

Thus an uncolored secondary value uses base type `0x13`; configured color IDs
1 through 8 yield `0x14` through `0x1b`. This is the same visual-type range used
by Color selector rows, although the row roles differ.

## Render-time controls

The render request controls pagination, the row-layout category, and whether
the secondary extractor runs. Argument numbers below are one-based wire
positions including context, offset, and count. Argument 4 is a low-word
first-row character seek key; zero uses ordinary pagination. Argument 5 is the
client-reported total and is unread by the renderer. Both fields are present
even in the five-argument shape **[DEC]**.

| Render shape | Argument 6 | Argument 7 | Argument 8 | Secondary behavior |
| --- | --- | --- | --- | --- |
| 5 arguments | absent | absent | absent | Default-sort capture uses the list-buffer value; the complete non-default active-sort cross is declared and awaits real-Rekordbox record/repeat |
| 6 arguments | low-word category ID | absent | absent | Maps the category through `DBCommon_GetCateKind` and preserves the right column materialized by the preceding list request |
| 7 arguments | low-word category ID | present on wire but unread | absent | Statically follows the six-argument control path; the complete active-sort/gate-value cross awaits real-Rekordbox record/repeat |
| 8 arguments | low-word category ID | override gate | selector override | Maps row-layout category and independently reconciles the materialized secondary value with the explicit selector or persisted Column fallback |

The category table maps 1-24, 30-32, 40, and 50-51 to themselves. IDs 25-29,
33-39, 41-49, zero, and values above 51 map to category kind zero. The queued
`render-numeric-fields` oracle covers each range and the high-word truncation
of arguments 4 and 6 **[DEC, OBS plan]**.

When argument 7 is nonzero, a nonzero argument 8 is used directly as the sort
ID. A zero argument 8 invokes the `djmdSort.Disable & 2` query. When argument 7
is zero, the renderer ignores argument 8. If that eight-argument effective
selector differs from the type already materialized by the list request,
Rekordbox clears the cached value and regenerates the selected column. The live
selector-14 control returns an empty secondary, zero high type byte, and base
track type `0x0004`. The static extractor sends IDs outside 2-17 to the same
empty-output return path; their serialized rows await the boundary matrix
**[OBS, DEC, OBS plan]**.

The decoder preserves more width than those ordinary controls exercised.
Argument 7 is read as 32 bits and canonicalized to boolean. Argument 8 is read
as 32 bits; its signed low byte reaches `ReturnIconID`, while all 32 bits reach
`Get_SubCategoryValue`. The `render-override-controls` matrix tests the
resulting disagreement classes: selector one, first-outside selector 18,
low-byte `0xff` and wrap `0x100`, a high-word Artist lookalike `0x00010002`,
and signed/unsigned boundaries. It also crosses five non-control gate values.
The static path is exact, but serialized row types remain pending real-
Rekordbox record/repeat under generation `ar18` **[DEC, OBS plan]**.

The six-argument RX3 cross removes that reconciliation control entirely. Every
captured page sent `[context, offset, count, 0, total, 12]`; argument 6 remained
`12` for Default, Alphabet, Artist, Album, BPM, Rating, Genre, Label, Key, Date
Added, and DJ Play Count. Nevertheless, arguments 0, 5, and 6 changed to the
active sort's materialized column. Thus render argument 6 value `12` is not a
Key-column selector in this request form **[OBS]**.

The five-argument active-sort cross is declared separately as
`sort-secondary-render-5.json`. It holds the fixture, identity, setup, sort
set, pagination, and expected row width equal to the complete six-argument
oracle while omitting the final value `12`. Its reducer reports exact per-case
row equality or divergence against the six-argument golden without assuming
either result. Until that record/repeat stage finishes, the six-argument rule
must not be generalized to five arguments **[OBS plan]**.

The seven-argument active-sort matrix crosses the same 11 sorts with wire
argument 7 values zero, one, and `UINT32_MAX`. The pinned `GetListBufContents`
body reads argument 6 when the count is at least six, but reads arguments 7 and
8 together only when the count is at least eight. Seven arguments therefore
have a source-derived prediction of the six-argument behavior regardless of
the supplied seventh value. The queued 33-case oracle tests that prediction;
it is not promoted as live behavior yet **[DEC, OBS plan]**.

`render-arity-boundaries.json` expands the arity axis independently of column
semantics. It sweeps total counts 3-32 under Default sort and crosses every
visible non-default sort at the underlong 3/4 and overlong 9/32 boundaries.
The declarations use `expect.outcome = any`; malformed or ignored optional
fields are authority questions for the queued real-Rekordbox record/repeat,
not assumptions derived from the eight-argument path **[OBS plan]**.

`render-arity-underflow.json` covers the remaining correctly framed counts
zero, one, and two. Each probe follows an initialized Default Track list on the
same connection and is followed by a fresh-connection health request. Raw
reply, timeout, and disconnect outcomes remain unconstrained until the queued
real-Rekordbox record/repeat completes **[OBS plan]**.

`conformance/suites/generated/render-secondary-controls.json` asserts the gate,
database selection, reserved hole, and every override from 2 through 17. This
separates render-time selection from the persisted settings suites.

These 5/6-argument rules describe ordinary track-list row rendering. Request
`0x2002` Display Song Info uses the same selector IDs but has an observed
exception: 5/6-argument renders and an eight-argument zero gate produce a
title-only composite row. Gate one with selector zero loads the database
selection, while selectors 2-17 use this table. The exact API-specific matrix
is in `DISPLAY_SONG_INFO_ORACLE.md`.

Request `0x2602` Delivery Info also uses selectors 2-17 for its composite Title
row, with the same values and high type bytes. Forward and reversed control
suites prove that its other metadata-row permutation is independent of selector
identity. Cold-process interleaving with all adjacent Song Info families shows
shared builder/list-buffer state: some precursor paths preserve the standalone
ordinal sequence, some force baseline order, and populated Display introduces
an additional alternating permutation. Request `0x2102` Play Song Info ignores
every tested gate and selector. The full matrices and ordering evidence are in
`SONG_INFO_SIBLINGS_ORACLE.md` **[OBS]**.

The renderer first compares the effective selector's type with the right type
already stored in `djmdLeftBuf`. A match preserves the precomputed numeric key
and server-formatted `rightStr`. A mismatch clears both, removes the stale high
type byte, and regenerates the requested value through
`Get_SubCategoryValue`. Consequently, database-selected and override rendering
can differ for the same conceptual column: the former can retain richer cached
formatter text and its numeric sentinel, while the latter uses the raw
extractor path.

## Length and empty-value rules

The dynamic extractor truncates secondary strings by JUCE character count
before converting them to UTF-16:

| Source | Maximum characters |
| --- | ---: |
| Lookup-backed fields, including Color | 127 |
| Comment and Date Added | 255 |
| Numeric fields | No secondary string |

The limits are characters, not UTF-16 bytes. A supplementary Unicode character
occupies one JUCE character but two UTF-16 code units. The wire length remains
the UTF-16 byte length including the two-byte NUL terminator. An empty result
stores a null secondary pointer; row serialization still reports the empty
wire string length as 2.

Key-name exchange runs after the lookup value is truncated and copied to
UTF-16. The extractor computes the original pre-truncation character count as
its return value, but `GetListBufRowContent` ignores that return value and later
derives wire lengths from the resulting UTF-16 pointer.

A second limit applies when `DsqlListBuf_Insert` stores a precomputed
`rightStr`: primary, right, and internal sort strings of 255 or more UTF-16 code
units are terminated at code-unit index 255. This list-buffer limit counts
UTF-16 units rather than JUCE characters and mutates the supplied buffer. It
can therefore be the effective limit for cached formatter output even when the
dynamic extractor has a different cap.

The boundary fixtures include 126-, 127-, and 128-character lookup values;
254-, 255-, and 256-character Comment and Date Added values; and controlled
supplementary-character values around 255 UTF-16 code units.
`secondary-string-boundaries.json` records the eight lookup-backed families:
126 and 127 characters survive, while 128 is truncated to 127. The two
fresh-connection isolation suites prove that Comment and Date Added accept and
preserve 255 UTF-16 units, while 256 is the first width that returns a menu
header and then stalls rendering. ASCII input at 256 characters succeeds after
truncation to 255. `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md` contains the complete
case table and fixture hashes.

## String ownership

The secondary value is not guaranteed to be a literal rendering of the column
named by its type. Composite text belongs to the list-builder cache. Default
sort with persisted Key, and six-argument active Key sort, produce:

```text
3A - 112.2 bpm
```

Six-argument active BPM sort reverses the components:

```text
112.2 bpm - 3A
```

Artist, Album, Genre, Label, Date Added, and Alphabet produce one text value.
Rating and DJ Play Count carry their number in argument 0 and leave argument 5
empty. An eight-argument selector that differs from the materialized column
uses the dynamic extractor instead: Artist and Album still return one lookup
string, Key returns only the key spelling, and BPM returns its number with an
empty argument 5. An eight-argument selector matching the materialized Key or
BPM type preserves the cached composite. The complete same-track matrix is in
`SECONDARY_COLUMN_ORACLE.md` **[OBS]**.

## Joined four-path authority

`data/secondary-column-semantics.json` extracts fields 0, 5, 6, and 12-15 for
the same track from 63 canonical real-Rekordbox profiles: all 15 persisted
Default columns, all 11 visible six-argument active sorts, and 19
eight-argument gate/override controls, plus all 18 active sorts rendered through
the eight-argument persisted-column fallback. The artifact projects all eight
fixture tracks in every profile, for 504 row projections, while retaining typed
focus-row fields, the request, first render, and source hash **[OBS]**.

The join makes the cache boundary exact. Persisted materialization and a
Default-list explicit override agree in all selected fields for 14 of 15
columns. BPM alone differs: persisted BPM carries `120.0 bpm - Am`, while a
Key-materialized Default list dynamically overridden to BPM carries the same
numeric value and `0x0d04` type but an empty argument 5. The explicit Key
selector matches the already materialized Key type and preserves
`Am - 120.0 bpm`. Thus an eight-argument selector name alone does not predict
whether composite text exists; equality with the list buffer's high type is
the deciding condition **[OBS, DEC]**.

The all-track comparison produces the same result on every content ID:
persisted versus explicit override differs only at BPM argument 5, for all
eight tracks. Nonzero Rating, Time, Bitrate, and DJ Play Count values introduce
no further difference **[OBS]**.

Persisted and active-sort materialization preserve the same display text,
item type, and fields 12-15 for every shared visible column. Their only
same-track differences are argument 0 for Artist, Album, Genre, Label, Key,
and Date Added: active lookup sorts use zero, active Key uses normalized sort
key 14, and active Date Added uses zero instead of the persisted content ID.
All 63 profiles retain `5001, 6, "Am", 12000` in fields 12-15 **[OBS]**.
Across the other seven tracks, each path likewise retains that track's own
KeyID, key length/text, and BPM. The unassigned-Album track is the sole
per-track exception to the argument-0 difference set: its persisted AlbumID and
active Album sort key are both zero **[OBS]**.

The 18-sort eight-argument fallback cross holds the request tail at
`[12, 1, 0]`, so the effective requested column is persisted Key even after a
non-default sort. Default and active Key have already materialized Key and
retain the cached `Key - BPM` composite. Every other active sort has a
different materialized type; reconciliation returns KeyID in argument 0,
single Key text in argument 5, and Key type `0x0f04` in argument 6. Comparing
the 11 shared visible sorts with six-argument rendering gives complete row
equality for Default and Key. Every row under the other nine sorts differs in
exactly fields 0, 5, and 6. Fields 12-15 remain unchanged **[OBS]**.

The composite type remained `0x0f04`, and tertiary argument 14 contained the
key spelling. An older capture carried comparable key/BPM text under composite
type `0x2304` (Comment). Clients must use the type for layout semantics while
treating the text as server-authored display content.

The static extractor calls `exchangeKeyNameIfNeed` for Key after copying the
lookup string to UTF-16. The controlled desktop-preference matrix remains
Classic in all four states because the serving path reads the local CDJ style
from `DEVSETTING.DAT`. The direct two-state device-setting oracle changes
`Am - 120.0 bpm` to `8A - 120.0 bpm` and tertiary `Am` to `8A`, while every
numeric field and row order remains fixed. `KEY_NOTATION_ORACLE.md` contains
the complete file format, static call chain, and wire evidence.

## Track-row placement

For the captured Key selection, the 16-field row correlates as follows:

| Argument | Value |
| ---: | --- |
| 0 | `djmdContent.KeyID` |
| 1 | `djmdContent.ID` |
| 2 | UTF-16 byte length of argument 3, including NUL |
| 3 | `Title`, or `FileNameL` for File Name browsing |
| 4 | UTF-16 byte length of argument 5, including NUL |
| 5 | Key/BPM summary |
| 6 | `0x0f04` |
| 7 | Scope/state flags |
| 8 | Content ID |
| 9 | Scope-specific position or track number |
| 10 | `0x00000100` because `HotCueAutoLoad` was nonempty |
| 11 | Converted/new-key ID when the key-category path populates it |
| 12 | Original `djmdContent.KeyID` |
| 13 | UTF-16 byte length of argument 14, including NUL |
| 14 | Key spelling |
| 15 | BPM multiplied by 100 |

Argument 0 is the effective right-column numeric key. Argument 12 is populated
separately from the full content row and remains the original KeyID regardless
of the secondary selection. All 15 persisted selections have now been captured
and repeat-verified. `SECONDARY_COLUMN_ORACLE.md` gives the exact argument 0,
argument 5, packed type, numeric sweeps, and Sort-menu transformation;
`ROW_LAYOUT.md` traces the fields end to end.

The Preferences reader and serving renderer do not share a selected-row
snapshot. Preferences reads every nondeleted sort row in `Seq` order, reports
the first selected ID, and logs when more than one exists. Configured-fallback
rendering performs its own unordered selected-ID query, while six-argument
non-default-sort rendering uses the right-column role already materialized by
the active list builder. This distinction is observable only in corrupted
zero/multiple-selection states and is detailed in `CONFIGURATION.md` **[DEC,
OBS]**.

## Legacy and extended rows

The two-argument setup observed in the current probes receives all 16 fields.
The one-argument RX3-style setup receives the first 12 fields. Rekordbox builds
the full logical row before serialization, so the legacy form retains argument
5 and the composite type in argument 6. Implementations should truncate at the
serialization boundary rather than rebuild a title-only row.

## Controlled verification matrix

Selection, sort-menu, and complete eight-row capture are complete for all 15
selectable values in the extended XDJ-RX3 setup. Lookup-backed string
boundaries, the hidden-selected state, and the exact Comment/Date Added UTF-16
stall threshold are complete. The supported Column refresh lifecycle is also
complete: the UI locks while Link is active, then a Key-to-Comments change is
consumed by the next Link activation without restarting rekordbox.

The matching legacy matrix is complete for all 15 selections. Each legacy suite
uses the identical fixture and two cases as its extended partner. All 15
hash-bound fresh-fixture/process repeats preserve Sort-menu behavior, totals,
row counts, and row kinds. The strict reducer proves that every 12-field legacy
row is the exact prefix of the corresponding 16-field extended row. The
canonical result is
`data/experiments/secondary-column-legacy/summary.json` **[OBS, DB]**.

Remaining orthogonal coverage includes hidden and malformed selection states,
same-process settings refresh, render gates and explicit selector overrides,
and string-width boundaries in legacy setup. Those behaviors already have
extended evidence but are outside the current 15-selection legacy cross.

`SETTINGS_SESSION_REFRESH_ORACLE.md` records the completed UI and wire
experiment. `SETTINGS_EXPERIMENTS.md` supplies the remaining transaction-level
procedure. The table above is implementation evidence; formatter output remains
capture evidence.
