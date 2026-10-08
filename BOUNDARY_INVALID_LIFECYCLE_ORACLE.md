# Boundary, invalid-data, compatibility, and lifecycle oracle

This document records the live rekordbox 7.2.19 behavior for database values
that do not fit the ordinary navigation fixtures. All runs used the isolated
Windows guest, the XDJ-RX3 player-11 discovery identity, extended setup,
context `0x01010301`, root mask `0x05cfffff`, and five-argument rendering.
Every golden was repeated after reinstalling the fixture and restarting
rekordbox. The physical RX3 was unreachable from the experiment network.

The canonical evidence is under
`conformance/goldens/rekordbox-7.2.19/xdj-rx3/`. The nine suites described
here contribute 99 real-rekordbox case executions:

| Suite | Cases | Fixture |
| --- | ---: | --- |
| `boundaries.json` | 30 | `boundaries` |
| `secondary-string-boundaries.json` | 8 | `boundaries` |
| `secondary-date-added-boundaries.json` | 1 | `boundaries` |
| `secondary-comment-boundaries.json` | 1 | `boundaries` |
| `generated/secondary-string-thresholds.json` | 16 | `boundaries` |
| `generated/secondary-unicode-thresholds.json` | 16 | `unicode-boundaries` |
| `invalid.json` | 15 | `invalid` |
| `compatibility.json` | 2 | `compatibility` |
| `history-lifecycle.json` | 10 | `full`, reset before each run |

## Fixture identity

The fixture fingerprint hashes the canonical decrypted schema and contents and
is stable across SQLCipher salt changes. The database SHA-256 identifies the
exact encrypted file used by the run.

| Profile | Encrypted database SHA-256 | Logical fixture fingerprint |
| --- | --- | --- |
| `boundaries` | `a4780456448104d2391b267b9d8c0ba8a9be49a739a044a144158906483d31fc` | `076ebc495465e7d0e35274dad4a8c91c76ad67cd509ef0569d13105374b3116c` |
| `unicode-boundaries` | `242c2f0e3cb28082219d839b71839b8a37d9c06820fce3a84b4762731cf194bb` | `82340bb91a66d4906a2aede9f429891f429948ed9d0d7e61191f14e0c45fcb8b` |
| `invalid` | `109f6301e93fdeb5a3c108a517ec8e2f902718b2c5d89beb647379d4fe91fdb8` | `e7407607ca436169421b4ddc544a73c9a6cc35e3379063525c1240ca10f8cdc9` |
| `compatibility` | `9faae665c7abe7caf6cac6dd9fba75deffefbb47709e834f1af851ec539d5088` | `c54ff3eb49e7827d6a991730ac7fbac5b0be765ee355f589d1db4f59eb7ef145` |

Each contains eight live rows and one `rb_local_deleted = 1` control row.
`PRAGMA integrity_check` returned `ok` for every generated database.

## Numeric grouping boundaries

### BPM

The stored fixture values are hundredths of a BPM: `0`, `49`, `50`, `99`,
`100`, `149`, `150`, and `49949`. The `1006` root advertises only selectors
`0`, `100`, `200`, and `49900` **[OBS]**.

| Advertised selector | Stored BPM values returned by `1206` |
| ---: | --- |
| `0` | `0`, `49` |
| `100` | `50`, `99`, `100`, `149` |
| `200` | `150` |
| `49900` | `49949` |

The grouping operation therefore rounds to the nearest whole BPM expressed as
hundredths, with exact half values rounding upward. The root selector is not the
stored BPM and clients must send the advertised rounded value.

### Release year and decade

The stored values are `0`, `9`, `10`, `1999`, `2000`, `2999`, `3000`, and
`4000`. The `1008` decade root advertises `2990`, `2000`, `1990`, and `10`.
Years 3000 and 4000 are absent from the root **[OBS]**.

The decade-zero `1108` result is unusual: it contains `ALL` with selector
`0xffffffff`, followed by years `9` and `0`. Selecting decade `0` plus
`0xffffffff` returns both tracks; exact year selectors `0` and `9` each return
one. Decade `2990` advertises year `2999`.

Root omission is not query rejection. Direct `1208` requests for year 3000 and
year 4000 each return their matching track. This separates the advertised
navigation domain from the database predicate accepted by the drilldown.

### Duration

The eight fixture lengths remain `59`, `60`, `61`, `599`, `600`, `601`,
`10799`, and `10800` seconds. The `1010` root advertises minute selectors
`179`, `10`, `9`, `1`, and `0`; selector `180` is omitted **[OBS]**.

| Selector | Returned stored lengths |
| ---: | --- |
| `0` | `59` |
| `1` | `60`, `61` |
| `9` | `599` |
| `10` | `600`, `601` |
| `179` | `10799` |
| direct `180` | `10800` |

As with release year, the root enforces an advertising ceiling while the
`1110` drilldown accepts the first selector beyond it.

### DJ play count

Stored values are `0`, `1`, `254`, `255`, `256`, `257`, `32767`, and `65535`.
The `100e` root advertises all eight as
`0xffffffff, 0, 1, 254, 255, 256, 257, 32767`. The stored unsigned maximum is
sign-extended to `0xffffffff`; `65535` is not advertised literally **[OBS]**.

The `110e` request path narrows the selector to its low byte:

| Wire selector | Track actually returned |
| ---: | --- |
| `254` | stored count `254` |
| `255` | stored count `255` |
| `256` | stored count `0` |
| `257` | stored count `1` |
| `32767` | stored count `255` |
| `65535` | stored count `255` |
| `0xffffffff` | stored count `255` |

Consequently the root can advertise counts above 255 that cannot select their
own rows through this request form. This is a server-side navigation defect, not
fixture ambiguity.

The soft-deleted control row is absent from the all-tracks menu and every
numeric root and drilldown.

## Secondary string limits

Eight independent cases select Artist, Album, Genre, Remixer, Label, Original
Artist, Key, and Color as the rendered secondary column. Lookup values contain
126, 127, and 128 ASCII characters. Rekordbox preserves 126 and 127 characters
and truncates 128 to 127 in both the selected secondary field and the extended
tertiary field **[OBS]**. A null Album reference renders ID `0` and an empty
secondary string without dropping the track.

Comment and Date Added require a separate boundary statement. Their original
fixture values include lengths 0, 126, 127, 128, 254, 255, 256, and 256
supplementary Unicode characters. In an eight-row query, selecting either
column produces a render request followed by no messages and a socket
`WouldBlock` timeout **[OBS]**:

| Selected sort | Render argument 8 | Menu header total | Outcome |
| --- | ---: | ---: | --- |
| Comment | `7` | `8` | `render_timeout` |
| Date Added | `17` | `8` | `render_timeout` |

The two isolation suites use direct Release Year drilldowns to select one row
at a time and set `fresh_connection` on every case. This avoids both substring
search collisions and contamination from a preceding stalled render. Every
case was recorded and repeated against real rekordbox **[OBS]**.

ASCII inputs of 0, 126, 127, 128, 254, 255, and 256 characters all render for
both fields. A 256-character ASCII input is truncated to 255 characters. The
supplementary fixture then crosses the same storage boundary with surrogate
pairs:

| Input | UTF-16 code units | Comment | Date Added |
| --- | ---: | --- | --- |
| 126 supplementary characters | 252 | menu, value preserved | menu, value preserved |
| 127 supplementary characters | 254 | menu, value preserved | menu, value preserved |
| 127 supplementary + `a` | 255 | menu, value preserved | menu, value preserved |
| 128 supplementary characters | 256 | `render_timeout` | `render_timeout` |
| 128 supplementary + `a` | 257 | `render_timeout` | `render_timeout` |
| 254-256 supplementary characters | 508-512 | `render_timeout` | `render_timeout` |

The exact first failing width is therefore 256 UTF-16 code units; 255 units is
the largest observed successful value. The menu header still reports total 1,
but the render request yields zero rows before timing out. This agrees with the
decompiled list-buffer terminator at index 255 and proves that the operative
limit counts UTF-16 units rather than Unicode scalar values **[OBS, DEC]**.

## Invalid and dangling database values

The `invalid` fixture mutates one independent concern per live row:

- null Title, FileName, SearchStr, and Comment;
- dangling Artist, Album, Genre, Label, Original Artist, Remixer, and Key IDs;
- zero file type, sample rate, bit depth, and bitrate;
- file type and bit depth 255, sample rate 1, and bitrate `2147483647`;
- BPM, length, release year, track number, and play count `-1`;
- ColorID `999999` and Rating `99`;
- StockDate `not-a-date`;
- empty title, filenames, paths, and search string.

All 15 queries completed and repeated. The all-tracks and filename menus retain
all eight live rows. Null and empty titles/filenames become empty strings rather
than removing the row. The dangling KeyID remains visible as raw row argument 0
`999999`, while the formatted key/BPM secondary omits the key name. The negative
BPM is formatted as `0.0 bpm` in the track row **[OBS]**.

Dangling lookup references do not synthesize root rows. Artist, Album, Genre,
Label, Original Artist, and Remixer roots contain only valid referenced lookup
records. The Key root is independent of track references and still returns the
canonical 24-key list. The Color root likewise returns configured colors 1-8
and does not expose ColorID `999999`.

Out-of-domain numeric values are filtered differently by family:

- BPM root: `12000, 12100, 12200, 12300, 12400`; negative BPM omitted.
- Rating root: `4, 3, 2, 1, 0`; rating 99 omitted.
- Decade root: `2990, 2020, 2000, 1990`; negative year omitted.
- Time root: `179, 10, 9, 1, 0`; negative length omitted.
- Bitrate root: `1411, 320, 256, 192, 32, 0`; signed maximum omitted.

This is family-specific validation at root construction. The retained invalid
track rows show that root omission must not be generalized into a global
content-row validity rule.

## Track compatibility flag

The compatibility fixture varies only `FileType`, filename extension,
`SampleRate`, and `BitDepth`; no media files exist. Both the track and filename
menus return all eight rows, proving that these compatibility results are
derived from database metadata for this path **[OBS]**.

Extended track-row argument 10 is `0x100` for a supported row and `0x101` when
compatibility bit 0 is set:

| FileType | Extension | Rate | Depth | Argument 10 | Result |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | MP3 | 44100 | 16 | `0x100` | supported |
| 1 | MP3 | 48000 | 16 | `0x100` | supported |
| 4 | M4A | 44100 | 16 | `0x100` | supported |
| 5 | FLAC | 48000 | 24 | `0x101` | unsupported |
| 5 | FLAC | 96000 | 24 | `0x101` | unsupported |
| 11 | WAV | 44100 | 16 | `0x100` | supported |
| 11 | WAV | 88200 | 24 | `0x101` | unsupported |
| 12 | AIFF | 96000 | 24 | `0x101` | unsupported |

This matches the decompiled branch: raw file-type bytes 5 and 6 are rejected,
types 11 and 12 accept only 44.1 or 48 kHz, and every other byte returns true.
The helper reads `FileType` and `SampleRate` but never `BitDepth`. The sampled
live result establishes eight cells; the completed 382-row exhaustive oracle
confirms the complete byte domain, wide narrowing, sample-rate boundaries, and
depth invariance under both row widths. It records 298 supported and 84
unsupported rows, and every legacy row is the exact 12-field prefix of its
extended partner. Argument 7 is a separate membership/status field and must
not be interpreted as the compatibility result **[OBS, DEC, DB]**.

## Link History lifecycle

The lifecycle suite starts from a freshly installed `full` fixture and performs
the following sequence on one live connection:

| Step | Request | Exact rekordbox result |
| --- | --- | --- |
| Initial root | `1012` | zero rows |
| Insert first | `3001(context, 10001)` | message sent, no reply awaited |
| Root after first | `1012` | one `LINK HISTORY 2026-09-30` row |
| Render history | `1112(context, sort, returned ID)` | track 10001 |
| Insert second | `3001(context, 10002)` | message sent, no reply awaited |
| Render history | `1112(...)` | tracks 10001, 10002 in insertion order |
| Remove first | `3401(context, 10001)` | menu header total 0 |
| Render history | `1112(...)` | track 10002, renumbered to position 1 |
| Delete history | `3101(context, returned ID)` | message sent, no reply awaited |
| Final root | `1012` | zero rows |

The generated history selector changes between clean runs. The recorder follows
the real returned selector during execution and canonicalizes only the saved
typed-number occurrences to `0xca5e0000`. The golden carries a
`case_item_selector` normalizer declaration naming the source case, row, and
argument. This makes independent runs comparable without fabricating the live
request value.

The first recording and a reset/restart repeat are identical after this semantic
normalization. A stale headless rekordbox process can retain port 12523 briefly
without a usable Link Export listener; oracle preparation must terminate such a
process before a clean interactive launch.

## Current rbxport comparison

The canonical replay is version `c144f19+tree.80e87ec8aace` and retains actual
responses, semantic diffs, and run logs. Results for these suites are:

| Suite | Cases | Field-exact | Same outcome/total/row count |
| --- | ---: | ---: | ---: |
| boundaries | 30 | 0 | 13 |
| secondary lookup strings | 8 | 0 | 8 |
| Date Added boundary | 1 | 0 | 0 |
| Comment boundary | 1 | 0 | 0 |
| Isolated ASCII/supplementary thresholds | 16 | 0 | 10 |
| Isolated UTF-16-unit thresholds | 16 | 0 | 4 |
| invalid values | 15 | 0 | 11 |
| compatibility | 2 | 0 | 2 |
| History lifecycle | 10 | 4 | 4 |

For History, rbxport accepts both `3001` insert messages but its subsequent
`1012` root remains empty. The dependent renders and delete therefore record
`dependency_unavailable`; compare mode continues and emits a readable diff.
Its `3401` response is the unavailable sentinel (`0xffffffff`) rather than
rekordbox's zero-total response. The exact cases are the initial empty root, the
two send-only inserts, and the final empty root.

These mismatches are conformance results, not runner failures. Strict oracle
mode still rejects an unavailable dependency; only non-strict backend comparison
turns it into a structured outcome.
