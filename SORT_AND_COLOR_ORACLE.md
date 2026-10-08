# Sort and color configuration oracle

This chapter records the live rekordbox 7.2.19 sweep of `djmdSort` visibility
and order, the independence of sort visibility from secondary-column
selection, and custom `djmdColor` labels. Static construction details remain in
`CONFIGURATION.md`; secondary value formats remain in
`SECONDARY_COLUMN_ORACLE.md`.

## Experiment envelope

The oracle used the deterministic eight-track `settings` fixture, the isolated
XDJ-RX3 player-11 identity, extended setup, context `0x01010301`, and no media
files. Each encrypted database was installed while rekordbox was stopped. Every
case was then recorded through the real port-query and dbserver sockets and
immediately repeated with exact canonical equality.

Artifacts are retained as:

```text
conformance/fixtures/generated/sort-*-toggled/
conformance/fixtures/generated/sort-order-reversed/
conformance/fixtures/generated/hidden-selected-comment/
conformance/fixtures/generated/custom-colors/
conformance/goldens/rekordbox-7.2.19/xdj-rx3/sort-*.json
conformance/goldens/rekordbox-7.2.19/xdj-rx3/hidden-selected-comment.json
conformance/goldens/rekordbox-7.2.19/xdj-rx3/custom-colors.json
```

## Baseline sort menu

The baseline has 17 active `djmdSort` rows. Eleven are visible and six carry
visibility-disable bit `0x01`:

```text
Default, Alphabet, Artist, Album, BPM, Rating, Key, Label, Genre,
Date Added, DJ Play Count
```

Key has `Disable = 2`: selected as the secondary column and visible. Hidden
rows have `Disable = 1`. Visibility is therefore exactly bit 0 and selection
is independently bit 1.

## Sort affects RX3 track-row presentation

Sort ID is not only an ordering input. In the real-Rekordbox
`sort-secondary-render-6` cross, each non-default `0x1004` request materializes
the matching right-column role, and a following six-argument `0x3000` preserves
it. Artist, Album, Genre, Label, and Date Added return one text value; Rating
and DJ Play Count return a numeric argument 0 with empty argument 5; BPM returns
`BPM - Key`; Key returns `Key - BPM`; Alphabet returns Title under composite
type `0x0404`. Default alone retains the persisted Rekordbox Column selection.

All render pages kept final argument `12`. The physical RX3 capture also uses
six arguments and value `12` for Default track browsing. The observed response
change therefore does not require a sort-dependent render argument. Exact
arguments 0, 5, 6, and 12-15 are in `SECONDARY_COLUMN_ORACLE.md` **[OBS]**.

## Individual visibility sweep

Each fixture flips visibility bit 0 on exactly one sort row without changing
its other bits or sequence. Visible rows disappear and reduce the total from
11 to 10. Hidden rows appear and increase the total to 12. All hidden rows have
persisted `Seq = 0`, so newly visible rows sort before Default.

| Sort ID | Menu item | Baseline | `Seq` | Observed toggle |
| ---: | --- | --- | ---: | --- |
| 0 | Default | Visible | 1 | Removed; total 10 |
| 1 | Alphabet | Visible | 2 | Removed; total 10 |
| 2 | Artist | Visible | 3 | Removed; total 10 |
| 3 | Album | Visible | 4 | Removed; total 10 |
| 4 | BPM | Visible | 5 | Removed; total 10 |
| 5 | Rating | Visible | 6 | Removed; total 10 |
| 6 | Genre | Visible | 9 | Removed; total 10 |
| 7 | Comments | Hidden | 0 | Inserted first; total 12 |
| 8 | Time | Hidden | 0 | Inserted first; total 12 |
| 9 | Remixer | Hidden | 0 | Inserted first; total 12 |
| 10 | Label | Visible | 8 | Removed; total 10 |
| 11 | Original Artist | Hidden | 0 | Inserted first; total 12 |
| 12 | Key | Visible, selected | 7 | Removed from menu; total 10 |
| 13 | Bitrate | Hidden | 0 | Inserted first; total 12 |
| 15 | Color | Hidden | 0 | Inserted first; total 12 |
| 16 | DJ Play Count | Visible | 11 | Removed; total 10 |
| 17 | Date Added | Visible | 10 | Removed; total 10 |

The missing sort ID 14 is not an active row. Toggling Key preserves selection
bit `0x02`, producing `Disable = 3`; the visibility test omits it from the Sort
menu even though it remains selected in the database.

Only membership and total change. Unaffected sort rows retain their selector,
label token, class, typed empty fields, and relative sequence.

## Complete order reversal

`sort-order-reversed` assigns reversed sequence values to all 17 rows without
changing visibility. Rekordbox returns the 11 visible rows in exact ascending
sequence order:

```text
Date Added, DJ Play Count, Key, Label, Genre, Rating, BPM, Album, Artist,
Alphabet, Default
```

Hidden rows do not reserve positions. No menu-item identity or built-in
priority overrides `Seq`.

## Hidden selected column

`hidden-selected-comment` selects Comments with bit `0x02` while retaining its
visibility-disable bit, yielding `Disable = 3`. The two live cases establish
both sides of the independent state:

- the Sort menu remains the ordinary 11 visible rows and omits Comments;
- all eight track rows still render Comment as the secondary column with
  composite type `0x2304` and values `comment-1` through `comment-8`.

This closes the question left by the valid secondary fixtures: selection bit
`0x02` does override neither visibility nor rendering. Each consumer reads its
own bit. A hidden row can be the active secondary column.

## Custom color labels

`custom-colors` changes color ID 1 from Pink to `Fixture Magenta` and color ID
8 from Purple to `Fixture Violet`, explicitly enables Color in the Sort menu,
moves it to sequence 12, and selects it as the secondary column.

The Color root preserves IDs and order while returning the two exact custom
strings. Its protocol string-length fields expand to 32 and 30 bytes,
respectively, including the UTF-16 terminator. The eight track rows retain raw
color IDs in argument 0 and use the same configured strings in argument 5:

| Track | Color ID | Secondary text |
| --- | ---: | --- |
| Alpha One | 1 | Fixture Magenta |
| Alpha Two | 2 | Red |
| Beta One | 3 | Orange |
| Boundary Fifty Nine | 4 | Yellow |
| Boundary Sixty | 5 | Green |
| Maximum Ordinary | 8 | Fixture Violet |
| Unicode Omega Search | 6 | Aqua |
| Unknown Album | 7 | Blue |

Custom labels therefore come from `djmdColor`, not a fixed protocol label
table, for both Color navigation and secondary rendering.

## rbxport replay

The backend-neutral replay supplies the exact representable visible sort list
for each fixture. Rbxport's `Sort` API represents the 11 baseline rows but does
not represent Comments, Time, Remixer, Original Artist, Bitrate, or Color as
sort-menu choices. Those six reveal-toggle suites therefore retain explicit
row-count diffs rather than substituting another type.

Across these 20 suites and 22 cases:

- no case is field-exact;
- 16 cases preserve outcome, total, and row count;
- all ten representable removals and reversed ordering preserve shape;
- all six unrepresentable reveal toggles differ in shape;
- both hidden-selected track and sort cases preserve shape after applying the
  explicit 11-sort control;
- both custom-color cases preserve shape, but rbxport emits fixed Pink/Purple
  labels rather than the database labels.

Track rows also retain the already documented rbxport differences in extended
arguments, footer width, and metadata IDs. Exact actuals and readable diffs are
under `conformance/results/rbxport/c144f19+tree.80e87ec8aace/xdj-rx3/`.

## Reproduction

With the isolated VM prepared:

```sh
./conformance/build_settings_fixtures.sh --all
./conformance/record_settings_batch.sh \
  sort-{00,01,02,03,04,05,06,07,08,09,10,11,12,13,15,16,17}-toggled \
  sort-order-reversed hidden-selected-comment custom-colors
python3 conformance/replay_rbxport.py
```

The first command is idempotent and verifies existing fixtures. The recorder
requires the private VM network and real rekordbox; replay is loopback-only.
