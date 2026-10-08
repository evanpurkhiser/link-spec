# Link Export conformance coverage

This ledger maps the intended conformance surface to concrete fixtures and
suites. A declaration is only the first coverage stage. Each row advances
through five independently reviewable states:

1. **Declared**: deterministic fixture and suite cases exist.
2. **Recorded**: a canonical golden was captured from rekordbox 7.2.19.
3. **Repeated**: a second clean rekordbox run produced the same canonical data.
4. **Replayed**: a future implementation phase ran the identical suite and
   retained its actual response plus semantic diff.
5. **Verified**: the future implementation matched the complete envelope.

The current phase stops after repeated real-Rekordbox recording. Historical
rbxport columns remain provenance and are not extended by current work.

The `full` and `empty` XDJ-RX3 rows have real 7.2.19 goldens and independent
repeat passes. The private L2 segment has no physical member, so synthetic
discovery cannot reach the physical RX3.

## Declared corpus

The corpus contains 5,730 case declarations in 933 suite files. This is the
recursive count of every `*.json` under `conformance/suites/`; every file is a
suite with a nonempty `cases` array. The Python runner test recursively reads
the same set, validates it with the runner's schema, and rejects an empty suite.
`generate_matrices.py` and the focused matrix generators own the mechanical
declarations.

Those cases declare 95 distinct request kinds; 74 already have completed live
menu-oracle coverage. The generated
`data/static-analysis/menu-database-query-map.json` assigns every declared kind
exactly once across 47 database-path families. The assignment records tables,
predicates, ordering, result semantics, and evidence, or explicitly classifies
a rejected/recognized kind as having no database builder. Its focused test
derives the domain from the suite files, so adding a request kind without
documenting its database behavior fails validation.

`data/static-analysis/link-export-navigation-graph.json` adds the transition
view of the same domain: every request has a named menu stage and terminal
response class; hierarchy edges are explicit; recursive Playlist and Hot Cue
Bank paths have self-edges; and all list-buffer paths point to `3000` rendering.
The generated vocabulary partitions these 95 kinds into 74 live menu-oracle,
16 exact static-dispatch, and five recognized log-only kinds. The graph also
projects 301 distinct argument-count/wire-type signatures directly from the
hash-pinned 933-suite, 5,730-case declaration corpus, including implicit render
requests.

| Requirement | Fixture/suite | Declared | Recorded | Repeated | Replayed | Verified |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Complete known request/reply vocabulary | 185-kind generated ledger joining the pinned 173-name CDJ-3000 enum, the physical RX3 `0x0001` client control, conformance probes, Rekordbox-only arms, the 74-kind live menu corpus, and exact switch/direct dispatch | Yes | 74 menu kinds live; 54 adjacent kinds exact-static; 27 rejected; eight log-only; one physical-client control; zero source-only; every physical RX3 request kind is accounted for | Byte-identical extractor/generator, physical-PCAP hash, top-level/default-reply, Year-table, and direct-client-handler tests | Deferred | Adjacent static commands remain live-oracle gaps; `0x0001` is retained as client control rather than ordinary server dispatch |
| User info / DJ ID (`0x3006` / `0x4d02`) | Ten authority executions and 142 cases: ordinary RX3, genuine RX3-status, and CDJ-3000-status identities; argument counts 0-32; string/blob type substitutions; packed-context boundaries; absent, valid, checksum-invalid, short, long, wrong-extension, and directory-at-target profile states | Yes | Pending behind the guarded render-control queue; static 7.2.19 evidence establishes the four-argument empty reply and 160-byte DJ-ID construction, but supplies no live outcome | Declared as 284 fresh-fixture/process record/repeat executions with profile-state hashes, process health, exact typed replies, guest backup/restoration, per-execution receipts, strict reduction, and final stopped-VM receipt | Deferred | Record the live matrix and promote only observed authority results |
| Production-shaped streaming-provider paths | `streaming-provider-paths` / `generated/streaming-provider-paths.json` (7): local, exact Beatport path, URL/mid-string variants, case variation, missing slash, singular path, Beatport/Beatsource URI syntax, and near-match controls across Collection default/Key, File Name, ordinary playlist, Smart playlist, Search, and History | Yes | Pending behind the user-info/DJ-ID authority stage; the pinned 7.2.19 manager audit predicts only the three case-exact `/v4/catalog/tracks/` substring rows are filtered from ordinary serving, while History remains unfiltered | Declared as 14 fresh-fixture/process record/repeat executions with exact observed ContentID sets, static-prediction conflicts, fixture/golden hashes, baseline restoration, and final stopped-VM receipt | Deferred | Promote only real-Rekordbox rows; account-conditioned roots and other Rekordbox versions remain separate questions |
| Adjacent artwork, analysis, and cue payload services | `adjacent-payload-fileless.json` (196): all 16 exact dispatch kinds x packed track types 0-6, zero/maximum content IDs or complete contexts as applicable, representative location bytes, and specified-atom tag/extension gates; 96 generated one-case malformed suites: six cold-process arity/type/tag-list probes per kind; `adjacent-payload-missing-files.json` (31): ten filesystem-backed kinds x nonempty missing, empty, and SQL-null paths plus playlist artwork; `adjacent-payload-success.json` (15): deterministic JPEG plus DAT/EXT/2EX success controls across all ten filesystem-backed kinds; four status/setup success suites (60): genuine RX3 player 11 and matched CDJ-3000 player 1 x extended/legacy setup; 30 generated parser-boundary suites (57): JPEG 1 MiB and 800-pixel gates, PQTZ 6,248-beat ceiling, PWAV/PWV2/PVBR fixed-count edges, PWV3/PKEY count and stride behavior, and duplicate aligned/unaligned specified atoms; eight cue-payload suites (114): successful `2104`/`2b04`, 0/1/3/255/256 rows, every serialized field, null/deleted controls, isolated seek states, type/location invariance, and genuine RX3/CDJ x setup width | Yes | Fileless complete: exact repeat across 196 cases, 176 replies and 20 healthy timeouts; malformed complete: exact independent-process repeat across 96 cases, 80 replies and 16 healthy timeouts; missing-path complete: 31/31 paths return exact service envelopes; baseline valid assets complete: 15/15 direct replies, 12 payload-bearing, with exact JPEG, analysis, VBR, segmented-key, EXT, and 2EX bytes and observed empty/scalar `2204`/`2504`/`2804`; status/setup, parser-boundary, and cue matrices remain in the guarded queue | Every semantic, path, success, and boundary case uses a fresh connection; every malformed or risky seek case receives an independent process; staged assets are verified inside the guest before every cold pass and removed after baseline restoration; cue replies are decoded into 36-byte legacy records, timing extensions, and variable-width extended records; difference-preserving reducers retain outcomes and payload signatures; all generators, fixture hashes, reducers, cleanup ordering, and the 16-kind static service map have tests | Deferred | Complete the remaining guarded stages and interpret exact boundary and seek-parser transitions |
| Complete populated navigation tree | `full` / `full.json` (47) | Yes | Yes | Yes | Yes | No |
| Hot Cue Bank request discovery and full tree/membership/count matrix | `full` discovery (11) plus `hot-cue-banks` / `hot-cue-bank-matrix.json` (31) | Yes | Yes | Yes | Deferred | Deferred |
| Hot Cue Bank location/render forms and state | Matching controls (10), complete header-location x render-location x six/eight-argument cross (32), and distinct-selector stale-buffer sequence (8) | Yes | Yes: matching locations render; uninitialized foreign locations time out; initialized foreign locations return stale location-keyed rows across fresh TCP connections; all processes remain responsive with zero new Application errors | Yes | Deferred | Known location/form cross complete; buffer invalidation and player UI state remain separate |
| XDJ-RR client navigation and complete source-defined location domain | Hash-pinned extraction of 121 request wrappers and 304 direct call sites over 102 kinds; literal locations `1..8`; constructor-fixed location-9 Delivery wrapper; six location-9 suites (36 cases) across ordinary/RX3/CDJ identities and both row widths | Yes | Locations `1..8` have live generic evidence; location-9 matrix is pending behind the cue-payload stage | Independent cold record/repeat per variant; health and hash receipts; distinguishable-track current/stale-buffer assertions; identity equality and legacy-prefix reducer | Deferred | Complete the guarded location-9 handoff and interpret exact buffer behavior |
| XDJ-RR old-Key and CueTrack browser | Exact client constructors and Rekordbox `OnKeyListCmd`/`OnListClientCmd` targets; six suites declare 48 cases across locations 1/2, ordinary/RX3/CDJ identities, and both setup widths | Yes | Static terminal paths are exact; live evidence is pending behind location 9 | Independent cold record/repeat, strict root/track totals, two bounded silent probes, fresh-connection post-timeout health controls, model/setup signatures, and legacy-prefix analysis | Deferred | Complete guarded recovery generation `ae18` and interpret any identity-dependent row differences |
| Hot Cue Bank buffer lifetime across device disconnect | Cold-process control and 40-second same-identity disappearance/rejoin arms; location-1 root warmup followed by location-2 Beta header rendering old location 1 and current location 2; two runs per arm | Yes | Yes: both arms repeat exactly; old location 1 returns item 9002 and current location 2 returns item 9032 after both continuous-presence and disappear/rejoin sequences | Yes | Deferred | Device disconnect does not clear context-keyed rows; database close/reopen remains separate |
| Hot Cue Bank buffer lifetime across same-process LINK toggle | Existing distinguishable location-1 root and location-2 Beta suites; two uninterrupted controls and two supported LINK deactivate/reactivate runs | Yes | Pending behind the corroborating XDJ-XZ stage | Each run receives a fresh encrypted fixture and Rekordbox process, five schema-2 health captures, explicit port-12523 absent/present proof, same-PID assertion, complete typed warmup/post responses, and a hash-bound receipt; the reducer accepts only the already characterized persisted or cleared old-location shapes and requires exact within-arm repeat | Deferred | Complete guarded generation `ag18` and promote the observed buffer-invalidation rule |
| Hot Cue Bank complete count boundary | Track-mode count 17, 255/256, 65535/65536, 1048576, `INT32_MAX`, `0x80000000`, and `UINT32_MAX` over the ten-row resolvable bank | Yes | Yes: all signed-positive controls return ten rows; both bit-31 controls return normal empty menus; all isolated processes stayed responsive with zero new application errors | Yes | Deferred | Active AppSync path complete; alternate master-database implementation remains a path-selection question |
| Hot Cue Bank large-bank pagination | `hot-cue-bank-pagination` / 70 deterministic memberships; page sizes 1/32; explicit 32/32/6 pages; both page boundaries; zero/end/past-end/overrun/overlap/max-offset windows (15) | Yes | Yes: complete ordered walks, clamp/right-alignment rules, duplicate overlap row, and maximum-offset render timeout | Yes | Deferred | No known catalog-render pagination gap |
| Hot Cue Bank cue-info and mutation direct responses | Legacy `2101`/`4702`; extended `2301`/`4e02`; counts 0-8; populated/empty/error; legacy/stateful; RX3/RR; status/no-status; compact/fixed tags; fixed and option fields; comments and seek controls; `2401` before/set/after with single-row controls; `2201` known/unknown bank/content and wrong-slot controls; complete D/E/F mutation matrix; eleven outside-gate ordinal controls through `0xffff`; live-WAL database proofs for mutations and acknowledged no-ops | Yes | Yes: decoded `4702`/`4e02`, exact extended echo/readback, ContentID-specific legacy replies, exact 4/5/6 mutation gate, field-level durable deltas and non-deltas | Yes | Deferred | Complete for real Rekordbox together with the adjacent extended-parser, mutable-field, seek-descriptor, legacy-parser, and identical-request lifecycle matrices |
| Extended Hot Cue setter parser and reply lifecycles | 57 one-axis structural probes; 20 declared-length `UINT32_MAX` timing cells with three observations each; three cold-process slot-8 observations; and three cold-process returned-slot `UINT32_MAX` observations, each retaining immediate getter, health, database state, and same-database restart getter | Yes | Yes: 54 ordinary variants, declared-length `UINT32_MAX` 60/60, slot 8 3/3, and returned-slot `UINT32_MAX` 3/3; the combined strict summary covers 366 evidence cases | Exact repeats for every ordinary variant; strict hash-bound lifecycle reducers preserve measured transport and database behavior | Deferred | Complete for real Rekordbox: returned-slot `UINT32_MAX` commits before its reply getter stalls, and restart returns the identical canonical mutation in all three runs |
| Extended Hot Cue setter mutable fields | 56 one-axis probes: signed extrema for milliseconds and four MPEG fields; complete byte controls for color and color-table index; unsigned/signed boundaries for microseconds and beat-loop packing; empty, ASCII, Unicode, embedded-NUL, unpaired-surrogate, and maximum-even-length UTF-16 comments | Yes | Yes: strict reducer accepted 56/56 variants and 112 fixture/process executions; maximum Comment has exact 8,192-byte response-prefix and 65,656-byte declared-record validation plus complete 32,766-character database proof | Yes: independent fixture/process repeat and hash-bound database receipts for every variant | Deferred | Complete for real Rekordbox; seek descriptors are covered by the adjacent completed health-aware matrix |
| Extended Hot Cue setter seek descriptor | 17 health-aware probes: available-byte boundaries `74/81/82/121/122/123/124`, descriptor lengths `0/1/43/44/45/UINT32_MAX`, inbound validity `0/1/UINT32_MAX`, and outbound-only validity | Yes | Yes: strict reducer accepted all 17 variants and 34 cold-process runs; 14 controls return the canonical status-zero record, while length 82 and both nonzero inbound-validity forms commit seek strings before timeout and process replacement | Exact response, health class, deterministic database values, and repeat assertions; the 82-byte uninitialized values retain exact evidence and compare by unsigned-triplet shape | Deferred | Complete for real Rekordbox; the out-of-bounds copy and getter interior-free fault are localized statically and dynamically |
| Legacy Hot Cue setter parser safety matrix | 57 declared `0x2201` probes: actual/declared cue lengths, full accepted flag interval and neighbors, actual/declared extension lengths, ContentID resolution, and zero/maximum values for fixed words 2-8; two isolated processes, health/event capture, conditional getter, live database snapshot, same-database restart after unavailable getters, and request-equivalence audit | Yes | Yes: strict reducer accepted 57/57 repeat pairs across 114 independent processes; both cue-length axes, the complete 12-value flag axis, both six-value extension-length axes, all four ContentIDs, and every fixed word from 2 through 8 are repeat-verified; mutation requires both cue lengths equal 36; exact flag admission is inclusive `0x00040000..0x0006ffff`; actual extension lengths 0..8 are zero-padded and bytes after eight are ignored; declared zero commits a zero-filled mutation before empty `0x0100`; declared one/seven share crash `0xc0000374` with pristine state; one identical canonical request has four earlier healthy pairs and three later port-query-outage pairs, so the lifecycle cannot be attributed to declared length eight; ContentIDs zero/`UINT32_MAX`/999999/10001 return zero/zero/one/two cue records after their mutations, with unresolved IDs returning status one; fixed word 2 is dynamically ignored, and words 3 through 8 map solely to `InFrame`, `OutFrame`, `InMpegFrame`, `OutMpegFrame`, `InMpegAbs`, and `OutMpegAbs`; declared `UINT32_MAX` returns empty `0x0100`, remains pristine, and times out the immediate getter | Hash-bound setter/health/database/getter/restart receipts preserve raw transport timing and post-failure health; request fingerprints group nominal axes by actual input and expose lifecycle conflicts; `fixed_word_analysis` requires each completed zero/maximum pair to change exactly its decompiled field; stable crash signature plus durable restart state define within-variant equivalence, and `transport_repeat_exact` reports stricter equality separately | Deferred | Complete for real Rekordbox, including the separately completed interleaved history control |
| Legacy identical-request lifecycle history | Two cycles interleave four byte-identical canonical setters around declared-extension-length one/seven crash setters and a full isolated-VM restart: 12 request observations, four VM restarts, cold Rekordbox per request, schema-2 helper/listener/process/Application/database/getter evidence | Yes | Yes: all eight canonical requests share one status-zero/mutated/immediate-port-query-timeout/restart-changed lifecycle; both crash phases repeat pristine durable state, while cycle-specific lifecycle groups preserve Application-event timing and length-seven disconnect-versus-timeout variation | Hash-bound phase/cycle/finalization receipts; reducer separates exact durable state from transport/process/getter/event telemetry; successful 66-test gate, baseline restore, zero identities, and stopped VM | Deferred | Complete for real Rekordbox 7.2.19 |
| Hot Cue Bank deleted-bank predicate split | Soft-deleted bank with one live membership crossed through parent tree, direct catalog, legacy cues, and extended cues | Yes | Yes: hidden tree node; direct track and both cue formats served | Yes | Deferred | No known gap in the bank-deletion predicate split |
| Backend-returned selector navigation | `full` / `chained-navigation.json` (16) | Yes | Yes | Yes | Yes | No |
| Empty database behavior | `empty` / `empty.json` (21) | Yes | Yes | Yes | Yes | No |
| Legacy 12-field and extended 16-field rows | `full` / `legacy.json`, `full.json` | Yes | Yes | Yes | Yes | No |
| Root capability masks | `full` / `generated/root-capabilities.json` (31) | Yes | Yes | Yes | Yes | No |
| Requested sort IDs 0-17 | `full` / `generated/sort-ids.json` (18) | Yes | Yes | Yes | Yes | No |
| RX3 active sort x six-argument track render | `full` / `generated/sort-secondary-render-6.json` (11): Default, Alphabet, Artist, Album, BPM, Rating, Genre, Label, Key, Date Added, and DJ Play Count, plus retained physical RX3 request extraction | Yes | Yes: all 88 complete rows; fixed render argument 6 value `12`; exact arguments 0, 5, 6, and 12-15 | Yes: independent fresh-fixture/process repeat, four health captures, hash-bound golden/CSV/PCAP receipt | Deferred | Complete for the visible RX3 Sort menu; exact player-11/location-1/slot-4 replay is separated below |
| Physical RX3 setup/context/root/render envelope | `full` / `generated/physical-rx3-session-envelope.json` (2): legacy device 11, main-menu context `0x0b010401` (location 1, Rekordbox slot 4, track type 1), root mask `0x05fdffff`, and six-argument Default-track render | Yes | Complete retained transcript covers 106 client messages, 268 server messages, 144 rows, four contexts, and 23 hashed binary payloads; fresh 7.2.19 response golden is pending behind the serial authority queue | Declared authority-only with captured-status identity, fresh fixture/process repeat, health evidence, physical-PCAP hash, deterministic transcript and strict reducer, cleanup, and stopped-VM finalization | Deferred | Separates the physical request shape from the unknown Rekordbox version in the retained capture; see `PHYSICAL_RX3_SESSION.md` |
| RX3 active sort x five-argument track render | `full` / `generated/sort-secondary-render-5.json` (11): the same visible-sort set with `[context, offset, count, 0, total]` rendering | Yes | Pending real-Rekordbox rows; reducer preserves arguments 0, 5, 6, and 12-15 and reports exact equality/divergence against the six-argument golden | Declared: guarded fresh-fixture/process record and repeat after the active serial queue | Deferred | No result is inferred from the six-argument oracle |
| RX3 active sort x seven-argument track render | `full` / `generated/sort-secondary-render-7.json` (33): all 11 visible sorts x wire argument 7 values zero, one, and `UINT32_MAX` | Yes | Pending real-Rekordbox rows; source-derived decoder boundary predicts argument 7 is unread below eight arguments | Declared: guarded fresh-fixture/process record and repeat after the five-argument cross | Deferred | Reducer reports exact equality/divergence against six-argument rows without assuming the static prediction is live truth |
| Track render arities 3 through 32 | `full` / `generated/render-arity-boundaries.json` (70): complete Default-sort count sweep plus every non-default visible sort at 3/4/9/32 | Yes | Pending authority outcomes; overlong fields use position-distinct sentinels and every declaration accepts reply/error/timeout/disconnect | Declared: guarded fresh-fixture/process record and repeat after the seven-argument cross | Deferred | Count 33 remains the separately recorded malformed-framing ceiling control |
| Track render arities 0 through 2 | `full` / `generated/render-arity-underflow.json` (9): a valid Default Track list, same-connection correctly framed underlength render, and fresh-connection health control for each arity | Yes | Static decoder audit proves missing slots are zero and projects `[0,0,0]`, `[context,0,0]`, and `[context,offset,0]`; response/transport outcomes remain pending authority observations | Declared: guarded fresh-fixture/process record and repeat after the 3-32 sweep | Deferred | Distinguishes initialized-list parsing from the existing pre-list render control |
| Track render argument types | `full` / 16 generated two-case suites: valid Default Track warmup followed by an eight-argument `0x3000` with exactly one of positions 1-8 replaced by string or blob | Yes | Static decoder audit proves tag-2/tag-3 preceding-length dependencies, position-1 rejection, pointer-valued decoded slots, and untyped render-slot reads; all reply/timeout/disconnect/process outcomes remain pending real authority | Declared: 16 independently cold record/repeat probes after the arity-underflow stage, with four health captures and a receipt per probe | Deferred | Preserves normal neighboring values instead of manufacturing parser-admissible lengths; parser rejection is an observed outcome, not a failed setup |
| Track render numeric fields | `full` / `generated/render-numeric-fields.json` (42): normal control, 15 position-4 seek keys, six position-5 client totals, and 20 position-6 category IDs | Yes | Static audit proves position 4 is a low-word normalized first-character seek, position 5 is unread, and position 6 is a low-word sparse `DBCommon_GetCateKind` lookup; returned rows remain pending real authority | Declared: guarded fresh-connection record/repeat after the argument-type matrix, with four process/Application health captures | Deferred | Covers every category-map equivalence range, zero/`0xffff` boundaries, representative characters, and high-word aliases without assuming static/live equality |
| Track render override controls | `full` / `generated/render-override-controls.json` (17): Artist control, five argument-7 gate boundaries, and eleven argument-8 selector boundaries | Yes | Static audit proves argument 7 is canonicalized from 32 bits to boolean, while argument 8 reaches icon dispatch as a signed low byte and the secondary extractor as the full 32-bit value; returned rows remain pending real authority | Declared: guarded fresh-connection record/repeat after the numeric-field matrix, with four process/Application health captures | Deferred | Covers selector zero/one, reserved 14, valid 17, first invalid 18, low-byte wrap, a high-word Artist lookalike, and signed/unsigned 32-bit boundaries |
| Location-2 malformed-history timing | Seven three-case suites hold the authentic RX3 player-11 `play-extra-argument -> delivery-blob-content -> Delivery probe` sequence fixed and vary only a 0/50/100/250/500/1000/3000 ms delay before the probe connection; four cold-process observations each | Yes | Yes: 0 ms is four-of-four zero; every 50-3000 ms cell is four-of-four 13 | Yes: 28 receipt/hash/context/health-validated observations, clean finalization, quarantined mixed-player controls | Deferred | Establishes immediate-versus-delayed boundary; routing matrix identifies the response owner |
| Location-2 malformed-history delayed-reply routing | Malformed blob Delivery and valid extra-argument Delivery controls x 0/50/100 ms replacement delay x four cold processes; replacement setup, no-send read, same-socket probe, and fresh health probe | Yes | Yes: all 24 setups are setup-only; four immediate malformed runs receive identical transaction-1 `0x4000 [0x2602, 0]`; the other 20 no-send reads time out; all 48 probes return 13 | Yes: 24 observation receipts, 48 health captures, static/declaration/pinned-binary hashes, aggregate CSV/summary, exact failed-attempt provenance, clean finalization | Deferred | Proves pair-48 zero is an orphaned prior reply, not valid-probe output or persistent builder state; ordered-pair runner must model/drain the lifecycle |
| Location-2 malformed-history lifecycle-aware ordered pairs | Complete 16 x 16 ordered precursor cross; three fresh connections per pair; every connection retains setup, performs a 1200 ms no-send drain, then sends its declared request; a blob-valued Delivery is followed by a measured 3000 ms no-client settling interval before the next connection; fresh fixture/process record and repeat | Yes: 256 suites / 768 declared requests / 1,536 authority executions | Active: the partial reducer verifies 198 promoted pairs / 594 request executions; generation `z34` completed all 16 successors after blob-valued Play and all 16 after zero-context Play. The complete alternate-location-Play, argumentless-Delivery, missing-content-Delivery, and extra-argument-Delivery rows each preserve every successor's ordinary result. In each row, blob-content Play queues its exact delayed `0x2102` frame into the health drain; every other drain is silent, including blob-content Delivery after its measured no-client interval, and every health request returns 13 rows. Every extra-argument-Delivery precursor returns 13 rows. The first six string-context-Delivery pairs preserve argumentless Play's timeout, missing- and string-content Play's zero-row menus, extra-argument Play's seven-row menu, and the string- and blob-context Play headers without totals, with three silent drains and 13-row health. The divergent `z34` pair-135 runs remain quarantined; `z35` promoted two wholly fresh delayed-frame runs | Receipt-backed pairs are hash-verified and resumable; setup, settling delay, and drain fields participate in exact behavior equality; pair-99, pair-104, pair-106, pair-111, and pair-135 race attempts remain retained; pair-141 activation/readiness/guard and pair-194 activation attempts remain hash-bound; final reducer, health, cleanup, and checksum gates run only after all 256 pairs | Deferred | Separates queued player-routed traffic from each new transaction while preserving the original semantic pair matrix; immediate drain connections can still race orphan delivery, so promotion requires exact repeat rather than inferred normalization |
| Packed player/location/slot context candidates | `full` / `generated/contexts.json` (19) | Yes | Yes | Yes | Yes | No |
| Packed Track final-byte domain | `full` / `context-track-types.json` (256) | Yes | Yes: 254 eight-row menus; `0x03`/`0x04` time out; only `0x01` preserves argument-10 `0x100` | Yes | Deferred | Complete byte domain |
| Packed context across all list families | `full` / `context-track-type-families.json` (329) | Yes | Yes: all 47 families x types `0x00..0x06`; exact pre-header gate, Root/Search admission, argument-7 propagation, and argument-10 enrichment | Yes | Deferred | Additional status/setup identity crosses remain |
| Packed context across Song Info | `full` / `context-analysis-track-types.json` (49) | Yes | Yes: Display/Play/Delivery accept only type 1; Rekordbox-local no-builder kinds return `0x4003`; every type reaches class-2 dispatch | Yes | Deferred | Player-hosted builders are statically documented; native response capture remains |
| Packed context across Hot Cue Bank | `hot-cue-banks` / `context-hot-cue-track-types.json` (21) plus `context-hot-cue-catalog-status*.json` under matched RX3/CDJ status and both setup widths (84) | Yes | Yes: type 1 returns tree/populated/empty totals 3/8/0; every other type advertises 50 rows then times out after a 32-row render request; normalized identities are equal and legacy rows are exact extended-row prefixes | Yes | Deferred | Additional genuine model status shapes remain |
| Packed context x ordinary identity x setup width | `context-device-setup-{extended,legacy}.json` (16 each) across eight identities | Yes | Yes: 16 goldens/256 cases; all identity envelopes equal within setup; legacy rows are exact 12-field prefixes; routing and arguments 7/10 invariant | Yes | Deferred | No known ordinary-identity/setup gap |
| Packed Display context x status source x requester x setup | `context-display-status*.json`: authentic RX3 player 11, RX3-template-derived CDJ-3000 player 1, and RX3-status/requester-1 control (42 cases) | Yes | Yes: only type 1 succeeds; exact ordinary/AIO property order; requester-keyed classification; legacy prefix equality | Yes | Deferred | Other class-2 builders and native status shapes remain |
| Packed Play context x status source x setup | `context-play-status*.json`: authentic RX3 player 11 and RX3-template-derived CDJ-3000 player 1 (28 cases) | Yes | Yes: only type 1 succeeds; normalized identity envelopes are equal within setup; legacy prefix equality | Yes | Deferred | Additional native model shapes remain |
| Remaining Song Info class-2 context x status source x setup | `context-class2-status*.json`: Delivery and recognized kinds `2202`-`2502` under authentic RX3 player 11 and derived CDJ-3000 player 1 controls (140 cases) | Yes | Yes: Delivery admits only type 1; all no-builder kinds return kind-specific `4003`; normalized identities are equal; legacy prefix equality | Yes | Deferred | Additional native model shapes remain |
| Historical RX3 location-2 malformed-history ordered pairs | 16 malformed Play/Delivery precursor forms crossed as ordered pairs in cold-process suites, each followed by the matched location-2 Delivery probe | Yes | 47 pairs promoted; pair 48 retained a record/repeat 13-versus-zero conflict and halted the original queue | The conflict is explained by the completed timing/routing oracle: an immediate replacement can receive the prior player-routed reply. Historical goldens and conflict captures remain immutable | Deferred | Superseded for exhaustive execution by the lifecycle-aware 256-pair row above, which drains every fresh connection before its declared request |
| Hot Cue direct getters x packed type x status source x setup | `context-hot-cue-getter-status*.json`: legacy `2101` and extended `2301`, populated/empty selectors, authentic RX3 and derived CDJ-3000 controls (112 cases) | Yes | Yes: type 1 returns database payloads; all other types return direct status 50 with empty blobs; identities and setups are byte-equal after request removal | Yes | Deferred | No known getter admission gap within these controls |
| Extended Hot Cue setter x packed type x status source x setup | `context-hot-cue-setter-status*.json`: `2401`, all seven packed types, authentic RX3 and derived CDJ-3000 controls, extended/legacy setup, and a type-1 database read after every setter (56 cases) | Yes | Yes: type 1 mutates and reads back the canonical record; all other types return status 50 and every following getter proves the pristine record; complete decoded sequences are identity/setup invariant | Yes | Deferred | Additional native model status shapes remain |
| Legacy Hot Cue setter x packed type x status source x setup | `context-hot-cue-legacy-setter-status*.json`: `2201`, all seven packed types, authentic RX3 and derived CDJ-3000 controls, extended/legacy setup, and a type-1 six-slot membership read after every setter (56 cases) | Yes | Yes: type 1 mutates slot 4 only; all other types return the legacy status-50 envelope and every following getter proves pristine D/E/F records; complete decoded sequences are identity/setup invariant | Yes | Deferred | Additional native model status shapes remain |
| Common render request arities 5, 6, and 8 | `full` / `generated/render-*.json` | Yes | Yes | Yes | Yes | No |
| Render-time secondary gate and overrides | `full` / `generated/render-secondary-controls.json` (19) | Yes | Yes | Yes | Yes | No |
| Every persisted secondary-column selection | 15 extended `settings` suites (30), 15 matching legacy suites (30), and 42 string/UTF-16 boundary cases | Yes | Yes: all 15 selections under both setup widths; legacy Sort menus/results match and every row is the exact 12-field extended prefix | Yes: 15/15 legacy variants have hash-bound fresh-fixture/process repeat receipts | Historical extended results only; current work deferred | Deferred |
| Smart playlist persisted secondary selection | 15 selected columns plus no/multiple-selection controls (17) | Yes | Yes | Yes | Yes | No |
| Desktop Classic/Alphanumeric and normalized/database key preferences | four generated suites, 13 cases each (52) | Yes | Yes | Yes | Yes | No |
| Local CDJ Classic/Alphanumeric key style | two `DEVSETTING.DAT` suites (26) plus persisted ordinary/Smart BPM controls (3) | Yes | Yes | Yes | No | Yes |
| BPM/year/time/play-count numeric boundaries | `boundaries` / `boundaries.json` (30) | Yes | Yes | Yes | Yes | No |
| BPM ±0–6% inclusion edges | `bpm-tolerance-boundaries` / `bpm-tolerance-boundaries.json` (7) over 43 one-hundredth-BPM controls bracketing the special zero-percent whole-BPM bucket and every nonzero percentage edge | Yes | Yes: tolerance zero is inclusive 119.50–120.49 around 120.00; tolerances 1–6 include both integer-truncated endpoints and exclude both immediate outside neighbors; totals nest as 5/11/17/23/29/35/41 | Exact independent fixture/process repeat, encrypted fixture fingerprint, and static-predicate cross-check | Deferred | Complete for real Rekordbox |
| Rating/Bitrate/Color complete selectors and hidden-domain boundaries | `scalar-selector-drilldowns.json` (32) and `scalar-selector-boundaries.json` (7) | Yes | Yes | Yes | Yes | No |
| Smart playlist Attribute/rule/membership precedence | `smart-playlists` / `smart-playlists.json` (12) | Yes | Yes | Yes | Yes | No |
| Smart rule operators, groups, and parser defaults | `smart-rule-matrix` / `smart-rule-matrix.json` (39) | Yes | Yes | Yes | Yes | No |
| Smart stored-scale numeric comparisons and conversion boundaries | `smart-numeric-matrix` / `smart-numeric-matrix.json` (60) | Yes | Yes | Yes | Yes | No |
| Smart SQL null, REAL fraction, wide-integer, and missing numeric-attribute conversion | `smart-numeric-boundaries` / `smart-numeric-boundaries.json` (100) | Yes | Yes | Yes | Yes | No |
| Smart property vocabulary, field mapping, My Tag representation, and aliases | `smart-property-matrix` / `smart-property-matrix.json` (33) | Yes | Yes | Yes | Yes | No |
| Smart fixed-date equality, ordering, ranges, blanks, and malformed values | `smart-date-matrix` / `smart-date-matrix.json` (30) | Yes | Yes | Yes | Yes | No |
| Smart relative-date units, counts, lower boundaries, invalid values, and future dates | `smart-relative-date-matrix` / `smart-relative-date-matrix.json` (56) | Yes | Yes | Yes | Yes | No |
| Smart fixed-date parser length, separators, character classes, normalization, and null values | `smart-date-format-matrix` / `smart-date-format-matrix.json` (117) | Yes | Yes | Yes | Yes | No |
| Smart text operators, ICU collation, normalization direction, Unicode scripts, entities, empty/null, and embedded NUL | `smart-text-matrix` / `smart-text-matrix.json` (55) | Yes | Yes | Yes | Yes | No |
| Smart string collation across nine lookup and four direct properties, including empty names and missing relations | `smart-string-property-matrix` / `smart-string-property-matrix.json` (104) | Yes | Yes | Yes | Yes | No |
| Smart My Tag operators, signed parsing boundaries, ignored fields, and multi-tag Boolean logic | `smart-mytag-matrix` / `smart-mytag-matrix.json` (49) | Yes | Yes | Yes | Yes | No |
| Smart XML document/root/child structure, malformed forms, attributes, entities, case, and integer coercion | `smart-xml-matrix` / `smart-xml-matrix.json` (73) | Yes | Yes | Yes | Yes | No |
| Smart result sort IDs, secondary render controls, pagination, packed contexts, and both setup widths | `smart-serving-crosses.json` (65) and `smart-serving-legacy.json` (1) | Yes | Yes | Yes | Yes | No |
| Smart populated/empty results across every ordinary device identity | `smart-device-cross.json` (2) across eight identity goldens | Yes | Yes | Yes | Yes | No |
| File Name formatting, Unicode width, and all sort IDs | `filename-boundaries` / `filename-boundaries.json` (18) | Yes | Yes | Yes | Yes | No |
| Invalid/null/dangling database values | `invalid` / `invalid.json` (15) | Yes | Yes | Yes | Yes | No |
| Soft-deleted content exclusion | `full`, `boundaries` track cases | Yes | Yes | Yes | Yes | No |
| File type/sample rate/bit depth compatibility | Sampled `compatibility.json` (2), plus exhaustive extended/legacy suites over 382 deterministic rows: all 256 FileType bytes, 14 wide narrowing controls, 56 SampleRate boundaries, and 56 BitDepth invariance controls | Yes | Yes: 382/382 rows in both setup widths; 298 supported and 84 unsupported; exact byte/wide/rate predicate and BitDepth invariance | Independent cold-process record/repeat, clean schema-2 health, hash-bound setup/finalization receipts, backend/suite/fixture/identity guards, and exact 12-field legacy-prefix equality | Historical sample only; current replay deferred | Complete for real Rekordbox 7.2.19; backend comparison remains deferred |
| Category disable special cases | `category-special-bits.json` (2) | Yes | Yes | Yes | Yes | No |
| Every persisted category disabled alone | 21 generated settings/suites | Yes | Yes | Yes | Yes | No |
| Complete category order reversal | `category-order-reversed.json` | Yes | Yes | Yes | Yes | No |
| Every persisted sort visibility toggled alone | 17 generated settings/suites | Yes | Yes | Yes | Yes | No |
| Complete sort order reversal | `sort-order-reversed.json` | Yes | Yes | Yes | Yes | No |
| Hidden selected secondary sort | `hidden-selected-comment.json` (2) | Yes | Yes | Yes | Yes | No |
| Missing/multiple secondary selections | Two settings fixtures and suites | Yes | Yes | Yes | Yes | No |
| Supported settings session refresh | UI lock plus repeated same-process Album category removal, Comments sort activation, and KEY-to-COMMENTS Column probes | Yes | Yes | Yes | N/A | Yes |
| Search and Search Track matching, Unicode/NUL, Category-gated domains, sort paths, and ceilings | `search.json` (44), four Category settings suites (16), `search-ceiling.json` (16), `search-text.json` (19), `search-track.json` (34), `search-track-ceiling.json` (12), and `search-track-large-title-sort.json` (19) | Yes | Yes | Yes | Yes | No |
| Custom color names | `custom-colors.json` (2) | Yes | Yes | Yes | Yes | No |
| Device/model identity matrix | 8 controls x full/legacy/capability/compatibility plus same-process reconnect (460 cases) | Partial | 8 identities | 8 identities | 8 identities | No |
| Genuine CDJ-2000nexus status matrix | Unmodified 284-byte player-1 status payload from Dysentery `S05-link-browse`, paired generation-2 CDJ keepalive, and 13 existing suites spanning ordinary menus, both setup widths, Display/Play/Delivery/no-builder context crosses, and Hot Cue catalog/getters (249 cases) | Yes | Yes: 13/13 variants and 249/249 cases; all semantic envelopes match the derived CDJ-3000 controls | Yes: every variant has a fresh-fixture/process repeat and hash-bound receipt | Deferred | Twelve raw envelopes match exactly; Display differs only by declaration-level render pagination of the same ordered 16 rows |
| Stateful History mutation and restart | `history-lifecycle.json` (10), reset/restart repeat strategy | Yes | Yes | Yes | Yes | No |
| Link-played row/scalar lifecycle | `link-played-state.json` (19): two tracks crossed through baseline, `3001` insertions, `3401` per-track removal, and `3101` whole-history deletion | Yes | Active in guarded generation `ah18` behind `ag18` | Observation-preserving reducer declared; live summary pending | Deferred | Static ownership and physical CDJ-3000 corroboration complete; recorder forces deterministic reset options, snapshots/restores guest settings and `AnotherHistories.xml`, and repeats from a fresh fixture/process |
| Link-played option persistence across process restart | `link-played-persistence-prime.json` (7) + `link-played-persistence-restart.json` (3), executed for all four ordinary/Link reset-persist combinations in two independent runs | Yes | Declared as guarded generation `ai18` behind `ah18` | Reducer preserves exact settings, clean-shutdown proof, properties-file XML, scalar replies, row bits, PIDs, health, and hashes; live summary pending | Deferred | Eight fresh-fixture runs, sixteen suite executions, sixteen clean `WM_CLOSE` shutdowns; separates `PlayedTrackOption` from `LinkPlayedTrackOption` without inferred protocol outcomes |
| Link-played state across same-process LINK toggle | Reused seven-case prime suite + `link-played-link-toggle-post.json` (3), two uninterrupted controls and two deactivate/reactivate runs | Yes | Declared as guarded generation `aj18` behind `ai18` | Reducer requires listener absence/presence, one responsive PID throughout each run, exact repeat, and preserves both scalar and row-bit channels; live summary pending | Deferred | Uses deterministic reset settings and fresh fixtures; separates Link server refresh from process-restart persistence |
| Two-player Link-played ownership | Four generated seven-case phases alternate RX3 players 1/2 through insert-first, insert-second, remove-first, and remove-second; both scalars and both rows bracket every mutation | Yes | Declared as guarded generation `ak18` behind `aj18` | Reducer requires two stable simultaneous discovery identities, one responsive Rekordbox PID, player-correct setup/context/provenance, exact repeat, and preserves the complete 28-case timeline; live summary pending | Deferred | Distinct addresses, MACs, packet hashes, and packed requester bytes distinguish shared global state from player-partitioned or asymmetric behavior |
| Invalid request argument shapes | `request-errors.json` (9) | Yes | Yes | Yes | Yes | No |
| Malformed wire framing | `malformed-framing.json` (6) | Yes | Yes | Yes | Yes | No |
| Pagination boundaries and overlap | `pagination.json` (9) | Yes | Yes | Yes | Yes | No |
| Twelve simultaneous player-1 sessions | `concurrent.json` (12), barrier and canonical outcome multiset | Yes | Yes | Yes | Yes | No |
| Populated Play Count, Prepare, Date Added, and My Tag paths | `extended-families-full.json` (21) | Yes | Yes | Yes | Yes | No |
| Empty Play Count, Prepare, Date Added, and My Tag paths | `extended-families-empty.json` (9) | Yes | Yes | Yes | Yes | No |
| Display Song Info ordinary field list and missing IDs | `display-song-info.json` (4) under three identities | Yes | Yes | Yes | Yes | No |
| Display Song Info AIO field order | `display-song-info-aio-player-11.json` (1), captured RX3 status | Yes | Yes | Yes | Yes | No |
| Display Song Info category-enabled flags | 21 `category-*-disabled` cases | Yes | Yes | Yes | Yes | No |
| Display Song Info render arities, gate, and selectors 2-17 | `display-song-info-render.json` (21) | Yes | Yes | Yes | Yes | No |
| Display Song Info pagination normalization | `display-song-info-pagination.json` (9) | Yes | Yes | Yes | Yes | No |
| Display Song Info malformed arity/type/context | `display-song-info-errors.json` (9) | Yes | Yes | Yes | Yes | No |
| Display Song Info legacy row width | `display-song-info-legacy.json` (4) | Yes | Yes | Yes | Yes | No |
| Display Song Info numeric/null/dangling field boundaries | three eight-track boundary suites (24) | Yes | Yes | Yes | Yes | No |
| Display Song Info ASCII/non-BMP limits for every string field | four focused string profiles/suites | Yes | Yes | Yes | Yes | No |
| Display Song Info status-shape/model consistency | four model-mutated RX3 status suites (16) | Yes | Yes | Yes | Yes | No |
| Play/Delivery Song Info rows and sibling dispatch | `song-info-siblings.json` (24) | Yes | Yes | Yes | Yes | No |
| Play/Delivery render controls | `song-info-sibling-render.json` (42) | Yes | Yes | Yes | Yes | No |
| Play/Delivery pagination normalization | `song-info-sibling-pagination.json` (18) | Yes | Yes | Yes | Yes | No |
| Play/Delivery malformed arguments and parser state | ordinary 17-case suite, two status-backed 14-case suites, and ordered cold experiments | Yes | Yes | Yes | Yes | No |
| Play/Delivery legacy row width | `song-info-sibling-legacy.json` (8) | Yes | Yes | Yes | Yes | No |
| Play/Delivery status-backed controls | Authentic RX3 player 11 and RX3-template-derived CDJ-3000 player 1 x baseline/render/pagination/errors/legacy (212) | Yes | Yes | Yes | Historical only | Native CDJ-3000 status remains unproven |
| Delivery-only null/dangling/127-unit fields | `delivery-boundaries` / `song-info-delivery-boundaries.json` (8) | Yes | Yes | Yes | Yes | No |
| DeliveryComment/ISRC 255-unit limits | `delivery-wide-strings` / `song-info-delivery-wide-strings.json` (8) | Yes | Yes | Yes | Yes | No |
| Play path/cloud/file-presence and HotCueAutoLoad | `play-paths` / `song-info-play-paths.json` (14), including file, directory, and zero-byte sentinels | Yes | Yes | Yes | Yes | No |
| Play path `CLSSyncMethod=0` equivalence class | `cloud-sync-zero` / `song-info-cloud-sync-zero.json` (10): null/negative/zero local controls; service IDs 1/2/5/6; matched/mismatched DBIDs; existing original file/directory; successful, missing, and unsupported moved-root candidates | Yes | Pending behind production-shaped provider paths; the pinned 7.2.19 audit proves this is the sole unrecorded integer equivalence class | Declared as 20 fresh-fixture/settings/process record/repeat executions with exact settings snapshots, arbitrary filesystem sentinels, guest-settings restoration, authority-first row reduction, baseline restoration, and final stopped-VM receipt | Deferred | Authenticated provider share roots remain a separate environment dimension |
| Link Export `FolderPath` visibility | `link-visibility` / `link-visibility.json` (7), covering Collection, File Name, ordinary/Smart playlists, Search, History, provider states, and false-positive controls | Yes | Yes | Yes | Yes | No |
| Delivery row-order state | seventeen suites, 556 executions: ordinal/render controls, six precursor families on reused/replaced TCP, and repeated RX3 rejoin/RX3-to-CDJ lifecycles | Yes | Yes | Yes | No | No |
| RX3-status menu-location-2 state | seventeen declarations, 496 completed executions, two expected socket-close transcripts: valid/zero/malformed precursors, reconnect/shared-socket cross, and render-location control | Yes | Yes | Yes | N/A | Yes |

`Matrix only` means the required combinations are explicit and the identity
adapter can emit them, while oracle recordings for those combinations have not
yet been made.

The canonical `rbxport` replay is
`conformance/results/rbxport/c144f19+tree.80e87ec8aace/`. It completed 2,403
case executions across all 211 recorded goldens. No whole suite is exact.
Across the full corpus, 365 cases are field-exact and 1,223 preserve outcome,
total, and row count. The 17 settings suites contribute 32 cases: all execute, 26 preserve
shape, and none is field-exact. The 23 category suites contribute 45 cases:
all execute, 23 preserve shape, and none is field-exact. The 20
sort/hidden-selection/color suites contribute 22 cases: all execute, 16
preserve shape, and none is field-exact. All eight identity controls produce
identical rekordbox and backend behavior for their shared suites.
The Smart device cross adds two cases under each identity. Rekordbox returns
the same populated eight-track rule result and empty result under all eight;
rbxport is exact only for each empty control because its Link Export catalog
does not evaluate the populated rule.
The 17 Smart secondary-column cases all return eight rows in Rekordbox and zero
rows in rbxport. The four desktop key-preference suites contribute 52 replayed
cases: none is field-exact and 36 preserve outcome, total, and row count. The
29 local CDJ key-style cases are real-Rekordbox-only canonical expectations.
They prove the complete Classic-to-Camelot string transformation, including
persisted ordinary and Smart `BPM - Key`, while holding all numeric and ordering
fields constant. Backend replay is intentionally deferred.
The ten Search suites contribute 160 cases: 23 are field-exact and 61 preserve
shape. The ordinary ceiling suite proves Rekordbox truncates 1,005 eligible
tracks to 1,000 and right-aligns overrun windows; rbxport exposes all 1,005.
Search Track proves sort 0 truncates at 5,000 while explicit sorts return all
10,005 eligible rows; rbxport ignores the sort distinction.
The smart-playlist suite contributes 12 cases: six are exact and seven preserve
shape. Rbxport's Link Export catalog reads materialized membership, while
Rekordbox evaluates valid Attribute 4 rules and ignores those rows.
The 39-case smart-rule matrix adds 19 exact empty-result controls. All 20
nonempty Rekordbox results diverge because the same rbxport catalog path does
not invoke its separate rule evaluator.
The 60-case stored-numeric matrix adds 15 exact empty-result controls. Its 45
nonempty Rekordbox results diverge through the same integration boundary.
The 49-case My Tag matrix adds 12 exact empty-result controls. Its 37 nonempty
membership results diverge through the same integration boundary.
The 56-case relative-date matrix has no empty oracle result, so all 56 cases
diverge. It proves that only case-insensitive singular `month` receives month
arithmetic; every other unit uses days, future dates match operator 6, and
blank or malformed track dates match neither relative operator.
All 18 filename cases preserve shape and none is exact. The oracle records nine
sort-order classes and a 255-UTF-16-unit primary-string cap that rbxport does
not apply.
The text suite proves Rekordbox's BMP code-unit comparison, lack of canonical
normalization and non-ASCII case expansion, supplementary-query limitation,
UTF-16 length accounting, and embedded-NUL termination.
The populated 47-case suite has 29 matching outcome/total/row-count shapes and
two exact cases; the empty 21-case suite has 20 matching shapes and 16 exact
cases. Chained navigation has 14 matching shapes across 16 paths; its two
shape differences are extra `Unknown` album rows. The new capability suites
show that rbxport ignores root masks, accepts player bytes rekordbox times out,
uses only menu location 1 while rekordbox accepts 1-8, and regularizes invalid
pagination that rekordbox clamps, wraps, or ignores. The eleven data and
lifecycle suites add 99 same-shape cases. The History lifecycle adds
four exact cases and records the missing current-session history row as
structured `dependency_unavailable` outcomes for four dependent requests.
The 19 Display Song Info replays contain 100 cases: 19 are field-exact and 78
preserve outcome, total, and row count. The render matrix preserves shape for
all 21 cases. Pagination differs on Rekordbox's zero/end/overrun/max-offset
normalization; malformed inputs expose five dispatch differences. Populated
rows retain measurable field and AIO-order differences. The eight ordinary
Play/Delivery sibling replays contain 139 cases: 19 are field-exact and 101 preserve outcome,
total, and row count. Rbxport matches populated menu sizes and missing-content
results, but differs in row fields, ten pagination edges, malformed-input
handling, the `4003` no-builder responses, and the null/empty Play path guard.
The ten status-backed Play/Delivery replays contain 212 cases: 36 are
field-exact and 146 preserve outcome, total, and row count. Both status
identities expose the same stable behavior after requester-context
normalization; argumentless Delivery is the one stable malformed result that
differs from the ordinary identity.
`RBXPORT_AUDIT.md` groups
the measured gaps, while each retained
`*.diff.txt` remains the field-level evidence.

## Navigation families

`full.json` covers roots and drilldowns for tracks, genre, artist, album, BPM,
rating, year/decade, label, color, duration, bitrate, history, filename, key,
matching, Hot Cue Bank, search, Original Artist, Remixer, and playlists. The
golden stores every typed response and rendered row; the short inline
expectations are fixture guards, not substitutes for exact golden equality.
`chained-navigation.json` obtains selector arguments from earlier returned rows
and therefore tests practical navigation independently of exact database-ID
parity.
The two extended-family suites record Play Count, Prepare, Date Added
year/month/day, My Tag hierarchy, and tags on a track. Their populated and empty
goldens establish exact row rendering and errors. New Key root/range/track cases
are part of the base full/empty suites.

## Device dimensions

The declared device matrix includes eight identity controls, player numbers
1-6 and 11, four keepalive device classes, three generations, legacy and extended
setup, three root masks, and the three common render arities. Seven arguments
form a fourth parser-accepted shape; its dedicated active-sort/gate-value
matrix is declared and queued separately.
The direct runner controls every dimension except model identity. The adapter
must emit isolated Pro DJ Link discovery/keepalive identity and must record the
identity used beside each golden.

The full Cartesian product would contain 9,072 combinations before protocol-case
selection. The execution plan uses pairwise coverage plus full crosses for
model x setup, model x root mask, and model x render arity. Compatibility smoke
cases run for every model identity. The status-backed AIO boundary is
live-recorded: an `XDJ-RX3` identity places Comment before
Key/Rating/Color/Genre/Stock Date, while the matched `CDJ-3000` control places
Comment after Stock Date. A keepalive alone exposes LINK but does not populate
the model cache used by this request. `DISPLAY_SONG_INFO_ORACLE.md` records the
complete wire and lifecycle evidence.
Authentic RX3 status and the RX3-template-derived CDJ-3000 control are crossed
through all
stable Play/Delivery rows, render controls, pagination, malformed type/arity
forms, and both setup widths. Their normalized stable envelopes are exact;
only Display Song Info takes the recovered AIO ordering branch.

The static device-predicate matrix is also explicit. The pinned x86-64 audit
tracks 23 peer identity/capability helpers across 67 x86-64 and 68 ARM64 direct
references. The only
model-derived database-serving decision is Display Song Info's XDJ-prefix
classification. Exact XDJ-XZ/XDJ-AZ/XDJ-RR/XDJ-RX2/OPUS-QUAD comparisons and
`isCDJNetwork` calls are confined to UI and remote-settings owners; the
OPUS-QUAD drag-and-drop deck form is a separate output path. Genuine status
packets remain required before promoting native behavior for other models.
`DEVICE_PREDICATE_AUDIT.md` is the evidence authority.

## Media assumption

Fixture rows contain plausible filenames, paths, sizes, file types, sample
rates, and bit depths. They intentionally contain no audio. Current static
evidence shows the Link Export row compatibility path reading database metadata;
an actual file is added only if an isolated oracle run demonstrates a file
existence or content dependency.

The adjacent static audit identifies narrower non-audio dependencies. Artwork
success resolves the active AppSync `djmdContent.ImagePath`/`djmdPlaylist.ImagePath`
lookup or the fallback Master `djmdImage` path to image bytes. Waveform, beat-grid, VBR,
key-analysis, and specified-atom requests parse analysis files. Minimal image
or ANLZ fixtures may therefore be added for those protocol probes without
adding playable audio media.

## Completion rule

The real-Rekordbox oracle phase is exhaustive only when every table row above
is declared and recorded twice with identical canonical output. Every golden
must retain its fixture hash, suite hash, rekordbox version, client identity,
setup width, root mask, render arity, and capture provenance. Backend replay is
tracked separately and does not change this completion rule.
