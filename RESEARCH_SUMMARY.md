# Rekordbox Link Export research: complete project summary

Snapshot: 2026-10-05, America/New_York

This is the compact handoff for the research under
`workspace/rx3-research/rekordbox-link-export-research`. It summarizes the lab,
the evidence corpus, the important protocol and database findings, the live
Rekordbox oracle, and the remaining gaps. The individual oracle chapters and
machine-readable artifacts remain authoritative when this summary and a live
queue counter differ.

## Purpose and scope

The project is an evidence-first investigation of everything Rekordbox 7.2.19
serves through Pro DJ Link **Link Export**:

- the complete browse/menu navigation tree;
- configuration of root categories, sorts, colors, and the right-hand column;
- exact request, response, row, pagination, and error behavior;
- the SQL/database paths behind each request family;
- device identity, status packet, requester, setup-width, menu-location,
  capability-mask, packed-context, and compatibility dimensions;
- Song Info, Hot Cue Bank, artwork, waveform, analysis, cue, and mutation
  services adjacent to ordinary menus;
- static correspondence with the Windows/macOS Rekordbox binaries, player
  firmware, Dysentery/Beat Link, and historical rbxport behavior.

Real Rekordbox is the authority. Current work records canonical expectations
from Rekordbox only. The suites are backend-neutral so they can eventually be
replayed against rbxport, but current research neither changes nor accepts
results from rbxport. Historical replay evidence is retained for context.

## Safety and isolation

Rekordbox runs in a Windows QEMU VM managed through Podman/systemd. The active
guest NIC is a private layer-2 segment with no default route and no physical
member. The physical RX3 cannot receive synthetic discovery traffic.

Important operational properties:

- the physical-LAN VM path is inactive;
- an isolation gate must pass before any synthetic identity starts;
- guest operations use a project-only SSH key with `IdentityAgent=none`;
- no personal SSH agent is needed;
- VM control uses a narrow polkit rule;
- long campaigns are bounded transient user services;
- actual audio media is unnecessary for menu tests; arbitrary sentinels are
  sufficient for the proven file-presence and file-size branches.

The setup, teardown, host changes, retained services, large artifacts, and
later cleanup actions are recorded in `CLEANUP.md`.

## Evidence model

The documentation labels evidence explicitly:

| Label | Meaning |
| --- | --- |
| OBS | Direct UI, packet, log, or repeatable live observation |
| CAP | Existing packet capture |
| DB | Copied database or configuration state |
| DEC | Static Rekordbox executable analysis |
| RX3DEC | Static player-firmware analysis |
| RBX | Historical rbxport source or replay evidence |
| DYS | Dysentery/Beat Link documentation |
| INF | Named inference not directly verified |
| OPEN | Unresolved question or planned experiment |

Every canonical golden embeds the suite hash, fixture fingerprint, encrypted
database hash, identity, setup exchange, complete typed messages, Rekordbox
version, and recording time. Promotion requires an independent clean run to
match the normalized behavior. Failed candidates and races remain preserved as
provenance rather than being rewritten into authority.

## Lab and conformance architecture

The corpus currently declares **5,730 cases in 933 suite files**, covering
**95 distinct request kinds**. A generated query map assigns every kind exactly
once to one of **47 database-path families**. A navigation graph supplies menu
stages, hierarchy edges, recursive edges, render paths, direct replies,
mutations, and terminal errors. It derives **301 distinct argument-count and
wire-type signatures** from the suite corpus.

Coverage advances through separate states:

1. deterministic fixture and declarative suite exist;
2. real Rekordbox golden recorded;
3. clean independent Rekordbox repeat matched;
4. a future backend replay executes the identical suite;
5. a future backend matches the complete envelope.

The current phase stops at step 3. `CONFORMANCE_COVERAGE.md` is the case-level
ledger; `REKORDBOX_RESEARCH_GAPS.md` is the real-Rekordbox completion ledger.

Fixture profiles include populated, empty, boundary/invalid, configuration
variants, compatibility inputs, large pagination sets, Smart playlists, Hot
Cue banks, settings files, path/cloud states, and disposable mutation
databases. Fixtures are deterministic encrypted `master.db` databases with
fingerprints and manifests.

## Protocol session model

A normal menu transaction is:

1. discovery/status makes a player visible;
2. the client asks port 12523 for the dbserver port;
3. TCP setup negotiates either legacy or extended rows;
4. a `0x1xxx` request materializes a context/location-keyed list;
5. Rekordbox returns a `0x4000` header containing request kind and total;
6. `0x3000` renders one or more windows of `0x4101` rows;
7. the list buffer can survive fresh TCP connections and, for some paths,
   disappearance/rejoin of the synthetic device.

Legacy setup serializes 12-field rows. Extended setup serializes 16 fields;
legacy rows are exact prefixes of extended rows. Setup width is client-selected
and is not forced by model identity.

The request context packs requester, menu location, slot, and track type.
Those bytes are independent dimensions. Requester selects requester-keyed
state and the Display Song Info AIO lookup. Location selects list buffers and
some service routes. Packed track type controls admission and several row
flags. Model text in discovery is not a substitute for genuine status-backed
classification.

## Root menu and configuration

Rekordbox uses four primary configuration tables:

| Table | Role |
| --- | --- |
| `djmdMenuItems` | stable menu identity, localization token, row class |
| `djmdCategory` | root identity, order, visibility, information order |
| `djmdSort` | sort identity, order, visibility, selected right column |
| `djmdColor` | the eight color labels and order |

The deterministic database has 21 category rows. Folder is admitted by the
predicate but explicitly suppressed by the root builder, yielding a 20-entry
root. Folder remains valid inside Playlist navigation. Empty libraries return
the same configured root because root serving does not inspect content.

The root request supplies a capability mask. Most categories use bit
`MenuItemID - 1`. Date Added is remapped to bit 24. Matching and Date Added
have special `Disable` semantics; Matching remains visible with `Disable=2`.
The server combines database visibility and the supplied mask. It does not
infer the mask from the player model.

All individual category disables, complete reversed ordering, special bits,
empty state, and both setup widths are recorded and independently repeated.
Category, Sort, and Column UI changes are also crossed with same-process LINK
refresh and the UI's active-Link edit lock.

## Navigation tree

The recorded navigation domain covers:

- Genre, Artist, Album, Original Artist, Remixer, and Label hierarchies;
- Track/Collection and File Name;
- BPM, Rating, Year/Decade, Time, Bitrate, Key, Color, and DJ Play Count;
- ordinary and recursive Playlist folders;
- Search and Search Track;
- Matching, Prepare, Date Added, My Tag, and Link History;
- Smart playlists and their XML rule engine;
- Hot Cue Bank folder, bank, track, and cue paths;
- Display, Play, and Delivery Song Info;
- artwork, waveform, analysis, VBR, key, and cue payload services;
- recognized no-builder and log-only commands;
- write/mutation and other `0x3xxx` control commands.

Returned-selector chained navigation is tested rather than assuming fixture
IDs. Deleted rows, dangling foreign keys, duplicates, wildcard/unknown nodes,
empty branches, pagination, signed boundaries, overrun windows, and stale
list-buffer behavior are included.

`LINK_EXPORT_NAVIGATION.md`, `PROTOCOL_REFERENCE.md`, `REQUEST_SHAPES.md`, and
`data/static-analysis/link-export-navigation-graph.json` are the main tree and
wire references.

## Database query behavior

`DATABASE_QUERIES.md` maps every request family through:

- interface selection and liveness predicates;
- exact tables and joins;
- soft-deletion filters;
- hierarchy selection and wildcard rows;
- ordering and numeric grouping;
- relationship tables for playlists, My Tag, History, Hot Cue Bank, Prepare,
  Matching, and Smart lists;
- row materialization and render-time lookups;
- direct replies and mutations;
- commands with no database builder.

`DATABASE_FIELD_REFERENCE.md` inventories **389 fields across 22 physical
AppSync tables** and provides a 95-kind inverse request index. The active Link
Export library uses the AppSync interface installed by `SetSharedDBInfo`.
Master-database paths belong to separate filter/track arms, not the shared
menu path. `SQL_LITERAL_INDEX.md` retains exact recovered SQL literals and
source provenance.

## Sorting and the right-hand column

This is one of the most important findings.

There are two independent inputs:

1. the persisted Rekordbox **Column** selection stored through `djmdSort` bit
   `0x02`;
2. the active track-list sort selected by the player.

The renderer has materially different request shapes:

- a six-argument RX3 form:
  `0x3000 [context, offset, count, 0, total, 12]`;
- an eight-argument explicit/fallback form with gate and selector fields.

For six-argument rendering, the final value remains **12** for every observed
sort. Nothing else in the render changes. Rekordbox derives the displayed
right column from the preceding active `0x1004` track request.

The complete real-Rekordbox cross covers Default, Alphabet, Artist, Album,
BPM, Rating, Genre, Label, Key, Date Added, and DJ Play Count. For the same
track (`Alpha One`), the key fields are:

| Active sort | Argument 0 | Argument 5 | Argument 6 |
| --- | ---: | --- | ---: |
| Default | raw KeyID | `Am - 120.0 bpm` | `0x0f04` |
| Alphabet | 0 | `Alpha One` | `0x0404` |
| Artist | 0 | `Alpha Artist` | `0x0704` |
| Album | 0 | `Album One` | `0x0204` |
| BPM | BPM x100 | `120.0 bpm - Am` | `0x0d04` |
| Rating | 0 | empty | `0x0a04` |
| Genre | 0 | `Fixture House` | `0x0604` |
| Label | 0 | `Fixture Label One` | `0x0e04` |
| Key | normalized key sort value | `Am - 120.0 bpm` | `0x0f04` |
| Date Added | 0 | `2021-02-02` | `0x2e04` |
| DJ Play Count | 0 | empty | `0x2a04` |

Extended arguments 12-15 remain independent track metadata in every case:
original KeyID, key-string byte length, key text, and BPM x100. Legacy setup
removes these four fields only at serialization; it does not change argument 5
or the composite row type.

All 15 persisted Column selections are also recorded, plus missing and
multiple-selection states. Persisted selections include Artist, Album, BPM,
Rating, Genre, Comment, Time, Remixer, Label, Original Artist, Key, Bitrate,
Color, DJ Play Count, and Date Added.

When no row is selected, track rows are title-only (`argument 6 = 0x0004`).
When Comment and Key are both selected, the builder consumes SQLite row zero
and chooses Comment for the controlled fixture. This is deterministic evidence
for that layout, not a portable precedence guarantee.

Eight-argument rendering can explicitly reconcile another selector. A zero
selector falls back to persisted Column. Default/Key materialization preserves
cached `Key - BPM`; other active sorts can dynamically return Key alone.
Persisted BPM includes the server-authored `BPM - Key` composite, while a
mismatching dynamic BPM override can leave argument 5 empty and rely on
numeric/tertiary metadata.

This explains the physical RX3 observation and the historical rbxport gap:
correct ordering alone is insufficient. The row's secondary raw value, text,
composite type, and key/BPM metadata must follow the active sort and render
form exactly.

See `SECONDARY_COLUMNS.md`, `SECONDARY_COLUMN_ORACLE.md`, `ROW_LAYOUT.md`, and
`SORT_AND_COLOR_ORACLE.md`.

## Key notation and Camelot

Link Export key notation is controlled by the local device-setting file
`DEVSETTING.DAT`, not directly by Rekordbox's desktop View preference.

| Device style | Key root | Key/BPM example |
| --- | --- | --- |
| Classic | `Abm ... Am, C ...` | `Am - 120.0 bpm` |
| Alphanumeric/Camelot | `1A, 1B ... 8A, 8B ... 12B` | `8A - 120.0 bpm` |

Changing the setting modifies only key text and its UTF-16 length. Numeric Key
IDs, BPM, memberships, ordering, pagination, and unrelated metadata remain
unchanged. Key sort produces `Key - BPM`; BPM sort produces `BPM - Key`.
Artist, Album, and other sorts return their own single value.

The setting is byte `0x74` in a 140-byte device file, with a CRC-CCITT over
the payload. Four desktop preference combinations remained byte-identical
while `DEVSETTING.DAT` stayed Classic. `KEY_NOTATION_ORACLE.md` contains the
complete matrices and hashes.

## Search and Smart playlists

Search covers validation, tokenization, Unicode, embedded NUL, category-gated
domains, mixed entity/content rows, active sorts, pagination, signed argument
boundaries, and 1,000/5,000/10,005-row ceilings.

Smart playlist work covers rule-versus-membership precedence, all observed
operator codes, text and decimal BPM conversion, fixed/relative dates, My Tag
conditions, grouping, direct-child XML parsing, ignored nested nodes,
malformed boundaries, pagination, setup widths, device invariance, and
persisted secondary-column rendering.

## Track rows, visibility, and compatibility

Track rows are traced from query results into the insert record, materialized
list buffer, secondary reconciliation, flags, and 12/16-field wire layouts.

The compatibility flag depends on content metadata, not peer model identity.
FileType low byte and selected SampleRate values affect argument 10 bit 0;
BitDepth is not read on the recovered path. All tested rows remain visible in
Track and File Name menus.

The visibility oracle isolates exact provider-path filtering across Collection,
File Name, ordinary and Smart playlists, Search, and persisted History.
Production-shaped Beatport paths are queued; account-conditioned roots remain
a separate environment question.

## Device identity and classification

Ordinary menus were recorded under CDJ-3000, CDJ-2000NXS2, XDJ-XZ, XDJ-AZ,
XDJ-1000MK2, XDJ-RX3, and two unknown mixer/DJM controls. Across the completed
ordinary menu, capability, compatibility, Smart playlist, packed-context, and
setup matrices, behavior is invariant after normalizing the requester.

Identity dimensions must remain separate:

| Dimension | Proven effect |
| --- | --- |
| Keepalive model/class/generation | no ordinary-menu field difference |
| Setup form | 12 versus 16 row fields |
| Requester player | requester-keyed state and Display AIO lookup |
| Menu location | buffer identity and service routing |
| Packed track type | request admission and row flags |
| Status model | Display Song Info AIO property order |
| Root mask | category admission and special synthesis |
| Content compatibility | presentation flag in track rows |

Static analysis found 23 identity/capability helpers and validated their direct
references. Exact model checks overwhelmingly belong to UI or remote-settings
code. The positive database-serving model branch is Display Song Info's
status-backed `isAIO`: XDJ-prefix requesters receive AIO property ordering.
Play, Delivery, Hot Cue catalog/getters/setters, ordinary rows, root, sort, and
pagination are RX3/CDJ invariant in their completed matched-status crosses.

Captured hardware status and derived classifier probes are never conflated.
Authentic RX3 and CDJ-2000nexus evidence exists; several modern-model packets
remain acquisition gaps. See `DEVICE_MATRIX_ORACLE.md`,
`DEVICE_PREDICATE_AUDIT.md`, and `DEVICE_STATUS_PROVENANCE.md`.

## Packed context

The ordinary Track context's final byte is exhausted over `0x00..0xff`.
Exactly `0x03` and `0x04` time out; only `0x01` enables the row-renderer
`HotCueAutoLoad` bit. A further 329 cases cross 47 list families over packed
types `0x00..0x06`, localizing the gate in `OnClientReq` and proving separate
Root/Search and hierarchy effects.

Song Info and Hot Cue requests have their own type-admission behavior. Type
`0x01` is the successful database-serving type in the completed matched-status
crosses; rejected Hot Cue direct getters return structured status-50 replies,
while some list paths advertise totals and later time out during render.

## Song Information

The project distinguishes:

- Display Song Info `0x2002`;
- Play Song Info `0x2102`;
- recognized adjacent kinds `0x2202..0x2502`;
- Delivery Info `0x2602`.

Display has complete fixed metadata rows, ordinary/AIO ordering, all render
selectors, pagination, malformed requests, exact field limits, missing/invalid
content, setup widths, packed types, requester mismatch, and status/model
controls.

Play and Delivery have complete row payloads, render controls, pagination,
malformed forms, missing content, both setup widths, status controls, and
Delivery-only field/string limits. The path oracle covers local/cloud path
selection, `ContentLink`, `FolderPath`, `OrgFolderPath`, file existence and
size, and `HotCueAutoLoad` without playable media.

An active 16-by-16 lifecycle matrix crosses malformed Song Info precursors and
successors with per-connection setup, a 1200 ms pre-request no-send drain, and
a 3000 ms no-client interval after blob-valued Delivery. At this snapshot,
**228/256 pairs and 684 request executions** are independently promoted; the
next pair is `delivery-string-content__then__play-blob-context`.

Important lifecycle findings:

- blob-valued Play queues delayed `0x4000 [0x2102, 0]` to a later connection;
- health-connection admission of that frame can race, so conflicting failed
  attempts are preserved separately;
- blob-valued Delivery instead observes the measured no-client interval and
  leaves the later drain silent;
- health requests return 13 rows throughout the promoted matrix;
- complete precursor rows exist for blob-valued Play, zero-context Play,
  alternate-location Play, argumentless Delivery, missing-content Delivery,
  extra-argument Delivery, string-context Delivery, and blob-context Delivery;
- the string-content Delivery row is currently in progress.

`SONG_INFO_SIBLINGS_ORACLE.md` and the partial lifecycle reducer are the live
authorities.

## Hot Cue Bank and cue mutation

Hot Cue Bank is a direct non-category service rooted at `0x2001`. Coverage
includes recursive folders/leaves, ordered memberships, count caps, deletion,
dangling and duplicate rows, signed positions, locations, render arities,
process-wide location-keyed stale buffers, large-bank pagination, and the
bit-31 count boundary.

Direct cue services include legacy `0x2101/0x4702`, extended
`0x2301/0x4e02`, the extended setter `0x2401`, and legacy change `0x2201`.
Their decoded record layouts, variable comments/colors/loops, seek controls,
database mutations, WAL evidence, resolver cardinality defects, accepted slot
and flag ranges, parser boundaries, durable post-crash state, and restart
recovery are extensively repeat-verified.

The corpus deliberately retains crash and listener-loss evidence. Examples
include the extended inbound seek-info free defect and legacy declared-length
heap corruption. Each risky probe uses disposable fixtures, health sampling,
event capture, and same-database restart checks.

See `HOT_CUE_BANK_ORACLE.md`, `CONTROL_AND_MUTATION_REFERENCE.md`, and
`BOUNDARY_INVALID_LIFECYCLE_ORACLE.md`.

## Artwork and analysis payloads

The adjacent payload corpus covers artwork, waveform formats, beat grids,
legacy and extended cues, VBR data, segmented key information, quantize data,
specified atoms, malformed arities/types, missing/empty/null paths,
deterministic success assets, parser boundaries, status/setup crosses, and
fileless or log-only commands.

The active AppSync path, Master fallback boundary, JPEG loader, PMAI analysis
atoms, cue serialization, payload sizes, count ceilings, and error envelopes
are documented in `ADJACENT_PAYLOAD_SERVICES.md`.

## Physical RX3 evidence

The physical RX3 is used only through offline captures. Its native session
establishes:

- player/requester 11;
- legacy setup;
- context `0x0b010401` for the captured track browse;
- root mask `0x05fdffff`;
- six-argument track renders;
- ordered browse, prefetch, selected-track, artwork, waveform, beat-grid, cue,
  and cancellation cadence.

The controlled synthetic client reproduces the relevant server envelopes on
the isolated network. `PHYSICAL_RX3_SESSION.md` clearly separates capture
authority from later Rekordbox 7.2.19 oracle evidence.

## Dysentery, firmware, and static analysis

The project includes a pinned local Dysentery clone and a complete crosswalk.
It adopts Dysentery's protocol framing where supported, corrects or extends it
with real 7.2.19 observations, and keeps disagreements explicit.

Static analysis pins the exact Rekordbox Windows/macOS binaries, recovered
functions, vtables, SQL, format strings, dispatch tables, and evidence hashes.
Player-side work includes a 304-call-site XDJ-RR navigation inventory over 102
request kinds, source-defined menu locations, old-Key/CueTrack paths, write
commands, and model-generation vocabulary.

Static evidence predicts experiments; it never overrides a conflicting live
golden.

## Historical rbxport comparison

Before the current Rekordbox-only boundary, 211 goldens containing 2,403 case
executions were replayed against fingerprinted rbxport source
`c144f19+tree.80e87ec8aace`. Of those, 365 cases were field-exact and 1,223 had
the same outcome, total, and row count; no suite passed in full.

Known historical differences include extended footer shape, key notation,
secondary-column availability and formatting, sort-menu choices, extended
metadata ownership, hierarchy details, and missing request families.

Those results are frozen evidence only. No current expected row or behavior is
inferred from rbxport, and rbxport is not presently under test.

## What is complete

For the tested AppSync path and recorded client/status controls, the strongest
completed areas include:

- all 95 declared request kinds classified across 47 database families;
- complete known navigation graph and request-shape inventory;
- root configuration, masks, category/sort/column persistence, and refresh;
- ordinary hierarchy, Search, Smart playlist, History, relationship, numeric,
  invalid/boundary, and pagination behavior;
- all persisted secondary columns and the RX3 active-sort/six-argument cross;
- Classic and Camelot notation across menus, rows, Song Info, and sorting;
- row layout, setup widths, packed context, compatibility, and ordinary device
  invariance;
- Display/Play/Delivery Song Info stable surfaces;
- Hot Cue Bank catalog, cue getters, setters, mutations, and parser boundaries;
- broad artwork/analysis/cue payload semantics and deterministic assets;
- fixture fingerprints, repeat promotion, health evidence, and network
  isolation.

## Important remaining work

The project is intentionally not declared complete. Important live or source
gaps include:

- finish the remaining malformed Song Info lifecycle pairs;
- complete queued five-, seven-, and boundary render-argument matrices;
- complete render type, numeric-field, and override-control matrices;
- record XDJ-RR location 9 and old-Key/CueTrack live crosses;
- complete same-process LINK buffer invalidation and Link-played ownership;
- finish production-shaped provider paths and `CLSSyncMethod=0` path cases;
- record user-info/DJ-ID behavior;
- finish remaining payload status/setup, parser, and cue matrices;
- obtain captured-verbatim modern native status packets with provenance;
- capture native-player `0x2202`/`0x2302` rows and investigate any generation
  that actually serves `0x2402`;
- pursue account-conditioned provider roots without weakening isolation;
- eventually replay the finalized backend-neutral suite against rbxport as a
  separate implementation phase.

The broad research is complete only when every dynamic row in
`REKORDBOX_RESEARCH_GAPS.md` is either closed or has a documented,
evidence-backed reason it is unreachable from Rekordbox's serving role.

## Reading guide

| Topic | Primary document |
| --- | --- |
| Overall entry point | `README.md` |
| Sources and hashes | `SOURCES.md` |
| Chronological work | `EXPERIMENTS.md` |
| Live completion ledger | `REKORDBOX_RESEARCH_GAPS.md` |
| Case-level coverage | `CONFORMANCE_COVERAGE.md` |
| Lab design and commands | `CONFORMANCE.md` |
| Cleanup and retained state | `CLEANUP.md` |
| Navigation tree | `LINK_EXPORT_NAVIGATION.md` |
| Protocol details | `PROTOCOL_REFERENCE.md` |
| Request signatures | `REQUEST_SHAPES.md` |
| Observed inverse index | `OBSERVED_RESPONSE_SHAPES.md` |
| Database pipelines | `DATABASE_QUERIES.md` |
| Database fields | `DATABASE_FIELD_REFERENCE.md` |
| Configuration | `CONFIGURATION.md` |
| Secondary columns | `SECONDARY_COLUMNS.md` |
| Live column/sort oracle | `SECONDARY_COLUMN_ORACLE.md` |
| Key/Camelot | `KEY_NOTATION_ORACLE.md` |
| Track row layout | `ROW_LAYOUT.md` |
| Search | `SEARCH_ORACLE.md` |
| Smart playlists | `SMART_PLAYLIST_ORACLE.md` |
| Device matrix | `DEVICE_MATRIX_ORACLE.md` |
| Device predicates | `DEVICE_PREDICATE_AUDIT.md` |
| Status provenance | `DEVICE_STATUS_PROVENANCE.md` |
| Packed context | `PACKED_CONTEXT_ORACLE.md` |
| Display Song Info | `DISPLAY_SONG_INFO_ORACLE.md` |
| Play/Delivery siblings | `SONG_INFO_SIBLINGS_ORACLE.md` |
| Play/cloud paths | `PLAY_SONG_INFO_PATH_ORACLE.md` |
| Hot Cue Bank | `HOT_CUE_BANK_ORACLE.md` |
| Payload services | `ADJACENT_PAYLOAD_SERVICES.md` |
| Control/mutation commands | `CONTROL_AND_MUTATION_REFERENCE.md` |
| Static analysis | `STATIC_ANALYSIS.md` |
| Physical RX3 session | `PHYSICAL_RX3_SESSION.md` |
| XDJ-RR client paths | `XDJ_RR_CLIENT_NAVIGATION.md` |
| Dysentery comparison | `DYSENTERY_CROSSWALK.md` |
| Historical rbxport audit | `RBXPORT_AUDIT.md` |

## Reproduction principles

Use the declarative suite and fixture manifests rather than hand-constructing
requests. Start every authority run from the required fresh fixture/process
boundary. Verify the isolation gate before emitting an identity. Promote only
an independently matching real-Rekordbox result. Preserve mismatches, crashes,
races, and activation failures separately. Regenerate derived indexes after
stable golden batches, and update the checksum ledger only when the active
queue reaches its documented finalization boundary.

This structure is what makes the corpus useful as both a human protocol
reference and a future implementation-neutral conformance suite.
