# Settings experiment matrix

The goal is to map one visible rekordbox setting to one database/configuration
delta and one player-visible protocol delta. All tests operate on the disposable
Windows library and an isolated synthetic client.

## Established UI gate

Preferences -> DJ System contains Category, Sort, and Column tabs. Rekordbox
disables all three and displays `Not allowed while link is active.` during an
active Link session. The supported same-process sequence is therefore:
deactivate LINK, change a setting, and reactivate LINK. Live experiments prove
that Key-to-Comments Column selection, Album category removal, and Comments
sort activation are consumed by the next Link activation without an application
restart. See `SETTINGS_SESSION_REFRESH_ORACLE.md` **[OBS, DB]**.

## Capture protocol

For each experiment:

1. Stop Link Export and close rekordbox cleanly.
2. Copy `master.db`, rekordbox preferences, and any device-setting files to a
   timestamped experiment directory. Record SHA-256 hashes and row counts.
3. Start rekordbox, make exactly one UI change, and record a before/after
   screenshot naming the control and value.
4. Close rekordbox cleanly. Snapshot the same files and generate structured
   SQLite table/row diffs rather than binary diffs alone.
5. Start rekordbox and the isolated synthetic player. Capture discovery,
   setup, root, the affected branch, sort menu, and one track render.
6. Deactivate and reactivate LINK without restarting rekordbox to test the
   supported refresh boundary. Repeat after application restart only if the
   next Link session remains unchanged.
7. Restore the baseline snapshot. Verify hashes or documented expected deltas.

Every result records application version, database hash, VM disk checkpoint,
synthetic-player version, request bytes, response bytes, and rendered labels.

## Category matrix

Test each category through the rekordbox UI where possible:

| Change | DB expectation | Wire/UI observation |
| --- | --- | --- |
| Disable one populated category | `djmdCategory.Disable & 1` changes | Root count minus one; row absent |
| Re-enable category | disable bit clears | Root row returns at stored sequence |
| Move category first/last | `Seq` values change | Root render order changes |
| Change category info order | `InfoOrder` changes | No root or Display Song Info wire effect in the recovered serving paths |
| Disable empty category | one row changes | Row disappears; root visibility does not inspect content tables |
| Populate a disabled category | content rows change only | Row remains hidden while its `Disable` predicate rejects it |

Run the visibility/reorder test against Track, Playlist, Remixer, and an empty
category to cover leaf, recursive, populated hierarchy, and empty hierarchy.

The complete empty fixture returns the same 20 enabled root rows with no
content. Twenty visible one-category-disabled fixtures each remove exactly the
configured row, and reversing `Seq` reverses the wire order. Static serving
control flow independently proves that `InfoOrder` is absent from root and
Display Song Info construction. See `CONFIGURATION.md`, `CATEGORY_ORACLE.md`,
and `data/static-analysis/category-configuration-fields.disasm.txt`.

## Sort matrix

The real-Rekordbox baseline exposes Default, Alphabet, Artist, Album, BPM,
Rating, Key, Label, Genre, Date Added, and DJ Play Count. All 18 request sort
IDs, every persisted sort row, hidden-row activation, selected-but-hidden
behavior, and complete `Seq` reversal are recorded. `SORT_AND_COLOR_ORACLE.md`
is the result authority.

| Change | Database/configuration observation | Wire observation |
| --- | --- | --- |
| Disable each visible sort | `djmdSort.Disable & 1` controls visibility | Each disabled row is absent and the total falls by one |
| Enable each hidden sort | clearing the disable bit makes the row active | Comments, Time, Remixer, Original Artist, Bitrate, and Color appear with their fixed IDs |
| Reverse every sort | reversed `Seq` values | All 17 persisted rows reverse exactly |
| Select a hidden sort | selected bit and visibility remain independent | Hidden selected Comments stays absent while requests may still carry sort ID 12 |
| Request sort IDs 0-17 | no configuration mutation | All IDs have canonical real-Rekordbox results, including inactive ID 14 |

Track ordering boundaries, including filename ordering and null/dangling values,
are covered by `SORT_AND_COLOR_ORACLE.md`, `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md`,
and the `filename-boundaries`, `invalid`, and generated sort suites.

## Secondary-column matrix

All 15 selectable columns are recorded against the same eight deterministic
tracks in extended setup: Artist, Album, BPM, Rating, Genre, Comment, Time,
Remixer, Label, Original Artist, Key, Bitrate, Color, DJ Play Count, and Date
Added. The corpus also records databases with no selected column and with both
Comment and Key selected. `SECONDARY_COLUMN_ORACLE.md` contains every argument-0
value, display string, composite item type, and Sort-menu effect **[OBS, DB]**.

Lookup/string columns carry their raw database key in argument 0 and formatted
text in argument 5. Numeric columns carry the raw value in argument 0 and leave
argument 5 empty. Argument 12 remains the track's original KeyID, argument 14
its key spelling, and argument 15 BPM x100 for every selection. Classic Key
produces `Am - 120.0 bpm`; local Alphanumeric/Camelot mode produces
`8A - 120.0 bpm`. `KEY_NOTATION_ORACLE.md` records that transformation.

The matching 15-column legacy setup matrix contains 30 declarations. Its live
record/repeat batch and all 15 hash-bound receipts are complete. Every Sort
menu and selected secondary value matches its extended partner, and every
legacy track row is the exact 12-field prefix of the corresponding 16-field
extended row **[OBS]**.

## Data-dependent branch results

The reversible fixture families now establish these results against real
Rekordbox:

| Feature | Established coverage | Authority |
| --- | --- | --- |
| Original Artist | Referenced root, ALL and concrete albums, concrete tracks, empty root, invalid relations, sorting, search, Smart rows, and secondary rendering | `PROTOCOL_REFERENCE.md`, `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md` |
| Remixer | Referenced root, ALL and concrete albums, concrete tracks, empty root, invalid relations, sorting, search, Smart rows, and secondary rendering | `PROTOCOL_REFERENCE.md`, `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md` |
| Hot Cue Bank | Recursive catalog, empty/deleted/boundary memberships, both getters, mutation setters, parser boundaries, and connection/process health | `HOT_CUE_BANK_ORACLE.md` |
| History | Empty start, create, repeated additions, ordering, removal, reset, and application restart | `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md` |
| Matching | Zero, one, multiple, chained, dangling, duplicate, deleted, and seed-selector behavior | `PROTOCOL_REFERENCE.md`, `DATABASE_QUERIES.md` |
| Rating | Complete 0-5 roots/drilldowns, hidden 99 boundary, direct selectors, null and secondary rendering | `PROTOCOL_REFERENCE.md`, `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md` |
| Color | IDs 1-8, unassigned/invalid values, custom labels, direct selectors, sorting, and secondary rendering | `SORT_AND_COLOR_ORACLE.md`, `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md` |
| Date Added | Year/month/day hierarchy, ALL selectors, invalid selectors, ordering, rendering, and date parsing boundaries | `PROTOCOL_REFERENCE.md`, `SMART_PLAYLIST_ORACLE.md` |
| Smart playlist | Membership precedence, AND/OR, nested nodes, every property/operator class, XML/parser boundaries, sorting, columns, contexts, and setup widths | `SMART_PLAYLIST_ORACLE.md` |

The remaining Hot Cue Bank item is player-UI load state beyond the proven
catalog and protocol paths. It requires authentic player-side behavior rather
than another database fixture.

## Failure and boundary cases

- Empty result, unknown ID, deleted row, and stale parent ID.
- Page sizes 0, 1, 32, exact count, beyond count, and overlapping pages.
- Unicode, combining characters, punctuation, and maximum search length.
- Concurrent edit while a menu is open; reconnect and refresh behavior.
- Database/server restart between count and render.
- Track without analysis, artwork, file, artist, album, key, or BPM.
