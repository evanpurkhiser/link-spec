# Database query pipelines

Rekordbox does not express every Link Export menu as a literal SQL statement.
Its `djeplGet*` functions build materialized rowsets through the embedded
database API, filter them with callbacks, sort them, and copy them into a
temporary left/list buffer. This chapter names the tables, constraints, and
pipeline stages visible in rekordbox 7.2.19.

The machine-readable companion
`data/static-analysis/menu-database-query-map.json` classifies every request
kind declared anywhere under `conformance/suites/`. Each classification names
its operation, tables, predicate, ordering, result shape, and evidence tier.
`conformance/test_menu_database_query_map.py` rejects duplicate assignments,
unclassified declared kinds, database paths without tables, and empty table
sets that are not explicitly classified as having no database builder.

`SQL_LITERAL_INDEX.md` complements that semantic map with the exact SQL text
present in the retained disassembly. Its generated JSON preserves every source
file, line, address, nearest function heading, platform, duplicate occurrence,
and whether the literal is structurally complete or an explicit fragment.
Literal SQL and reconstructed runtime query behavior are kept separate.

`DATABASE_FIELD_REFERENCE.md` supplies the field-level companion. It reads
schema metadata from the deterministic encrypted AppSync fixture, covers all
22 physical tables and 389 columns named by this map, and classifies
`djmdLeftBuf`, `djmdTrackSort`, and `djmdImage` without pretending they are
physical tables in that fixture. Each table and semantically identified field
links back to its concrete wire request kinds across the complete 95-kind map.
The generated request-kind index provides the inverse lookup while marking its
field list as family-level rather than stage-specific evidence.
A `SELECT *` label means the complete row was retrieved; it does not imply
every returned field affects Link Export output.

## Common pipeline

Most request families follow this shape:

```text
request handler
  -> clear djmdLeftBuf/list buffer
  -> choose database context and rowset helper
  -> select live IDs and/or values
  -> apply selector predicate and Link Export visibility filter
  -> materialize distinct entities
  -> add ALL/Unknown synthetic rows when the hierarchy requires them
  -> djdsqlFlexSort for track lists
  -> insert typed rows into the list buffer
  -> terminate the buffer
```

The render request later reads the buffer; it does not rerun the original
category query. The first `djmdLeftBuf` column stores the query's complete
32-bit packed context. `DsqlListBuf_Clear(context, 1)` deletes only rows with
that value, and `DsqlListBuf_Insert(context, row)` writes the same value into
each new row. `GetListBufContents` passes the render context to
`WhereListBuf_Condition`, which accepts a row only when column zero equals that
context. The embedded table is shared by the Rekordbox process, so independent
TCP connections page the same context-keyed snapshots with `3000` **[OBS,
DEC]**.

### Serving interface selection

`PSvDBMain::SetSharedDBInfo` constructs a 40-byte `PSvAppSyncDBIF`, installs
its object pointer at `PSvDBMain + 0x690`, and changes the associated
`FilterSettingManager` database index to `3`. The same function constructs a
new filter manager with index `3` when one does not yet exist. This is the
database-interface object used for the shared library exposed by Link Export
**[DEC]**.

The parallel `PSvMasterDBIF` vtable belongs to a different database-index arm,
not an alternate shared-server state. `FilterSettingManager` construction,
`FilterSettingManager::setDBIndex`, and `TrackFilter` construction each select
`PSvAppSyncDBIF` when the index equals `3` and `PSvMasterDBIF` for every other
index. The complete x86-64 text scan finds all three Master-vtable LEA sites in
those functions. Its six AppSync sites comprise their three index-3 arms,
`SetSharedDBInfo`, and two destructor vptr resets. No Master-vtable selection
site belongs to `PSvDBMain` or the Link Export request dispatch **[DEC]**.

This distinction explains why Master wrappers appear beside AppSync query
builders in the executable: desktop filtering can operate on either database
class, while the network-shared library is installed as AppSync. See
`data/static-analysis/db-interface-selection.{json,md}` and
`data/static-analysis/db-interface-selection.disasm.txt`. The bounded scan is
for the pinned x86-64 slice; computed, dynamically loaded, and arm64-only
construction remain outside that static claim.

The Hot Cue Bank location-state oracle varies only the location byte and binds
this implementation to live behavior. A query replaces its own location's
rows while older locations remain readable. A render for an uninitialized
location times out, and a foreign initialized location returns its stale rows.
See `HOT_CUE_BANK_ORACLE.md` and
`data/static-analysis/list-buffer-location.disasm.txt`.

The ordinary Track final-byte oracle holds requester, location, and slot fixed
while exhausting the low context byte. The active `getTrack_Root` membership
path does not branch on that byte: 254 successful values return the same eight
content rows. The renderer does branch on it, admitting cache and
`HotCueAutoLoad` enrichment only for type `0x01`; this changes only row argument
10 from zero to `0x100`. Values `0x03` and `0x04` are diverted by
`PSvDBMain::OnClientReq` before the `0x1xxx` list dispatcher, so they never
reach these queries or return a header. See `PACKED_CONTEXT_ORACLE.md`
**[OBS, DEC]**.

The 47-family context cross also establishes that Root and Search admission is
restricted to `TT == 1`: other normally dispatched types receive zero-row
menus. Direct category, hierarchy, and scalar leaf queries still execute.
Seven hierarchy/playlist track builders copy `TT << 24` into row argument 7;
ordinary Track and scalar-filter leaves do not. These are presentation/builder
differences over the same controlled database, not membership changes.

### Liveness rules

The database uses soft deletion. At minimum, served content must satisfy
`djmdContent.rb_local_deleted = 0`. Lookup, membership, and relation tables
also have `rb_local_deleted`; joining a live content row through a deleted
relationship produces behavior rekordbox itself filters out.

`dsqlIsLinkExportVisibleTrack` is exactly the inverse of
`streaming::isStreamingProtocol(djmdContent.FolderPath)`. Both overloads fetch
only content column 1 (`FolderPath`) for this decision. In the active runtime,
exact lowercase SoundCloud, Tidal, Spotify, and Apple Music protocol paths are
filtered. Beatport is constructed and classifies paths containing
`/v4/catalog/tracks/`; the live `beatport:tracks:` row is a nonmatching syntax
control. Beatsource has a reserved null service slot and a constant-false
standalone helper in this build.
Unknown, case-changed, embedded, prefix-only, empty, null, and ordinary local
paths remain visible **[OBS, DEC]**.

Collection, File Name, ordinary playlist, Smart playlist, and Search all return
the same filtered membership. Persisted History request `1112` returns all
fourteen controlled rows. The active Windows `PSvAppSyncDBIF` builder selects
each live `djmdContent` row by `djmdSongHistory.ContentID` and constructs it
without reading `FolderPath`; its vtable-resolved function has no streaming
gate. The pinned macOS `djeplGetTrack_History` instead filters both of its
loops. Codec compatibility, cloud Song Info path selection, and media-file
existence are separate decisions. See `LINK_EXPORT_VISIBILITY_ORACLE.md`.

## Configuration queries

### Root categories

`DsqlCategory_GetEnableItem` selects materialized rows from `djmdCategory`,
applies `WhereCategory_Enable`, sorts by column 1 (`Seq`) ascending, and returns
columns 0 and 1 (`ID`, `MenuItemID`). `DsqlMenuItem_GetItem` then resolves the
localization token and class from `djmdMenuItems`.

The predicate is capability-aware and is specified exactly in
`CONFIGURATION.md`; it is more selective than the UI-oriented SQL string
`(Disable & 1) = 0` found elsewhere in the executable.

### Sort menu

The root category reader opens only `djmdCategory`. Its predicate reads
`MenuItemID` and `Disable`, it sorts by `Seq`, and it returns `ID` plus
`MenuItemID`. It never opens a content table, so enabled empty categories stay
in the root. `InfoOrder` is preserved by the settings editor but is not read by
the root or active Display Song Info serving path **[DEC, OBS, DB]**.

`DsqlSort_GetEnableItem` selects materialized rows from `djmdSort`, applies
`WhereSort_Enable`, sorts by `Seq`, and returns `ID` and `MenuItemID`. The
predicate accepts rows where `(Disable & 1) == 0`.

### Secondary column

The Preferences settings model separately reads every nondeleted `djmdSort`
row in `Seq` order and returns the first selected ID, logging multiple
selections. It does not supply an ordered selection snapshot to Link Export.

List construction scans live `djmdSort` rows for `Disable & 2` and takes the
first selected row's `MenuItemID` without an explicit order. That menu item is
mapped to an internal content-field selector, item type, and table-string
formatter. `insertLeftBuf_Track` stores the resulting key and formatted
`rightStr` in `djmdLeftBuf`.

The row renderer independently executes:

```sql
SELECT ID FROM djmdSort
WHERE rb_local_deleted = 0 AND (Disable & 2) = 2;
```

It reads row zero, obtains a full content record, and dispatches the selected
sort ID through `Get_SubCategoryValue` only when the requested type differs
from the precomputed type. A matching type preserves the materialized key and
string. See `SECONDARY_COLUMNS.md` and `ROW_LAYOUT.md`.

### Display Song Info

The AppSync implementation of request `0x2002` selects one live content row:

```sql
select * from djmdContent
where rb_local_deleted = 0 and ID = %lu
```

It separately snapshots `MenuItemID, Disable` from every live `djmdCategory`
row. It reads Title, Length, BPM, KeyID, Rating, ColorID, GenreID, StockDate,
Commnt, BitRate, ReleaseYear, LabelID, OrgArtistID, and RemixerID directly from
the content record. Artist, Album, Genre, Label, Original Artist, and Remixer
text are resolved from entity tables by ID. The generic lookup column is
`Name`; Key uses `djmdKey.ScaleName`, and Color uses `djmdColor.Commnt`
**[DEC]**.

The builder inserts 16 fixed metadata rows for the populated fixture. Persisted
category state sets the argument-0 enabled flag on associated simple rows; it
does not change membership. All 21 one-category-disabled fixtures are recorded
and mapped in `CATEGORY_ORACLE.md`. The
Master-database path uses `DsqlCategory_GetInfo` and
`DsqlContent_GetSongInf`. `DISPLAY_SONG_INFO_ORACLE.md` contains the complete
wire rows, both database-interface paths, and the bounded open questions.

### Play Song Info and Delivery Info

The adjacent `0x2102` and `0x2602` AppSync builders begin with the same live
content query as Display Song Info:

```sql
select * from djmdContent
where rb_local_deleted = 0 and ID = %lu
```

Play Song Info constructs seven rows from FileType, Length, BPM, Commnt,
HotCueAutoLoad, and KeyID. Its delivery-path row also reads ContentsLink,
FolderPath, OrgFolderPath, FileSize, ServiceID, MasterDBID, and local DBID.
Cloud/local path selection can query `select DBID from djmdProperty` **[DEC,
OBS]**.

The repeated path oracle establishes the database semantics for the active
runtime configuration. Null or empty `FolderPath` suppresses the complete Play
menu; `FileSize` is reduced to 32 bits; `HotCueAutoLoad` tests string
nonemptiness; and a positive `ServiceID` with matching `MasterDBID` selects an
existing regular-file `OrgFolderPath`. Directories fail that file test, while
zero-byte files pass. `PLAY_SONG_INFO_PATH_ORACLE.md` records all fourteen
input/output cases **[OBS, DEC]**.

The path branch reads raw integer `CLSSyncMethod` with default 1 and tests only
zero versus nonzero. Nonzero values use the DBID/regular-file rule and a fixed
share-root switch: ID 0 is empty, ID 1 uses the current master-database
directory plus `/share`, and IDs 2/3/4 use Dropbox/Google Drive/OneDrive local
roots plus `/rekordbox`. Zero uses any existing `OrgFolderPath`, otherwise the
`MovedFromCloudDir` helper for service IDs 0 and 2-5; its default comes from
special-location kind 3 plus `PioneerDJ/Moved from Cloud`. The zero class has a
ten-track authority recording queued; all other integer classes are statically
closed **[DEC, OBS plan]**.

Delivery Info constructs thirteen live AppSync rows from ComposerID, BPM,
DeliveryComment, KeyID, FileType, GenreID, LabelID, ArtistID, Lyricist,
DeliveryControl, ISRC, Title, AlbumID, and Length. It queries the live property
DBID and resolves entity names dynamically from `djmdArtist`, `djmdAlbum`,
`djmdGenre`, `djmdKey`, and `djmdLabel`; Key uses `ScaleName`, while the other
lookups use `Name`. The recovered static fallback builder has 19 insertion
sites and is a separate path from the observed 13-row AppSync response
**[DEC, OBS]**.

`SONG_INFO_SIBLINGS_ORACLE.md` records every returned row and identifies the
exact Delivery-only field limits. ComposerID resolves through `djmdArtist`;
dangling IDs retain their numeric value with empty text. Composer names and
Lyricist cap at 127 UTF-16 units, while DeliveryComment and ISRC cap at 255.
DeliveryControl is a case-insensitive comparison with `ON`. Authenticated
cloud configurations that change the runtime sync method or cloud roots remain
open; the database-controlled Play path axes are recorded.

## Track rowsets and sorting

All ordinary track-producing getters converge on `getRowset_Track`, followed
by `djdsqlFlexSort` and `dsqlInsertLeftBuf_Track`. Static rowset storage names
identify `djmdTrackSort` as the intermediate sorting table.

`getRowset_Track` accepts the database index, a selector/category byte, and up
to four integer selectors. That signature matches root, album, artist/album,
genre/artist/album, label/artist/album, rating, bitrate, color, length, BPM
range, key range, and release-year callers. Wildcard `0xffffffff` selectors
remove an intermediate constraint.

`djdsqlFlexSort` uses the requested sort ID. The visible sort map is:

| Sort ID | Database basis | Default direction/role |
| ---: | --- | --- |
| 0 | Context-specific sequence | Playlist/album/default semantics |
| 1 | `djmdContent.Title` | Alphabetic |
| 2 | `djmdArtist.Name` through `ArtistID` | Alphabetic |
| 3 | `djmdAlbum.Name` through `AlbumID` | Alphabetic |
| 4 | `djmdContent.BPM` | Numeric |
| 5 | `djmdContent.Rating` | Numeric |
| 6 | `djmdGenre.Name` through `GenreID` | Alphabetic |
| 10 | `djmdLabel.Name` through `LabelID` | Alphabetic |
| 12 | `djmdContent.KeyID` / normalized key | Musical-key order |
| 16 | `djmdContent.DJPlayCount` | Numeric |
| 17 | `djmdContent.StockDate` | Date |

Hidden sort IDs 7, 8, 9, 11, 13, and 15 remain valid configuration identities
for Comment, Time, Remixer, Original Artist, Bitrate, and Color.

The live sort-ID sweep confirmed that every ID 0 through 17 returns all eight
fixture tracks, including hidden IDs and reserved ID 14. Their exact title
orders group as follows **[OBS]**:

| Sort IDs | Ordered fixture titles |
| --- | --- |
| 0, 1, 2, 9, 11, 14 | Alpha One; Alpha Two; Beta One; Boundary Fifty Nine; Boundary Sixty; Maximum Ordinary; Unicode Omega Search; Unknown Album |
| 3 | Alpha One; Beta One; Boundary Fifty Nine; Maximum Ordinary; Unicode Omega Search; Alpha Two; Boundary Sixty; Unknown Album |
| 4, 7, 15 | Alpha One; Alpha Two; Beta One; Boundary Fifty Nine; Boundary Sixty; Unicode Omega Search; Unknown Album; Maximum Ordinary |
| 5 | Unicode Omega Search; Boundary Sixty; Boundary Fifty Nine; Beta One; Alpha Two; Maximum Ordinary; Alpha One; Unknown Album |
| 6, 10, 12 | Alpha One; Beta One; Boundary Sixty; Unknown Album; Alpha Two; Boundary Fifty Nine; Maximum Ordinary; Unicode Omega Search |
| 8, 13, 16 | Maximum Ordinary; Unknown Album; Unicode Omega Search; Boundary Sixty; Boundary Fifty Nine; Beta One; Alpha Two; Alpha One |
| 17 | Boundary Fifty Nine; Maximum Ordinary; Beta One; Unknown Album; Alpha Two; Unicode Omega Search; Alpha One; Boundary Sixty |

The golden retains the original Greek omega in the fixture title; the spelling
above keeps the table ASCII-only. Hidden status controls sort-menu visibility,
not whether an explicit track request may use the ID.

## Menu-family query map

| Wire family | Static getter path | Tables and constraints |
| --- | --- | --- |
| Track `1004` | `djeplGetTrack_Root` -> `getRowset_Track` | Live `djmdContent`; normal flex sort |
| File Name `1013` | `djeplGetFileName_Root` -> `getRowset_Track` | Same content IDs; `FileNameL` primary text |
| Album `1003/1103` | `getRowset_Album`, then `getRowset_Track` | Referenced `djmdAlbum`; content `AlbumID` |
| Artist `1002/1102/1202` | `getRowset_Artist`, `getRowset_Album`, track rowset | `djmdArtist` through content `ArtistID`; optional album |
| Genre `1001..1301` | `getRowset_GenreLabel`, artist, album, track | `djmdGenre` through `GenreID`, then optional artist/album |
| Label `100a..130a` | `getRowset_GenreLabel`, artist, album, track | `djmdLabel` through `LabelID`, then optional artist/album |
| Remixer `1602..1802` | artist, album, track getters | `djmdArtist` through `RemixerID`, then optional album |
| Original Artist `1302..1502` | artist, album, track getters | `djmdArtist` through `OrgArtistID`, then optional album |
| Key `1014..1214` | `getRowset_Key`, range builder, track rowset | Content `KeyID`, `djmdKey`, normalized 24-key model |
| Old Key `100B/110B` | `getKey_Root`, `getTrack_Key` | Every live `djmdKey` row at root; live visible content filtered by exact `KeyID` for tracks |
| Cue Track root `130C` | recognized `OnListClientCmd` arm | No database builder and no reply |
| New Key family | New-key root/range/track getters | Converted key IDs and `Dsql_getNewKeyTrackRowset` |
| BPM `1006..1206` | BPM root/range getters, track rowset | Distinct rounded BPM; percentage-range predicate |
| Rating `1007/1107` | rating root, track rowset | Distinct `Rating`, then equality filter |
| Release Year `1008..1208` | decade/year getters, track rowset | `ReleaseYear` decade and exact-year filters |
| Stock Year client names `1308..1608` | no database builder | Shared invalid branch in `OnYearListCmd`, followed by `4003` unknown-command reply |
| Date Added `1708..1a08` | date-added root/track getters | `StockDate`, parsed year/month, date predicate |
| Color `100d/110d` | `getRowset_Color`, track rowset | All `djmdColor`; content `ColorID` equality |
| Time `1010/1110` | length root, track rowset | `Length` minute buckets |
| Bitrate `1011/1111` | bitrate root, track rowset | Distinct `BitRate`, then equality filter |
| DJ Play Count | play-count root/track getters | Distinct/ranged `DJPlayCount`; play-count predicate |
| Matching `1017` | `getRowset_Matching` | Bidirectional `djmdRecommendLike` endpoints |
| Search `1300` | `djeplGetNewSearchResult` | Artist, Album, Content/Title, and File Name search domains |
| History `1012/1112` | history and song-history rowsets | `djmdHistory`, `djmdSongHistory`, active Link lifecycle |
| Playlist `1105` | playlist-specific getters | `djmdPlaylist`, `djmdSongPlaylist`, recursive ParentID |
| Hot Cue Bank | `PSvDBMain::GetHCBnkList` | `djmdHotCueBanklist`, `djmdSongHotCueBanklist`, content |
| Provider browsers `5000..5202`; 64-bit track ID `6100` | no database builder | Request class bypasses `1xxx`/`2xxx`/`3xxx` handlers and returns `4003` through `OnUnknownClientCmd` |

The filename boundary fixture makes the `FileNameL` source exclusive:
`FileNameS`, `FolderPath`, `OrgFolderPath`, and `rb_LocalFolderPath` all contain
deliberately different basenames. The wire preserves dots and path separators,
stops at embedded NUL, normalizes null to empty, and caps the rendered value at
255 UTF-16 units. A split surrogate at that cap becomes U+FFFD **[OBS, DB]**.

## Hierarchical entity rowsets

### Genre and Label

Genre and Label share `getRowset_GenreLabel`; a category/table selector chooses
the lookup. The root contains only values referenced by visible content. Later
levels constrain distinct artists and albums through the same content rows.
ALL removes that dimension rather than looking up an entity with ID
`0xffffffff`.

### Artist, Remixer, and Original Artist

These families share `getRowset_Artist` with different content foreign keys.
The lookup table is always `djmdArtist`. Album rowsets then constrain content by
the chosen foreign key and `AlbumID`.

### Album and Unknown

`getRowset_Album` returns referenced album IDs. Hierarchical getters call
`djdsqlAddItem_ALL` and `dsqlInsertLeftBuf_Unknown` around concrete rows. ALL is
conditional on multiple children. Database ID 0 can produce a concrete Unknown
row and remains distinct from the wildcard.

## Numeric selectors

### BPM

The root normalizes raw integer hundredths with:

```text
rounded = ((BPM + 50) / 100) * 100
```

It excludes zero, de-duplicates normalized values, and orders them numerically.
The range selector supplies tolerance 0-6. Selector 6 in `getRowset_Track`
handles zero specially: it rounds the selected value to a whole BPM and filters
the inclusive interval `[rounded - 50, rounded + 49]`. For nonzero percentage
`p`, it constructs signed integer bounds
`(100 - p) * selected / 100` and `(100 + p) * selected / 100`, truncating toward
zero, then applies `lower <= BPM && BPM <= upper`. The focused control flow is
preserved in `data/static-analysis/bpm-tolerance-boundaries.disasm.txt`
**[DEC]**. A 43-track real-Rekordbox record/repeat brackets every bound by one
hundredth and confirms the predicate exactly. For selected BPM 120.00,
tolerance zero includes 119.50 through 120.49 and excludes 119.49/120.50.
Tolerances 1 through 6 include both computed endpoints and exclude their
immediate outside neighbors. The deliberately overlapping fixture produces
nested result totals 5, 11, 17, 23, 29, 35, and 41 **[OBS, DB]**.

### Time

The root groups integer seconds by `Length / 60`, accepts values through 10,799
seconds, and orders buckets descending. A selected bucket constrains the track
rowset to its 60-second interval.

### Bitrate, Rating, and play count

Bitrate and Rating roots scan distinct content values, apply different root
domain guards, and use equality-like track stages. Bitrate preserves a zero
bucket but suppresses stored `INT32_MAX`; directly selecting that value also
returns zero. Rating advertises only 0-5, yet direct selector 99 returns a
stored rating-99 track. Color similarly advertises only palette IDs 1-8, while
direct selector 0 reaches an unassigned track; a dangling color ID does not.
The repeat-verified 39-case scalar oracle distinguishes these root and direct
paths **[OBS, DB, DEC]**. DJ Play Count has its
own `wherefuncGet_PlayCountTrack` rather than the generic track helper. The root
sorts field key `0x17`, reads 16-bit values, de-duplicates adjacent counts, and
inserts selector type `0x2a`. The track predicate compares a one-byte request
selector with a one-byte read of the same field **[DEC]**. Counts above 255 can
therefore collide on their low byte; the boundary fixture explicitly exercises
254, 255, 256, 257, 32767, and 65535 before the oracle assigns wire behavior.

## Relationship and stateful families

### Matching

`Dsql_GetMatchingContents` reads `djmdRecommendLike`. If the seed equals either
endpoint, the other endpoint is added to a sorted set. `LikeRate` is not needed
for the observed list. The resulting content IDs pass through normal visibility
and sorting.

### Playlist

Folders and playlists are a recursive `djmdPlaylist.ParentID` tree. Concrete
ordinary-playlist membership and order come from `djmdSongPlaylist.TrackNo`.
For `Attribute = 4`, Rekordbox evaluates `djmdPlaylist.SmartList` and ignores
materialized membership rows. A contradictory fixture proves that a valid
House rule wins over two stored Techno members; malformed and absent rules win
over stored members by returning empty. `Attribute = 0` does not activate a
rule merely because `SmartList` is populated **[OBS, DB]**.

The evaluated candidate set then passes through the same `FolderPath`
streaming visibility gate as an ordinary playlist. The controlled visibility
fixture proves identical ten-of-fourteen membership for both paths **[OBS,
DEC]**.

The property oracle maps all 23 written SmartList names to controlled source
columns and lookup relations. In particular, `dateCreated` reads the track
`DateCreated` field rather than the conflicting `created_at` audit timestamp,
`mixName` reads `Subtitle`, and custom `myTag` rules match raw positive tag IDs.
The `filename` spelling is accepted alongside `fileName`; `title`, `color`,
`playCount`, `remixer`, and `composer` controls return empty **[OBS, DB]**.

Date predicates parse `StockDate`, `DateCreated`, and `ReleaseDate` into the
same comparison domain. Equality/range behavior includes leap day and both
ordered endpoints. Rows whose selected field is blank or malformed are
excluded even from not-equal, while numeric predicates instead coerce blank
and malformed rule text to zero **[OBS, DB]**.

Relative operators 6 and 7 use only `ValueLeft`; `ValueRight` does not affect
their results. Case-insensitive singular `month` selects calendar-month
conversion. Every other `ValueUnit`, including `day`, `week`, `year`, plural,
empty, and unknown strings, selects day conversion. Blank, malformed,
fractional, zero, and negative count inputs all produce the zero-count result.
Future dates pass operator 6's lower-bound test, while blank and malformed
track dates pass neither relative operator **[OBS, DB, DEC]**.

The shared fixed-date converter requires a 10-character string but reads only
positions 0-3, 5-6, and 8-9. Separator positions 4 and 7 are unconstrained.
The consumed code points are combined arithmetically without a digit check,
then handed to the C time conversion routine, so calendar overflow is
normalized rather than rejected. Live rows prove equivalent hyphen, slash,
dot, space, letter, Unicode, and newline separators; parseable month/day
overflow; and a parseable ASCII letter in the year field. Wrong lengths,
nonpositive conversions, embedded NUL, and SQL `NULL` do not enter the
comparison domain. `smart-date-conversion.disasm.txt` contains the complete
converter and the 117-case live result is summarized in
`data/experiments/smart-date-format-matrix/summary.json` **[OBS, DB, DEC]**.

String predicates use a shared collation/search layer rather than SQL text
comparison. The Comments matrix establishes primary-strength-like case,
accent, and width folding, kana equivalence, Greek sigma folding, selective
Turkish-I behavior, asymmetric sharp-S/SS and AE/AETHER expansions, and
significant punctuation and whitespace. Precomposed accented candidates join
the base equality class, while rules containing combining marks and the two
tested combining-order rules return empty. Embedded NUL truncates stored text;
empty equality includes SQL `NULL`, empty inequality includes every nonempty
row, and the four empty substring rules return empty. XML entities and
supplementary emoji survive the SmartList XML path. The 55 exact sets are in
`data/experiments/smart-text-matrix/summary.json`, and
`smart-collation.disasm.txt` preserves the ICU 51 US-locale `StringSearch`
construction, primary collator strength, and boundary helpers **[OBS, DB, DEC]**.

The cross-property fixture assigns each of ten controlled strings to nine
lookup relations and four direct content fields. All 104 rule/property pairs
return identical sets by rule. In database terms, an existing lookup row with
an empty name is indistinguishable from a direct empty string, and a zero
lookup relation is indistinguishable from a direct SQL `NULL` for these
operators. Both empty forms match equality against an empty rule, both are
excluded by empty inequality, both enter nonempty inequality, and neither
enters nonempty not-contains **[OBS, DB]**.

The exported track wrapper reaches `getRowset_Playlist`; the lower-level
`dsqlGetPlaylistTrack` helper directly materializes table key 9 by playlist ID
and sorts column 2. The live contradiction result shows that the complete
serving path adds Attribute/SmartList semantics beyond treating that helper as
the final query. `playlist-queries.disasm.txt` and
`smart-playlist-paths.disasm.txt` preserve both sides of that boundary.
`smart-condition-evaluator.disasm.txt` preserves the parser, relative-unit
dispatch, date conversions, and comparison helpers **[DEC]**.
`smart-date-conversion.disasm.txt` isolates the complete `dateToDay`,
`pastMonthToDay`, and `pastDayToDay` bodies **[DEC]**.
`smart-collation.disasm.txt` isolates `CollationRule` construction, equality,
contains, prefix, and suffix helpers **[DEC]**.

The populated rule result is consumed by the same downstream track table
machinery used elsewhere. `getRowset_Playlist` reaches `SetTrackSort`, names
`djmdTrackSort`, and calls `Sort_SortTrackTable`; the live serving cross binds
that static path to exact orders for all 18 sort IDs. Render-time secondary
selection, pagination normalization, packed-context validation, and setup row
widths also operate on the evaluated result without changing its membership.
Search requests do not contain a playlist foreign key and cannot express a
SmartList-scoped database query **[OBS, DB, DEC]**.

The rule parser ignores nested `NODE` groups and evaluates only direct
`CONDITION` children. It uses the first root when the XML contains two.
Missing or unknown root `LogicalOperator` values behave
as all-of, while empty all/any groups, unknown single conditions, and
conditions outside the selected root yield no rows. `Id` and
`AutomaticUpdate` do not alter Link Export results. Operator applicability is
property-sensitive: text accepts codes 1, 2, and 8-11 in the measured Genre
matrix, while 3-7 return empty. BPM conditions compare XML numerics directly
with `djmdContent.BPM`'s stored integer scale **[OBS, DB]**.

`db::getSmartlistContentData` parses the `SmartList` string with JUCE and hands
the first document element to `db::getSmartlistNode`. That function validates
`NODE` case-insensitively, reads the case-sensitive `LogicalOperator`
attribute, walks the element's direct-child linked list, and invokes
`getSmartlistCondition` only for `CONDITION` children. The 73-case XML oracle
binds malformed documents, namespaces, duplicate/missing attributes, entities,
case, leading/trailing data, and integer coercion to exact result sets
**[OBS, DB, DEC]**.

Across `BPM`, `Rating`, `DJPlayCount`, `Length`, and `ReleaseYear`, numeric
codes 3 and 4 are exclusive and code 5 is inclusive. The range evaluator does
not reorder endpoints. Empty or nonnumeric XML values become zero for equality
and inequality; controlled zero rows in Rating, Play Count, and Year prove the
conversion directly. Fractional rule text truncates to zero, missing numeric
attributes become zero, and positive rule values at or above `INT32_MAX`
saturate to `INT32_MAX`. SQL null, REAL, negative, and wide-integer content
cells then pass through property-specific conversions: BPM, Rating, and the
shared Play Count/Length/Year group have three distinct observed partitions.
The exact sets are recorded in `SMART_PLAYLIST_ORACLE.md` and the 100-case
machine summary **[OBS, DB]**.

### Link History

The getters name `djmdHistory` and `djmdSongHistory`, but create, append,
remove, and delete symbols show that Link history is mutable session state. The
empty live root despite ordinary historical records demonstrates that a query
over every persisted history row is not equivalent to the served menu.

The live lifecycle uses `3001` to create/append the date-named current history,
`1012` to enumerate it, `1112` to return insertion-ordered tracks, `3401` to
remove a content ID and close the remaining ordinal gap, and `3101` to delete
the returned history ID. The sequence is exact within one process and repeats
after a clean fixture/process reset. Cross-day rollover, restart persistence
without deletion, and simultaneous multi-player partitioning remain separate
experiments.

### Hot Cue Bank

Request `2001 [context, selector, mode, count]` reaches
`PSvDBMain::OnCueBnkCmd`, which dispatches through the active database
interface. The observed local-library behavior matches
`PSvAppSyncDBIF::getHCBnkList`. Mode 1 reads immediate live children from
`djmdHotCueBanklist`; Attribute selects folder (`01`) versus bank (`2b`) and
Seq determines mixed row order. Mode 0 reads `djmdSongHotCueBanklist` for one
HotCueBanklistID in signed TrackNo order, takes at most `max(count, 3)` rows, and
resolves each through the ordinary live-content getter **[OBS, DB, DEC]**.

The AppSync routine runs one joined SQL query before iterating its result. It
computes unsigned `max(count, 3)` but compares the signed 32-bit loop index to
the stored limit with `jge`. Counts 17 through `INT32_MAX` return the same ten
resolvable rows; 255/256 and 65535/65536 prove there is no 8- or 16-bit
narrowing. Counts `0x80000000` and `0xffffffff` stop before row zero and return
normal empty menus **[OBS, DEC]**.

`PSvDBMain::GetHCBnkList`, reached through the separate master-database
interface wrapper, uses three `count * 4` candidate arrays and a legacy query.
That alternative is statically established but is not the implementation
matching these local AppSync oracle results **[DEC]**.

Duplicate memberships remain distinct. A locally deleted membership remains
visible, so the membership flag is not a serving predicate. Soft-deleted and
dangling content disappears during content resolution. Stored TrackNo -1 sorts
before 0 and becomes wire argument 9 value 65535. `hotCueBanklistCue` belongs
to the adjacent cue-information/change path, not the catalog row set. The exact
fixture and 31-case proof are in `HOT_CUE_BANK_ORACLE.md`.

A dedicated deleted-bank fixture separates node liveness from membership
liveness. The parent-folder query excludes soft-deleted bank 9031, but direct
bank-ID requests still serve its live membership: catalog `2001` returns track
10005, legacy `2101` returns one cue record, and extended `2301` returns one
new-format record. The direct paths do not resolve or validate the owning
`djmdHotCueBanklist` row before querying `djmdSongHotCueBanklist`; bank deletion
only controls tree enumeration **[DB, DEC, OBS]**.

The adjacent `2101 [context, bank_id]` path looks up membership `TrackNo` 1,
2, and 3. The static master-database implementation follows `CueID` into
`djmdCue`; the active Windows AppSync implementation reads the timing and MPEG
columns directly from `djmdSongHotCueBanklist`. A paired fixture with
conflicting cue rows proves the live oracle uses the AppSync path. Real
Rekordbox returns `4702` with one 36-byte cue record and one 8-byte timing
extension for each resolved slot. Alpha Bank returns three records, Root Bank
returns two, and empty or invalid selectors return a valid empty `4702`.
Setup/status/model/framing variants have identical decoded payloads **[DB,
DEC, OBS]**.

Extended request `2301 [context, bank_id, slot_count]` uses the active AppSync
query below once for each `TrackNo` from 1 through the requested count:

```sql
select * from djmdSongHotCueBanklist
where rb_local_deleted = 0
  and HotCueBanklistID = %lu
  and TrackNo = %d
```

The resulting `4e02` records copy membership millisecond/MPEG timing, Color,
Comment, BeatLoopSize, CueMicrosec, and conditionally parsed seek information.
`ColorTableIndex` is read into the option object but is not emitted by the
observed serializer. The master-database alternative resolves membership
`CueID` into `djmdCue` and cue-option tables; it is not the active Windows path
**[DB, DEC, OBS]**.

Extended setter `2401` first resolves the mutation target through
`HCBnkSong_GetCueID` using the same SQL. The AppSync implementation has a
literal cardinality anomaly: `size() == 1` returns failure, while other sizes
continue to row zero. Live single-row fixtures therefore returned status 50;
two active rows with the same bank and slot allowed the mutation to proceed.
The resolver returns row-zero `CueID` and `ContentID`, then
`setHCBnkCuePointExt` updates `djmdSongHotCueBanklist` by the resolved CueID.
The deterministic fixture uses `CueID == membership.ID`, making membership
94001 the target **[DB, DEC, OBS]**.

The setter admits slot values 1 through 8 through the unsigned 16-bit predicate
at `0x1016d3fbd..0x1016d3fc9`. Bank 9060 has no `TrackNo=8` row, so slot 8
produces an empty result and reaches the resolver's row-zero access rather than
its exact-one rejection. Three cold-process observations produced setter and
immediate-getter timeouts with a responsive process, clean Application log,
and pristine logical database. The same getter returned the identical
status-zero 124-byte baseline record after restarting Rekordbox against that
database in all three runs. The empty-row access is the recovered mechanism
consistent with the serving stall; assigning it as the exact blocking cause
remains an inference rather than a dynamically traced proof **[DB, DEC, OBS]**.

The successful live WAL changes membership columns `InMsec`, `InFrame`,
`InMpegFrame`, `InMpegAbs`, `OutMsec`, `OutFrame`, `OutMpegFrame`,
`OutMpegAbs`, `Color`, `BeatLoopSize`, `CueMicrosec`, `rb_local_usn`, and
`updated_at`. It leaves the second same-slot membership and both `djmdCue` rows
unchanged. This proves that the active Windows setter writes the membership
table, matching the AppSync getter's source rather than the master-database
alternative **[DB, OBS]**.

After a successful setter resolves a nonzero CueID, the server's update helper
invokes the callback installed by `UiProDJLink` at database-server startup.
Callback class 3 maps directly to the in-process call
`DatabaseIF::notifyDBUpdated(0x1e, CueID, 0)`. This path performs application
database invalidation; it does not serialize or send a Link Export notification
to connected players **[DEC]**.

Static control flow makes the write set more precise. The setter issues up to
three ordered `SongHotCueBanklist.updateById` calls for the resolved CueID. The
fixed call carries ContentID, all eight millisecond/frame/MPEG timing columns,
and `Color=-1`. If option parsing produced a complete option object and that
call succeeded, a second call carries Color, ColorTableIndex, Comment,
BeatLoopSize, and CueMicrosec. If a complete seek descriptor is also present,
a third call carries InPointSeekInfo and OutPointSeekInfo. Each later call is
skipped after an earlier failure. The observed canonical WAL shows the final
fixed and option values; unchanged ContentID and unavailable seek strings do
not create visible value deltas in that capture **[DEC, DB]**.

Seek admission has a narrower safety boundary than the three update phases
suggest. After the comment, the setter requires only eight available bytes,
reads a 32-bit descriptor length, caps that value at 44, and copies the capped
count into its local option object. It does not compare the capped count with
the bytes remaining in the request. The completed 17-case health matrix crosses
both the eight-byte admission edge and the 44-byte copy edge while preserving
process and WAL state. Fourteen variants return the canonical status-zero
record; actual length 82 and both nonzero inbound-validity controls commit seek
strings before the reply path times out and a replacement process overlaps the
faulting process **[DEC, OBS, DB]**.

When inbound validity is nonzero, the third update formats and stores a
nonempty `InPointSeekInfo`. The canonical reply path then calls the AppSync
getter, whose advancing decimal parsers leave an interior cursor in the local
pointer slot; the getter passes that cursor to `djrfree`. This invalid free is
the precise cause of the observed process exit for a nonempty inbound seek
string. Outbound-only text is gated off by zero inbound validity **[DEC, OBS]**.

Legacy change request `2201` reaches the same resolver with the cue record's
D/E/F ordinal. The AppSync implementation uses ordinal 4 directly for D, while
the master implementation subtracts three. The live fixture therefore supplies
two active bank-9060 rows at `TrackNo=4`; a duplicate `TrackNo=1` control cannot
resolve and times out. After resolving row zero, `setHCBnkCuePoint` updates the
membership from the fixed cue record and extension. Its successful live WAL
maps the sentinel values to frame/MPEG fields and `InMsec`, sets `OutMsec` to
`0xffffffff`, and leaves the second membership and both `djmdCue` rows unchanged.
The handler then calls `GetUsbCue` with the request record's ContentID, so the
`4702` response contains the track's `djmdCue` rows instead of the updated bank
membership **[DB, DEC, OBS]**.

The repeat-verified ordinal matrix supplies duplicate rows for all three wire
ordinals. Requests 4, 5, and 6 update the row-zero memberships at `TrackNo` 4,
5, and 6 respectively. One live WAL contains all three changes with sequential
local USNs, while each row-one duplicate and all corresponding `djmdCue` rows
remain unchanged. The three responses independently contain the `djmdCue` rows
selected by request ContentIDs 10001, 10002, and 10003 **[DB, OBS]**.

The request handler gates the legacy setter before this query. Its unsigned
flag-word comparison admits `0x00040000..0x0006ffff`; with the observed low
word `0x0100`, only ordinals 4, 5, and 6 reach `setHCBnkCuePoint`. Controlled
requests for ordinals 0, 1, 2, 3, 7, 8, 255, 256, 32767, 32768, and 65535
still continue to `GetUsbCue` and return status-zero `4702` responses selected
by ContentID. A live WAL view retains all 22 paired membership rows and all 22
cue rows byte-for-field at their fixture values. Those responses acknowledge a
no-op; they do not prove a database update **[DEC, DB, OBS]**.

### Prepare

`Dsql_GetPrepareList` reads `djmdSongTagList`, orders memberships by
`TrackNo`, resolves each referenced `djmdContent` row, and then applies the
requested `djmdTrackSort` ordering where appropriate **[DEC]**.
`DsqlContent_GetPrepareList` is the content-facing wrapper. Prepare is therefore
a persisted ordered membership list rather than a file-system or media-file
query. The fixture deliberately inserts two members in the opposite order from
their content IDs so the oracle can distinguish membership order from default
content order.

The populated oracle returned membership `TrackNo` 1 (content 10002) before
`TrackNo` 2 (content 10001) for sort 0. Requesting Key sort returned content
10001 before 10002 instead, while retaining membership positions 2 and 1 in
row argument 9. This confirms that membership defines the candidate set and
default order, while an explicit content sort can reorder it **[OBS]**.

### My Tag

`Dsql_GetMyTag(RbDBIndex, int, uint, bool)` reads the My Tag hierarchy and
membership view selected by its integer/tag selector and boolean mode.
`Dsql_GetMyTagOnTrack` resolves the tags assigned to one content ID through
`djmdSongMyTag` **[DEC]**. The latter returns tag rows for a track; it is not the
inverse query for tracks under a tag. The deterministic full fixture contains
two groups, overlapping Warm Up/Vocal assignments, and an empty leaf so both
cardinality and empty-state behavior are observable.

The oracle returned both groups for selector 0/mode 0 and one Warmup leaf for
the concrete genre group. Selector 0 or a concrete group with mode 1 returned
the `ffffffff` unavailable count, as did using a leaf as the hierarchy
selector. `Dsql_GetMyTagOnTrack` returned group+leaf pairs for each assignment:
four rows for the doubly tagged first track, two for the singly tagged second
track, and zero for both an untagged live track and an unknown content ID
**[OBS]**.

When the generated empty database contained no `djmdMyTag` rows, rekordbox
persisted a factory tree of four groups and 24 leaves during startup. The empty
root query exposed the four groups even though `djmdContent` remained empty.
The deterministic empty baseline now carries those exact 28 rows. A stopped
post-start comparison found no changes in any Link Export table; only
`agentRegistry` platform paths, timestamps, and opaque agent credentials were
rewritten for Windows **[DB, OBS]**.

SmartList `myTag` conditions operate on the same `djmdSongMyTag` membership
loaded into each track row. The evaluator property type is `0x40`; operators
8 and 9 scan the track's tag-ID array for membership and its complement.
`ValueLeft` is parsed as a signed JUCE integer and compared as the resulting
32-bit bit pattern. Consequently `-1` addresses tag ID `4294967295`,
`-2147483648` addresses `2147483648`, and raw positive values above
`INT32_MAX` saturate to `2147483647`. Blank text yields no match for either
operator, while malformed nonblank text becomes zero. `ValueRight` and
`ValueUnit` are ignored. The 49-case ordered-set oracle and decompiled offsets
are bound in `data/experiments/smart-mytag-matrix/summary.json`
**[OBS, DB, DEC]**.

### Date Added

The Date Added family extracts year, month, and day from
`djmdContent.StockDate`. The executable has distinct getter branches for
`1708` years, `1808` months within a year, `1908` days within a year/month, and
`1a08` tracks within a year/month/day. A `-1` selector takes explicit wildcard
paths at the lower levels **[DEC]**.

The populated oracle confirmed five year rows descending, concrete month/day
rows with the same numeric selector type `0x2e`, and `0xa0` ALL rows where a
level has multiple descendants. Wildcard month at the day stage yielded only
ALL; wildcard day at the track stage selected the concrete February track
**[OBS]**.
With zero tracks the year and track stages were empty, while requested month
and day stages each synthesized one `0xa0` ALL row **[OBS]**.

## Search

`djeplGetNewSearchResult` selects multiple domains and applies
`dsqlIsLinkExportVisibleTrack` to content results. The observed result mixes
entity headings and tracks. Search input is UTF-16BE, split on spaces,
NUL-terminated, and length-counted including the terminator. Rekordbox folds
ASCII lowercase to uppercase, requires every token as an order-independent
substring, does not normalize precomposed and decomposed BMP text, and does not
expand non-ASCII case pairs. Supplementary-plane queries produce no matches,
and the first embedded NUL terminates the effective query **[OBS, DEC]**.

Four enabled `djmdCategory.MenuItemID` values independently gate the query:
Artist 2 selects `djmdArtist.Name`, Album 3 selects `djmdAlbum.Name`, Track 4
selects `djmdContent.Title`, and File Name 16 selects
`djmdContent.FileNameL`. Four category-disable fixtures prove each removal on
the wire. Content matches pass `dsqlIsLinkExportVisibleTrack` and are
deduplicated by ID. The wrapper caps insertion at 1,000 rows **[OBS, DB, DEC]**.
Search Track `0x1500` reaches the same virtual search interface with a
four-argument request and the new-command content path. Default sort 0 uses a
5,000-row insertion budget. Explicit sorts 1-17 return every eligible row in
the 10,005-track cache-independent title fixture. A SearchStr-only fixture
returns zero for ordinary Search and Search Track, while the equivalent title
fixture returns all eligible rows; `djmdContent.SearchStr` is therefore not a
direct query domain on this path **[OBS, DB, DEC]**.
`SEARCH_ORACLE.md` gives the exact queries, results, length boundary,
pagination, static control flow, and rbxport differences.

## Row rendering queries

After a track row is selected, `GetListBufRowContent` performs additional
lookups that are not category membership queries:

- Full `djmdContent` row by content ID.
- Selected secondary sort ID from `djmdSort.Disable` bit 1.
- Content compatibility: the active Windows AppSync branch queries `FileType`
  and `SampleRate` inline; its Master-interface branch calls the standalone
  predicate at `0x14227e200`; both macOS slices call
  `DsqlContent_GetNewCDJSupported(contentID)`.
- `HotCueAutoLoad` from content.
- Old/new key conversion through `djmdKey.ScaleName`.
- Tag-list membership through `djmdSongTagList`.
- Lookup text for the selected secondary column.

This division matters because membership, content compatibility, packed track
type, and setup width are independent. The recovered compatibility low bit
depends only on content metadata and is identical across the eight sampled
client identities. Packed track type separately controls `HotCueAutoLoad` bit `0x100`,
while setup selects 12- versus 16-argument serialization without changing
either predicate. The exact materialized-column-to-wire mapping and both flag
words are specified in `ROW_LAYOUT.md` **[OBS, DEC]**.
