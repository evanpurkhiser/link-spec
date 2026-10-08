# link-spec

`link-spec` is a research corpus and conformance suite for rekordbox Link
Export. It records how rekordbox exposes a library to Pioneer/AlphaTheta
players. Existing RX3
captures are evidence; new experiments use a synthetic client and do not expose
the physical RX3.

The investigation covers:

- whether the Windows rekordbox VM can expose Link Export on an isolated LAN;
- every observed menu, submenu, row type, sort and category configuration;
- navigation semantics, request/response sequences and menu identifiers;
- how rekordbox preferences and library configuration change the served tree;
- correspondence between observed rekordbox, Dysentery/Beat Link, and the
  decompiled rekordbox implementation;
- known gaps, ambiguous fields and reproducible experiments needed to close them.

## Repository map

- `docs/PROTOCOL_REFERENCE.md` is the consolidated wire-protocol reference.
- `docs/RESEARCH_SUMMARY.md` summarizes the strongest findings and remaining gaps.
- `docs/CONFORMANCE.md` documents the oracle, fixtures, recording workflow, and
  safety boundaries.
- `conformance/` contains suite declarations, canonical goldens, the protocol
  client, and backend adapters.
- `conformance/BACKENDS.md` documents the adapter interface and replay commands.
- `conformance/reports/` contains compact reports from complete backend runs.
- `data/` contains compact retained evidence and a larger local raw-evidence
  archive; `docs/PUBLISHING.md` defines the Git boundary.

Run the local unit and protocol-client checks with `make test`. See
`CONTRIBUTING.md` for development conventions.

## Current research boundary

Rekordbox 7.2.19 remains the behavioral oracle. Backend-neutral declarations
and goldens can be replayed against implementations through the adapter
interface in `conformance/conformance_backend.py`. Backend results measure
conformance to the recorded oracle; they do not modify or redefine it. The
active automated catalog contains 287 safe replay suites, while 149 mutation
and lifecycle suites remain explicitly deferred.

## Rekordbox oracle baseline

The isolated real-rekordbox path is operational. The private Windows guest has
no default route, the physical-LAN VM unit is inactive, and the host isolation
gate must pass before an identity is emitted. Routine VM and guest operations
use a narrow polkit rule and a project-only SSH key; they do not use Evan's SSH
agent.

rekordbox 7.2.19 has recorded and repeat-verified the 47-case populated suite
and 21-case empty suite with the captured XDJ-RX3 player-11 identity, plus the
same populated suite with a CDJ-3000 player-1 identity. A two-case legacy setup
suite is also recorded and repeated under both identities. The device-paired
behavior envelopes are identical within each setup mode. Their canonical
results are under `conformance/goldens/rekordbox-7.2.19/`. The XDJ-RX3 oracle
also records and repeats 21 populated Play Count, Prepare, Date Added, and My
Tag cases plus nine empty-state counterparts. A 16-case chained-navigation
golden follows selectors returned by each backend through genre, artist,
album, and label paths. All 15 persisted secondary-column selections plus the
missing- and multiple-selection database states are recorded and repeated.
All 21 persisted categories disabled individually, complete reversed category
ordering, and the category special-bit controls are also recorded and repeated.
Every persisted sort visibility toggle, complete reversed sort ordering, the
hidden-selected secondary state, and custom color labels are recorded and
repeated as well. Numeric boundary, invalid/null/dangling-value, compatibility,
secondary-string boundary, exact UTF-16 width, and ten-step Link History
lifecycle suites are recorded and independently repeated. Root capabilities,
sort IDs, packed contexts, all render arities and overrides, pagination, request
errors, malformed framing, and twelve-session concurrency are recorded and
repeated. The ordinary Track context's final byte is exhausted over
`0x00..0xff`: exactly `0x03` and `0x04` time out, while only `0x01` enables the
row-renderer `HotCueAutoLoad` bit. This 256-case suite is real-rekordbox-only in
the current phase and is deferred from backend replay. A further 329 cases
cross all 47 list families over types `0x00..0x06`, localizing the `0x03`/`0x04`
gate in `OnClientReq` and proving the Root/Search, argument-7, and argument-10
effects. Separate repeat-verified 49-case Song Info and 21-case Hot Cue Bank
crosses establish the distinct `0x2xxx` behavior. None of these suites has been
run against rbxport. A final 256-case interaction matrix crosses the informative
Track/Root/Search context cases over all eight ordinary identities and both
setup widths. Identity does not change behavior; legacy rows are exact
12-field prefixes of extended rows. A further 42-case Display cross uses
authentic RX3 status, a derived CDJ-3000 control, and an
RX3-status/requester-1 control: only type `0x01`
succeeds, and the requester byte selects whether RX3 AIO ordering applies.
A matched RX3/CDJ Play cross adds 28 cases over types `0x00..0x06` and both
setup widths. Only type `0x01` succeeds, and the complete normalized Play
response is identity-invariant within each setup, so Play does not reproduce
Display's AIO ordering branch. A further 140-case matched-status cross covers
Delivery and recognized kinds `0x2202..0x2502`: Delivery again admits only
type `0x01`, every recognized no-builder kind returns its own `0x4003`, and
both setup widths are identity-invariant after requester normalization. This
completes the known Song Info kinds across packed type, matched RX3/CDJ status,
and setup width.
The adjacent Hot Cue Bank direct getters add a 112-case status-backed matrix
over `0x2101`/`0x2301`, populated/empty selectors, all seven packed types, and
both setup modes. Type `0x01` alone serves database records. Every other type
gets a well-formed direct reply with status `50` and empty blobs, identically
for RX3 and CDJ-3000.
A further 56-case matrix crosses the extended setter `0x2401` over the same
seven types, matched RX3/CDJ status, and both setup shapes. Type `0x01` alone
mutates; every rejected setter returns status 50 and is followed by a type-1
getter proving the pristine database record. All four decoded response
sequences are identical and match independent fixture-reset repeats.
The legacy `0x2201` change path has the same 56-case cross. Type `0x01` alone
mutates slot 4; the other six types return the legacy status-50 envelope, and
24 following six-slot getters prove D/E/F records remain pristine. RX3/CDJ and
both setup shapes again produce identical decoded sequences.
The `0x2001` catalog has a separate 84-case status-backed cross over its root,
populated bank, empty bank, all seven packed types, both models, and both setup
shapes. Type `0x01` returns totals 3, 8, and 0; every other type advertises 50
rows and times out after a 32-row render request. RX3 and CDJ-3000 are
identical after requester normalization, and legacy rows are exact 12-field
prefixes of extended rows. These goldens are real-Rekordbox oracle evidence
and remain deferred from backend replay.
The named-model/setup/mask/render/compatibility/reconnect device sweep is
complete. The separate `0x2002` Display Song Info API is recorded with complete
16-field rows for ordinary and status-backed RX3/AIO ordering, including a
matched CDJ-3000 status control, the complete seven-type packed-context cross,
requester-player mismatch evidence, missing-content cases, both row widths, every
render selector, pagination normalization, malformed requests, invalid values,
and exact ASCII/Unicode field limits. The adjacent `0x2102` Play Song Info and
`0x2602` Delivery Info builders are also recorded across their complete rows,
every render selector, pagination, malformed requests, missing content, and
both setup widths. Authentic RX3 status and the RX3-template-derived CDJ-3000
control additionally
cover the complete stable Play/Delivery surface and the context-sensitive
malformed forms. This includes exact Delivery-only string and lookup limits and
repeat-verified row-order interactions with every adjacent Song Info family,
TCP lifetime, discovery rejoin, RX3-to-CDJ replacement, and an independently
repeated RX3-status menu-location-2 precursor matrix across reconnect and
shared-socket operation, including the malformed request that closes dbserver.
The Play path oracle adds repeated local/cloud identity, file-presence,
file-size, `ContentLink`, `FolderPath`, `OrgFolderPath`, and `HotCueAutoLoad`
branches without requiring media files.
The Hot Cue Bank oracle proves the non-category request `0x2001`, recursive
folder/leaf rows, ordered track memberships, its minimum-three count cap,
deleted/dangling/duplicate behavior, signed positions, and locations 1/2/3/7.
Its complete 4 x 4 x 2 render cross proves process-wide, location-keyed menu
buffers: cold foreign renders time out, while initialized foreign renders
return stale rows across fresh TCP connections. Both six- and eight-argument
forms have the same state behavior. A separate repeat-verified 70-track bank
proves complete 1-row and 32-row walks, exact 31/32 and 63/64 boundaries,
zero/end/past-end normalization, right-aligned overruns, overlap duplication,
and the maximum-offset render timeout. It also recovers the two-argument
`0x2101` cue-info request and its recorded `0x4702` reply, including populated
and empty payloads across setup, status, model, framing, and stateful variants.
Its paired field fixture maps every legacy cue-record word and proves the live
Windows server reads the AppSync membership row rather than referenced
`djmdCue` data. The extended `0x2301` getter is also recorded and repeated:
its `0x4e02` reply supports requested counts through eight and has a decoded
56-byte fixed header plus variable color, comment, beat-loop, microsecond, and
seek-option area. Isolated fields expose an inbound seek-info process-exit edge;
the extended setter `0x2401` is now recorded and independently repeated with a
disposable fixture. Its successful `0x4e02` echo and same-connection `0x2301`
readback are byte-identical, and a captured live WAL proves that it updates the
`djmdSongHotCueBanklist` membership while leaving `djmdCue` unchanged. Two
single-row negative controls expose an AppSync resolver defect: exactly one
matching row returns status 50, while two active rows at the same bank/slot let
the setter select row zero. The zero-row side is now repeat-proven at admitted
slot 8: setter and immediate getter stall without mutation or process exit,
and restarting Rekordbox against the same database restores the identical
status-zero 124-byte getter record in three of three cold-process runs. The
complete 57-variant extended-setter structural matrix is now strictly reduced:
54 fixture-reset golden pairs plus three lifecycle variants covering 366
evidence cases. Returned-slot count `UINT32_MAX` reveals a separate ordering
boundary: all three runs commit the canonical mutation before setter reply and
immediate getter stall, and same-database restart returns that identical
124-byte mutation. Reproducible vtable resolution proves the successful setter
performs its final database update before calling `getHCBnkCuePointExt` with
the requested returned-slot count to construct the reply. The complete
57-variant legacy parser matrix covers 114 independent Rekordbox processes.
Zero actual cue bytes repeatably stall the setter and
immediate getter with a responsive process and pristine database, while
same-database restart restores the canonical three-record getter. The
one/three/four-byte controls return status 1; seven, eight, 35, and 37 bytes return status 0 and
two ordinary cue records through the handler's post-error ContentID query,
while still leaving the membership database pristine. Exactly 36 bytes admit
the mutation in both runs: membership 94201 receives all nine legacy fixed-field
sentinels, and the following extended getter returns record widths 56/124/124.
The exact 35/36/37 cross proves the live mutation gate requires equality with
36, rather than accepting a minimum length. The complete declared-length axis
proves mutation also requires declared length exactly 36. Declarations 0/1/35
return empty `0x0100` messages with pristine immediate getters; 37 reaches the
post-error `0x4702` cue query without mutation; and `UINT32_MAX` returns empty
`0x0100`, leaves the database pristine, but stalls the immediate getter until
same-database restart. The flag axis repeat-proves the lower mutation edge:
values 0 and `0x0003ffff` are pristine, while `0x00040000` mutates membership
94201. Within ordinal 4, flag byte 0 is also the loop discriminator:
`0x00040001` stores extension `OutMsec`, while `0x00040000` and the observed
`0x00040100` store `UINT32_MAX`; `0x0004ffff` confirms every other byte-0 value
takes the latter branch. High word 5 routes the identical mutation to row-zero
E membership 94203 and moves the getter's compact record to 124/56/124;
`0x0005ffff` preserves both effects while again storing `UINT32_MAX`, proving
the upper-word route and byte-0 loop test remain independent across ordinals.
High word 6 completes the admitted ordinal routing cross by changing only
row-zero F membership 94205 and moving the compact getter record to
124/124/56; `0x0006ffff` retains both effects and again stores
`UINT32_MAX`. The upper neighbor `0x00070000` and extreme `0xffffffff` both
return the ordinary cue-query response with a pristine database and canonical
124/124/124 getter, completing the inclusive `0x00040000..0x0006ffff`
admission interval. The extension-length axis proves that a zero-byte extension
is accepted for the non-loop cue form: both runs mutate membership 94201 and
return the 56/124/124 getter with `OutMsec=UINT32_MAX`. A one-byte `0x77`
extension stores `InMsec=0x77`, proving short extensions are little-endian
zero-padded values rather than rejected records. Seven bytes store the complete
first dword as `InMsec=0x77777777`; the non-loop form still stores
`OutMsec=UINT32_MAX`. Exact length eight produces the identical stored fields,
closing the zero-filled-copy side at its boundary. Lengths 9 and 16 produce
the same semantic row, setter-response signature, and getter payload hash as
length 8, proving every byte after the first eight is ignored.
Declared extension length zero still commits the same membership mutation with
a zero-filled extension, but returns a generic empty `0x0100`; the independent
getter exposes the durable 56/124/124 change.
Declared extension length one is a separate crash boundary. Both canonical
cold runs disconnect without a reply, leave the membership database pristine,
and log the same `ntdll.dll` heap-corruption exception `0xc0000374` at fault
offset `0x00000000001176e5`. The process is gone before the immediate getter;
a same-database restart restores the canonical pristine 124/124/124 response.
Two retained discovery runs observed the same exception through timeout and a
stale advertised dbserver port, documenting the scheduling-sensitive transport
edge without promoting those incomplete runs.
Declared extension length seven is the delayed form of the same crash. Both
setters time out while the first health sample still sees Rekordbox alive and
no Application error. The immediate getter then finds the advertised dbserver
port dead; its bound follow-up health sample sees zero processes and the same
`0xc0000374`/fault-offset signature. The database remains pristine and the
same-database restart restores the canonical 124/124/124 response in both runs.
Declared lengths eight and nine produced identical successful mutations and
replies in their four late-epoch observations. Both
return the same status-zero two-cue `0x4702`, persist the same eight-byte
extension semantics, and then leave Link Export's port query unavailable while
the Rekordbox process remains alive with no Application error. Restarting the
process exposes the identical durable 56/124/124 getter. The length-eight wire
request is identical across seven nominal cells: four earlier pairs served
their immediate getters, while the later declared-length, ContentID-10001, and
fixed-word-2-zero pairs lost the listener. This outage is tracked as a hidden lifecycle/history
dimension, not a declared-length-eight property. Declared
`UINT32_MAX` instead returns empty `0x0100`, leaves the database pristine, and
stalls only the immediate getter until restart.
The legacy `0x2201` change
operation is also
repeat-proven with a two-row `TrackNo=4` fixture. It persists its fixed-record
sentinels to the selected membership, then returns the track's unchanged
`djmdCue` rows in a `0x4702` response. Unknown-bank, unknown-content, and
duplicate-`TrackNo=1` controls time out, exposing both the same cardinality
defect and AppSync's unadjusted wire ordinal. A separate repeat-verified D/E/F
matrix proves ordinals 4/5/6 update `TrackNo` 4/5/6 respectively, with a live
WAL showing only the first member of each duplicate pair changed. An 11-case
boundary matrix proves every tested ordinal outside 4/5/6 returns a
status-zero cue reply while performing no membership or cue mutation. A
deleted bank with a live membership is omitted from its parent tree, while direct
`0x2001`, `0x2101`, and `0x2301` requests for that bank ID still return its
track and cue data. Catalog count controls through `0x7fffffff` return the ten
resolvable fixture rows, while `0x80000000` and `0xffffffff` return successful
empty menus. This repeat-verified bit-31 boundary identifies the active
AppSync implementation's signed loop comparison; process-health captures show
no crash, hang, or count-proportional allocation on that route.
The list-visibility oracle isolates `FolderPath` protocol classification across
Collection, File Name, ordinary and Smart playlists, Search, and persisted
History, including provider-specific syntax, construction, and false-positive
controls.
Recognized request kinds `0x2202` through `0x2502` return exact `4003` errors.
Before this boundary was established, 211 goldens covering 2,403 case
executions were replayed against the exact fingerprinted `rbxport`
source tree `c144f19+tree.80e87ec8aace`; 365 cases are field-exact and 1,223 have
the same outcome, total, and row count, while no suite passes in full. Actual responses,
semantic diffs, logs, source hashes, and a readable summary are under
`conformance/results/rbxport/`. `docs/CONFORMANCE_COVERAGE.md` is the status
authority.

## Documents

- `CONTRIBUTING.md` defines the test, golden, and adapter contribution
  boundaries.
- `docs/PUBLISHING.md` defines the public Git boundary and pre-publication review.
- `docs/RESEARCH_SUMMARY.md` is the self-contained project handoff: lab architecture,
  major protocol/database findings, current authority status, remaining work,
  and a reading map into the detailed evidence chapters.
- `docs/SOURCES.md` records every source and its evidentiary role.
- `docs/PUBLIC_STATUS_SOURCE_AUDIT.md` pins six public packet-source candidates,
  distinguishes captured bytes from modeled fixtures, and records the
  unresolved modern-model acquisition set.
- `docs/EXPERIMENTS.md` is the chronological lab notebook.
- `docs/LINK_EXPORT_NAVIGATION.md` is the behavioral navigation-tree reference.
- `data/static-analysis/link-export-navigation-graph.json` is the generated
  47-family, 95-request transition graph joining root choices, hierarchy
  stages, database tables, rendering, direct replies, mutations, and terminal
  error/no-builder paths. It also inventories every declared argument-count and
  wire-type signature with suite/case provenance.
- `docs/REQUEST_SHAPES.md` is the generated readable form of that graph, with all
  301 signatures grouped by request family and navigation stage, plus exact
  per-position suite symbols, literal cardinalities, and bounded examples.
- `docs/OBSERVED_RESPONSE_SHAPES.md` and
  `data/observed-response-shapes.json` provide the inverse real-Rekordbox
  index: every request kind present in canonical 7.2.19 goldens, its observed
  outcomes, exact immediate-reply signatures, separately attributed `0x3000`
  page signatures, row item types, source files, setup widths, and exact
  keepalive/status identity profiles. Its readable request table exposes exact
  profile and model counts, status-backed coverage, and setup widths. The five
  classified kinds without canonical responses remain an explicit gap table
  bound to all 222 declarations across their 36 suite files. Setup exchanges
  and asynchronous drains retain their own exact identity/setup coverage; a
  drained frame remains prior-transaction evidence rather than a reply to the
  following request.
- `data/device-behavior-matrix.json` consolidates ordinary identity invariance,
  seven status-backed surfaces, eight independent serving dimensions, static
  serving predicates, and native-status provenance without collapsing
  synthetic, derived, and captured controls.
- `docs/PHYSICAL_RX3_SESSION.md` is the complete ordered physical XDJ-RX3 session
  transcript, including native contexts, browse and prefetch cadence, selected-
  track payload requests, and the boundary between captured and 7.2.19 oracle
  evidence.
- `docs/XDJ_RR_CLIENT_NAVIGATION.md` maps 304 hash-pinned decompiled XDJ-RR direct
  call sites to 102 request kinds and literal/dynamic menu locations, including
  the functional roles of locations 4-8 and the source-defined location-9
  Delivery wrapper.
- `docs/XDJ_RR_ADJACENT_COMMANDS.md` joins the old-Key/Cue Track browsers and every
  directly reached XDJ-RR write/modification command to its exact Rekordbox
  target, reply constructor, database/filesystem effect, and live-test safety
  boundary. Its guarded old-Key/CueTrack campaign declares 48 real-Rekordbox
  cases with post-timeout health controls across three identity envelopes and
  both row widths.
- `docs/PROTOCOL_REFERENCE.md` is the detailed message, field, database and
  request-family reference derived from the exhaustive capture.
- `docs/DATABASE_QUERIES.md` and its machine-readable query map tie every declared
  request kind to tables, predicates, materialized rowsets, sorting, mutation
  behavior, rendering-time lookups, or an explicit absence of a database
  builder.
- `docs/DATABASE_FIELD_REFERENCE.md` and
  `data/database/link-export-schema.json` enumerate all 389 fields in the 22
  physical AppSync tables reached by that map, distinguish three runtime or
  alternate-interface names, provide a 95-row inverse request-kind index over
  families, operations, tables, and family-named fields, and label schema
  presence, exact SQL retrieval, and reconstructed semantic use separately.
- `docs/SQL_LITERAL_INDEX.md` separately indexes all exact SQL literals retained in
  the disassembly, including fragments and duplicate source provenance.
- `docs/ITEM_TYPE_REFERENCE.md` and `data/item-type-reference.json` catalog every
  one of the 85 represented `0x4101` item types across 51,148 corpus row
  occurrences, including menu, Song Info, synthetic, and track-composite roles
  with producing requests and source provenance.
- `docs/CONTROL_AND_MUTATION_REFERENCE.md` joins the complete write/database-modify
  and `0x3xxx` control namespace to Rekordbox routes and XDJ-RR caller sites.
- `docs/PACKED_CONTEXT_ORACLE.md` records the complete context-byte layout, exhaustive
  Track final-byte domain, row delta, static control flow, and provenance.
- `docs/CONFIGURATION.md` specifies root construction, capability bits, category and
  sort visibility, selected-column persistence, exact AppSync setting
  transactions, and the distinct Preferences-versus-renderer selected-row
  readers.
- `data/configuration-behavior-map.json` is the generated field-to-wire map for
  Category, Sort, Column, capability masks, refresh, and render-shape behavior.
- `docs/SECONDARY_COLUMNS.md` maps every secondary sort ID to its database value,
  wire type, and rendering behavior.
- `docs/SECONDARY_COLUMN_ORACLE.md` records all 15 live settings selections, the
  missing/multiple-selection states, exact row values, sort-menu coupling, and
  the complete 11-sort RX3 six-argument render cross with physical request
  provenance and fresh-process repeat.
- `data/experiments/physical-rx3-session/session-envelope.json` reduces the
  retained physical session to its exact player-11 setup, packed contexts,
  `0x05fdffff` root mask, root rows, and six-argument renders; its focused
  authority suite replays that envelope separately from the semantic sort
  matrix.
- `docs/KEY_NOTATION_ORACLE.md` separates the desktop key preference, local CDJ
  `DEVSETTING.DAT` style, and raw database spelling; it records exact Classic
  and Camelot behavior across key menus, collection and Smart rows, sorting,
  Display Song Info, and Delivery Info.
- `docs/HOT_CUE_BANK_ORACLE.md` proves the `0x2001` catalog request, tree and track
  modes, fourth-argument limit, exact rows, database predicates, player call
  sites, locations, invalid behavior, and retained fixture provenance.
- `docs/LINK_EXPORT_VISIBILITY_ORACLE.md` proves the exact `FolderPath` streaming
  predicate, fixed-provider classification, six filtered serving paths,
  persisted-History exception, and no-media requirement.
- `docs/CATEGORY_ORACLE.md` records every persisted category-disable mutation,
  complete ordering reversal, special disable bits, masks, and replay results.
- `docs/SORT_AND_COLOR_ORACLE.md` records every sort visibility toggle, complete
  ordering reversal, hidden selection, custom color labels, and replay results.
- `docs/SETTINGS_SESSION_REFRESH_ORACLE.md` records the Category/Sort/Column UI,
  active-Link edit lock, complete Column choices, and same-process refresh for
  category visibility, sort visibility/order, and Column selection.
- `docs/SEARCH_ORACLE.md` records Search request validation, token and Unicode
  matching, mixed entity/content rows, Category-controlled domains,
  pagination, static control flow, and rbxport differences.
- `docs/SMART_PLAYLIST_ORACLE.md` records rule/membership precedence, all operator
  codes over text and decimal BPM inputs, direct-child and ignored nested XML,
  malformed/parser boundaries, fixture fingerprints, and the rbxport gap.
- `docs/BOUNDARY_INVALID_LIFECYCLE_ORACLE.md` records numeric selector boundaries,
  string caps and stalls, invalid database values, track compatibility flags,
  Link History mutation, and their replay results.
- `docs/DISPLAY_SONG_INFO_ORACLE.md` records request `0x2002`, every fixed metadata
  row, ordinary/AIO ordering, database construction, status-packet lifecycle,
  dispatch path, and rbxport differences.
- `docs/SONG_INFO_SIBLINGS_ORACLE.md` records Play Song Info, Delivery Info, the
  four recognized no-builder kinds, complete row payloads, render selectors,
  pagination, malformed parser state, cross-family row-order state, database
  paths, and rbxport differences.
- `docs/USER_INFO_DJID_ORACLE.md` records the `0x3006`/`0x4d02` DJ-ID exchange,
  `djprofile.nxs` configuration and validation path, 160-byte reply builder,
  and CDJ-3000 post-load browsing dependency.
- `docs/PLAY_SONG_INFO_PATH_ORACLE.md` records every observed local/cloud path,
  file-presence, file-size, and hot-cue-auto-load branch.
- `docs/ROW_LAYOUT.md` follows track rows through the insert record, materialized
  list buffer, secondary reconciliation, flags, and 12/16-field wire layouts.
- `docs/LINK_EXPORT_REQUEST_VOCABULARY.md` separates the complete known client
  command vocabulary from Rekordbox 7.2.19's exact dispatch, rejection, reply,
  database, artwork, and analysis-file evidence, including the physical RX3's
  transaction-reusing `0x0001` cancellation command (called "invalid data" by
  Dysentery).
- `docs/ADJACENT_PAYLOAD_SERVICES.md` gives the direct-response artwork, waveform,
  beat-grid, cue, VBR, key, and analysis-atom contracts, including the active
  AppSync/fallback Master database split, deterministic success files, the
  JPEG/PMAI parser-boundary matrix, and decoded legacy/extended cue payloads
  over deterministic count, field, deletion, seek, device, and setup states.
- `docs/DEVICE_COMPATIBILITY.md` separates setup width, request capabilities,
  model-name classification, and per-track compatibility checks.
- `docs/DEVICE_MATRIX_ORACLE.md` records all named model identities, all four
  keepalive classes, generations 0/2/3, both setup widths, exact behavior
  hashes, and remaining cross-product work.
- `docs/DEVICE_PREDICATE_AUDIT.md` inventories 23 peer-identity and capability
  helpers, all 67 validated direct references, exact model literals, the three
  distinct AIO-like decisions, and their database-serving boundary.
- `docs/DEVICE_STATUS_PROVENANCE.md` separates captured hardware status packets from
  RX3-template-derived classifier probes and inventories the remaining native
  packet-source gaps.
- `docs/STATIC_ANALYSIS.md` pins the analyzed binary and records reproducible tools,
  addresses, generated evidence, and confidence limits.
- `docs/CONFORMANCE.md` specifies the fixture profiles, declarative oracle recorder,
  backend-neutral verifier, coverage/device matrices, and guarded VM workflow.
- `docs/CONFORMANCE_COVERAGE.md` is the requirement-to-suite ledger. Current work
  advances declarations through repeat-verified real-Rekordbox evidence; its
  replay columns preserve earlier historical results for context.
- `docs/REKORDBOX_RESEARCH_GAPS.md` is the real-Rekordbox-only completion ledger. It
  separates the active serial queue from native-packet, account-conditioned-provider,
  opposite-serving-role, and safety-boundary gaps.
- `conformance/` contains the Python protocol runner, fixture builder, suites,
  results, settings variants, matrix generator, VM switch scripts, and the
  explicit-opt-in backend adapters.
- `docs/GAP_MATRIX.md` compares rekordbox, `rbxport`, Dysentery/Beat Link and current
  observations.
- `docs/RBXPORT_AUDIT.md` records exact current implementation coverage and gaps.
- `docs/DYSENTERY_CROSSWALK.md` maps this work to the relevant Dysentery model.
- `docs/SETTINGS_EXPERIMENTS.md` defines reproducible one-variable settings tests.
- `docs/CLEANUP.md` inventories host changes, runtime state and retained artifacts.
- `data/` contains derived, reviewable datasets. Large source captures and
  binaries remain in their existing workspace locations and are named precisely
  in `docs/SOURCES.md`.
- `../dysentery/` is the local shallow clone of the upstream Dysentery research,
  pinned in `docs/SOURCES.md` by commit.

## Evidence labels

Statements in this research use these labels:

- **OBS**: directly observed in UI, packets, logs or a reproducible live test.
- **CAP**: derived from an existing packet capture.
- **DB**: derived from the copied rekordbox database or configuration files.
- **DEC**: derived from static inspection of the rekordbox executable.
- **RX3DEC**: derived from static inspection of the pinned XDJ-RX3 firmware.
- **RBX**: behavior or intent found in `rbxport`.
- **DYS**: behavior documented by Dysentery or Beat Link.
- **INF**: inference combining named evidence; not yet directly verified.
- **OPEN**: unresolved question or planned experiment.

Dates use America/New_York unless a capture or source explicitly uses UTC.

## Regenerating the indexes

From the repository root:

```sh
python tools/summarize_menu_tree.py data/source-menu-tree.json data
```

This deterministically rewrites `summary.json`, `menu-nodes.csv`,
`request-signatures.csv`, and `item-types.csv`. The source capture itself and
the checksum ledger are not modified.

The configuration export and static-analysis commands are documented in
`docs/STATIC_ANALYSIS.md`. They write only beneath this research directory.
`tools/update_checksums.py` regenerates the retained-artifact checksum ledger;
the real-Rekordbox campaign finalizers run it after writing their completion
receipts, and it excludes atomic `.next` promotion files. Run it manually after
other retained-artifact changes. Then
verify available artifacts with
`sha256sum --ignore-missing --check data/SHA256SUMS`. The ledger also names
retained local evidence that is intentionally outside the public Git tree.

## License

The repository is licensed under the [MIT License](LICENSE).
