# Item type reference

This generated reference catalogs every represented numeric item type in
argument 6 of a `0x4101` row across the canonical Rekordbox 7.2.19
goldens. It expands the original bounded-capture `data/item-types.csv`
inventory to the complete retained conformance corpus.

The corpus contains 85 types across
51,148 represented row occurrences
in 281 row-bearing golden files:
62 simple/menu values and
23 secondary-over-title composites.
Every represented meaning is resolved; no type is labeled from backend
behavior. Raw samples and every source file remain in
`data/item-type-reference.json`.

## Encoding

Simple rows place their role in the low byte. Track composites use
`(secondary_role << 8) | 0x04`, where `0x04` is the title/track primary
role. All represented values fit in the low 16 bits; this is a versioned
corpus fact rather than a cross-version wire restriction.

## Complete domain

| Type | Class | Meaning | Occurrences | Producing requests | Representative text |
|---:|---|---|---:|---|---|
| `0x0000` | simple-row | zero type; path or explicitly untyped row | 200 | `0x2102` | Z:/tracks/link-export-fixture/fixture-01.wav |
| `0x0001` | simple-row | folder | 208 | `0x1105`, `0x1315`, `0x2001` | Fixture Folder |
| `0x0002` | simple-row | album | 912 | `0x1003`, `0x1102`, `0x1201`, `0x120a`, `0x1300`, `0x1402`, `0x1702`, `0x2002`, `0x2602` | Album One |
| `0x0004` | simple-row | title or track | 310 | `0x1004`, `0x1105`, `0x2002`, `0x2102`, `0x2602` | empty |
| `0x0006` | simple-row | genre | 498 | `0x1001`, `0x2002`, `0x2602` | Fixture House |
| `0x0007` | simple-row | artist | 796 | `0x1002`, `0x1101`, `0x110a`, `0x1300`, `0x2002`, `0x2602` | Alpha Artist |
| `0x0008` | simple-row | playlist or SmartList | 100 | `0x1105` | Empty Fixture Playlist |
| `0x000a` | simple-row | rating | 390 | `0x1007`, `0x2002` | empty |
| `0x000b` | simple-row | duration | 802 | `0x1010`, `0x2002`, `0x2102`, `0x2602` | empty |
| `0x000d` | simple-row | BPM | 988 | `0x1006`, `0x1106`, `0x2002`, `0x2102`, `0x2602` | empty |
| `0x000e` | simple-row | label | 492 | `0x100a`, `0x2002`, `0x2602` | Fixture Label One |
| `0x000f` | simple-row | key | 1,816 | `0x1014`, `0x1114`, `0x2002`, `0x2102`, `0x2602` | Am |
| `0x0010` | simple-row | bitrate | 452 | `0x1011`, `0x2002` | empty |
| `0x0011` | simple-row | release year | 422 | `0x1008`, `0x1108`, `0x2002` | empty |
| `0x0012` | simple-row | file type | 226 | `0x2602` | empty |
| `0x0014` | simple-row | color 1 / Pink | 196 | `0x100d`, `0x2002` | Pink |
| `0x0015` | simple-row | color 2 / Red | 42 | `0x100d`, `0x2002` | Red |
| `0x0016` | simple-row | color 3 / Orange | 42 | `0x100d`, `0x2002` | Orange |
| `0x0017` | simple-row | color 4 / Yellow | 42 | `0x100d`, `0x2002` | Yellow |
| `0x0018` | simple-row | color 5 / Green | 42 | `0x100d`, `0x2002` | Green |
| `0x0019` | simple-row | color 6 / Aqua | 40 | `0x100d`, `0x2002` | Aqua |
| `0x001a` | simple-row | color 7 / Blue | 42 | `0x100d`, `0x2002` | Blue |
| `0x001b` | simple-row | color 8 / Purple | 42 | `0x100d`, `0x2002` | Purple |
| `0x0023` | simple-row | comment or DeliveryComment | 628 | `0x2002`, `0x2102`, `0x2602` | comment-1 |
| `0x0024` | simple-row | history | 2 | `0x1012` | LINK HISTORY 2026-09-30 |
| `0x0028` | simple-row | original artist | 232 | `0x1302`, `0x2002` | Fixture Original |
| `0x0029` | simple-row | remixer | 238 | `0x1602`, `0x2002` | Fixture Remixer |
| `0x002a` | simple-row | DJ play count | 32 | `0x100e` | empty |
| `0x002b` | simple-row | Hot Cue Bank | 102 | `0x2001` | Root Bank |
| `0x002e` | simple-row | Stock Date / Date Added | 218 | `0x1708`, `0x1808`, `0x1908`, `0x2002` | 2021-02-02 |
| `0x002f` | simple-row | HotCueAutoLoad | 194 | `0x2102` | empty |
| `0x0036` | simple-row | composer artist lookup | 238 | `0x2602` | empty |
| `0x0037` | simple-row | lyricist | 232 | `0x2602` | empty |
| `0x004a` | simple-row | My Tag group or leaf | 20 | `0x1015`, `0x1315` | Fixture Genre Tags |
| `0x004f` | simple-row | DeliveryControl and ISRC | 238 | `0x2602` | empty |
| `0x0052` | simple-row | invalid ColorID-derived type (0x13 + low byte) | 2 | `0x2002` | empty |
| `0x0080` | menu-row | menu choice: Genre | 276 | `0x1000`, `0x1400` | ￺GENRE￻ |
| `0x0081` | menu-row | menu choice: Artist | 276 | `0x1000`, `0x1400` | ￺ARTIST￻ |
| `0x0082` | menu-row | menu choice: Album | 276 | `0x1000`, `0x1400` | ￺ALBUM￻ |
| `0x0083` | menu-row | menu choice: Track | 174 | `0x1000` | ￺TRACK￻ |
| `0x0084` | menu-row | menu choice: Playlist | 178 | `0x1000` | ￺PLAYLIST￻ |
| `0x0085` | menu-row | menu choice: BPM | 276 | `0x1000`, `0x1400` | ￺BPM￻ |
| `0x0086` | menu-row | menu choice: Rating | 276 | `0x1000`, `0x1400` | ￺RATING￻ |
| `0x0087` | menu-row | menu choice: Year | 178 | `0x1000` | ￺YEAR￻ |
| `0x0088` | menu-row | menu choice: Remixer | 184 | `0x1000`, `0x1400` | ￺REMIXER￻ |
| `0x0089` | menu-row | menu choice: Label | 276 | `0x1000`, `0x1400` | ￺LABEL￻ |
| `0x008a` | menu-row | menu choice: Original Artist | 184 | `0x1000`, `0x1400` | ￺ORIGINAL ARTIST￻ |
| `0x008b` | menu-row | menu choice: Key | 276 | `0x1000`, `0x1400` | ￺KEY￻ |
| `0x008c` | menu-row | menu choice: Date Added | 98 | `0x1400` | ￺DATE ADDED￻ |
| `0x008e` | menu-row | menu choice: Color | 184 | `0x1000`, `0x1400` | ￺COLOR￻ |
| `0x0091` | menu-row | menu choice: Search | 178 | `0x1000` | ￺SEARCH￻ |
| `0x0092` | menu-row | menu choice: Time | 184 | `0x1000`, `0x1400` | ￺TIME￻ |
| `0x0093` | menu-row | menu choice: Bitrate | 184 | `0x1000`, `0x1400` | ￺BITRATE￻ |
| `0x0094` | menu-row | menu choice: File Name | 178 | `0x1000` | ￺FILE NAME￻ |
| `0x0095` | menu-row | menu choice: History | 178 | `0x1000` | ￺HISTORY￻ |
| `0x0096` | menu-row | menu choice: Comments | 6 | `0x1400` | ￺COMMENTS￻ |
| `0x0097` | menu-row | menu choice: DJ Play Count | 98 | `0x1400` | ￺DJ PLAY COUNT￻ |
| `0x0098` | menu-row | menu choice: Hot Cue Bank | 174 | `0x1000` | ￺HOT CUE BANK￻ |
| `0x00a0` | synthetic-or-sort-row | synthetic ALL selector | 248 | `0x1101`, `0x1102`, `0x1108`, `0x110a`, `0x1201`, `0x120a`, `0x1402`, `0x1702`, `0x1808`, `0x1908` | ￺ALL￻ |
| `0x00a1` | synthetic-or-sort-row | sort choice: Default | 98 | `0x1400` | ￺DEFAULT￻ |
| `0x00a2` | synthetic-or-sort-row | sort choice: Alphabet | 98 | `0x1400` | ￺ALPHABET￻ |
| `0x00aa` | menu-row | menu choice: Matching | 142 | `0x1000` | ￺MATCHING￻ |
| `0x0204` | composite-track | album secondary over title or track primary | 120 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Album One |
| `0x0404` | composite-track | title or track secondary over title or track primary | 16 | `0x1004` | Boundary Fifty Nine |
| `0x0604` | composite-track | genre secondary over title or track primary | 120 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Fixture Techno |
| `0x0704` | composite-track | artist secondary over title or track primary | 120 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Alpha Artist |
| `0x0a04` | composite-track | rating secondary over title or track primary | 104 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Alpha One |
| `0x0b04` | composite-track | duration secondary over title or track primary | 88 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Alpha One |
| `0x0d04` | composite-track | BPM secondary over title or track primary | 352 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | 120.0 bpm - 8A |
| `0x0e04` | composite-track | label secondary over title or track primary | 120 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Fixture Label One |
| `0x0f04` | composite-track | key secondary over title or track primary | 32,954 | `0x1004`, `0x100f`, `0x1013`, `0x1017`, `0x1103`, `0x1105`, `0x1107`, `0x110d`, `0x110e`, `0x1110`, `0x1111`, `0x1112`, `0x1202`, `0x1206`, `0x1208`, `0x1214`, `0x1300`, `0x1301`, `0x130a`, `0x1500`, `0x1502`, `0x1802`, `0x1a08`, `0x2001`, `0x2002`, `0x2602` | Am - 120.0 bpm |
| `0x1004` | composite-track | bitrate secondary over title or track primary | 88 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Alpha One |
| `0x1404` | composite-track | color 1 / Pink secondary over title or track primary | 22 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Fixture Magenta |
| `0x1504` | composite-track | color 2 / Red secondary over title or track primary | 14 | `0x1004`, `0x1105` | ooooooooooooooooooooooooooooooooooooooooooooooo... |
| `0x1604` | composite-track | color 3 / Orange secondary over title or track primary | 14 | `0x1004`, `0x1105` | ooooooooooooooooooooooooooooooooooooooooooooooo... |
| `0x1704` | composite-track | color 4 / Yellow secondary over title or track primary | 14 | `0x1004`, `0x1105` | ooooooooooooooooooooooooooooooooooooooooooooooo... |
| `0x1804` | composite-track | color 5 / Green secondary over title or track primary | 14 | `0x1004`, `0x1105` | ooooooooooooooooooooooooooooooooooooooooooooooo... |
| `0x1904` | composite-track | color 6 / Aqua secondary over title or track primary | 14 | `0x1004`, `0x1105` | ooooooooooooooooooooooooooooooooooooooooooooooo... |
| `0x1a04` | composite-track | color 7 / Blue secondary over title or track primary | 14 | `0x1004`, `0x1105` | ooooooooooooooooooooooooooooooooooooooooooooooo... |
| `0x1b04` | composite-track | color 8 / Purple secondary over title or track primary | 14 | `0x1004`, `0x1105` | ooooooooooooooooooooooooooooooooooooooooooooooo... |
| `0x2304` | composite-track | comment or DeliveryComment secondary over title or track primary | 156 | `0x1004`, `0x1105`, `0x1208`, `0x2002`, `0x2602` | comment-1 |
| `0x2804` | composite-track | original artist secondary over title or track primary | 104 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Fixture Original |
| `0x2904` | composite-track | remixer secondary over title or track primary | 104 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Fixture Remixer |
| `0x2a04` | composite-track | DJ play count secondary over title or track primary | 104 | `0x1004`, `0x1105`, `0x2002`, `0x2602` | Alpha One |
| `0x2e04` | composite-track | Stock Date / Date Added secondary over title or track primary | 124 | `0x1004`, `0x1105`, `0x1208`, `0x2002`, `0x2602` | 2021-02-02 |

## Interpretation boundaries

- The same numeric type can occur in several request families with
  request-specific argument ownership. Type identifies presentation role;
  it does not make every argument position universal.
- `0x0052` is retained because an invalid ColorID produces it through
  `0x13 + low_byte(ColorID)`; it is evidence of arithmetic type construction,
  not a configured ninth color.
- Root, sort-choice, synthetic ALL, Song Info, and ordinary browse rows
  share the same `0x4101` envelope but have distinct layouts.
- Composite text is server-authored cached presentation. A matching Key or
  BPM materialization can contain two components, while a dynamic override
  of the same nominal type may contain only one or an empty string.

## Reproduce

```bash
.venv/bin/python tools/audit_item_type_domain.py
.venv/bin/python tools/generate_item_type_reference.py
.venv/bin/python -m unittest conformance.test_item_type_reference
```
