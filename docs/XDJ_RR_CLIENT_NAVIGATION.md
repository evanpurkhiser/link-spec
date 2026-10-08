# XDJ-RR client navigation and menu locations

This chapter maps the decompiled XDJ-RR application from player actions to
remote-database request kinds and menu locations. It complements the Rekordbox
server oracle: a firmware call site proves that a player can ask for a command,
while the live oracle proves how Rekordbox 7.2.19 answers it.

## Evidence and method

`data/static-analysis/xdj-rr-client-navigation.json` is generated from every C
file in the pinned XDJ-RR decompilation that contains a `dbcl_` symbol. The
extractor identifies request wrappers through their `SetHeader`, `dbcl_GetRoot`,
or `dbcl_GetULong*` command constructors, propagates the constructor's actual
location expression into direct named callers, and retains source path, line,
caller name, caller address, and literal or dynamic location **[RR-DEC]**.

The inventory covers six hash-pinned source chunks, 121 request wrappers for
116 request kinds, and 304 direct call sites spanning 102 request kinds. Sixty-
two call sites retain a dynamic location expression. Calls through function
pointers are outside this direct-call inventory. The generator rejects a
wrapper when its command constructor is ambiguous and a byte-reproduction test
guards the checked-in JSON.

## Location roles

The firmware contains direct call evidence for every literal location from 1
through 8. These are independent protocol contexts and list buffers. The role
column describes the observed callers; it is not a claim that the number names
a universal screen across every player generation.

| Location | XDJ-RR caller association | Representative requests |
| ---: | --- | --- |
| 1 | ordinary single-track information, filters, key translation, play state, and several analysis helpers | `2002`, `2302`, `2804`, `2904`, `2c04`, `3a03..3f03` |
| 2 | right/secondary browse trees and their list rendering | the complete category hierarchy, `2001`, `2002`, `2006`, `2202`, `3000` |
| 3 | playlist/history/content leaves and their rendered records | `100f`, `1105`, `1112`, `1200`, `2001`, `2006`, `3000`, `3100` |
| 4 | loaded-music, playing-list, and CD-ROM first-track paths | `2006`, `3000`, `3100` |
| 5 | sort menu and one-track Song Info | `1400`, `2002`, `3000` |
| 6 | Prepare and Tag List operations | `100f`, `3000`, `3100`, `3102`, `3202`, `3402` |
| 7 | root/category reload, information jump, cue-bank drag/drop, and folder hierarchy | `1000`, `2001`, `2006`, `2106`, `2206`, `3000`, `3100`, `3603` |
| 8 | artwork, waveform, cue, mutation, history, playlist, and property operations | `2003..2005`, `2101..2105`, `2201`, `2204..2205`, `2305`, `2404..2505`, `2b04`, `3000..3503`, `3903` |

The existing generic location sweep proves that Rekordbox accepts locations
`1..8` for ordinary Track and keeps a separate list buffer per location. The
Hot Cue Bank location oracle separately proves initialized/stale-buffer behavior
at locations 1, 2, 3, and 7. The source inventory explains why accepting eight
locations is functional behavior rather than merely permissive parsing
**[OBS, RR-DEC]**.

The location-1 play-state path is concrete. `SendBrowseMenu` calls
`dbcl_GetTrackPlayState(remote, 1, content_id, &state)`. The wrapper constructs
`0x3b03` with one numeric ContentID and waits for a `0x4000` DWORD. It stores
the reply's low byte and uses its bit `0x02` to choose the Played versus
Unplayed row action. Rekordbox derives that value from the same Link-played ID
snapshot that supplies track-row argument-7 bit `0x100` **[RR-DEC, DEC]**.

## Location 9

`dbcl_GetDeliverySongInfo` constructs request `2602` through
`dbcl_GetULong(param_1, 0x2602, 9, content_id)`. Location 9 is fixed inside the
wrapper, so its public second argument is the ContentID rather than a location.
No non-`dbcl_` XDJ-RR function directly calls this wrapper in the recovered
decompilation. CDJ-3000 firmware independently documents a live Delivery Info
ticket after a Rekordbox track load, establishing that `2602` is used by a
newer player even though the XDJ-RR direct caller is absent **[RR-DEC, ALPHA]**.

The current Rekordbox oracle exhausts locations `1..8` but has not exercised a
location-9 context. Six handed-off suites now declare 36 cases: ordinary,
RX3-status, and CDJ-status identities under both setup widths, with location-1
and location-2 controls, location-9 current renders, and two-track stale-buffer
crosses. Each variant receives an independent cold record and repeat plus
health and hash receipts. Until that queue stage completes, `1..8` is the
complete observed generic location domain, not the complete client-defined
domain.

## Navigation consequences

The client source makes several server contracts more precise:

- The player owns Back, depth, and view switching. Rekordbox receives a fresh
  category request and never receives a generic "navigate back" command.
- Left/right and specialized views reuse the same category requests with a
  different location, so a request kind alone does not identify the screen.
- Render request `3000` appears at every literal location `1..8`. The list
  buffer key must therefore include location, matching Rekordbox's observed
  process-wide stale-buffer behavior.
- Location 5 couples `1400` Right Menu with `3000`, and separately couples
  `2002` Song Info with `3000`. The location is a protocol workspace, not a
  unique request-family namespace.
- Location 6 groups Prepare reads and mutations with Tag List operations. This
  explains why those workflows do not need distinct list-render commands.
- Location 8 is the dominant non-browser service context, including artwork,
  waveforms, cue getters/setters, history mutations, and property retrieval.
  The active adjacent-payload queue uses source-appropriate location controls.
- Location 7 is not limited to Hot Cue Bank. It also carries the root/category
  reload and folder-hierarchy paths used by information jumps and media reloads.

`XDJ_RR_ADJACENT_COMMANDS.md` resolves the remaining directly called old-Key,
Cue Track, write, and database-modification kinds against the pinned Rekordbox
binary. The join leaves zero directly called XDJ-RR kinds in the
`source-vocabulary-only` state.

The old-Key/CueTrack live follow-up is recovery generation `ae18`: six suites and 48
cases cross locations 1/2, ordinary RX3, authentic RX3 status, derived CDJ
status, and both setup widths. Each silent CueTrack request is isolated on a
fresh connection and followed by a fresh old-Key request that proves dbserver
health. It waits for the location-9 campaign before recording.

## Reproduction

```sh
tools/extract_xdj_rr_client_navigation.py
cd conformance
../.venv/bin/python -m unittest test_xdj_rr_client_navigation
```

The extractor pins the AlphaTheta documentation repository commit and the
SHA-256 of every included decompiled source chunk. `SOURCES.md` records the
provenance and `LINK_EXPORT_NAVIGATION.md` places these client-side contexts
beside the live Rekordbox navigation tree.
