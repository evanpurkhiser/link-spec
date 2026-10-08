# Category configuration oracle

This chapter records the live rekordbox 7.2.19 category-settings sweep. It
complements the static predicate and capability-mask analysis in
`CONFIGURATION.md` with deterministic, repeat-verified database mutations.

## Experiment envelope

Every run used the XDJ-RX3 player-11 identity, extended setup, context
`0x01010301`, sort ID 12, and root capability mask `0x05cfffff`, except the
explicit all-bits special case. Each fixture starts from the same eight-track
`settings` profile and changes only the named `djmdCategory` fields. The VM ran
on the private `172.31.96.0/24` lab network with no route to the physical RX3.

For every fixture the recorder stopped rekordbox, installed and
integrity-checked the encrypted `master.db`, launched rekordbox under the
sampler-write guard, emitted a fresh synthetic-player identity, recorded the
root and Display Song Info requests, and repeated the complete suite with exact
canonical equality.

The manifests are under `conformance/fixtures/generated/`, generated suites
under `conformance/suites/generated/`, and canonical recordings under
`conformance/goldens/rekordbox-7.2.19/xdj-rx3/category-*.json`. The fixtures
can be rebuilt with `conformance/build_settings_fixtures.sh --all`.

## Baseline root

The baseline contains 21 active `djmdCategory` rows. Folder is filtered after
the visibility predicate, so the wire menu has 20 rows:

```text
Track, Key, BPM, Genre, Artist, Album, Matching, Search, Playlist, History,
Bitrate, Color, File Name, Hot Cue Bank, Label, Original Artist, Rating,
Remixer, Time, Year
```

The root response header reports the same total rendered by the paged rows.
Each row's selector is its `djmdCategory.ID`, not its `MenuItemID`.

## Individual disable sweep

Each fixture sets `Disable = 1` on exactly one persisted category row. Twenty
fixtures remove exactly the associated visible row and reduce the total from
20 to 19. Category 17 targets Folder and remains a 20-row no-op because Folder
is already suppressed by root construction. Unaffected rows preserve their
relative order and complete typed contents.

| Category ID | Menu item | Baseline `Seq` | Observed result |
| ---: | --- | ---: | --- |
| 1 | Genre | 4 | Genre removed; total 19 |
| 2 | Artist | 5 | Artist removed; total 19 |
| 3 | Album | 6 | Album removed; total 19 |
| 4 | Track | 1 | Track removed; total 19 |
| 5 | Playlist | 9 | Playlist removed; total 19 |
| 6 | BPM | 3 | BPM removed; total 19 |
| 7 | Rating | 18 | Rating removed; total 19 |
| 8 | Year | 21 | Year removed; total 19 |
| 9 | Remixer | 19 | Remixer removed; total 19 |
| 10 | Label | 16 | Label removed; total 19 |
| 11 | Original Artist | 17 | Original Artist removed; total 19 |
| 12 | Key | 2 | Key removed; total 19 |
| 15 | Color | 13 | Color removed; total 19 |
| 17 | Folder | 11 | No wire change; total 20 |
| 18 | Search | 8 | Search removed; total 19 |
| 19 | Time | 20 | Time removed; total 19 |
| 20 | Bitrate | 12 | Bitrate removed; total 19 |
| 21 | File Name | 14 | File Name removed; total 19 |
| 22 | History | 10 | History removed; total 19 |
| 23 | Hot Cue Bank | 15 | Hot Cue Bank removed; total 19 |
| 26 | Matching | 7 | Matching removed; total 19 |

The non-contiguous category IDs are database identities. Missing IDs are not
implicit categories and disabling a category does not renumber selectors.

## Display Song Info flags

The same 21 one-variable fixtures were recorded through
`2002 [context, content_id]`. Every response retained all 16 rows in ordinary
order. A disabled category clears argument 0 from `1` to `0` on the associated
simple metadata row; it does not remove that row **[OBS]**.

| Category ID | MenuItemID | Setting label | Display row type | Argument 0 result |
| ---: | ---: | --- | ---: | --- |
| 1 | 1 | Genre | `0x06` | `0` |
| 2 | 2 | Artist | `0x07` | `0` |
| 3 | 3 | Album | `0x02` | `0` |
| 4 | 4 | Track | title `0x0f04` | Complete row unchanged |
| 5 | 17 | Playlist | none | Complete list unchanged |
| 6 | 5 | BPM | `0x0d` | `0` |
| 7 | 6 | Rating | `0x0a` | `0` |
| 8 | 7 | Year | `0x11` | `0` |
| 9 | 8 | Remixer | `0x29` | `0` |
| 10 | 9 | Label | `0x0e` | `0` |
| 11 | 10 | Original Artist | `0x28` | `0` |
| 12 | 11 | Key | `0x0f` | `0` |
| 15 | 13 | Color | `0x14` | `0` |
| 17 | 24 | Folder | none | Complete list unchanged |
| 18 | 20 | Search | none | Complete list unchanged |
| 19 | 14 | Time | `0x0b` | `0` |
| 20 | 15 | Bitrate | `0x10` | `0` |
| 21 | 16 | File Name | none | Complete list unchanged |
| 22 | 19 | History | none | Complete list unchanged |
| 23 | 18 | Hot Cue Bank | none | Complete list unchanged |
| 26 | 27 | Matching | none | Complete list unchanged |

The eleven rows shown with `0` differ from the baseline only at argument 0.
The other ten complete row arrays are byte-for-byte equal to baseline. The
title row is a special composite track row: its argument 0 remains KeyID
`5001`, rather than exposing the category-membership boolean used by simple
metadata rows.

Comment (`MenuItemID 21`) and Date Added (`MenuItemID 22`) have no persisted
category row in this fixture, so their argument 0 is already `0` in every
recording. Their absence does not suppress either metadata row. Static
inspection agrees with the wire result: the AppSync builder collects enabled
`MenuItemID` values, then each simple-row insertion checks membership and
stores the boolean in the field serialized as argument 0 **[DEC, OBS]**.

## Sequence order

`category-order-reversed` assigns sequence values 1 through 21 in reverse
category-table order. Rekordbox returns the 20 visible rows in exact ascending
`Seq` order while still suppressing Folder:

```text
Matching, Hot Cue Bank, History, File Name, Bitrate, Time, Search, Color,
Key, Original Artist, Label, Remixer, Year, Rating, BPM, Playlist, Track,
Album, Artist, Genre
```

No independent presentation order is imposed by menu-item identity, class,
label, or selector. This also demonstrates that Folder is removed after the
ordered category query rather than occupying a visible placeholder.

## Disable bits and masks

`category-special-bits` makes three controlled changes:

| Category | Mutation | Result |
| --- | --- | --- |
| Matching (26) | `Disable = 2`, `Seq = 1` | Visible and first |
| Track (4) | `Disable = 1`, `Seq = 2` | Hidden |
| Hot Cue Bank (23) | `Disable = 1`, `Seq = 3` | Hidden |

Both the controlled lab mask `0x05cfffff` and `0xffffffff` return the identical
18-row menu. Capability bits therefore cannot re-enable a database-hidden
ordinary row. Matching's bit-1 value remains visible, confirming its special
`Disable & 1` predicate in a live run. The experiment does not add a Date
Added category row, so Date Added's special `Disable == 1` rule remains static
evidence rather than a live settings result.

The legacy `0x00ffffff` Hot Cue Bank synthesis branch is intentionally outside
this fixture. Its exact behavior is covered by the root-capability oracle.

## Protocol invariants

Across the sweep, only membership, total, and explicitly changed sequence
position vary. Setup negotiation, response kinds, page framing, category
selectors, localization-token strings, row classes, empty fields, and footer
shape remain stable. A disabled row is omitted rather than returned with a
disabled marker. The server provides no placeholder or error identifying the
hidden category.

The generated suites request pages in chunks of three through the normal
recorder, so the goldens also pin membership across page boundaries. Immediate
independent verification matched all 45 cases in all 23 suites.

## rbxport replay

`conformance/replay_rbxport.py` replays all 23 category suites against the
same fixture databases. The current rbxport adapter exposes a fixed root and
does not consume `djmdCategory` visibility or ordering settings. Consequently:

- none of the 45 category cases is field-exact;
- all 21 Display Song Info cases preserve outcome, total, and row count while
  differing in populated row fields;
- category 17's Folder-disable no-op preserves outcome, total, and row count;
- reversed ordering preserves outcome, total, and row count while row order
  differs;
- every visible-row disable and both special-bit cases differ in row count.

The retained replay is
`conformance/results/rbxport/c144f19+tree.80e87ec8aace/`; each suite has an
actual JSON result, run log, and readable diff. Implementing category settings
in rbxport requires loading active `djmdCategory` rows, applying the exact
visibility predicate and request mask, sorting by `Seq`, suppressing Folder,
and preserving the legacy Hot Cue Bank branch.

## Reproduction

With the isolated VM already running and prepared:

```sh
./conformance/build_settings_fixtures.sh --all
./conformance/refresh_category_display_batch.sh
python3 conformance/replay_rbxport.py
```

The recorder requires real rekordbox and the isolation gate. The replay binds
only to loopback and requires no VM or media files.
