# Link Export configuration

This chapter describes how rekordbox 7.2.19 constructs the root and sort menus
from `master.db`. Decimal database IDs and hexadecimal protocol values are
shown separately because several values look deceptively similar.

## Configuration tables

The copied database has four directly relevant tables:

| Table | Link Export role |
| --- | --- |
| `djmdMenuItems` | Stable menu-item identity, localization token, and item class |
| `djmdCategory` | Root category identity, order, visibility state, and information order |
| `djmdSort` | Sort identity, order, visibility state, and selected secondary-column state |
| `djmdColor` | Eight color labels and their order |

Sanitized exports are in `data/database/`. They omit UUIDs, synchronization
bookkeeping, timestamps, and every library/content row. `metadata.json` records
the source database hash and complete table schemas. The export tool decrypts
the database in memory and never prints or writes the key.

`data/configuration-behavior-map.json` is the generated, machine-readable join
across these four tables, the three known root masks, field ownership, settings
refresh evidence, render arities, and the complete RX3 active-sort/six-argument
golden. `tools/generate_configuration_behavior_map.py` regenerates it, and its
focused conformance test pins source hashes, row domains, visibility/selection
invariants, and every observed sort.

## Menu-item identity

`djmdMenuItems.ID` is a decimal database ID. The complete active map is:

| Decimal ID | Hex ID | Name | Class |
| ---: | ---: | --- | ---: |
| 1 | `01` | Genre | -128 |
| 2 | `02` | Artist | -127 |
| 3 | `03` | Album | -126 |
| 4 | `04` | Track | -125 |
| 5 | `05` | BPM | -123 |
| 6 | `06` | Rating | -122 |
| 7 | `07` | Year | -121 |
| 8 | `08` | Remixer | -120 |
| 9 | `09` | Label | -119 |
| 10 | `0a` | Original Artist | -118 |
| 11 | `0b` | Key | -117 |
| 12 | `0c` | Cue | -115 |
| 13 | `0d` | Color | -114 |
| 14 | `0e` | Time | -110 |
| 15 | `0f` | Bitrate | -109 |
| 16 | `10` | File Name | -108 |
| 17 | `11` | Playlist | -124 |
| 18 | `12` | Hot Cue Bank | -104 |
| 19 | `13` | History | -107 |
| 20 | `14` | Search | -111 |
| 21 | `15` | Comments | -106 |
| 22 | `16` | Date Added | -116 |
| 23 | `17` | DJ Play Count | -105 |
| 24 | `18` | Folder | -112 |
| 25 | `19` | Default | -95 |
| 26 | `1a` | Alphabet | -94 |
| 27 | `1b` | Matching | -86 |

The root row ID is `djmdCategory.ID`, not `MenuItemID`. For example, the
captured Search root row ID is decimal 18 (`0x12`), while that category points
to menu item decimal 20 (`0x14`). The menu item controls the label/class and
capability bit; the category ID controls the root row selected by the client.

## Root construction

`PSvDBMain::GetRootMenu(list_buffer, capability_mask)` performs this sequence:

1. Clear the destination list buffer.
2. Iterate `djmdCategory` through `DsqlCategory_GetEnableItem`, ordered by
   `Seq` ascending.
3. Apply `WhereCategory_Enable` to the row's `MenuItemID`, `Disable`, and the
   client-provided capability mask.
4. Resolve label and row class with `DsqlMenuItem_GetItem(MenuItemID)`.
5. Remember whether menu item 18 (Hot Cue Bank) was returned.
6. Suppress menu item 24 (Folder) even when its category row is enabled.
7. Insert at most 100 rows.
8. For capability mask `0x00ffffff` only, append category ID 23 pointing to
   menu item 18 when Hot Cue Bank was not already returned.

The copied configuration contains 21 categories. Folder is the one suppressed
row, producing the 20-entry captured root. Folder remains a valid row type
inside the Playlist hierarchy.

### Exact category predicate

The executable implements the following equivalent predicate. `menu_item` and
`disable` are database values; `capability_mask` is the final argument of the
`1000` request.

```text
if menu_item == 27:                 # Matching
    hidden = (disable & 1) != 0
elif menu_item == 22:               # Date Added
    hidden = disable == 1
else:
    hidden = disable != 0

if hidden:
    return false

if menu_item == 22:
    required_bit = 1 << 24
else:
    required_bit = 1 << (menu_item - 1)

return (capability_mask & required_bit) != 0
```

These special cases give `Disable` bit 1 two configuration meanings without
hiding the row:

- Matching is visible with `Disable = 2` in the copied database.
- Date Added would also be visible with `Disable = 2`, but uses capability bit
  24 rather than its ordinary bit 21.

The ordinary UI enable/disable state remains bit 0. Values outside the known
bit patterns need a controlled settings delta before assigning semantics.

### Field consumption and empty categories

Root serving sorts `djmdCategory` by `Seq`, applies visibility using
`MenuItemID`, `Disable`, and the request mask, then returns `ID` and
`MenuItemID`. It does not read `InfoOrder` or consult any content/entity table
**[DEC]**. The empty deterministic library consequently returns the same 20
enabled root rows as the populated configuration **[OBS, DB]**. Populating a
disabled category cannot make it visible because the rejection occurs before
any category-specific data query.

`InfoOrder` is retained by the settings editor's `RawCategorySetting` read and
write path. The active Display Song Info builder separately reads only
`MenuItemID, Disable`; its 16-row order is fixed by code. No recovered Link
Export root or Display builder consumes `InfoOrder` **[DEC]**. The exact field
accesses are preserved in
`data/static-analysis/category-configuration-fields.disasm.txt`.

### Capability-bit map

For every ordinary menu item, bit `MenuItemID - 1` enables the category.
Date Added is the sole observed remapping.

| Menu item | Name | Required mask |
| ---: | --- | ---: |
| 1 | Genre | `0x00000001` |
| 2 | Artist | `0x00000002` |
| 3 | Album | `0x00000004` |
| 4 | Track | `0x00000008` |
| 5 | BPM | `0x00000010` |
| 6 | Rating | `0x00000020` |
| 7 | Year | `0x00000040` |
| 8 | Remixer | `0x00000080` |
| 9 | Label | `0x00000100` |
| 10 | Original Artist | `0x00000200` |
| 11 | Key | `0x00000400` |
| 12 | Cue | `0x00000800` |
| 13 | Color | `0x00001000` |
| 14 | Time | `0x00002000` |
| 15 | Bitrate | `0x00004000` |
| 16 | File Name | `0x00008000` |
| 17 | Playlist | `0x00010000` |
| 18 | Hot Cue Bank | `0x00020000` |
| 19 | History | `0x00040000` |
| 20 | Search | `0x00080000` |
| 21 | Comments | `0x00100000` |
| 22 | Date Added | `0x01000000` |
| 23 | DJ Play Count | `0x00400000` |
| 24 | Folder | `0x00800000` (then suppressed by root builder) |
| 25 | Default | `0x01000000` (not a root category) |
| 26 | Alphabet | `0x02000000` (not a root category) |
| 27 | Matching | `0x04000000` |

The controlled lab mask `0x05cfffff` sets bits 0-19, 22-24, and 26. It admits
every configured root row in the deterministic database, including Matching
with `Disable = 2`. Folder is admitted by the predicate and then removed by
`GetRootMenu`. The mask does not enable Comments or Alphabet. Date Added is
mask-enabled but has no `djmdCategory` row in this library.

The retained physical RX3 sent `0x05fdffff`, not the controlled lab mask. It
sets bits 0-16, 18-24, and 26. The exact request was
`1000 [0x0b010401, 0, 0x05fdffff]`; Rekordbox returned 19 root rows from that
user's library. The physical and deterministic libraries have different
category configuration, so equal or unequal totals would not isolate the mask
effect. `data/experiments/physical-rx3-session/session-envelope.json` retains
the exact setup, root exchange, rows, contexts, and source-PCAP hash. The
authority-only `physical-rx3-session-envelope` suite replays this exact mask
against the deterministic fixture so the response is learned from Rekordbox
rather than predicted **[CAP]**.

Dysentery records the older root form with `0x00ffffff`. Rekordbox treats that
exact value specially for Hot Cue Bank synthesis. Neither the controlled lab
mask `0x05cfffff` nor the physical RX3 mask `0x05fdffff` takes that exact-mask
compatibility branch.

### Live mask sweep

The isolated 7.2.19 oracle tested zero, every single menu-item bit, the legacy
mask, the controlled lab mask, and all bits. Zero returned a valid empty menu.
Single bits for configured menu items 1-11, 13-20, and 27 returned exactly that
one row. Menu item 12 (Cue) and items 21-26 returned zero rows because this
database has no visible corresponding category or, for Folder, because the
root builder suppresses it. The legacy mask returned the same 19 rows as the
controlled root except Matching. Controlled and all-bit masks returned the same 20
rows, with Matching between Album and Search. The 31 cases matched on an
immediate independent run **[OBS]**.

### Live category settings sweep

All 21 persisted `djmdCategory` rows were independently changed to
`Disable = 1`. Twenty runs removed exactly their visible root row and reduced
the total to 19. Category 17 (Folder) was the sole wire-level no-op because
root construction already suppresses it. Reversing every category `Seq`
reversed the returned root order exactly while Folder remained absent.

A special-bit fixture kept Matching visible at `Disable = 2` and moved it
first, while Track and Hot Cue Bank at `Disable = 1` remained hidden under both
the captured and all-bits capability masks. The expanded 45-case corpus also
records Display Song Info for every one-category-disabled fixture: simple
metadata rows retain membership and clear argument 0 when their corresponding
`MenuItemID` is disabled. All cases across 23 suites matched on immediate
repeat **[OBS, DB]**. `CATEGORY_ORACLE.md` contains the complete root and
display-flag tables, exact order, artifacts, replay gaps, and limitations.

## Sort-menu construction

`PSvDBMain::GetSortMenu` iterates `djmdSort` in `Seq` order, resolves each
row's `MenuItemID` through `djmdMenuItems`, and inserts at most 100 rows. The
two signed-byte parameters passed into `DsqlSort_GetEnableItem` are stored in
the predicate context, but `WhereSort_Enable` does not read them in this build.

The exact visibility predicate is:

```text
return (Disable & 1) == 0
```

The current 11 visible rows are Default, Alphabet, Artist, Album, BPM, Rating,
Key, Label, Genre, Date Added, and DJ Play Count. Comment, Time, Remixer,
Original Artist, Bitrate, and Color have bit 0 set and are absent.

### Live sort settings sweep

All 17 persisted sort rows were independently visibility-toggled. Each of the
11 visible rows disappeared and each of the six hidden rows appeared first at
its persisted `Seq = 0`. Reversing all sequence values produced the exact
reverse of the 11 visible rows. All 18 cases matched on immediate repeat
**[OBS, DB]**.

The independent hidden-selected fixture gave Comment `Disable = 3`. Comment
remained absent from the 11-row Sort menu while all eight track rows rendered
Comment as their secondary value. Visibility and secondary selection therefore
consume bits 0 and 1 independently in live behavior. `SORT_AND_COLOR_ORACLE.md`
contains every result and retained artifact.

## Selected secondary column

The selected secondary column is stored in `djmdSort.Disable` bit 1:

```sql
SELECT ID
FROM djmdSort
WHERE rb_local_deleted = 0 AND (Disable & 2) = 2;
```

The copied database returns sort ID 12, Key. Rekordbox clears the selection with
`Disable = Disable & ~0x02` and selects a row with
`Disable = Disable | 0x02`. Bit 0 and bit 1 are independent, so a secondary
column can be selected while remaining visible (`Disable = 2`) or hidden
(`Disable = 3`). See `SECONDARY_COLUMNS.md` for row rendering.

The read query has no `ORDER BY` and the renderer consumes only its first row.
Zero selected rows produce title-only type `0x0004`; multiple selected rows
violate the single-selection invariant and have order-dependent behavior. The
fixture settings format uses `secondary_sorts: []` and
`secondary_sorts: [7, 12]` to preserve these invalid states for oracle tests.

### Live secondary settings sweep

The 15 valid oracle fixtures combine three explicit mutations on the selected
row: set selection bit `0x02`, clear visibility-disable bit `0x01`, and set
`Seq = 20`. Rekordbox repeatably reflected all three **[OBS, DB]**:

- a base-visible row moved from its normal position to the end of the 11-row
  Sort menu;
- Comment, Time, Remixer, Original Artist, Bitrate, or Color changed from
  hidden to a twelfth visible row at the end;
- track rows used the selected row's exact composite type and value source.

The no-selection fixture produced title-only `0x0004` rows. The fixture with
Comment and Key selected chose Comment twice. Because the selection query has
no order clause, the latter pins this fixture's behavior rather than defining a
portable priority rule. `SECONDARY_COLUMN_ORACLE.md` contains every emitted
row value and retained golden.

The combined valid fixtures do not answer whether selection bit `0x02` alone
overrides a still-set visibility bit. The recorded hidden-selected Comment
fixture shows that it does not: the row stays out of the Sort menu while its
values render on track rows **[OBS, DB]**.

### Reader and writer ownership

The Preferences model and the Link Export row builder read the same bit through
different code paths **[DEC]**:

1. `AppSyncDBController::getSortSetting` executes
   `select * from djmdSort where rb_local_deleted = 0 order by Seq`. It builds
   the settings lists from every row, tests `Disable & 1` for visibility, and
   separately appends every row satisfying `Disable & 2` to a selected-ID
   array. It returns the first selected ID in `Seq` order. Two or more selected
   rows produce the diagnostic `ERROR Right Column multiply-selected` but do
   not make the read fail.
2. The Link Export track-row builder queries
   `select ID from djmdSort where rb_local_deleted = 0 and (Disable & 2) = 2`
   only when the render path enables configured fallback and supplies no
   explicit selector. That query has no `ORDER BY` and consumes row zero.
   Therefore the Preferences reader's `Seq`-ordered first ID must not be used
   to define the server's behavior for a corrupted multiple-selection state.
3. Six-argument RX3 rendering after a non-default track sort uses the active
   list builder's materialized right-column role. It does not run the persisted
   fallback query. Default sort does run that fallback, which is why the
   configured Column reappears there.

The AppSync writer normally preserves the single-selection invariant in a
transaction. `resetSubColumn` clears bit `0x02` only on nondeleted rows that
currently carry it:

```sql
update djmdSort
set Disable = (Disable & ~0x02),
    rb_data_status = case when usn != 0 then 257 else 0 end,
    rb_local_usn = __RB_LOCAL_USN__,
    updated_at = CURRENT_TIMESTAMP
where rb_local_deleted = 0 and (Disable & 0x02)
```

`setSubColumn(id)` first invokes the controller's reset operation, then sets
bit `0x02` on the requested nondeleted ID and updates the same synchronization
fields. It also advances per-row local-USN bookkeeping for the other
nondeleted sort rows. Selection therefore preserves visibility bit `0x01`, and
the supported UI path cannot create the zero/multiple-selection fixtures used
by the invalid-state oracle. Those states require an out-of-band database
mutation **[DEC, OBS]**.

The generated trace is
`data/static-analysis/subcolumn-controller-paths.disasm.txt`. It covers the
Dev SQLite, AppSync, and desktop routing implementations from the pinned
7.2.19 x86-64 executable; the conformance test regenerates it byte-for-byte and
pins every SQL/control-flow claim above.

## Color labels

The recorded custom-color fixture changes color IDs 1 and 8 to `Fixture
Magenta` and `Fixture Violet`. Rekordbox returns those strings in the Color
root and on tracks using Color as the selected secondary column. IDs, order,
and unaffected labels remain stable **[OBS, DB]**. See
`SORT_AND_COLOR_ORACLE.md` for the exact rows and rbxport differences.

## Played-track presentation state

Played highlighting is a separate configuration and runtime surface from the
encrypted library tables. `SettingIF` reads `PlayedTrackOption` and
`LinkPlayedTrackOption`. `PlayedSettingFile` configures a JUCE properties file
with application name `AnotherHistories`, suffix `xml`, folder
`Pioneer/rekordbox6`, and macOS library subfolder `Application Support`. Its
`MASTER` XML children are grouped into ordinary and `LINK` sets. A false
ordinary option admits the ordinary set; a false Link option admits the Link
set. Loading returns without reading when both options are true. Saving first
attempts to delete the prior file, then recreates only the sets whose option is
false; two true options leave it deleted **[DEC]**.

During main-database initialization, `getPlayedTracks` supplies both ID arrays
to `rekordboxDBController::setInitialPlayedStatus`. Ordinary IDs set
`RowDataTrack +0x3f8` bit `0x08`; Link IDs set bit `0x10`. Runtime
`updatePlayedStatus(content_id, state, link)` selects and updates the same two
bits. The Link ID set is then copied through `DatabaseIF::getAllLinkPlayed` and
`PSvDBServer::NotifyLibraryUpdatedPlayed` into the Link Export server.

The runtime producers and clearers are also exact. Desktop playback history
calls `updatePlayedStatus(content_id, true, false)`. Link-history update type 1
calls `updatePlayedStatus(content_id, true, true)` and update type 2 calls it
with `false, true`; either successful Link change sends database-server
notification `0x12`. Per-track Link-history deletion clears the affected Link
bits, whole-history deletion can clear every Link bit, and the played-color UI
reset calls `DatabaseIF::clearAllLinkPlayedStatus` in Link mode **[DEC]**.

This state has two protocol surfaces: track-list argument 7 uses bit `0x100`,
and `0x3b03` `CMD_GET_PLAYSTATE` returns `2` when a ContentID is in the
Link-played snapshot. The XDJ-RR client requests that scalar at location 1 and
stores its low byte as the browse row's play-state flags **[DEC, RR-DEC]**.
`ROW_LAYOUT.md` records the renderer path. The 19-case live state-transition
oracle in `conformance/suites/link-played-state.json` is queued as generation
`ah18`. It uses deterministic reset-option settings, two fresh fixture/process
passes, and exact restoration of the guest settings and `AnotherHistories.xml`.
Its canonical golden remains pending, so exact Windows transition and refresh
timing remain open.

The process-restart persistence boundary is declared separately. The
`link-played-persistence-prime.json` and
`link-played-persistence-restart.json` suites cross all four combinations of
the ordinary and Link options. Each run primes one Link ContentID, closes
Rekordbox through an accepted main-window close without force-terminating the
main process, retains the resulting `AnotherHistories.xml`, and observes both
protocol state channels after starting a distinct Rekordbox PID against the
same database. Guarded generation `ai18` repeats each combination from a fresh
fixture and restores the original guest files; its live result is pending.

The independent Link-server refresh boundary is declared in
`link-played-link-toggle-post.json`. Generation `aj18` primes one Link-played
ID, then compares uninterrupted controls with supported LINK deactivation and
reactivation while retaining one Rekordbox PID. Port 12523 must disappear and
return in the toggle arm. Both scalar and row-bit observations are recorded
after the boundary without assigning an expected state in advance.

Multi-player ownership is a separate queued boundary. Generation `ak18` runs
simultaneous RX3 player-1 and player-2 discovery packets from distinct isolated
addresses. Player-correct setup device numbers and packed contexts alternate
two inserts and two removals. Both scalar and row-bit representations bracket
every mutation, while five checkpoints require both identity processes and the
single Rekordbox process to remain stable. The declaration does not assume
whether the Link-played cache is global or partitioned.

## Refresh and mutation boundary

Symbols and SQL strings establish read and write paths including
`getCategorySetting`, `getSortSetting`, `selectRawCategorySetting`,
`selectRawSortSetting`, `updateAllCategory`, and `setAllSort`. Static evidence
is now bounded by a live UI experiment. Preferences -> DJ System exposes
Category, Sort, and Column tabs. All three display `Not allowed while link is
active.` and disable their controls during an active Link session. After LINK
is deactivated, all three setting families are consumed by the next Link
session in the same rekordbox process **[OBS, DB]**. Key-to-Comments produces
Comment-backed `0x2304` rows; moving Album inactive removes it from the 19-row
root; moving Comments active appends it as the twelfth Sort row. The UI writes
Album as `(Seq=0, Disable=1)` and Comments as `(Seq=12, Disable=0)`.
`SETTINGS_SESSION_REFRESH_ORACLE.md` contains the complete sequences, typed
responses, lifecycle proof, and encrypted database/WAL snapshot.
