# Secondary-column oracle results

This chapter records the live rekordbox 7.2.19 results for every persisted
track-list secondary-column selection. `SECONDARY_COLUMNS.md` explains the
implementation and database path; this document is the capture ledger. Every
row below comes from a deterministic encrypted settings fixture, was recorded
through the real port-query and RemoteDBServer protocol, and matched an
immediate second execution against the same golden **[OBS, DB]**.

## Corpus and provenance

The oracle corpus contains 17 settings goldens:

- 15 valid selections, one for every selectable `djmdSort` row;
- one database with no row carrying secondary-selection bit `0x02`;
- one invalid database with both Comment and Key carrying the bit.

The valid suites contain a complete Sort menu and all eight deterministic track
rows. The two invalid-state suites contain the eight track rows. Together they
add 32 extended-setup case executions. The matching 15-suite legacy matrix adds
30 recorded case executions using the same fixtures and case IDs. All 15
variants have fresh-fixture/process repeat receipts, and the strict validator
accepted every legacy row as the exact 12-field prefix of its 16-field extended
partner **[OBS, DB]**.

Canonical evidence is in:

```text
conformance/goldens/rekordbox-7.2.19/xdj-rx3/secondary-*.json
conformance/goldens/rekordbox-7.2.19/xdj-rx3/no-secondary-selection.json
conformance/goldens/rekordbox-7.2.19/xdj-rx3/multiple-secondary-selections.json
conformance/fixtures/generated/<variant>/manifest.json
conformance/suites/generated/secondary-*-legacy.json
data/experiments/secondary-column-legacy/repeats/*.json
data/experiments/secondary-column-legacy/summary.json
```

Each golden embeds the suite hash, fixture fingerprint, encrypted database
hash, client identity, rekordbox version, setup form, complete typed messages,
and recording time. Repeat verification compares the normalized behavior
envelope rather than timestamps or backend labels.

## Active sort with RX3 six-argument rendering

The focused `sort-secondary-render-6.json` oracle crosses every sort visible
in the captured RX3 Sort menu. Each case sends `0x1004 [context, sort]`, then
renders every page as:

```text
0x3000 [context, offset, count, 0, 8, 12]
```

The final render argument remains `12` in all 33 page requests. The active sort
alone changes the materialized right column. These are the exact fields for
the same track, `Alpha One`; using one track avoids confusing a column change
with the different first row produced by Rating, Date Added, and Play Count
ordering **[OBS]**:

| Sort | Argument 0 | Argument 5 | Argument 6 | Arguments 12-15 |
| --- | ---: | --- | ---: | --- |
| Default | `5001` | `Am - 120.0 bpm` | `0x0f04` | `5001, 6, "Am", 12000` |
| Alphabet | `0` | `Alpha One` | `0x0404` | `5001, 6, "Am", 12000` |
| Artist | `0` | `Alpha Artist` | `0x0704` | `5001, 6, "Am", 12000` |
| Album | `0` | `Album One` | `0x0204` | `5001, 6, "Am", 12000` |
| BPM | `12000` | `120.0 bpm - Am` | `0x0d04` | `5001, 6, "Am", 12000` |
| Rating | `0` | empty | `0x0a04` | `5001, 6, "Am", 12000` |
| Genre | `0` | `Fixture House` | `0x0604` | `5001, 6, "Am", 12000` |
| Label | `0` | `Fixture Label One` | `0x0e04` | `5001, 6, "Am", 12000` |
| Key | `14` | `Am - 120.0 bpm` | `0x0f04` | `5001, 6, "Am", 12000` |
| Date Added | `0` | `2021-02-02` | `0x2e04` | `5001, 6, "Am", 12000` |
| DJ Play Count | `0` | empty | `0x2a04` | `5001, 6, "Am", 12000` |

Argument 0 is path-dependent. Active lookup sorts use the builder's zero sort
key rather than the entity ID returned by the dynamic eight-argument
extractor. Active Key uses normalized sort key `14`, while persisted-Key
Default uses raw `KeyID` `5001`. Arguments 12-15 remain independent content
metadata: original KeyID, key-string byte length, key spelling, and BPM x100.

The generated `data/secondary-column-semantics.json` joins this active-sort
matrix with every persisted profile, eight-argument control, and active-sort
eight-argument persisted fallback for the same track. Its 63 profiles contain
504 row projections. Fields 12-15 remain
path-invariant for every track. Persisted versus
explicit override differs for BPM alone, at argument 5: cached persisted BPM
is `120.0 bpm - Am`, while dynamic BPM extraction from a Key-materialized list
is empty. Shared persisted/active-sort profiles differ only in argument 0 for
Artist, Album, Genre, Label, Key, and Date Added **[OBS]**.
The all-track comparison confirms BPM argument 5 as the only persisted/override
difference on all eight rows; nonzero numeric-column rows add no exception.

The 18-case active-sort fallback cross renders with
`[context, offset, count, 0, total, 12, 1, 0]`. The zero selector reads
persisted Key. Default and Key sort retain cached `Key - BPM`; the other 16
sorts dynamically reconcile the requested Key against a different materialized
column and return Key alone. Against the matching six-argument cases, Default
and Key are row-identical, while the other nine shared visible sorts differ in
fields 0, 5, and 6 on every track **[OBS]**.

The retained physical RX3 PCAP contains three Default-track pairs with
`0x1004 [0x0b010401, 0]` followed by exactly
`0x3000 [0x0b010401, 0, 12, 0, 4342, 12]`. It also establishes legacy setup
device 11 and root mask `0x05fdffff`. An earlier keepalive-only synthetic
session rejected the player-11 packed context, so the completed semantic sort
oracle isolates the render rule with admitted context `0x01010301`. The
separate `physical-rx3-session-envelope` suite now replays the native context,
mask, setup width, and six-argument form under the captured status-backed
player-11 identity. Its outcomes are deliberately unconstrained until real
7.2.19 record/repeat completes. The physical capture establishes the native
request form; the completed controlled oracle establishes that no changing
render field is required for the sort-driven response change **[CAP, OBS]**.

Canonical evidence is retained together:

```text
conformance/suites/generated/sort-secondary-render-6.json
conformance/goldens/rekordbox-7.2.19/xdj-rx3/sort-secondary-render-6.json
data/experiments/sort-secondary-render-6/summary.json
data/experiments/sort-secondary-render-6/rows.csv
data/experiments/sort-secondary-render-6/receipt.json
data/experiments/sort-secondary-render-6/finalization.json
data/experiments/sort-secondary-render-6/physical-rx3-requests.json
data/experiments/sort-secondary-render-6/source-rx3-rekordbox-working-ap-20260927.pcap
data/experiments/physical-rx3-session/session-envelope.json
conformance/suites/generated/physical-rx3-session-envelope.json
```

The golden contains all 88 complete `0x4101` rows. Record and repeat each used
a fresh fixture and Rekordbox process; the finalization receipt binds the
suite, fixture, identity, golden, summary, CSV, decoded physical requests, and
source PCAP by SHA-256.

## Observed row matrix

The values below are the first deterministic track, `Alpha One`. Numeric-only
columns intentionally leave argument 5 empty: the player formats argument 0
according to the high byte of argument 6. Lookup and string columns carry both
the raw key in argument 0 and server-authored display text in argument 5.

| Sort ID | Selection | Argument 0 | Argument 5 | Argument 6 | Sort-menu effect |
| ---: | --- | ---: | --- | ---: | --- |
| 2 | Artist | `1001` | `Alpha Artist` | `0x0704` | Move ID 2 to end |
| 3 | Album | `2001` | `Album One` | `0x0204` | Move ID 3 to end |
| 4 | BPM | `12000` | `120.0 bpm - Am` | `0x0d04` | Move ID 4 to end |
| 5 | Rating | `0` | empty | `0x0a04` | Move ID 5 to end |
| 6 | Genre | `3001` | `Fixture House` | `0x0604` | Move ID 6 to end |
| 7 | Comment | `10001` | `comment-1` | `0x2304` | Append ID 7 |
| 8 | Time | `59` | empty | `0x0b04` | Append ID 8 |
| 9 | Remixer | `1003` | `Fixture Remixer` | `0x2904` | Append ID 9 |
| 10 | Label | `4001` | `Fixture Label One` | `0x0e04` | Move ID 10 to end |
| 11 | Original Artist | `1004` | `Fixture Original` | `0x2804` | Append ID 11 |
| 12 | Key | `5001` | `Am - 120.0 bpm` | `0x0f04` | Move ID 12 to end |
| 13 | Bitrate | `0` | empty | `0x1004` | Append ID 13 |
| 15 | Color | `1` | `Pink` | `0x1404` | Append ID 15 |
| 16 | DJ Play Count | `0` | empty | `0x2a04` | Move ID 16 to end |
| 17 | Date Added | `10001` | `2021-02-02` | `0x2e04` | Move ID 17 to end |

Argument 12 remains the track's original `KeyID` and argument 14 remains its
key spelling for every selection. On the first row they are `5001` and `Am`.
Argument 15 remains BPM x100 (`12000`). Changing the right column does not
repurpose these extended-row compatibility fields **[OBS]**.

Legacy setup removes arguments 12 through 15 only at serialization. Argument 5
and the packed composite type in argument 6 are unchanged for all 15 persisted
selections. In particular, BPM still carries `120.0 bpm - Am` under `0x0d04`,
and Key still carries `Am - 120.0 bpm` under `0x0f04` **[OBS]**.

The numeric sweeps prove that argument 0 carries the unformatted database
value:

| Column | Eight observed argument-0 values |
| --- | --- |
| Bitrate | `0, 32, 128, 160, 192, 1411, 256, 320` |
| BPM | `12000, 12050, 12100, 12150, 12200, 12350, 12250, 12300` |
| DJ Play Count | `0, 1, 2, 3, 4, 7, 5, 6` |
| Rating | `0, 1, 2, 3, 4, 1, 5, 0` |
| Time | `59, 60, 61, 599, 600, 10800, 601, 10799` |

Color's high byte is value-dependent. Color ID 1 produces `0x1404`; IDs 1-8
produce `0x1404` through `0x1b04`, while zero/255 use base `0x1304`. The table
therefore records the first row rather than a column-wide constant.

## Sort-menu coupling

The normal fixture order is:

```text
0, 1, 2, 3, 4, 5, 12, 10, 6, 17, 16
```

Every valid settings fixture both clears visibility-disable bit `0x01` and
assigns sequence 20 on the row whose selection bit `0x02` is set. Rekordbox
then applies the configured visibility and sequence exactly **[OBS]**:

1. If the selected ID is already visible, remove it from its current position
   and append it. The menu still has 11 rows.
2. If the selected ID is normally hidden, append it. The menu grows to 12 rows.

The rows normally hidden in the base fixture are Comment 7, Time 8, Remixer 9,
Original Artist 11, Bitrate 13, and Color 15. These experiments prove the
combined selected+enabled+sequence-20 state. They do not imply that selection
bit `0x02` alone overrides visibility bit `0x01`; the hidden-selected fixture
exists to test that independent combination.

The 11 base-visible menu IDs expose separate label/item-type mappings. A row
explicitly enabled by the settings fixture becomes a normal sort choice and
can be sent back as a track request sort ID. Independent visibility, selection,
and sequence fixtures prove that `Disable & 1`, selection bit `Disable & 2`,
and `Seq` compose without one field overriding the others. See
`SORT_AND_COLOR_ORACLE.md` **[OBS, DB]**.

## Missing selection

With no `djmdSort` row carrying bit `0x02`, rekordbox still returns all eight
tracks. Each row is title-only **[OBS]**:

```text
argument 0 = 0
argument 4 = 2
argument 5 = ""
argument 6 = 0x0004
```

The extended compatibility fields remain populated: argument 12 is the
original KeyID, argument 14 is the key spelling, and argument 15 is BPM x100.
This is a first-class wire state, not an error, empty menu, or request timeout.

## Multiple selections

The invalid fixture marks Comment (sort ID 7) and Key (sort ID 12) selected.
Across the recording and immediate repeat, rekordbox chose Comment **[OBS]**:

```text
argument 0 = djmdContent.ID
argument 5 = djmdContent.Commnt
argument 6 = 0x2304
```

The decompiled query has no `ORDER BY` and the implementation consumes row
zero. The observed winner is therefore deterministic for this fixture and
SQLite layout, but is not a portable precedence guarantee. A conforming fixture
builder normally enforces exactly one selected row; this fixture exists to pin
rekordbox's failure mode.

This is the Link Export builder/renderer rule, not the Preferences reader's
rule. Preferences queries all nondeleted rows in `Seq` order, returns the first
selected ID in that order, and logs `ERROR Right Column multiply-selected` for
this state. `CONFIGURATION.md` and the reproducible
`subcolumn-controller-paths.disasm.txt` trace separate those owners **[DEC]**.

## Frozen historical rbxport replay

This retained comparison predates the current real-Rekordbox-only phase. It is
provenance for later backend replay and is not executed or extended by the
active recorder queue.

`conformance/replay_rbxport.py` now declares the effective secondary column and
sort order per suite. The same 17 suites run through the loopback-only adapter
against the fingerprinted rbxport tree `c144f19+tree.80e87ec8aace` **[RBX,
OBS]**.

All 32 cases execute. Twenty-six preserve outcome, total, and row-count shape;
none is field-exact. The main measured differences are:

- rbxport has no absent-secondary representation. The no-selection replay uses
  Comment as an explicit runnable control and records the resulting title-row
  mismatch.
- rbxport can configure its 11 ordinary sorts but cannot advertise Comment,
  Time, Remixer, Original Artist, Bitrate, or Color as selected appended sort
  choices. Those six Sort menus differ in total as well as row content.
- rekordbox sends zero-argument extended footers; rbxport appends two numeric
  zero arguments.
- rbxport overwrites extended argument 12 with column-dependent/artwork data in
  several selections, while rekordbox always preserves the original KeyID.
- The retained backend comparison used Rekordbox's Classic local-device style,
  yielding `Am` and `C`, while the compared backend rows used `8A` and `8B`.
  The newer Alphanumeric Rekordbox oracle is intentionally not replayed yet.
- Numeric and lookup formatting differs for several columns even where the
  composite type, membership, and pagination shape agree.

Field-level evidence is retained as
`conformance/results/rbxport/c144f19+tree.80e87ec8aace/xdj-rx3/<suite>.diff.txt`.
The machine summary records each suite's adapter column and sort list.

## Reproduction

Generate declarations and fixtures from the workspace root:

```sh
python3 rekordbox-link-export-research/conformance/generate_matrices.py

for variant in secondary-album secondary-artist secondary-bitrate secondary-bpm \
  secondary-color secondary-comment secondary-date-added secondary-genre \
  secondary-key secondary-label secondary-original-artist secondary-play-count \
  secondary-rating secondary-remixer secondary-time no-secondary-selection \
  multiple-secondary-selections; do
  rekordbox-windows/.venv/bin/python \
    rekordbox-link-export-research/conformance/build_fixture.py settings \
    rekordbox-windows/shared/library/master.db \
    /mnt/documents/multimedia/djing/rekordbox/options.json \
    "rekordbox-link-export-research/conformance/fixtures/generated/$variant" \
    --settings-file \
    "rekordbox-link-export-research/conformance/settings/generated/$variant.json"
done
```

Recording uses the isolated VM only:

```sh
cd /home/evan/workspace/rx3-research/rekordbox-link-export-research
./conformance/record_settings_batch.sh <variant> [<variant> ...]
```

The batch refuses to overwrite a golden, atomically installs the fixture while
rekordbox is stopped, launches the UI in the logged-in Windows session, emits a
fresh synthetic identity, activates LINK, records, and immediately verifies.
The synthetic identity must be fresh for each application start; rekordbox can
retain a departed player's state long enough that reusing an identity without a
restart leaves LINK visible but the port-query service unavailable.

Replay every recorded golden against rbxport:

```sh
cd /home/evan/workspace/rx3-research/rekordbox-link-export-research
python3 conformance/replay_rbxport.py --no-build
```

The adapter binds only `127.0.0.1`; the real oracle path requires the separate
isolated-network gate documented in `CONFORMANCE.md`.
