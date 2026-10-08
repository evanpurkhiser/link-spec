# Rekordbox Link Export menu exploration

The complete protocol and database reference is
[`LINK_EXPORT_MENUS.md`](LINK_EXPORT_MENUS.md). This file is the short capture
summary.

Captured from Rekordbox at `10.0.0.119:61074` on 2026-09-28. The matching
read-only database is `/mnt/documents/multimedia/djing/rekordbox/master.db`.
The live interface and database both contain 4,342 tracks and 2,203 referenced
artists.

The structured bounded capture is `menu-tree.json`. It preserves all 16 typed
arguments for every captured row and contains 90 menu nodes.

## Root menus and live counts

| Root item | Request | Live result |
| --- | --- | ---: |
| Track | `1004 [context, sort]` | 4,342 tracks |
| Key | `1014` | 24 normalized keys |
| BPM | `1006` | 84 BPM values |
| Genre | `1001` | 27 genres |
| Artist | `1002` | 2,203 referenced artists |
| Album | `1003` | 765 albums |
| Matching | `1017 [context, sort, seed track]` | 1 result for seed 245834041 |
| Search | `1300 [context, sort, UTF-16 bytes including NUL, text, 0]` | 11 results for `ABITAN` |
| Playlist | `1105 [context, sort, 0, 1]` | 8 root folders/lists |
| History | `1012` | 0 current Link sessions |
| Bitrate | `1011` | 12 bitrate values |
| Color | `100d` | 8 fixed colors |
| File Name | `1013` | 4,342 tracks labeled by filename |
| Hot Cue Bank | `2001 [context, selector, mode, count]` | Dedicated populated oracle proves folder/bank tree and ordered tracks; old `1018` probe is a rejected guess |
| Hot Cue Bank cues | `2101 [context, bank_id]` -> `4702` | Windows/macOS handlers, XDJ-RR caller, and real-Rekordbox captures agree; the live Windows AppSync path reads membership timing/MPEG fields, emits fixed 36-byte cue plus 8-byte extension records, and returns an empty reply for invalid or empty selectors |
| Hot Cue Bank extended cues | `2301 [context, bank_id, slot_count]` -> `4e02` | Counts 0-8, empty selectors, and isolated timing/MPEG/color/comment/beat-loop/microsecond fields are repeat-proven; records are self-sized with a 56-byte fixed header and variable option area. Outbound seek is ignored without inbound validity; nonempty valid inbound seek exits Rekordbox |
| Hot Cue Bank setters | `2201` legacy and `2401` extended | Both paths are repeat-proven live with membership-only WAL persistence. Extended `2401` returns its canonical record and immediate readback. Legacy `2201` uses D/E/F ordinals 4/5/6 directly as TrackNo 4/5/6, requires a duplicate resolver row, updates fixed timing/MPEG fields, and then returns unchanged ContentID-selected `djmdCue` track cues in `4702`; unknown-bank/content controls time out |
| Hot Cue Bank bank deletion | Tree `2001` versus direct `2001`/`2101`/`2301` | A soft-deleted bank is omitted from its parent tree, but its numeric ID still serves a retained live membership through catalog, legacy cue, and extended cue paths; direct queries do not require a live owning bank row |
| Label | `100a` | 353 labels |
| Original Artist | `1302` | 0 referenced artists |
| Rating | `1007` | 2 values (0 and 1) |
| Remixer | `1602` | 540 referenced remixers |
| Time | `1010` | 12 minute buckets |
| Year | `1008` | 5 decade buckets |

Confirmed drilldowns include genre → artist → album → track,
artist → album → track, label → artist → album → track,
remixer → album → track, key → distance → track,
BPM → tolerance 0–6 → track, bitrate → track, color → track,
rating → track, time → track, year → track, and recursive playlist
folders/lists.

## RX3 legacy rows and the second column

The RX3-style one-argument setup was replayed directly against Rekordbox.
Rekordbox returns 12-argument rows, but retains the full track item type and
argument 5. Example:

```text
id       title                    second column       item type
206733291 Abandon All Hope Here   3A - 112.2 bpm      0x0f04
42296611  About To Fly            3B - 175.0 bpm      0x0f04
256934718 Above The Clouds        4B - 140.0 bpm      0x0f04
```

The local server's legacy path cleared argument 5 and changed the item type to
title-only before truncating the row. The compatibility path now only truncates
to 12 arguments, matching Rekordbox. The `rbl-dbserver` regression suite passes.

The item type's high byte identifies the selected secondary column. This live
library uses key (`0x0f`), producing track rows of type `0x0f04`; the existing
server is based on a comment-column capture (`0x2304`). Selecting/configuring
the secondary column remains a separate implementation task.

## Search shape

Search length includes the terminating UTF-16 NUL. `ABITAN` therefore uses 14
bytes, not 12. The response contains an artist row followed by track rows. The
track labels are filenames and argument 5 contains the key.
