# Display Song Info oracle

Rekordbox 7.2.19 serves the metadata shown by a player's track-information
screen through request `0x2002`. This is a separate Link Export surface from
the category and track-list requests dispatched by `OnListClientCmd`. It uses
the ordinary menu header and renderer, but constructs a fixed list of metadata
fields for one content ID.

This chapter combines repeated isolated-oracle recordings, the deterministic
`full` fixture, a captured XDJ-RX3 player-status packet, and static inspection
of the pinned Rekordbox executable. Evidence labels follow `README.md`.

## Proven scope

The baseline identity corpus contains twelve non-AIO requests and one AIO
request. The category matrix adds 21 populated non-AIO requests, and the
dedicated render, pagination, malformed-input, legacy, and boundary suites add
71 more:

| Identity | Query player/context | Cases | Repeated | Result |
| --- | --- | ---: | --- | --- |
| CDJ-3000 status | 1 / `0x01010301` | populated, deleted, zero, unknown | Yes | Ordinary order |
| XDJ-RX3 status | 11 / `0x0b010301` | populated | Yes | AIO order |
| XDJ-RX3 keepalive | 1 / `0x01010301` | populated, deleted, zero, unknown | Yes | Ordinary order |
| XDJ-RX3 keepalive | 11 / `0x01010301` | populated, deleted, zero, unknown | Yes | Ordinary order; model cache was not populated |
| XDJ-RX3 keepalive, 21 category fixtures | 1 / `0x01010301` | populated per fixture | Yes | Fixed rows with category-enabled argument-0 flags |
| XDJ-RX3 keepalive, extended setup | 1 / `0x01010301` | 21 render controls, 9 page plans, 9 malformed requests | Yes | Exact render normalization and error behavior |
| XDJ-RX3 keepalive, legacy setup | 1 / `0x01010301` | populated, deleted, zero, unknown | Yes | Same 16 fields with 12-argument rows |
| XDJ-RX3 keepalive, boundary fixtures | 1 / `0x01010301` | 24 per-track boundary/Unicode/invalid cases plus 4 all-field string thresholds | Yes | Complete rows with three string limits and exact invalid-value serialization |
| XDJ-XZ/AZ/1000MK2, RX3 status shape | 11 / `0x0b010301` | populated, deleted, zero, unknown per model | Yes | All requests time out |
| Unknown model, RX3 status shape | 1 / `0x01010301` | populated, deleted, zero, unknown | Yes | Ordinary order and ordinary missing-ID behavior |

The original RX3/CDJ status-backed pair is the classification control. Both
packets use the same captured RX3 packet shape. The CDJ control changes the
advertised model, player number, keepalive class, and the two player-number
bytes in the status packet. The resulting Comment position follows the model
classification predicted by `isAIO` **[OBS, DEC]**.

A second matrix mutates that same RX3 status shape to XDJ-XZ, XDJ-AZ,
XDJ-1000MK2, and `UNKNOWN-FIXTURE`. The three XDJ variants time out for all
four content IDs, including IDs that normally produce a zero-row menu. The
unknown player-1 control returns an ordinary 16-row populated menu plus the
three ordinary zero-row missing-ID menus. These results establish a
status-shape/model-consistency boundary. They do not describe genuine status
packets emitted by those three XDJ products **[OBS]**.

The fixture database SHA-256 is
`e8c45a7020a70103d6a15d5cf9aaa32a3d8c758c6c1f3f33b2a8d80872f7c812` and
its semantic fingerprint is
`c7b0b834a1a1320faaa3526c4792f0d31430c617ea9b8b6008521c514b67853c`.

## Wire transaction

The request has exactly the shape observed below:

```text
2002 [context, content_id]
```

For fixture content `10001`, player 1 sent:

```text
2002 [01010301, 00002711]
```

Rekordbox replied with the ordinary menu header:

```text
4000 [00002002, 00000010]
```

The second value is the 16-row total. The client then rendered the list with
the same eight-argument request used elsewhere in the oracle:

```text
3000 [context, 0, 16, 0, 16, 12, 1, 0]
```

The response was `4001`, sixteen `4101` rows, and `4201`. Every metadata row
had 16 arguments under extended setup. The header echoes request kind `0x2002`;
there is no special response kind for this API **[OBS]**.

Deleted content, content ID zero, and unknown content ID `0xfffffffe` each
returned a valid `4000 [0x2002, 0]` menu with no render pages. The content query
therefore distinguishes absence from a protocol failure **[OBS]**.

## Render controls

Display Song Info uses the same `0x3000` request kind as other menus, but its
secondary-selector behavior differs from ordinary track-list rendering. Five-
and six-argument renders produce a title-only composite row. An eight-argument
render with gate zero does the same, even when its final selector is nonzero.
With gate one, selector zero reads the selected database column; selectors
2-17 override it **[OBS]**.

Only the first, composite Title row changes. The other 15 metadata rows remain
byte-identical. This table gives the observed Title arguments 0, 5, and 6:

| Render control | Selected value | Argument 0 | Argument 5 | Argument 6 |
| --- | --- | ---: | --- | ---: |
| 5 arguments | none | `1` | empty | `0x0004` |
| 6 arguments | none | `1` | empty | `0x0004` |
| gate `0`, selector `0` or `7` | none | `1` | empty | `0x0004` |
| gate `1`, selector `0` | database Key | `5001` | `Am` | `0x0f04` |
| selector `2` | Artist | `1001` | `Alpha Artist` | `0x0704` |
| selector `3` | Album | `2001` | `Album One` | `0x0204` |
| selector `4` | BPM | `12000` | empty | `0x0d04` |
| selector `5` | Rating | `0` | empty | `0x0a04` |
| selector `6` | Genre | `3001` | `Fixture House` | `0x0604` |
| selector `7` | Comment | `10001` | `comment-1` | `0x2304` |
| selector `8` | Time | `59` | empty | `0x0b04` |
| selector `9` | Remixer | `1003` | `Fixture Remixer` | `0x2904` |
| selector `10` | Label | `4001` | `Fixture Label One` | `0x0e04` |
| selector `11` | Original Artist | `1004` | `Fixture Original` | `0x2804` |
| selector `12` | Key | `5001` | `Am` | `0x0f04` |
| selector `13` | Bitrate | `0` | empty | `0x1004` |
| selector `14` | reserved hole | `0` | empty | `0x0004` |
| selector `15` | Color | `1` | `Pink` | `0x1404` |
| selector `16` | DJ Play Count | `0` | empty | `0x2a04` |
| selector `17` | Date Added | `10001` | `2021-02-02` | `0x2e04` |

The selector map agrees with `Get_SubCategoryValue`, including the reserved
selector-14 hole. Dynamic BPM and Key overrides contain only their direct
field presentation; they do not inherit the richer combined formatter strings
seen in persisted ordinary track-list rows **[OBS, DEC]**.

The table records the Classic local CDJ style. The two-state
`DEVSETTING.DAT` oracle repeats selectors 4 and 12 under Alphanumeric: every
Key-bearing `Am` becomes `8A`, including the standalone Key detail and tertiary
track-row Key, while selector-4 numeric BPM remains `12000`. The Windows active
formatter calls `exchangeKeyNameIfNeed`, and the wire result confirms that the
local device style reaches Display Song Info **[OBS, DEC]**.

## Pagination normalization

The response header always advertises total 16. Rekordbox applies the following
normalization to render offset and count **[OBS]**:

| Requested window | Returned window | Rows |
| --- | --- | ---: |
| offsets 0-15, count 1 | same offset | 1 |
| offset 0, count 16 | 0-15 | 16 |
| offset 0, count 0 | offset 0 | 1 |
| offset 16 or 17, count 1 | offset 15 | 1 |
| offset 15, count 18 | offset 0 | 16 |
| offsets 0/count 3 then 2/count 3 | requested overlapping windows | 6, including duplicate row 2 |
| offset `0xffffffff`, count 1 | no response | `render_timeout` |

The `0x4001` page header reports the normalized offset. Zero count therefore
returns `[1, 0]`, end and past-end return `[1, 15]`, and the overrun returns
`[1, 0]`. These are server behaviors rather than runner-side range slicing.

## Malformed requests

Each malformed case used a fresh TCP connection and disabled rendering. The
exact header behavior is **[OBS]**:

| Request arguments | Result |
| --- | --- |
| none | socket read timeout; no response |
| context only | `4000 [0x2002, 0]` |
| context, content, extra number | extra value ignored; `4000 [0x2002, 16]` |
| string or blob context | `0100 []` |
| string content ID | `4000 [0x2002, 0]` |
| blob content ID | `0100 []` |
| numeric zero context | `4000 [0x2002, 0]` |
| location-2 context `0x01020301` | accepted; `4000 [0x2002, 16]` |

The generic `0x0100` response has no arguments and does not carry a menu total.
The no-argument timeout was repeated immediately and remained stable.

## Legacy setup

Legacy setup returns the same 16 metadata fields and ordinary order as extended
setup, but every `0x4101` row has 12 arguments. Deleted, zero, and unknown
content IDs retain the same exact zero-row `4000` response. This establishes
that setup controls row width, not field membership, for this request **[OBS]**.

## Field boundaries

Seven deterministic encrypted profiles cover all eight boundary, Unicode, and
invalid tracks plus focused 254/255/256 ASCII and 256-UTF-16-unit supplementary
strings. All 28 cases return a complete 16-row menu and repeat exactly. Display
Song Info does not inherit the ordinary track renderer's 256-unit stall
**[OBS]**.

The string paths have three independently observed limits:

| Wire field | Limit | 256-unit supplementary result |
| --- | ---: | --- |
| Primary Title and simple Artist/Album/Key/Color/Genre/Label/Original Artist/Remixer strings | 127 UTF-16 code units | 63 complete supplementary characters plus U+FFFD; wire length 256 bytes including NUL |
| Composite Title-row secondary Key string | 127 Unicode characters | 127 complete supplementary characters; wire length 510 bytes including NUL |
| Comment and Date Added | 255 UTF-16 code units | 127 complete supplementary characters plus U+FFFD; wire length 512 bytes including NUL |

ASCII confirms the thresholds directly. Primary and simple lookup strings are
127 characters for 254-, 255-, and 256-character inputs. Comment and Date Added
preserve 254 and 255 characters, then truncate a 256-character input to 255.
The supplementary controls prove that the primary/simple and direct-string
limits count UTF-16 units and can split a surrogate pair. The decoded U+FFFD is
therefore observable wire evidence, not a documentation substitution **[OBS]**.

The invalid fixture establishes these value rules:

- null or empty Title and null Comment serialize as empty strings with wire
  length 2; the metadata list still contains all 16 rows;
- dangling Artist, Album, Key, Genre, Label, Original Artist, and Remixer IDs
  remain in argument 1 while their text is empty;
- a zero Album ID uses the same numeric-zero/empty-text form;
- negative Length, BPM, and Release Year serialize as unsigned
  `0xffffffff`;
- out-of-range Rating `99` is preserved;
- Color ID `999999` is preserved numerically, has empty text, and produces item
  type `0x52` from `0x13 + low_byte(ColorID)`;
- malformed Stock Date text is returned verbatim;
- Bitrate `2147483647`, zero file metadata, empty paths, and invalid file enums
  do not remove or truncate the 16-field list.

The retained fixture fingerprints are:

| Profile | Semantic fingerprint |
| --- | --- |
| `boundaries` | `076ebc495465e7d0e35274dad4a8c91c76ad67cd509ef0569d13105374b3116c` |
| `unicode-boundaries` | `82340bb91a66d4906a2aede9f429891f429948ed9d0d7e61191f14e0c45fcb8b` |
| `invalid` | `e7407607ca436169421b4ddc544a73c9a6cc35e3379063525c1240ca10f8cdc9` |
| `display-strings-254` | `6edc82c6832c93dcd1643f546c66dbd9195d70987d08456dc86b746dc576f747` |
| `display-strings-255` | `980535a753c13b9b42265906ca813e346fe6d950f9dd8a0443b7bb88901b85f8` |
| `display-strings-256` | `d17758bff931dc3504e7d29418d4de1e452603586a42966fa440c4b4e9a1b702` |
| `display-strings-unicode-256` | `fe1cc7222f319cdbd74555b5fe2953c1a67d24cd9efff5b8248cb4369420f542` |

## Field order

The ordinary CDJ order is:

| Position | Item type | Field |
| ---: | ---: | --- |
| 1 | `0x0f04` | Title, composite title/key track row |
| 2 | `0x0007` | Artist |
| 3 | `0x0002` | Album |
| 4 | `0x000b` | Length |
| 5 | `0x000d` | BPM |
| 6 | `0x000f` | Key |
| 7 | `0x000a` | Rating |
| 8 | `0x0014` | Color, Pink in this fixture |
| 9 | `0x0006` | Genre |
| 10 | `0x002e` | Stock Date / Date Added |
| 11 | `0x0023` | Comment |
| 12 | `0x0010` | Bitrate |
| 13 | `0x0011` | Release Year |
| 14 | `0x000e` | Label |
| 15 | `0x0028` | Original Artist |
| 16 | `0x0029` | Remixer |

An AIO identity moves Comment from position 11 to position 6. All other fields
retain their relative order:

```text
0f04 0007 0002 000b 000d 0023 000f 000a
0014 0006 002e 0010 0011 000e 0028 0029
```

The ordinary sequence is:

```text
0f04 0007 0002 000b 000d 000f 000a 0014
0006 002e 0023 0010 0011 000e 0028 0029
```

The suite asserts these complete sequences rather than checking only the
Comment position **[OBS]**.

The packed-context cross establishes how the identity is selected. With
genuine RX3 status at player 11, requester byte 11 takes the AIO sequence while
requester byte 1 takes the ordinary sequence. The RX3-template-derived
CDJ-3000 control at player 1 also takes the ordinary sequence. Across all three
identity/context cells,
only track type `0x01` returns rows; the other six known types return
`0xffffffff`. Extended and legacy setups preserve the same ordering, with
legacy rows equal to the first 12 extended arguments **[OBS, DEC]**.

## Exact row values

The first fixture track has content ID `10001`, title `Alpha One`, key ID
`5001`, and BPM `12000`. These are the complete 16-argument rows returned by
the CDJ-3000 control. Decimal values are used here to match the JSON golden.

| Field | Complete `4101` arguments |
| --- | --- |
| Title | `[5001, 10001, 20, "Alpha One", 6, "Am", 3844, 1, 10001, 0, 256, 15, 5001, 6, "Am", 12000]` |
| Artist | `[1, 1001, 26, "Alpha Artist", 2, "", 7, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Album | `[1, 2001, 20, "Album One", 2, "", 2, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Length | `[1, 59, 2, "", 2, "", 11, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| BPM | `[1, 12000, 2, "", 2, "", 13, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Key | `[1, 5001, 6, "Am", 2, "", 15, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Rating | `[1, 0, 2, "", 2, "", 10, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Color | `[1, 1, 10, "Pink", 2, "", 20, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Genre | `[1, 3001, 28, "Fixture House", 2, "", 6, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Stock Date | `[0, 10001, 22, "2021-02-02", 2, "", 46, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Comment | `[0, 10001, 20, "comment-1", 2, "", 35, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Bitrate | `[1, 0, 2, "", 2, "", 16, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Release Year | `[1, 0, 2, "", 2, "", 17, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Label | `[1, 4001, 36, "Fixture Label One", 2, "", 14, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Original Artist | `[1, 1004, 34, "Fixture Original", 2, "", 40, 0, 0, 0, 0, 0, 0, 2, "", 0]` |
| Remixer | `[1, 1003, 32, "Fixture Remixer", 2, "", 41, 0, 0, 0, 0, 0, 0, 2, "", 0]` |

String widths are UTF-16 byte counts including the terminating NUL. The title
row is the ordinary composite track row, so it retains the configured Key
secondary text, compatibility flags, tertiary key, and BPM. The other rows
use the same serialization envelope but not the ordinary track-row field
semantics. In particular, argument 1 is the displayed numeric value for Length
and BPM, the lookup ID for lookup fields, and the content ID for Stock Date and
Comment **[OBS]**.

The first argument is the persisted category-enabled flag on most fixed
metadata fields: `1` for an enabled matching `MenuItemID` and `0` when disabled
or absent. Stock Date and Comment are `0` because their menu-item IDs have no
persisted category rows in this fixture. The composite title row is special:
argument 0 remains its selected secondary KeyID. These meanings are distinct
from the ordinary track-list interpretation in `ROW_LAYOUT.md`.

## Database construction

`PSvAppSyncDBIF::getDispSongInf(player, list, content_id)` begins by clearing
the list buffer, then executes:

```sql
select * from djmdContent
where rb_local_deleted = 0 and ID = %lu
```

It also loads the active category states:

```sql
select MenuItemID, Disable from djmdCategory
where rb_local_deleted = 0
```

The function reads the content columns directly for Title, Length, BPM, KeyID,
Rating, ColorID, GenreID, StockDate, Commnt, BitRate, ReleaseYear, LabelID,
OrgArtistID, and RemixerID. Artist and Album are resolved from their IDs in the
same manner **[DEC]**.

Lookup text is fetched by ID from the corresponding entity table. The common
path uses `Name`; Key uses `djmdKey.ScaleName`, and Color uses
`djmdColor.Commnt`. This matches the live `Am`, `Pink`, genre, label, artist,
album, original-artist, and remixer strings **[DEC, OBS]**.

The category snapshot is reduced to enabled `MenuItemID` values: rows with
`Disable == 1` or `Disable == 3` are excluded. Each simple metadata-row
insertion tests whether its menu-item ID is in that vector and serializes the
boolean as argument 0. It does not suppress the metadata row **[DEC, OBS]**.

All 21 persisted category rows were disabled individually and recorded twice.
Genre, Artist, Album, BPM, Rating, Year, Remixer, Label, Original Artist, Key,
Color, Time, and Bitrate clear argument 0 on their associated row. Track,
Playlist, Folder, Search, File Name, History, Hot Cue Bank, and Matching leave
the complete list unchanged. The title row is a special composite whose
argument 0 remains its secondary KeyID. Comment and Date Added have no
persisted category row in the fixture and already carry argument 0 equal to
zero. `CATEGORY_ORACLE.md` gives the database-ID/MenuItemID/type table.

The Master-database implementation follows a separate path:
`PSvMasterDBIF::getDispSongInf` calls `PSvDBMain::GetDispSongInfDB`, which uses
`DsqlCategory_GetInfo` and `DsqlContent_GetSongInf`. Both AppSync and Master
database interfaces occupy the same virtual method slot used by the command
handler, so the selected database backend supplies the implementation **[DEC]**.

## Dispatch path

The recovered path in the pinned macOS executable is:

```text
PSvDBMain::OnMAnlzClientCmd                     0x101d2e6b0
  -> PSvDBMain::OnSongInfCmd                   0x101d2edc0
     -> PSvDBMain::GetDispSongInf              0x101ab8190
        -> database-interface virtual call
           PSvAppSyncDBIF::getDispSongInf      0x1016c01b0
           PSvMasterDBIF::getDispSongInf       0x102523c40
              -> PSvDBMain::GetDispSongInfDB   0x101ab7b90
```

`OnSongInfCmd` recognizes `0x2002`, logs the request kind, extracts the packed
context and content ID, and invokes `GetDispSongInf`. The request wrapper
requires menu location byte 1 in the packed context for this path and passes
the context's high byte as the player number used by `isAIO` **[DEC, OBS]**.

The same handler family contains these adjacent request kinds:

| Kind | Static action |
| ---: | --- |
| `0x2002` | Build Display Song Info |
| `0x2102` | Build Play Song Info |
| `0x2202`-`0x2502` | Recognized Rekordbox-local log/error paths; player-hosted meanings are documented separately |
| `0x2602` | Build Delivery Info |

All seven kinds are now in the live conformance corpus. `0x2102` and `0x2602`
produce complete Play and Delivery menus; `0x2202` through `0x2502` return
kind-specific `4003` errors. `SONG_INFO_SIBLINGS_ORACLE.md` gives their exact
rows, rendering, pagination, malformed-state behavior, and database paths
**[OBS, DEC]**.

These four errors are not a global protocol classification. XDJ-RX firmware
serves `0x2202` and `0x2302` in the player-hosted role and defines client
contracts for `0x2402` and `0x2502`; `SONG_INFO_SIBLINGS_ORACLE.md` records the
role split and retained source evidence.

## AIO classification and lifecycle

`PSvDBMain::isAIO(player)` consults a player-number cache, asks Pro DJ Link for
that player's model, and returns true when the model starts with `XDJ`. The
function also performs a redundant `XDJ-AZ` prefix check. Disconnect clears
the cached entry **[DEC]**.

A `0x06` keepalive on UDP 50000 is sufficient to expose LINK, but it did not
populate the model lookup used by this request in the controlled player-11
experiment. The resulting response used ordinary ordering even though the
keepalive advertised `XDJ-RX3`. Adding a real `0x0a` player-status packet on
UDP 50002 populated the model state and produced the AIO order. This lifecycle
distinction is part of the test identity, not incidental transport noise
**[OBS]**.

The RX3 status template is a byte-exact payload extracted from player 11 in
`captures/rx3-rekordbox-working-ap-20260927.pcap`. Its length is 292 bytes and
its SHA-256 is
`49d262852bc10cbed30f9cd1f40283047b2423d4865ec5d1b240ae5fe6e20987`.
The adapter replaces the fixed-width model field and both player-number bytes
at offsets `0x21` and `0x24`. The resulting CDJ-3000/player-1 status payload
has SHA-256
`91d5cf34ad0f2f4dda18a3119ce27d1ab79a1ffad941d92fafce72695016a8d8`.

The corresponding keepalive hashes are:

| Identity | UDP 50000 SHA-256 | UDP 50002 SHA-256 |
| --- | --- | --- |
| XDJ-RX3 player 11 | `da12196004059977cdbcd83b9e0ae22366a2daf50320ed1a7b033c1d7ab157d4` | `49d262852bc10cbed30f9cd1f40283047b2423d4865ec5d1b240ae5fe6e20987` |
| CDJ-3000 player 1 | `0c395fba0abe6701fdabe6a7d3acd0d3a0d8ba95c510df57ea6cb3ecb86f516e` | `91d5cf34ad0f2f4dda18a3119ce27d1ab79a1ffad941d92fafce72695016a8d8` |

The model-mutation matrix keeps requester and context aligned, uses a fresh
connection for every request, and retains these status-packet hashes:

| Advertised identity | Player | UDP 50002 SHA-256 | Four-case result |
| --- | ---: | --- | --- |
| XDJ-XZ | 11 | `9ed356339a8b011698151ce2a01b00982ed9fd2857399b1eb41acd1a9f9959e2` | four timeouts |
| XDJ-AZ | 11 | `47b87e84977c62a068625822f91ca5b42c3a0e19662c4f44fd256023443e15a9` | four timeouts |
| XDJ-1000MK2 | 11 | `05cf87eef69f3bef0f210d8161ba75b7a7afe116badac8c6116aedc16e183b4e` | four timeouts |
| UNKNOWN-FIXTURE | 1 | `21bd992527810b82f76d197deba901db0d0c127cf0affeae4f5b17b913a6aa7b` | four ordinary menus |

An earlier control used discovery players 3-6 and is retained only in the run
manifests. The canonical player-11 variants remove the already-proven ordinary
requester-number rejection as a confound. Every canonical outcome repeated
immediately after recording **[OBS]**.

The keepalive-only player-11 observation is retained under
`data/experiments/display-song-info-player-11-keepalive-only.json`. It is a
negative lifecycle control, not a canonical AIO golden.

## rbxport comparison

rbxport accepts `0x2002` and returns 16 rows for the populated fixture. All
three missing-content controls are field-exact. The populated response has the
same outcome, total, and row count, with these measured differences **[RBX]**:

- the title secondary string is `8A - 120.0 bpm` instead of `Am`;
- the title row therefore differs in its secondary width and tertiary text;
- Artist, Album, and Genre use synthesized lookup IDs instead of fixture IDs;
- several fixed-field argument-0 values are `0` instead of `1`;
- Color uses type `0x13` with empty text instead of type `0x14` and `Pink`;
- Bitrate and Release Year appear in the opposite order;
- the AIO replay retains ordinary Comment placement because the backend does
  not receive or model the discovery/status classification.

The 21 category-fixture replays all preserve the 16-row shape and none is
field-exact. They demonstrate that rbxport does not yet reproduce Rekordbox's
persisted category-enabled argument-0 flags for this API.

The 19 Display Song Info replays now contain 100 cases. Nineteen are field-exact
and 78 preserve outcome, total, and row count. All 21 render cases
preserve shape but differ in populated fields. Pagination preserves shape for
the ordinary complete, one-row, last-row, and overlap plans; rbxport's
conventional empty/truncated range handling differs from Rekordbox's zero,
end, past-end, overrun, and maximum-offset normalization. Four malformed cases
are exact; rbxport regularizes the other five. The three missing-content legacy
cases are exact, while the populated legacy rows retain the known field and
ordering gaps. All 28 boundary cases preserve complete 16-row shape but differ
in one or more populated fields. Rbxport serves four menus for each mutated XDJ
status identity, so all 12 timeout controls differ in outcome. For the unknown
identity, the three missing-ID menus are exact and the populated case preserves
shape **[RBX, OBS]**.

The canonical result directory is
`conformance/results/rbxport/c144f19+tree.80e87ec8aace/`. It contains actual
JSON, logs, and readable diffs for all 19 registered display suites.

## Reproduction

Start from a clean Rekordbox process. A stopped identity can remain in the
application's peer cache long enough for the next port query to time out, so
the guarded UI startup script is part of the procedure.

```sh
cd /home/evan/workspace/rx3-research/rekordbox-link-export-research

../rekordbox-windows/vmctl isolated-start
conformance/start_oracle_ui.sh

conformance/oracle_record.sh \
  conformance/suites/display-song-info-aio-player-11.json \
  conformance/fixtures/generated/full/manifest.json \
  conformance/runs/xdj-rx3-player-11-status.json \
  conformance/goldens/rekordbox-7.2.19/xdj-rx3-status/display-song-info-aio-player-11.json

conformance/oracle_record.sh \
  conformance/suites/display-song-info.json \
  conformance/fixtures/generated/full/manifest.json \
  conformance/runs/cdj-3000-player-1-status.json \
  conformance/goldens/rekordbox-7.2.19/cdj-3000-status/display-song-info.json

conformance/record_display_song_info_batch.sh
conformance/record_display_song_info_status_batch.sh
```

Each recording command performs the host isolation gate, starts a bounded
identity service, checks the active fixture hash, records the behavior, and
immediately repeats the suite against the new golden. The Windows VM is
started only in isolated mode; the physical-network unit remains inactive.

Generate the static evidence from the pinned binary:

```sh
cd /home/evan/workspace/rx3-research
BIN=artifacts/rekordbox/7.2.19/extracted/app-root/rekordbox.app/Contents/MacOS/rekordbox
PY=rekordbox-link-export-research/.venv/bin/python

"$PY" rekordbox-link-export-research/tools/disassemble_symbols.py \
  "$BIN" 'OnMAnlzClientCmd|OnSongInfCmd|GetDispSongInf|getDispSongInf|isAIO|linkProc' \
  --output rekordbox-link-export-research/data/static-analysis/display-song-info-dispatch.disasm.txt

"$PY" rekordbox-link-export-research/tools/find_direct_xrefs.py "$BIN" \
  0x101d2edc0 0x101ab8190 0x102521e80 0x1003dce20 \
  > rekordbox-link-export-research/data/static-analysis/display-song-info-direct-xrefs.txt
```

## Remaining conformance matrix

The current evidence proves the request shape, response framing, ordinary and
AIO order, complete populated row values, missing-content behavior, and the
status-message requirement for the tested identities. Complete coverage still
requires:

1. Capture genuine XDJ-XZ, XDJ-AZ, and XDJ-1000MK2 status shapes, then cross
   their model fields and reconnect/cache replacement without borrowing the
   RX3 packet layout.
2. Populate Display fields unavailable in the current fixture and exercise
   authenticated cloud runtime modes beyond the completed database-controlled
   Play path/file-state matrix. The stable sibling-builder RX3/CDJ status cross
   and Delivery-only field matrix are complete.

These are explicit gaps. The existing observations are canonical for their
recorded fixtures and identities, but do not imply behavior outside that
matrix.
