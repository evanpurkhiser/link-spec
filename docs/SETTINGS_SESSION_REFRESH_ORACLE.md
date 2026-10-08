# Settings UI and Link-session refresh oracle

This report records the supported rekordbox 7.2.19 UI for Link Export category,
sort, and secondary-column configuration, and establishes when each setting
family becomes visible to dbserver. The experiments ran in the isolated Windows
guest with deterministic fixtures and the synthetic XDJ-RX3 player-11 identity.
The physical RX3 was unreachable.

## UI location and controls

All three controls are under **Preferences -> DJ System** **[OBS]**:

| Tab | Control | Baseline state |
| --- | --- | --- |
| Category | Inactive/Active Categories lists, transfer buttons, and Active-list up/down buttons | 21 active categories, no inactive categories |
| Sort | Inactive/Active Sort Options lists, transfer buttons, and Active-list up/down buttons | 11 active sorts and 6 inactive sorts |
| Column | `Select item which is shown next to track name on CDJ/XDJ` drop-down | `KEY` |

The Sort UI exactly exposes the database split already established by the
settings fixtures. Its active list is Default, Alphabet/Track Name, Artist,
Album, BPM, Rating, Key, Label, Genre, Date Added, and DJ Play Count. Its
inactive list is Bitrate, Color, Comments, Original Artist, Remixer, and Time
**[OBS, DB]**.

The Column drop-down contains Album, Artist, Bitrate, BPM, Color, Comments,
Date Added, DJ Play Count, Genre, Key, Label, Original Artist, Rating, Remixer,
Time, and Not Specified. This is the 15-value executable secondary matrix plus
the recorded no-selection state **[OBS]**.

Retained UI evidence:

```text
data/rekordbox-preferences-dj-system-category-inactive.png
data/rekordbox-preferences-dj-system-sort-inactive.png
data/rekordbox-preferences-dj-system-column-inactive.png
data/rekordbox-preferences-dj-system-column-options.png
data/rekordbox-preferences-dj-system-column-comments.png
```

## Active-Link lock

When Link is active, opening Category, Sort, or Column darkens the complete tab
and overlays the literal message `Not allowed while link is active.` The current
Column value remains visible but cannot be edited. Deactivating LINK unlocks all
three tabs immediately without restarting rekordbox **[OBS]**.

This is the supported refresh boundary: rekordbox prevents UI configuration
mutation during a live Link session. It does not require an application restart
before the controls can be changed.

Evidence of the lock is retained in:

```text
data/rekordbox-preferences-dj-system-category.png
data/rekordbox-preferences-dj-system-sort-link-active.png
data/rekordbox-preferences-dj-system-column-link-active.png
data/session-refresh/column-comments-link-active.png
```

## Same-process Column refresh

The live sequence was **[OBS]**:

1. Deactivate LINK while keeping the rekordbox application process running.
2. Open Preferences -> DJ System -> Column.
3. Change `KEY` to `COMMENTS`.
4. Close Preferences.
5. Start the isolated XDJ-RX3 identity and reactivate LINK.
6. Connect through port query and dbserver without restarting rekordbox.
7. Request the single Release Year 0 track and render with override gate 1 and
   selector 0, which means use the database-selected Column.

The one-row response has message kind `0x4101`, empty argument 5 because that
fixture row has an empty Comment, and composite type `0x2304` in argument 6.
The prior Key state would produce `0x0f04`. The next Link session therefore
consumes the changed Column selection in the same rekordbox process.
After reinstalling the baseline fixture and starting a new rekordbox process,
the complete UI mutation and Link reactivation sequence was repeated. The
one-case verifier matched the retained typed response exactly **[OBS]**.

The concise declaration and complete typed response are:

```text
data/session-refresh/column-comment-probe.json
data/session-refresh/column-comment-same-process.json
```

The probe deliberately selects one safe row. Rendering all eight boundary rows
with Comment would encounter the independently documented 256-UTF-16-unit
timeout and would obscure the refresh result.

## Same-process Category refresh

Rekordbox remained at PID 8 throughout this sequence **[OBS, DB]**:

1. Start the pristine `full` fixture and wait for the interactive process.
2. With LINK inactive, move Album from Active Categories to Inactive
   Categories.
3. Close Preferences, activate LINK, and request root with mask `0x1000`.
4. Record the response and repeat the identical request immediately.

The UI persisted the Album row as `(ID, MenuItemID, Seq, Disable, InfoOrder) =
('3', '3', 0, 1, 3)`. The encrypted base database remained byte-identical to
the pristine fixture; the mutation was present in its retained WAL. Both
protocol executions returned the same 19 rows in this exact order:

```text
TRACK, KEY, BPM, GENRE, ARTIST, MATCHING, SEARCH, PLAYLIST, HISTORY,
BITRATE, COLOR, FILE NAME, HOT CUE BANK, LABEL, ORIGINAL ARTIST, RATING,
REMIXER, TIME, YEAR
```

Album is absent and every unaffected row retains its baseline position. The
recorded golden has SHA-256
`c673162932788e23ce0adc61f76983472ba5f2772f3413291ce5879cec33f3cc`.

## Same-process Sort refresh

The same PID 8 then executed this sequence **[OBS, DB]**:

1. Deactivate LINK.
2. Move Comments from Inactive Sort Options to Active Sort Options.
3. Close Preferences, activate LINK, and request the Sort menu with kind
   `0x1400`.
4. Record the response and repeat the identical request immediately.

The UI persisted the Comments row as `(ID, MenuItemID, Seq, Disable) =
('7', '21', 12, 0)`: it appends at sequence 12 and clears the visibility bit.
Both protocol executions returned these 12 rows:

```text
DEFAULT, ALPHABET, ARTIST, ALBUM, BPM, RATING, KEY, LABEL, GENRE,
DATE ADDED, DJ PLAY COUNT, COMMENTS
```

The recorded golden has SHA-256
`5df29930ea1a24a568bee8ad850347d7b369a18a10a8cd923ad5717e423c3c2c`.

## Lifecycle and retained evidence

The Category capture occurred at Unix second 1790848330 and the Sort capture
at 1790848433. Both follow the recorded process start at 1790848132.419 and
interactive-ready marker at 1790848169. The machine-readable validator checks
that ordering, exact response labels and counts, suite and fixture hashes,
SQLCipher integrity, persisted rows, and every screenshot hash:

```sh
../rekordbox-windows/.venv/bin/python \
  tools/summarize_settings_refresh.py \
  --options /mnt/documents/multimedia/djing/rekordbox/options.json \
  --output data/session-refresh/settings-refresh-summary.json
```

Retained evidence includes:

```text
data/session-refresh/category-album-{before,inactive}.png
data/session-refresh/category-album-{probe,same-process}.json
data/session-refresh/sort-comments-{before,active}.png
data/session-refresh/sort-comments-{probe,same-process}.json
data/session-refresh/settings-refresh-lifecycle.json
data/session-refresh/settings-refresh-master.db{,-wal,-shm}
data/session-refresh/settings-refresh-summary.json
```

The database, WAL, and SHM snapshot is synthetic fixture state. Its SQLCipher
integrity check is `ok`; the base database SHA-256 is the pristine `full`
fixture hash
`e8c45a7020a70103d6a15d5cf9aaa32a3d8c758c6c1f3f33b2a8d80872f7c812`.

## Interpretation boundary

The experiments prove the supported lifecycle for all three setting families:
change while Link is inactive, then reactivate Link in the same process.
Category visibility, Sort visibility/order, and the selected Column are all
consumed by the next Link session without an application restart. Their wider
static database matrices remain covered in `CATEGORY_ORACLE.md`,
`SORT_AND_COLOR_ORACLE.md`, and `SECONDARY_COLUMN_ORACLE.md`.

An out-of-band database write while Link remains active is outside the supported
UI workflow and remains untested. The active-Link lock means such a test would
measure internal cache invalidation for an unsupported mutation rather than
normal rekordbox behavior.

## Restoration

After the captures, each temporary identity service was stopped and the
pristine `play-paths` fixture was reinstalled through `activate_fixture.sh`.
Its active marker again reports database SHA-256
`8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6`
and logical fingerprint
`c24aff6c06466a647d09e60f8cf5c872f6db8ae5d482a72cb31ef1d270db6f1a`.
Rekordbox was relaunched, the isolation check passed, the physical-LAN VM was
inactive, and no synthetic identity unit remained. The retained database/WAL/
SHM trio preserves the mutation evidence independently of disposable guest
state.
