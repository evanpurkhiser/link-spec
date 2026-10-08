# rekordbox Link Export navigation and configuration

Status: active research. Evidence labels are defined in `README.md`. The
physical XDJ-RX3 is deliberately outside the current experiment boundary;
future live tests must use a synthetic player on an isolated broadcast domain.

## What Link Export exposes

Link Export is a player-facing view of the rekordbox library, not a copy of the
desktop application's collection browser. A player discovers rekordbox over
PRO DJ LINK, establishes a remote database session, requests a root menu, and
navigates server-rendered menus. The player owns screen transitions and Back;
rekordbox answers each selected node with a new logical menu.

The two small controls at the lower left of rekordbox 7.2.19's Export UI are
Mobile Library Sync and "Connect to a mobile device". They are not Link Export
controls **[OBS]**. With no player present, the tested VM showed no LINK source,
did not listen on TCP 12523, and emitted no PDJL traffic **[OBS]**. This is a
useful negative baseline, not evidence that Link Export is unavailable.

## Session and render model

A remote database menu is a two-stage transaction **[DYS, CAP]**:

1. A request such as `1000`, `1004`, or `1105` selects a logical menu. The
   server returns `4000 [original request kind, count]`.
2. One or more `3000` render requests select an offset and count. The reply is
   `4001` (header), zero or more `4101` rows, then `4201` (footer).

The first request argument packs requester number, menu location, source slot,
and track type. Dysentery identifies menu locations 1 (main), 2 (overlay), 3
(metadata preview), and 8 (graphics) **[DYS]**. The decompiled XDJ-RR client
has direct named call sites at every literal location `1..8`: location 4 serves
loaded/playing views, 5 sort and one-track information, 6 Prepare/Tag List, and
7 category reload/information-jump/cue-bank drag/drop paths. Its Delivery Info
wrapper fixes location 9, although no direct XDJ-RR caller survives in the
decompilation. `XDJ_RR_CLIENT_NAVIGATION.md` contains the hash-pinned 304-call-
site inventory and separates client reachability from Rekordbox support
**[RR-DEC]**. A row carries parent/main IDs,
primary and secondary labels, composite item type, flags, auxiliary IDs,
playlist position, and additional numeric fields whose meaning varies by row kind
**[DYS, CAP]**. See `PROTOCOL_REFERENCE.md` for argument layouts, byte-level
examples, item-type inventory, and the complete request-family crosswalk.

`PHYSICAL_RX3_SESSION.md` gives the complete ordered transcript of the retained
physical XDJ-RX3 session. Its machine-readable companion preserves all 106
client messages, 268 captured server messages, 144 menu rows, four packed
contexts, and hashes for every binary payload. It establishes the native RX3
request cadence while keeping its unknown Rekordbox server version separate
from controlled 7.2.19 oracle evidence **[CAP]**.

For ordinary Track `0x1004`, the final byte has been exhausted over all 256
values on a fixed requester/location/slot context. Values `0x03` and `0x04`
time out before a header; the other 254 return the same eight-row membership.
Dysentery names `0x00` no track, `0x01` rekordbox track, `0x02` unanalyzed,
`0x05` audio CD, and `0x06` streaming. Only `0x01` enables rekordbox's
row-renderer cache/`HotCueAutoLoad` enrichment and therefore preserves
argument-10 bit `0x100`. `PACKED_CONTEXT_ORACLE.md` contains the full matrix,
static explanation, and fingerprints **[OBS, DEC, DYS]**.

A 329-case cross over every canonical list request shows this is a request-class
rule, not a Track-only quirk. `PSvDBMain::OnClientReq` diverts `0x03` and
`0x04` before all `0x1xxx` list dispatch. Root and Search populate only for
type `0x01`, while direct category and hierarchy leaves remain available for
the other successful types. Seven hierarchy/playlist track leaves encode
`TT << 24` in row argument 7. The `0x2xxx` Song Info and Hot Cue Bank families
bypass that gate but still accept only type `0x01` as a normal local-library
track context. Exact per-family outcomes are in `PACKED_CONTEXT_ORACLE.md`
**[OBS, DEC]**.

## Captured root tree

The normalized baseline is `data/source-menu-tree.json` (source SHA-256 in
`data/summary.json`). It contains 90 menus, 41 request signatures, and 43 item
types. The traversal was intentionally bounded to two branch rows, depth four,
64 rendered rows per menu, and 120 menus; it did not hit the menu limit **[CAP]**.

The sampled capture is complemented by
`data/static-analysis/link-export-navigation-graph.json`. That generated graph
joins all 47 database-path families and all 95 classified request kinds to
their menu stage, transition edges, database tables, response class, and
render behavior. It distinguishes the 20 configured root selections from
implemented direct routes, recursive Playlist and Hot Cue Bank navigation,
fixed Song Info lists, direct payloads and mutations, and recognized requests
with no serving builder. A request appears in exactly one family, and every
list-buffer family points explicitly to `3000`; byte-identical regeneration
and query-map equality are conformance-tested. Each request also carries every
distinct wire-type signature declared by the 5,730-case corpus, with numeric,
string, and blob arguments kept separate, declaration counts, origins, and
source examples. Each signature also retains per-position suite symbols,
literal cardinality, and bounded literal examples, including chained prior-row
selectors without assigning guessed meanings to literal-only positions. The
render inventory spans numeric argument counts 0 through 32 and isolates
string/blob substitution at each of the eight ordinary positions
**[OBS, DB, DEC]**.

`REQUEST_SHAPES.md` renders the same graph as a family-by-family reference.
It includes the menu stage, database tables, transition edges, response class,
and every declared argument-count/wire-type signature with declaration counts,
per-position declaration evidence, and source suite/case examples. The
document is generated and checked for byte-identical reproduction.

`OBSERVED_RESPONSE_SHAPES.md` is the corresponding response-side index over
canonical Rekordbox 7.2.19 goldens. It separates each selection or direct
request's immediate reply from its later `0x3000` page transactions, and lists
exact reply kinds, argument-count/type signatures, terminal outcomes, row item
types, source files, and per-request identity/model/status/setup coverage. Its
separate declaration-corpus snapshot lists exact case and suite-file counts for
every classified kind without a canonical response. This distinction prevents
asynchronous drain traffic or render rows from being attributed to the next
menu-selection request and prevents declared coverage from being described as
observed behavior **[OBS]**.

`DATABASE_FIELD_REFERENCE.md` provides the inverse database lookup for this
graph. Its 95-row request-kind index maps each request below to its family,
operation, table set, and the fields named by that family's reconstructed
predicate, ordering, or result description. Those fields are deliberately
marked as family-level evidence: a multi-stage hierarchy can name a field used
by only one stage. The machine-readable form is
`data/database/link-export-schema.json` **[DB, DEC]**.

| Order | Root row | Request | Baseline result | Next transition |
| ---: | --- | --- | ---: | --- |
| 1 | TRACK | `1004 [context, sort]` | 4,342 | track rows |
| 2 | KEY | `1014 [context, sort]` | 24 | key -> distance -> tracks |
| 3 | BPM | `1006 [context, sort]` | 84 | BPM -> tolerance 0-6 -> tracks |
| 4 | GENRE | `1001 [context, sort]` | 27 | genre -> artist -> album -> tracks |
| 5 | ARTIST | `1002 [context, sort]` | 2,203 | artist -> album -> tracks |
| 6 | ALBUM | `1003 [context, sort]` | 765 | album -> tracks |
| 7 | MATCHING | `1017 [context, sort, seed]` | 1 sampled | track rows |
| 8 | SEARCH | `1300 [...]` | 11 sampled | mixed artist/track results |
| 9 | PLAYLIST | `1105 [context, sort, id, folder]` | 8 root | recursive folder/list -> tracks |
| 10 | HISTORY | `1012 [context, sort]` | 0 | history session -> tracks |
| 11 | BITRATE | `1011 [context, sort]` | 12 | bitrate -> tracks |
| 12 | COLOR | `100d [context, sort]` | 8 | color -> tracks |
| 13 | FILE NAME | `1013 [context, sort]` | 4,342 | filename-labelled tracks |
| 14 | HOT CUE BANK | `2001 [context, selector, mode, count]` | populated and repeated | recursive folders/banks; leaf -> ordered tracks |
| 15 | LABEL | `100a [context, sort]` | 353 | label -> artist -> album -> tracks |
| 16 | ORIGINAL ARTIST | `1302 [context, sort]` | 0 | artist hierarchy, unpopulated |
| 17 | RATING | `1007 [context, sort]` | 2 | rating -> tracks |
| 18 | REMIXER | `1602 [context, sort]` | 540 | remixer -> album -> tracks |
| 19 | TIME | `1010 [context, sort]` | 12 | minute bucket -> tracks |
| 20 | YEAR | `1008 [context, sort]` | 5 | decade -> year -> tracks |

The recorded tree confirms every transition above except the explicitly empty
or unavailable categories **[CAP]**. `data/menu-nodes.csv` is the flattened
node inventory; `data/request-signatures.csv` preserves argument shapes and
sample values; `data/item-types.csv` inventories rendered row types in that
bounded capture. `ITEM_TYPE_REFERENCE.md` supplies the corpus-wide 85-type
catalog and retains every producing request and source golden in
`data/item-type-reference.json`.

Rating, Bitrate, and Color have a repeat-verified selector cross independent of
their roots. All ratings 0-5, all eight fixture bitrates, and all colors 1-8
reach the expected track rows. Root membership is not a complete statement of
direct navigation: rating 99 is hidden from the root but directly selectable;
color 0 is hidden yet directly selects unassigned tracks; bitrate `INT32_MAX`
and dangling color `999999` are hidden and also yield empty direct menus.
`data/experiments/scalar-selectors/summary.json` pins the exact golden hashes
and rbxport comparison **[OBS, DB]**.

Playlist root rows do not distinguish ordinary and intelligent playlists on
the wire: both use type `08`, with argument 9 carrying `Seq`. Opening an ID
with `folder_flag = 0` applies `djmdPlaylist.Attribute`: Attribute 0 uses
`djmdSongPlaylist`, while Attribute 4 evaluates `SmartList`. A valid rule with
no memberships and a valid rule with deliberately contradictory memberships
both return the rule-selected tracks. Malformed and absent rules return empty
even when membership rows exist. `folder_flag = 1` requests children and
returns empty for all five leaf controls. The twelve-case oracle and hashes are
in `data/experiments/smart-playlists/summary.json` **[OBS, DB]**.

Opening the Attribute 4 leaves in the Smart matrices proves the track-list
path includes a rule evaluator. Root all/any groups return exact ordered
subsets; nested `NODE` elements are ignored and only direct `CONDITION`
children contribute. Empty groups and invalid single
conditions return normal zero-row menus. Parser metadata does not create a
different navigation row or request shape. The complete per-operator table,
including the 49-case My Tag signed-boundary matrix and 73-case XML parser
matrix, is in
`SMART_PLAYLIST_ORACLE.md`
**[OBS, DB]**.

Once evaluated, a SmartList leaf follows the ordinary track presentation
pipeline. The rule-only all-eight control has repeat-verified cases for sort
IDs 0-17, every render secondary selector, pagination edges, requester,
location, and slot contexts, and both 16- and 12-field setup widths. Search remains a
separate global branch because neither Search request kind carries a playlist
selector **[OBS, DB]**.

The File Name root retains `FileNameL` as primary text for every requested sort
ID 0-17. The dedicated 20-row fixture produces nine exact ordering classes and
proves literal extension/dot/separator handling, NUL truncation, null/empty
normalization, and a 255-UTF-16-unit output cap. The canonical summary and
golden hashes are in `data/experiments/filename/summary.json` **[OBS, DB]**.

## Navigation beyond the original capture

The 7.2.19 list dispatchers add branches that the bounded RX3 traversal did not
visit. The populated oracle has now recorded the listed Play Count, Prepare,
Date Added, and My Tag paths; New Key was already part of `full.json`
**[DEC, OBS]**:

| Navigation | Request sequence | Database scope |
| --- | --- | --- |
| DJ Play Count | `100e` count -> `110e` tracks | `djmdContent.DJPlayCount` |
| Prepare | `100f` tracks | ordered `djmdSongTagList` membership |
| New Key | `1014` key -> `1114` distance -> `1214` tracks | key and distance predicates |
| Date Added | `1708` year -> `1808` month -> `1908` day -> `1a08` tracks | `djmdContent.StockDate` |
| My Tag browse | `1015` with selector and mode | `djmdMyTag` hierarchy and `djmdSongMyTag` membership |
| My Tags on track | `1315` with content ID | tag rows assigned to that content |

The 21 populated cases are retained in
`conformance/goldens/rekordbox-7.2.19/xdj-rx3/extended-families-full.json`.
They establish selector types, wildcard rows, errors, Prepare ordering, and My
Tag group/leaf shapes. The nine empty-state cases are also recorded:
zero-track roots remain valid
menus, Date Added month/day synthesize ALL, and My Tag exposes the four factory
groups.

## Per-track song-information menus

The song-information dispatcher is adjacent to ordinary browse navigation but
creates a fixed metadata menu for one content ID:

| Request | Result for content `10001` | Missing-content result |
| ---: | --- | --- |
| `2002` | 16-row Display Song Info | zero-row menu |
| `2102` | 7-row Play Song Info | zero-row menu |
| `2202`-`2502` | kind-specific `4003` | same kind-specific `4003` |
| `2602` | 13-row Delivery Info | zero-row menu |

Each successful builder first returns `4000 [request_kind, total]`. The client
then uses ordinary `3000` paging and receives `4001`, fixed heterogeneous
`4101` rows, and `4201`. Delivery applies the requested secondary selector to
its composite Title row; Play ignores it. All three builders use the same
clamp/reset/timeout pagination family. `DISPLAY_SONG_INFO_ORACLE.md` and
`SONG_INFO_SIBLINGS_ORACLE.md` give complete rows and navigation edge behavior
**[OBS, DEC]**.

## Track lists and the secondary column

RX3-style one-argument setup still receives 12-argument menu rows while keeping
the full composite item type and argument 5 **[CAP]**. In the captured library,
track rows use item type `0x0f04`; high byte `0x0f` means Key and low byte `0x04`
means Title. The visible secondary text is, for example,
`3A - 112.2 bpm`. Rekordbox therefore does not reduce legacy rows to a generic
title-only type.

Static and real-Rekordbox evidence identify secondary-column types for Album, Genre,
Artist, Rating, Duration, BPM, Label, Key, Bitrate, Color, Comment, Original
Artist, Remixer, DJ Play Count, and Date Added **[OBS, DEC, RBX]**. The desktop
Column preference persists selection as `djmdSort.Disable` bit 1. All fifteen
choices plus absent and multiple-selection states are repeat-verified in
`SECONDARY_COLUMN_ORACLE.md`.

Track sorting is a separate presentation input. A real-Rekordbox cross over
the 11 visible RX3 sorts sends the same six-argument render after every
`0x1004` request:

```text
3000 [context, offset, count, 0, total, 12]
```

Default materializes the persisted Column selection. Alphabet materializes
Title, and Artist, Album, BPM, Rating, Genre, Label, Key, Date Added, and DJ
Play Count each materialize their own right-column role. The final value `12`
does not select Key in this request shape. Active Key and BPM preserve cached
`Key - BPM` and `BPM - Key` text respectively; single-value sorts contain only
their own value. An eight-argument render instead enables selector
reconciliation: a matching selector preserves the cached composite, while a
mismatched selector invokes the dynamic extractor. The complete 88-row golden,
physical RX3 Default request evidence, exact fields 0/5/6/12-15, and request-
shape boundary are in `SECONDARY_COLUMN_ORACLE.md` **[OBS]**.

## Search

Search uses `1300 [context, sort, byte_length, text, trailing]`. Text is
UTF-16BE and NUL-terminated; the declared length includes the terminator.
Rekordbox tokenizes on spaces, folds ASCII case, requires every token as a
substring, and mixes Artist, Album, title-track, and file-name-track rows.
Those four domains are independently controlled by the corresponding Category
settings. Exact length rejection, Unicode, sort/trailing controls, and Search
pagination are repeat-verified in `SEARCH_ORACLE.md`. A 1,005-track fixture
proves the live result cap is 1,000 and records complete capped ordering plus
at-end, past-end, zero-count, and overrun rendering. A focused text fixture
records precomposed/decomposed BMP behavior, non-ASCII case pairs,
supplementary symbols, UTF-16 length accounting, and first-NUL termination
**[OBS, DB, DEC]**.

Search Track uses `1500 [context, sort, byte_length, text]`. All sort IDs 0-17
are accepted, with eight exact order classes on the text fixture. Sort is read
as a signed low byte: 256 aliases 0, while 127/128/255 return unavailable.
Default sort truncates at 5,000 and uses the same right-aligned pagination;
each explicit sort 1-17 returns all 10,005 matches in a cache-independent
title fixture. The physical RX3 was excluded from the isolated network, so the
client-side touchscreen route that emits this command remains outside this
server navigation tree **[OBS, DB, DEC]**.

## Configurable categories and sorts

`djmdCategory` stores `MenuItemID`, `Seq`, `Disable`, and `InfoOrder`;
`djmdSort` stores `MenuItemID`, `Seq`, and `Disable` **[DB]**. Root construction
applies menu-item capability bits plus special `Disable` handling for Matching
and Date Added, orders by `Seq`, and suppresses Folder **[DEC]**. Sort visibility
uses `Disable` bit 0; selected secondary-column state uses bit 1 **[DEC, DB]**.
`CONFIGURATION.md` gives the exact predicates and current rows.

Symbols expose read/write paths through `getCategorySetting`, `getSortSetting`,
`selectRawCategorySetting`, `selectRawSortSetting`, `updateAllCategory`, and
`setAllSort` **[DEC]**.

This establishes that visibility and order are data-driven. The UI locks
Category, Sort, and Column while Link is active. Changes made while Link is
inactive are consumed by the next Link session in the same Rekordbox process:
Album category removal, Comments sort activation, and Key-to-Comments Column
selection were each recorded and immediately repeated. The first two captures
share one process and retain their encrypted database/WAL state.
`SETTINGS_SESSION_REFRESH_ORACLE.md` records the exact lifecycle and evidence.

## Desktop UI observations

The VM reached Export mode with its copied collection and showed 4,356 tracks
in the UI **[OBS]**. A machine audit of both the source database and its
relocated copy finds exactly 4,342 `djmdContent` rows, all with
`rb_local_deleted = 0`, identical ordered ContentID hashes, and identical
ContentLink partitions **[DB]**. The relocation report accounts for the same
population as 4,274 mapped plus 68 unresolved paths. The September 28 Link
Export capture also served 4,342 rows **[CAP]**.

The extra 14 therefore belong to that initial desktop UI/session view rather
than the retained source or relocated database population. The guest database
and WAL from the screenshot moment were not retained, so cloud/account state,
another UI-only source, and a transient guest WAL cannot now be distinguished.
This is a bounded desktop-provenance gap, not uncertainty in the captured Link
Export total or the copied database's logical population. The machine receipt
is `data/experiments/source-library-count-audit.json`.

Reproduce the receipt without exposing the decrypted database key:

```sh
cd /home/evan/workspace/rx3-research/rekordbox-link-export-research
../rekordbox-windows/.venv/bin/python \
  tools/audit_source_library_counts.py \
  --options /mnt/documents/multimedia/djing/rekordbox/options.json \
  --source /mnt/documents/multimedia/djing/rekordbox/master.db \
  --relocated ../rekordbox-windows/shared/library/master.db \
  --relocation-report ../rekordbox-windows/shared/library/relocation-report.json \
  --output data/experiments/source-library-count-audit.json
```

Screenshots named `rekordbox-mobile-library-sync-popup.png` and
`rekordbox-connect-mobile-device-popup.png` document the lower-left controls.
`rekordbox-mobile-controls.pcap` contains only their connectivity checks; it is
not a Link Export activation capture **[OBS]**.

## Isolated live matrix

The private Windows/QEMU segment and synthetic client are operational. Every
live recording is gated on the physical-LAN VM being inactive and an isolation
check proving that no synthetic discovery packet can reach `lan0` or the
physical RX3. The direct RX3 location-2 precursor matrix is complete: all
valid/zero-context precursors preserve 13 Delivery rows, while blob content IDs
to Play or Delivery make the immediate next menu empty. Current navigation work
is the longer malformed-history extension, authenticated cloud sync modes,
and genuine non-RX3 status shapes. The database-controlled Play path/cloud/
file-presence matrix is complete. Reconnect and shared-socket
location-2 controls are exact; the wrong-typed Play context closes the shared
socket before its Delivery probe. The stable RX3/CDJ status cross
for both sibling builders is complete. The
completed cold-process family, TCP-lifetime, and discovery-identity matrices
are documented in
`SONG_INFO_SIBLINGS_ORACLE.md`. `CONFORMANCE.md` gives the reproducible commands
and `CLEANUP.md` tracks all retained and removable lab state.

Ordinary track-bearing navigation now also has a closed source-visibility
oracle. Collection, File Name, ordinary playlist, Smart playlist, and Search
apply the same fixed-provider `FolderPath` streaming predicate. Windows
AppSync persisted History returns the controlled streaming rows because its
vtable-resolved builder never reads `FolderPath`; the pinned macOS History
function instead filters both loops.
`LINK_EXPORT_VISIBILITY_ORACLE.md` records the exact fourteen-path matrix and
the production-shaped Beatport path control and account-conditioned
application-root behavior that remain open. Authentication is not an input to
the 7.2.19 Link Export path classifier, and Beatsource has no service instance
in this build.
