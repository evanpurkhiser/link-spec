# Physical XDJ-RX3 Link Export session

This chapter reduces the retained physical XDJ-RX3 RemoteDBServer capture into
an ordered client/server transcript. It establishes native request shapes and
client request cadence. The packet capture does not identify the serving
Rekordbox version, so its responses are not labeled as 7.2.19 behavior. Fresh
7.2.19 oracle evidence remains a separate authority layer **[CAP]**.

The source is
`data/experiments/sort-secondary-render-6/source-rx3-rekordbox-working-ap-20260927.pcap`,
SHA-256
`bee17ddfa72b093479a68c1590953ddc79629cdf43905769761c656a5149aa2b`.
`tools/summarize_physical_rx3_navigation.py` deterministically produces
`data/experiments/physical-rx3-session/navigation-transcript.json`. Large
binary arguments are represented by byte length, SHA-256, and a 16-byte
prefix. Menu rows retain arguments 0, 1, 3, 5, and 6. No payload bytes are
silently treated as text.

## Native connection envelope

The RX3 sent legacy setup transaction `0xfffffffe`, kind `0x0000`, argument
`[11]`. The server replied `0x4000 [0, 0x29]`. The capture version is unknown;
fresh 7.2.19 legacy sessions return second value `0x11` under the current lab
identities.

Every four-byte context follows Dysentery's `requester:menu:slot:type` layout:

| Context | Requester | Menu location | Media slot | Track type | Observed role |
| --- | ---: | ---: | ---: | ---: | --- |
| `0x0b010401` | 11 | 1 | 4 | 1 | root, main Track list, full Display information, specified atoms |
| `0x0b030401` | 11 | 3 | 4 | 1 | selected-track list window and list-buffer offset |
| `0x0b050401` | 11 | 5 | 4 | 1 | one-row Display information previews |
| `0x0b080401` | 11 | 8 | 4 | 1 | artwork, Play information, waveform, beat/VBR/cue payloads |

The byte order is requester, menu location, media slot, then track type.
Locations 1, 3, and 8 agree with Dysentery's main-menu, metadata-preview, and
graphics roles. Location 5 is independently present in the
decompiled XDJ-RR navigation inventory for sort and one-track information
**[CAP, DYS, RR-DEC]**.

## Complete captured vocabulary

The client sent 106 messages across 101 transaction IDs. The server side of
the capture contains 268 messages across 93 transaction IDs, including 144
`0x4101` rows.

| Request | Count | Captured use |
| --- | ---: | --- |
| `0000` | 1 | legacy setup |
| `0001` | 5 | same-transaction cancellation after artwork requests |
| `1000` | 1 | root menu |
| `1004` | 4 | Track list in locations 1 and 3 |
| `2002` | 22 | Display Song Info in locations 1 and 5 |
| `2003` | 17 | artwork prefetch in location 8 |
| `2004` | 1 | preview waveform in location 8 |
| `2102` | 3 | Play Song Info in location 8 |
| `2103` | 1 | content artwork in location 8 |
| `2204` | 1 | beat grid in location 8 |
| `2504` | 1 | VBR information in location 8 |
| `2b04` | 1 | extended cue information in location 8 |
| `2c04` | 16 | specified analysis atom in location 1 |
| `2d04` | 1 | alternate specified analysis atom in location 1 |
| `3000` | 30 | six-argument list rendering |
| `3100` | 1 | location-3 list-buffer offset operation |

The captured response vocabulary is one close `0100`, thirty `4000` headers,
thirty `4001` render headers, eleven `4002` image replies, 144 `4101` rows,
thirty `4201` footers, and one each of `4402`, `4502`, `4602`, and `4e02`, plus
eighteen `4f02` specified-atom replies.

Nine request transactions have no correlated response in the retained packet
stream: six artwork-related requests, one location-1 Display request, the
`3100` operation, and the one `2103` request. Packet absence does not establish
a server timeout or one-way contract. The transcript reports capture presence
only.

## Browse and prefetch sequence

The first menu request is exactly:

```text
1000 [0x0b010401, 0, 0x05fdffff]
```

It returns 19 legacy root rows in this order: Track, Key, BPM, Genre, Artist,
Album, Matching, Search, Playlist, History, Bitrate, Color, File Name, Label,
Original Artist, Rating, Remixer, Time, and Year. The RX3 renders all 19 with:

```text
3000 [0x0b010401, 0, 19, 0, 19, 0]
```

It then requests Default Track and twice renders the first 12 of 4,342 rows:

```text
1004 [0x0b010401, 0]
3000 [0x0b010401, 0, 12, 0, 4342, 12]
```

The first row is content `206733291`, title `Abandon All Hope Here`, secondary
text `3A - 112.2 bpm`, and composite type `0x0f04`. The next eleven rows carry
the same Key-plus-BPM presentation. A third identical Default request/render
appears after the artwork-prefetch phase.

For the visible first-page tracks, the RX3 performs an interleaved preview
pattern:

```text
2002 [0x0b050401, content_id]
3000 [0x0b050401, 3, 1, 0, 16, 0]
2c04 [0x0b010401, content_id, PWV4, EXT]
```

The location-5 Display request advertises 16 rows, but the RX3 renders only
offset 3. Every returned row is item type `0x0b` and carries the track duration
in argument 1. The `PWV4`/`EXT` request returns one `4f02` payload per captured
track; payloads are 7,228 bytes in these examples and have track-specific
hashes. The first track repeats this sequence once.

Artwork prefetch is separate and uses location 8. Seventeen `2003` messages
cover twelve unique content IDs. The capture contains four JPEG-bearing
responses, seven status-50 empty responses, and six requests without a
correlated response. Five artwork transactions also carry a client-originated
`0001 []` with the same transaction ID, 21,098 to 126,329 microseconds after
the request. Three reports follow a captured `4002`: the 28,040-byte JPEG and
two status-50 empty replies. Two follow requests with no correlated response
in the retained stream. No response to `0001` itself is captured. Dysentery
names this kind "invalid data," while the RX3 firmware's `RecvFromCommTask`
constructs it when a GUI cancellation is accepted. These are cancellations of
outstanding artwork transactions, not evidence of JPEG validation failures.

## Selected-track workflow

Content `193883336` (`Acidcore`) is the only track that receives the complete
payload and information sequence. The RX3 first materializes Default Track in
location 3 and renders one row at offset 7:

```text
1004 [0x0b030401, 0]
3000 [0x0b030401, 7, 1, 0, 4342, 0]
```

It requests Play Song Info three times in location 8. Every request advertises
seven rows, and each following render asks for all seven with final argument
zero. The returned rows carry type IDs for title, length, BPM, comment, file
path, color, and key.

Display Song Info is used in two distinct shapes for the selected track:

- location 1 renders all 16 rows;
- location 5 renders only row 0 (Title) and row 6 (Key).

This three-window pattern repeats later in the capture. It is direct evidence
that menu location is client presentation state, not an alias for track type
or media slot.

The selected-track payload requests are:

| Request | Selector/details | Captured reply |
| --- | --- | --- |
| `2004` | preview waveform | `4402`, 904-byte blob |
| `2d04` | `PWV6` / `2EX` | `4f02`, 3,624-byte blob |
| `2c04` | `PSSI` / `EXT` | `4f02`, status 50, empty |
| `2b04` | extended cues | `4e02`, status 1, empty |
| `2504` | VBR information | `4502`, 1,604-byte blob |
| `2204` | beat grid | `4602`, 12,948-byte blob |
| `2c04` | `PQT2` / `EXT` | `4f02`, status 50, empty |
| `2103` | content artwork | no correlated response captured |
| `2c04` | `PWV5` / `EXT` | `4f02`, 83,148-byte blob |

Each successful blob's exact SHA-256 is retained in the transcript. The table
states observed framing and sizes, not a claim that every RX3 action always
issues this sequence.

## Authority boundary

The packet capture is authoritative for the physical client's setup, context,
request order, arguments, and captured replies. It does not prove the server
version, user gesture that caused each phase, or the meaning of an absent
packet. The completed 7.2.19 semantic suites remain authoritative for
controlled database behavior. The queued `physical-rx3-session-envelope`
oracle replays the exact root and Default-track shapes against 7.2.19 without
using the physical network.
