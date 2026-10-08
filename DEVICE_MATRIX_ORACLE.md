# Device-model oracle

This report records how rekordbox 7.2.19 ordinary Link Export menus respond to
synthetic Pro DJ Link discovery identities. Every run used the same encrypted
`full` fixture, query device 1, context `0x01010301`, root mask `0x05cfffff`,
default sort, and five-argument render. Rekordbox was terminated and relaunched
between identities so `PSvDBMain::clearAIOMap` and discovery state could not
leak across runs. The isolated network cannot reach the physical RX3.

This is an identity-isolation matrix, not a claim about the RX3's native TCP
envelope. The retained physical session independently establishes query device
11, context `0x0b010401`, root mask `0x05fdffff`, legacy setup, and
six-argument rendering. `physical-rx3-session-envelope.json` preserves that
envelope as a separate authority-only 7.2.19 replay **[CAP]**.

`data/device-behavior-matrix.json` is the generated machine-readable index for
this chapter and the status-backed crosses. It binds all eight ordinary
identities and four invariant suites, the requester-keyed Display difference,
the six invariant Play/Delivery/Hot Cue surfaces including both setters, the
genuine CDJ-2000nexus 13-variant result, all three statically recovered serving
decisions, eight independent serving dimensions, and the native-status
provenance boundary. Each source summary and golden is retained with its
SHA-256; regeneration fails if an ordinary identity diverges.

## Recorded identities

The named matrix contains all six concrete models plus one encodable unknown
control. A second unknown control isolates keepalive classes 2 and 3. Model
names are limited to the protocol's 20-byte ASCII field; the original
21-character `unknown-fixture-model` declaration was unencodable and was
corrected to `UNKNOWN-FIXTURE`.

These ordinary-menu identities synthesize membership packets from declared
fields. Status-backed tests have a stricter provenance boundary: XDJ-RX3 and
CDJ-2000nexus retain captured hardware payloads, while CDJ-3000 and the other
named status probes derive from the captured RX3 packet by replacing only the
model and player bytes. `DEVICE_STATUS_PROVENANCE.md` records the exact tiers,
hashes, and conclusions each permits.

| Golden directory | Wire model | Discovery player | Class | Generation | Presence | Model code |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `cdj-3000` | CDJ-3000 | 1 | CDJ (`1`) | 3 | 1 | 100 |
| `cdj-2000nxs2` | CDJ-2000NXS2 | 2 | CDJ (`1`) | 2 | 1 | 100 |
| `xdj-xz` | XDJ-XZ | 3 | type 7 | 2 | 2 | 0 |
| `xdj-az` | XDJ-AZ | 4 | type 7 | 3 | 2 | 0 |
| `xdj-1000mk2` | XDJ-1000MK2 | 5 | CDJ (`1`) | 2 | 1 | 100 |
| `unknown-mixer` | UNKNOWN-FIXTURE | 6 | mixer (`2`) | 0 | 1 | 0 |
| `unknown-djm` | UNKNOWN-FIXTURE | 6 | DJM (`3`) | 0 | 1 | 0 |
| `xdj-rx3` | XDJ-RX3 | 11 | type 7 | 3 | 2 | 0 |

Each manifest retains the complete 54-byte packet SHA-256, MAC address, source
IP, broadcast/unicast destinations, peer count, and source port under
`conformance/runs/`. The adapter's CDJ-3000 and XDJ-RX3 encoders are covered by
byte-for-byte tests against captured packets.

## Per-identity oracle

Every identity caused rekordbox to expose a LINK source and accepted both
protocol setup forms, the capability cross, and the compatibility fixture
**[OBS]**:

- `full.json`: 47 cases with extended setup and 16-field track rows;
- `legacy.json`: 2 cases with legacy setup and 12-field track rows.
- `device-capabilities.json`: legacy/captured/all-bits root masks and render
  arities 5/6/8.
- `compatibility.json`: two menus over eight file-type/rate/depth combinations.

All 57 per-identity cases were recorded and then immediately verified against
the saved golden while the same identity remained active. A two-case probe was
also recorded before and after a same-process XDJ-to-CDJ replacement. This
produces 34 device-matrix goldens and 460 real-rekordbox executions.

The populated/empty SmartList cross adds one two-case golden per identity.
Every populated request evaluates the rule to Content IDs `10001` through
`10008`; every empty request returns zero rows. All eight complete SmartList
behavior envelopes normalize to SHA-256:

```text
8a38e105670fb5942da59cbb2bbb9754d36dccc45ab1bdb53db0392b67b3f002
```

The eight immediate repeats therefore extend the ordinary-menu identity
invariance result through rule evaluation and downstream Smart track-row
serving **[OBS]**. `SMART_PLAYLIST_ORACLE.md` and
`data/experiments/smart-device-cross/summary.json` retain the detailed proof.

The packed-context interaction cross adds two 16-case goldens per identity,
one for each setup width. It covers all seven known client track types on
ordinary Track, five normally dispatched types on a hierarchy Track leaf, and
type `0x00`/`0x01` Root/Search admission controls. All eight extended behavior
envelopes are identical, as are all eight legacy envelopes. Legacy rows are
the exact 12-field prefixes of extended rows; model, class, generation, player
number, and setup width do not alter packed-type routing or its argument-7 and
argument-10 effects **[OBS]**. The 16 goldens contain 256 cases and were each
immediately repeated. See `PACKED_CONTEXT_ORACLE.md`.

After canonical JSON key ordering, every extended `.behavior` envelope has the
same SHA-256:

```text
d8c262a03cb6d38a486bd096be3e2a196773d4c60fb407ebbc2d689f470404b5
```

Every legacy `.behavior` envelope likewise has the same SHA-256:

```text
d9c5ccd1fefb28c14b40e6aee23d8519ff1947b56164c00db9d24fab4c74f181
```

Every six-case capability envelope has SHA-256:

```text
0176da8936565b53d392d1c3050bf92776d611597850243dd78a7799939d3dc4
```

Every compatibility envelope has SHA-256:

```text
cab4d111a7f27985fe249a1ced865926383077baca2d4f1571493315d1ef0c98
```

The reproducible calculation is:

```sh
jq -cS .behavior conformance/goldens/rekordbox-7.2.19/<model>/<suite>.json \
  | sha256sum
```

The equality covers setup request/reply, root order and rows, every populated
hierarchy in the full suite, track membership and ordering, secondary fields,
search, Matching, playlists, History baseline, Hot Cue Bank error behavior,
render messages, and footer shapes. It also crosses XDJ/non-XDJ model prefixes,
all four declared keepalive classes, generations 0/2/3, and discovery player
numbers 1-6 and 11 **[OBS]**.

## Interpretation boundary

For a fixed dbserver request envelope, ordinary Link Export menu behavior did
not vary with any tested discovery identity. This agrees with direct static
inspection: model-name and `isAIO` calls are absent from `GetRootMenu`,
`GetSortMenu`, list-buffer insertion, row extraction, and list serialization
**[DEC, OBS]**.

The exhaustive direct-reference audit expands this beyond those hand-selected
functions: 23 peer identity/capability helpers produce 67 validated x86-64 and
68 validated ARM64 references.
All 35 exact-model comparisons and all five `isCDJNetwork` calls belong to UI
or remote-settings code. The only model-derived database-serving branch is the
known Display Song Info `isAIO` call; the other row-builder predicate named
"NewCDJSupported" reads content metadata rather than peer identity.
`DEVICE_PREDICATE_AUDIT.md` contains the complete inventory and limits **[DEC]**.

This is not a claim that model identity is unused everywhere. The pinned
binary's `isAIO(player)` returns true for every `XDJ` prefix, including
XDJ-1000MK2 even though its keepalive class is CDJ. Its validated caller,
`PSvAppSyncDBIF::getDispSongInf`, places Comment before Key/Rating/Color/Genre/
Stock Date for AIO identities and after Stock Date for non-AIO identities.
The extended harness now sends `0x2002`: captured RX3 status produces the AIO
order and the matched CDJ-3000 status control produces ordinary order. The
same XDJ keepalive without player status produces ordinary order because the
model lookup is not populated **[OBS, DEC]**. `DISPLAY_SONG_INFO_ORACLE.md`
contains the complete proof.

Authentic RX3 status and the RX3-template-derived CDJ-3000 control were also
crossed through Play
Song Info and Delivery Info baseline rows, every render control, pagination,
stable malformed type/arity cases, and legacy setup. After normalizing the
requester byte, all 106 stable cases per identity are exact. They also equal
the ordinary identity except for argumentless Delivery: ordinary times out,
while both status identities return an empty header that echoes Play kind
`0x2102`. The stable populated Play/Delivery builders therefore show no
RX3/CDJ or AIO classification branch **[OBS]**.

The setup form is independently client-selected. Every identity accepts both
legacy and extended setup; model name does not force row width in these tests.
Likewise, the query context still names query device 1 even when discovery uses
another player number. Discovery identity and request context must remain
separate conformance dimensions.

## Serving dimensions

The generated matrix keeps eight inputs separate. This is the decision table
to use when constructing a client or interpreting a capture:

| Dimension | Observed serving effect | Boundary |
| --- | --- | --- |
| Keepalive identity | No field difference in ordinary menu, capability, compatibility, or setup envelopes | Keepalive model text does not populate the status-backed AIO map |
| Setup width | `0x4101` rows contain 12 or 16 arguments; legacy is an exact prefix | Client-selected; model identity does not force width; direct blobs have no row suffix |
| Requester player | Selects requester-keyed buffer state and Display AIO lookup | RX3 player-11 status changes Display order only for requester 11 |
| Menu location | Participates in buffer identity and location-sensitive service routing | Generic locations 1-8 are exhausted; source-defined Delivery location 9 is queued |
| Packed track type | Controls ordinary dispatch admission, Root/Search population, hierarchy argument 7 high byte, HotCueAutoLoad bit `0x100`, and Song Info/Hot Cue admission | Independent of model identity and content compatibility |
| Status model classification | `isAIO` changes Display Song Info property order for an XDJ-prefix requester | Completed Play, Delivery, Hot Cue catalog/getter/setter, root, sort, pagination, and ordinary rows show no matched RX3/CDJ difference |
| Root capability mask | Controls configured category admission, Date Added remapping, and the exact legacy Hot Cue synthesis branch | Supplied by the request; the server does not infer it from model identity |
| Content compatibility | FileType low byte and selected SampleRate values set row argument 10 bit 0; BitDepth is unread | Presentation metadata only; all 382 rows remain members of Track and File Name menus |

The seven completed status-backed surfaces make the positive and negative
model result explicit. Display Song Info differs. Play, Delivery/no-builder,
Hot Cue catalog, both direct getters, the extended setter, and the legacy
setter are identical after requester normalization within their completed
RX3/CDJ and setup envelopes **[OBS]**.

## Same-process replacement

A clean rekordbox process first recorded and repeated the two-case root/track
probe under XDJ-RX3. That identity then stopped while rekordbox remained open.
A CDJ-3000 replacement started after 12 seconds, but port query did not reopen
before the runner timeout. After that failed attempt and an additional
25-second wait, a new CDJ-3000 emission reopened Link Export without an
application restart and recorded/repeated both cases **[OBS]**.

The before/after behavior hash is identical:

```text
d3f39e6f494696a6dc2b619e3193cc840c47e84a2515e43aaa29078844eb2cfb
```

This demonstrates that disconnect eventually clears enough peer and model
state to accept a different identity in the same process. Twelve seconds was
too short in this observed sequence. The experiment bounds recovery rather
than assigning the internal timeout exactly because the failed connection
attempt and UI activation also consume time.

The Delivery-order lifecycle sharpens both conclusions. Two runs warmed an RX3
process with six Delivery calls, removed discovery emission, then reintroduced
the same RX3; two more replaced it with CDJ-3000. The initial port query after
40 seconds of absence timed out in every automated run. A 30-second retry and
renewed emission reopened Link Export. Every warm-up was byte-identical
`AAABCD`; every post-rejoin response was byte-identical `ABCDABCD`. The latter
is the process sequence continuing at call seven, not a cold prefix. Neither
discovery expiry nor changing XDJ/type-7/generation-3/presence-2/model-code-0
to CDJ/class-1/generation-3/presence-1/model-code-100 resets or changes the
Delivery builder's ordering state **[OBS]**.

## rbxport replay

All 34 device goldens are registered individually in
`replay_rbxport.py`. For each identity, the 47-case full replay has 2 exact and
29 same-outcome/total/row-count cases; the 2-case legacy replay has 0 exact and
1 same-shape case; the 6-case capability replay has 0 exact and 5 same-shape
cases; the 2-case compatibility replay has 0 exact and 2 same-shape cases. Each
two-case reconnect replay also has 0 exact and 2 same-shape cases. The
duplication is intentional: it proves the adapter does
not silently omit a recorded oracle merely because backend behavior currently
collapses across identities.

## Remaining crosses

The named-model/setup/mask/render/compatibility/reconnect and packed-context
interaction sweeps are complete,
including Delivery state across RX3 rejoin and RX3-to-CDJ replacement. The
known AIO classifier is live-recorded with a matched status control.
The RX3-status-shape mutation cross is also complete: XDJ-XZ, XDJ-AZ, and
XDJ-1000MK2 time out at requester 11, while the player-1 unknown-model control
serves ordinary menus. The stable Play/Delivery RX3/CDJ status cross is
complete. A genuine generation-2 CDJ-2000nexus/player-1 status payload from
Dysentery is retained byte-for-byte and has a completed 249-case matrix over
ordinary menus, both setup widths, Display/Play/Delivery/no-builder context
crosses, and Hot Cue catalog/getters. All 13 variants passed an independent
fresh-fixture/process repeat and all 13 semantic envelopes match the derived
CDJ-3000 controls. Twelve raw envelopes match exactly; the Display baseline's
raw difference is solely its `3/3/3/3/3/1` render pagination versus the
reference's single 16-row render. Durable receipts bind every suite, fixture
manifest, genuine identity, and golden. Remaining packet-source
gaps require captured-verbatim status shapes from the other XDJ models, plus status-backed
reconnect replacement and synthetic model/class combinations justified by a
real capture or a newly discovered indirect/inlined predicate. The direct
predicate inventory is complete for the pinned x86-64 symbolized helpers.

Two complete 292-byte XDJ-XZ/player-1 status packets from a dated physical-unit
session are now retained as corroborating fixtures. Their parent capture and
key acquisition metadata are unavailable, so they remain below the genuine
RX3/CDJ-2000nexus tier. A player-1 CDJ-class lab identity binds the analyzed
fixture and preserves this provenance distinction. Its real-Rekordbox matrix
is declared as a 13-variant, 249-case record/repeat cross and waits behind the
active isolated-VM queue. Every variant starts with a fresh fixture and cold
Rekordbox process, records four process/Application health documents, and
receives a hash-bound receipt before promotion. The result will describe how
Rekordbox handles this exact packet; it will not upgrade the packet's hardware
provenance.

`conformance/record_device_model.sh` is the guarded reproducible batch command
for the full/legacy pair. It checks VM isolation and the active database hash,
starts a bounded identity service, activates LINK through the connected noVNC
session, records each suite, immediately verifies it, and stops the identity on
every exit path.

`conformance/record_context_device_setup_matrix.sh` performs the complete
eight-identity interaction batch and restores `play-paths` on every exit.
