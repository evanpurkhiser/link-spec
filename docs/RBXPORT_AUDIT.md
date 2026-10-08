# `rbxport` Link Export conformance audit

The audited checkout is `/home/evan/workspace/rbxport` at commit `c144f19` on
branch `evan/rx3-link-export-support`. It contains unrelated working changes,
so a commit ID alone does not identify the tested implementation. The canonical
replay records every file and SHA-256 in the compiled dependency closure. Its
source identity is:

```text
c144f19+tree.80e87ec8aace
full tree SHA-256 80e87ec8aacecbb46b9607e4fe196905039fa01aef0099992167bf9ec237309f
```

`conformance/results/rbxport/c144f19+tree.80e87ec8aace/` contains the source
manifest, actual response envelopes, semantic path diffs, runner logs, server
readiness records, machine-readable summary, and readable summary **[RBX,
OBS]**. The checkout remains read-only research input.

## Test boundary

`conformance/src/bin/rbxport_conformance_server.rs` is a loopback-only adapter.
It opens the same encrypted fixture read-only, loads `rbl-index`, constructs the
real `rbl-link::IndexCatalog`, and serves it through the real
`rbl-dbserver::CatalogHandler`. Only port query and RemoteDBServer are bound,
both to `127.0.0.1`. The adapter does not start Pro DJ Link discovery, beacon,
NFS, or a non-loopback listener.

The base and empty fixtures select Key. Each settings replay passes its
effective secondary column and, where representable, its exact visible sort
order. The multiple-selection fixture uses Comment because that is rekordbox's
repeat-verified winner. Rbxport has no absent-column state, so the no-selection
suite deliberately uses Comment as a runnable control and retains the semantic
diff as evidence of the missing capability. The first exploratory run used
`rbl-linkd`'s Comment default globally and is retained under
`conformance/results/rbxport/c144f19-dirty/`; it is not canonical.

`conformance/replay_rbxport.py` performs the canonical replay. It builds
offline, fingerprints source, starts one bounded child server per distinct
fixture/column/sort configuration, runs all 211 retained rekordbox goldens,
stops the server in a `finally`
path, and writes every result below the fingerprinted directory. A backend
mismatch is an expected result; connection, build, fixture, or artifact errors
abort the run.

## Measured results

The 211 executions cover 2,403 cases. Three hundred sixty-five cases are
field-exact and 1,223
have the same outcome, total, and row count. All eight recorded identity
controls produce identical results for the shared suites, matching the
corresponding rekordbox oracle finding.
"Same shape" means outcome, menu total, and row count agree; exact equality
also requires every typed header, row, render message, string, number, and
footer to match.

| Model | Suite | Cases | Exact | Same shape |
| --- | --- | ---: | ---: | ---: |
| XDJ-RX3 | full | 47 | 2 | 29 |
| XDJ-RX3 | chained navigation | 16 | 0 | 14 |
| XDJ-RX3 | root capabilities | 31 | 0 | 2 |
| XDJ-RX3 | sort IDs | 18 | 0 | 18 |
| XDJ-RX3 | packed contexts | 19 | 0 | 7 |
| XDJ-RX3 | render arities | 3 | 0 | 3 |
| XDJ-RX3/player-1 and player-11 controls | Display Song Info | 8 | 6 | 8 |
| XDJ-RX3/status | Display Song Info AIO | 1 | 0 | 1 |
| CDJ-3000/status | Display Song Info | 4 | 3 | 4 |
| RX3/CDJ status | Play/Delivery stable matrix | 212 | 36 | 146 |
| XDJ-RX3 | Play path/cloud/file-presence matrix | 14 | 0 | 12 |
| XDJ-RX3 | Link Export `FolderPath` visibility matrix | 7 | 0 | 1 |
| XDJ-RX3 | Display Song Info render controls | 21 | 0 | 21 |
| XDJ-RX3 | Display Song Info pagination | 9 | 0 | 4 |
| XDJ-RX3 | Display Song Info malformed requests | 9 | 4 | 4 |
| XDJ-RX3 | Display Song Info legacy | 4 | 3 | 4 |
| XDJ-RX3 | Display Song Info boundary/Unicode/invalid | 24 | 0 | 24 |
| XDJ-RX3 | Display Song Info all-field string thresholds | 4 | 0 | 4 |
| XDJ-XZ/AZ/1000MK2 mutated RX3 status | Display Song Info rejection boundary | 12 | 0 | 0 |
| Unknown-model mutated RX3 status | Display Song Info ordinary order | 4 | 3 | 4 |
| XDJ-RX3 | Play/Delivery sibling baseline | 24 | 6 | 8 |
| XDJ-RX3 | Play/Delivery sibling render controls | 42 | 0 | 42 |
| XDJ-RX3 | Play/Delivery sibling pagination | 18 | 0 | 8 |
| XDJ-RX3 | Play/Delivery sibling malformed requests | 17 | 7 | 7 |
| XDJ-RX3 | Play/Delivery sibling legacy | 8 | 6 | 8 |
| XDJ-RX3 | Delivery-only 127-unit boundaries | 8 | 0 | 8 |
| XDJ-RX3 | DeliveryComment/ISRC 255-unit boundaries | 8 | 0 | 8 |
| XDJ-RX3 | render secondary controls | 19 | 0 | 19 |
| XDJ-RX3 | pagination | 9 | 0 | 4 |
| XDJ-RX3 | request errors | 9 | 2 | 3 |
| XDJ-RX3 | malformed framing | 6 | 2 | 2 |
| XDJ-RX3 | concurrency | 12 | 0 | 12 |
| XDJ-RX3 | legacy | 2 | 0 | 1 |
| XDJ-RX3 | extended families, full | 21 | 3 | 11 |
| XDJ-RX3 | 15 selected secondary columns | 30 | 0 | 24 |
| XDJ-RX3 | missing/multiple secondary selection | 2 | 0 | 2 |
| XDJ-RX3 | category settings | 45 | 0 | 23 |
| XDJ-RX3 | Search/Search Track, Unicode/NUL, Category gates, sorts, and ceilings | 160 | 23 | 61 |
| XDJ-RX3 | Rating/Bitrate/Color scalar selectors and hidden-domain boundaries | 39 | 11 | 35 |
| XDJ-RX3 | Smart playlist rule/membership precedence | 12 | 6 | 7 |
| XDJ-RX3 | Smart rule/numeric/property/fixed/relative/date-format/text/cross-property/My Tag/XML evaluator matrices | 616 | 165 | 165 |
| XDJ-RX3 | Smart SQL null/REAL/wide-integer/missing-attribute matrix | 100 | 29 | 29 |
| XDJ-RX3 | Smart result sort/render/pagination/context/width crosses | 66 | 0 | 0 |
| Eight ordinary identities | Smart populated/empty device cross | 16 | 8 | 8 |
| XDJ-RX3 | Smart persisted secondary-column cross | 17 | 0 | 0 |
| XDJ-RX3 | Four key-notation preference states | 52 | 0 | 36 |
| XDJ-RX3 | File Name formatting, widths, and all sort IDs | 18 | 0 | 18 |
| XDJ-RX3 | sort visibility/order, hidden selection, colors | 22 | 0 | 16 |
| CDJ-3000 | full | 47 | 2 | 29 |
| CDJ-3000 | legacy | 2 | 0 | 1 |
| XDJ-RX3 | empty | 21 | 16 | 20 |
| XDJ-RX3 | extended families, empty | 9 | 6 | 8 |
| XDJ-RX3 | numeric boundaries | 30 | 0 | 13 |
| XDJ-RX3 | secondary lookup-string boundaries | 8 | 0 | 8 |
| XDJ-RX3 | Date Added boundary | 1 | 0 | 0 |
| XDJ-RX3 | Comment boundary | 1 | 0 | 0 |
| XDJ-RX3 | isolated ASCII/supplementary thresholds | 16 | 0 | 10 |
| XDJ-RX3 | isolated UTF-16-unit thresholds | 16 | 0 | 4 |
| XDJ-RX3 | invalid database values | 15 | 0 | 11 |
| XDJ-RX3 | track compatibility | 2 | 0 | 2 |
| XDJ-RX3 | History lifecycle | 10 | 4 | 4 |

The exact populated matches are History and an empty playlist. The exact
extended populated matches are the out-of-range Play Count request and the
empty/missing My Tag-on-track requests. Sixteen ordinary empty-library cases
and six extended empty cases match exactly. This establishes that framing,
setup, zero-row menu behavior, and many request dispatch paths already agree;
populated row identity and serialization account for much of the remaining
distance **[OBS]**.

The History lifecycle exposes a functional gap rather than a row-format-only
difference. Rbxport accepts `3001` insert messages, but its following `1012`
root remains empty. Four queries that require the returned current-history ID
therefore record `dependency_unavailable`; compare mode continues and names the
missing source selector in each diff. Its `3401` remove response is the
unavailable sentinel rather than rekordbox's zero-total response **[OBS]**.

The capability sweep adds these measured differences **[OBS]**:

- rekordbox projects the root through the supplied mask; rbxport returns its
  fixed 20-row root for every mask. Only captured/all-bit totals therefore
  share a shape.
- rekordbox accepts requester byte 1 and times out bytes 2-6. Rbxport accepts
  all six. Rekordbox renders menu locations 1-8; rbxport returns rows only for
  location 1. Both accept tested slot bytes 0-4.
- Every sort ID 0-17 returns eight rows in both implementations, but ordering,
  row fields, Key presentation, and footer serialization differ.
- Both produce twelve successful simultaneous player-1 sessions when the
  runner permits ten seconds for burst setup.
- All render arities and override cases have the same outcome and row counts.
  Five-argument rbxport rows additionally expose My Tag list positions where
  rekordbox writes zero.
- Rekordbox clamps zero/end/past-end render ranges, wraps an overrun to the
  complete list, and ignores offset `0xffffffff`; rbxport uses conventional
  empty/truncated ranges.
- Request-error exact matches are missing-sort and extra-argument track
  requests. Malformed-frame exact matches are the truncated header and short
  tag list, both timeouts.

## Persisted secondary-column sweep

The 17 settings suites run the same Sort and track-row declarations against
rekordbox and rbxport. All 32 cases execute; 26 preserve outcome, total, and
row-count shape; none is field-exact **[OBS]**.

Nine selected columns use sorts that rbxport can advertise: Artist, Album,
BPM, Rating, Genre, Label, Key, DJ Play Count, and Date Added. Their Sort and
track cases preserve shape. The six other settings fixtures explicitly enable
normally hidden rows while selecting them: Comment, Time, Remixer, Original
Artist, Bitrate, and Color. Rbxport's `Sort` enum has no corresponding choices, so
those Sort cases have an 11-row actual menu against rekordbox's 12-row oracle;
their track cases still preserve shape **[OBS, RBX]**.

Rekordbox's no-selection state returns title-only rows with argument 0 zero,
empty argument 5, and packed type `0x0004`. `Source::track_column` returns a
mandatory `TrackColumn`, so the adapter cannot express that state. With both
Comment and Key selected, rekordbox chooses Comment for the current fixture;
the Comment-configured rbxport control preserves menu shape but differs in
extended row fields **[OBS, RBX]**.

Across the selected-column rows, recurring field gaps are:

- the extended footer's extra two zero arguments;
- argument 12 being repurposed to column/artwork data instead of preserving
  the original database KeyID;
- Camelot Key strings in place of the previously recorded Classic oracle;
- column-specific numeric/string formatting and empty-value differences.

`SECONDARY_COLUMN_ORACLE.md` contains the complete observed matrix. Each
settings `*.diff.txt` remains the path-level authority.

## Wire serialization differences

### Extended footer

Rekordbox 7.2.19 sends an extended `4201` menu footer with zero arguments.
`rbxport` sends two numeric zero arguments. This difference affects otherwise
matching paginated roots, selectors, Date Added branches, colors, keys, and
playlists. Legacy footers are zero-width in both implementations **[OBS]**.

### Key presentation

The selected local CDJ style is now proven to govern every measured Rekordbox
key-bearing path: Classic produces `Am`, while Alphanumeric produces `8A`.
Those new canonical suites have not been run against rbxport. The comparison in
this audit remains limited to the older Classic desktop-preference oracle and
must not be treated as a device-style conformance result.

### Prepare sort payload

For Prepare sorted by Key, rekordbox puts the My Tag list position in argument
0 (`14`, `15` in the fixture). `rbxport` puts the selected key's database ID
there (`5001`, `5002`). Row membership and ordering agree **[OBS]**.

## Identity and hierarchy differences

Rekordbox exposes `djmdGenre.ID`, `djmdArtist.ID`, `djmdAlbum.ID`, and
`djmdLabel.ID` as wire selector IDs. The fixture deliberately uses separated
ranges such as genre `3001`, artist `1001`, album `2001`, and label `4001`.
`rbxport` exposes interner positions plus one (`1`, `2`, and so on). Album rows
repeat the synthetic value in argument 8 as well **[OBS, RBX]**.

The stable-ID suites then query nested menus with the fixture's database IDs.
Rekordbox returns the expected hierarchy; `rbxport` interprets those numbers as
its synthetic ID space and returns zero rows. This is both an exact parity gap
and an intentionally strong database-path test.

The chained-navigation suite feeds each backend the selector ID returned by an
earlier case. Fourteen of its sixteen paths match outcome, total, and row count,
showing that the synthetic IDs remain usable within the same backend. The genre
and label album menus with the ALL-artist sentinel return four rows in
`rbxport`, including `Unknown`, while rekordbox returns three. No chained case
is wire-exact because the returned ID values, extended footer, and track Key
presentation still differ **[OBS]**.

Playlist IDs remain database IDs. Playlist contents and empty-playlist
behavior work, while the root orders the system playlist before the folder;
rekordbox puts folders first and then applies sequence order within row class.
The focused smart fixture exposes a functional catalog gap. Rekordbox evaluates
valid `SmartList` XML for Attribute 4 and ignores deliberately contradictory
`djmdSongPlaylist` rows. Rbxport Link Export instead returns those stored rows:
rule-only is empty, the contradiction returns two Techno tracks, and malformed
or ruleless Attribute 4 rows return their stored members. Six child/empty
controls are exact; the root preserves shape but differs in row-class order and
footer width **[OBS, RBX]**.

The 39-case rule matrix has no materialized membership. Its 19 Rekordbox-empty
controls are exact against rbxport; all 20 Rekordbox-nonempty cases diverge.
Those exact cases only prove both serving paths returned empty. They do not
validate rbxport's separate rule parser, because Link Export never invokes it
for these playlist rows **[OBS, RBX]**.

The 60-case numeric matrix behaves the same at the integration boundary: 15
empty-result controls are exact and all 45 nonempty Rekordbox cases diverge.
This replay cannot validate rbxport's numeric evaluator until Link Export uses
it for Attribute 4 playlists **[OBS, RBX]**.

The 33-case property matrix adds every written property name plus aliases and
My Tag representation controls. Rbxport is exact for the eight Rekordbox-empty
controls and returns empty for all 25 populated oracle results. This includes
lookup, scalar, date, subtitle, filename, and raw My Tag membership cases, so
the same missing Link Export integration blocks the entire property surface
**[OBS, RBX]**.

The 30-case fixed-date matrix adds nine exact empty controls and 21 populated
divergences across Date Added, Date Created, and Date Released. The exact
controls do not validate rbxport's date parser or comparisons because the Link
Export path never reaches them **[OBS, RBX]**.

The 56-case relative-date matrix has nonempty Rekordbox results in every case,
so rbxport has zero exact and zero same-shape results. The missing integration
therefore blocks all measured relative-unit dispatch, lower-bound, count,
future-date, and invalid-date semantics **[OBS, RBX]**.

The 117-case date-format matrix has 54 exact empty controls and 63 populated
divergences. Every rbxport response is empty. The exact controls therefore do
not establish parser parity; the backend path exercises none of Rekordbox's
fixed-length gate, ignored separators, character arithmetic, calendar
normalization, or conversion-failure behavior **[OBS, RBX]**.

The 55-case Comments text matrix has eight exact empty controls and 47
populated divergences. Every rbxport response is empty. The exact controls do
not establish collation parity; the backend path exercises none of the
measured case, accent, width, kana, expansion, normalization, substring,
supplementary-character, whitespace, entity, empty/null, or embedded-NUL
behavior **[OBS, RBX]**.

The 104-case string-property matrix has zero exact and zero same-shape cases.
Every Rekordbox rule returns at least one row, including empty equality over an
empty lookup name plus a missing relation and empty inequality over the eight
nonempty rows. Rbxport returns an empty menu for all 13 properties and all
eight rule forms, so the missing Link Export integration blocks both lookup
and direct string evaluation uniformly **[OBS, RBX]**.

The filename fixture preserves total and row-count shape under all 18 sort IDs,
but no case is exact. Rekordbox caps primary filename output at 255 UTF-16 units
and replaces a surrogate split at the boundary; rbxport returns the full
256-unit database strings. Default and explicit sort orders, Key presentation,
extended fields, and footers also differ **[OBS, RBX]**.

## Request-family coverage

`rbl-dbserver::session::LinkSession` handles root; genre/artist/album/label
drilldowns; sort; key and related key; track and filename; Matching; BPM and
tolerance; rating; bitrate; color; duration; release decade/year; tag list;
playlists; history; Date Added; search; metadata/info/delivery; filters; edits;
and binary payload requests **[RBX]**.

The measured gaps are:

| Family | Current measured behavior |
| --- | --- |
| DJ Play Count | Populated root and track requests return zero; empty requests match |
| My Tag hierarchy | Root/group/track-tag content returns zero; invalid modes return an empty menu instead of `ffffffff` unavailable |
| Original Artist | Populated requests return zero |
| Remixer | Populated requests return zero |
| Hot Cue Bank | Returns a valid empty `4000` menu; rekordbox returns `4003` error |
| Search | Returns tracks only and uses conventional windows; `1500` ignores sort and shares the same implementation, while Rekordbox has signed-low-byte sort validation, eight observed orders, a 5,000 default ceiling, and uncapped explicit sorts through 10,005 rows |
| Legacy root | Advertises 20 rows including Matching; rekordbox advertises 19 and omits Matching |
| Date Added | Year/month/day/track membership and empty sentinels agree; extended footer differs |
| Comment/Date Added width | Does not reproduce rekordbox's first render timeout at 256 UTF-16 units; several direct-year selectors also differ |
| Prepare | Membership agrees; Key presentation, argument 0, and footer differ |

Root construction remains a fixed 20-row vector rather than a projection of
`djmdCategory`. All 23 live category suites confirm the divergence: every
visible-row disable and both special-bit cases differ in shape, while the
Folder no-op and reversed order preserve only outcome, total, and row count.
All 21 category-specific Display Song Info cases preserve their 16-row shape
but differ in populated fields; rbxport does not reproduce Rekordbox's
per-row category-enabled argument-0 flags.
All 21 dedicated render-control cases preserve shape. The pagination replay
differs on zero count, end/past-end clamping, overrun reset, and maximum-offset
timeout. Four malformed requests are exact; no arguments, three wrong-type
forms, and zero context differ. The populated legacy case preserves shape,
while its three missing-content cases are exact.
All 28 field-boundary cases preserve complete 16-row shape while differing in
populated values, string truncation, or row serialization.
Sort choices are configurable through
the `Source` trait but are not automatically read from `djmdSort` by the
headless server. The adapter can reproduce baseline order, ten visible-row
removals, and reversed order, but its `Sort` enum lacks the six hidden
rekordbox choices. Color labels are fixed rather than loaded from `djmdColor`
**[RBX, OBS]**.

## Priority work

1. Preserve rekordbox database IDs in named selector rows and resolve them back
   to index identities for every hierarchy.
2. Match zero-argument extended footers.
3. Defer the new local-device Classic/Alphanumeric suites until the Rekordbox
   oracle is complete; then model notation consistently across roots,
   distances, rows, and Song Info.
4. Implement Play Count, My Tag, Original Artist, Remixer, and Hot Cue Bank
   request behavior, including `ffffffff` unavailable versus valid empty.
5. Match search's heterogeneous result construction and playlist root ordering.
6. Make legacy root composition, category masks/order, sort choices, and
   selected secondary column fixture-driven, including enabled non-default sorts
   and an explicit absent-secondary state.
7. Remove the extra `Unknown` album row from ALL-artist genre and label paths
   while preserving valid blank-album behavior.

The result directory's `SUMMARY.md` names every exact and differing case. Each
`*.diff.txt` is the authoritative field-level list; this audit groups those
observations without replacing the raw evidence.
