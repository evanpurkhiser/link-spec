# Rekordbox research completion ledger

This ledger defines what remains before the real-Rekordbox Link Export oracle
can be described as exhaustive within its stated boundary. It is independent
of implementation comparison: rbxport is not under test in the current phase.

Evidence states have strict meanings:

- **Complete**: deterministic declarations, real Rekordbox capture, independent
  repeat, machine validation, provenance, and readable interpretation exist.
- **Active**: the complete experiment design exists and a bounded isolated-VM
  queue is recording it; partial output is not promoted evidence.
- **Declared**: fixtures, suites, and validators exist, but live evidence is
  incomplete.
- **Source needed**: the lab lacks an authentic packet, account state, or peer
  implementation required to make a hardware-representative claim.
- **Excluded**: the question is outside the approved safety boundary rather
  than silently treated as answered.

## Current active queue

The queue runs only against Rekordbox 7.2.19 on the private host-only network.
It cannot reach the physical RX3. Its stages are serial because each one
activates a different encrypted database fixture and Rekordbox process.

| Surface | Required completion evidence | Current state |
| --- | --- | --- |
| Extended `0x2401` `UINT32_MAX` reply lifecycle | 20 topology/delay cells x three independent cold-process observations; exact pristine getter after every observation | **Complete:** strict reducer accepted 60/60; same-socket disconnect, replacement-socket delivery, timing variation, and pristine database are recorded |
| Extended setter slot-8 lifecycle | Three independent cold processes; permissive setter/immediate-getter transcripts; process and Application health; logical base/WAL/SHM snapshots; same-database process restart and getter; hash-bound receipts | **Complete:** strict reducer accepted 3/3; setter and immediate getter time out with a responsive process and pristine database, while same-database restart restores the identical status-zero 124-byte getter record |
| Extended setter parser axes | 57 matrix entries total; 54 repeat-verified goldens plus declared-length `UINT32_MAX`, slot-8, and returned-slot `UINT32_MAX` lifecycle summaries | **Complete:** strict reducer accepted 57/57 variants and 366 evidence cases; all three returned-slot `UINT32_MAX` runs preserve the canonical mutation despite setter/immediate-getter timeouts, and same-database restart returns the identical 124-byte record |
| Legacy `0x2201` parser safety | 57 probes x two cold processes, process/Application health, conditional getter, live database snapshot, same-database restart after unavailable getters, and request-equivalence audit | **Complete:** strict reducer accepted 57/57 repeat pairs across 114 independent processes; both cue-length axes, the complete 12-value flag axis, both six-value extension-length axes, all four ContentIDs, and every fixed word from 2 through 8 are repeat-verified; mutation requires both cue lengths equal 36; exact inclusive flag admission is `0x00040000..0x0006ffff`; actual extension lengths 0..8 are zero-padded and bytes after eight are ignored; declared zero commits a zero-filled mutation but returns empty `0x0100`; declared one and seven reach the same `ntdll.dll` exception `0xc0000374` at different transport stages and leave the database pristine; one exact request has eight earlier healthy-getter observations and six later port-query outages, proving an unmodeled history/epoch dimension; ContentIDs zero/`UINT32_MAX`/999999/10001 return respectively zero/zero/one/two cue records after their mutations, with unresolved IDs returning status one; fixed word 2 is dynamically ignored, and words 3 through 8 map solely to `InFrame`, `OutFrame`, `InMpegFrame`, `OutMpegFrame`, `InMpegAbs`, and `OutMpegAbs`; declared `UINT32_MAX` returns empty `0x0100`, remains pristine, and stalls the immediate getter |
| Legacy `0x2201` identical-request lifecycle history | Interleave the exact canonical request before and after each crashing declared-length probe, then repeat after a full isolated-VM restart; identical request fingerprint, fixture, identity, setup, and health/database/restart evidence | **Complete:** strict reduction validates 12/12 request observations and four/four isolated-VM restarts. All eight canonical requests share one status-zero/mutated/immediate-port-query-timeout/restart-changed lifecycle before and after both crashes and the VM restart. Both malformed phases repeat pristine durable state exactly, while explicit lifecycle groups preserve cycle-dependent Application-event visibility and the length-seven disconnect-versus-timeout race. Phase/cycle/finalization receipts are hash-bound; cleanup restored `play-paths`, left zero identities, and stopped the VM |
| Hot Cue list-buffer lifetime over discovery disappearance | control and 40-second disappear/rejoin arms, two cold-process runs each | **Complete:** strict reducer accepted both arms; old location 1 renders item 9002 and current location 2 renders item 9032 in all four observations, proving the buffer persists across disappearance and same-identity rejoin |
| Hot Cue list-buffer lifetime over LINK deactivate/reactivate | Two uninterrupted controls and two supported same-process LINK toggle runs; explicit dbserver-port absence/presence, unchanged responsive PID, exact old/current location rows, health, and hash receipts | **Active behind `af18`:** bounded generation `ag18` is waiting on the corroborating XDJ-XZ finalization; declarations, recorder, strict reducer, handoff, cleanup contract, and focused tests are complete |
| Link-played row/scalar transition under reset options | Baseline, two `3001` insertions, `3401` per-track removal, and `3101` whole-history deletion; exact `0x3b03` scalars and `0x4101` argument-7 bits; fresh fixture/process repeat; guest settings and `AnotherHistories.xml` restoration | **Active behind `ag18`:** bounded generation `ah18` has a 19-case authority-only declaration, state-owning recorder, observation-preserving reducer, guarded handoff, and focused tests |
| Played-option persistence across process restart | Full 2x2 cross of `PlayedTrackOption` and `LinkPlayedTrackOption`; prime one Link-played ID, cleanly close Rekordbox, retain the exact properties file, and observe both protocol state channels after a same-database restart | **Declared behind `ah18`:** bounded generation `ai18` contains two suites, eight fresh-fixture runs, sixteen clean shutdowns, exact record/repeat goldens, properties-file XML and settings provenance, PID/health validation, guest restoration, strict reduction, and guarded finalization. Same-process LINK-refresh remains separate follow-up work |
| Link-played state across same-process LINK deactivate/reactivate | One primed Link ID and one unprimed control ID observed through both `0x3b03` and track-row bit `0x100`; uninterrupted control and actual listener disappearance/reappearance | **Declared behind `ai18`:** bounded generation `aj18` executes two control and two toggle runs, requires the same responsive Rekordbox PID at five checkpoints, validates port 12523 absent/present, records exact prime/post goldens, restores guest state, and preserves authority-only outcomes |
| Two-player Link-played ownership | Simultaneous ordinary RX3 player-1 and player-2 identities with distinct packets; alternating inserts/removals and player-correct setup/context; both state channels bracketing every mutation | **Declared behind `aj18`:** bounded generation `ak18` records and exactly repeats a four-phase, 28-case timeline while proving both identities and one Rekordbox PID remain stable at five checkpoints; no global or per-player result is assumed in the declarations |
| RX3 active track sort x five-argument render | Default-only five-argument capture plus the complete eleven-sort six-argument oracle | **Declared behind `ak18`:** `sort-secondary-render-5.json` holds the same fixture, identity, setup, pagination, and visible-sort set while omitting the sixth render argument; generation `al18` records and repeats all 88 rows, then reports exact per-case equality or divergence without importing six-argument expectations |
| RX3 active track sort x seven-argument render | The parser's count thresholds prove argument 6 is read at six or more while arguments 7/8 are read together only at eight; no live seven-argument track render exists | **Declared behind `al18`:** `sort-secondary-render-7.json` crosses all eleven visible sorts with seventh values zero, one, and `UINT32_MAX`; generation `am18` records and repeats 264 rows and tests the static ignored-value prediction without treating it as expected output |
| Track render arity boundaries | Recorded valid-header renders use only 5/6/8 arguments; count 33 has a malformed-framing control | **Declared behind `am18`:** `render-arity-boundaries.json` sweeps every total count 3-32 under Default and all non-default visible sorts at 3/4/9/32; generation `an18` records 70 unconstrained cases twice and preserves every terminal outcome |
| Track render arity underflow | The ordinary renderer always prepends context, offset, and count; the existing pre-list request-error control begins at three arguments | **Declared behind `an18`:** `render-arity-underflow.json` warms a valid Track list before correctly framed `0x3000` counts 0/1/2, preserves raw reply/timeout/disconnect evidence, and proves fresh-connection health after every probe; generation `ao18` records and repeats all nine cases |
| Track render argument types | All eight normal positions crossed with string and blob after same-connection warmup | **Active behind `ao18`:** generation `ap18` records 16 isolated probes twice with health evidence |
| Track render numeric fields | Positions 4-6 crossed over seek, ignored-total, and category-map boundaries | **Active behind `ap18`:** generation `aq18` records 42 cases twice with authority-only outcomes |
| Track render override controls | Gate normalization and split-width selector dispatch crossed at their missing boundaries | **Declared behind `aq18`:** generation `ar18` records 17 cases twice, then validates receipts, focused tests, cleanup, and isolated-VM shutdown |
| User info / DJ ID (`0x3006` / `0x4d02`) | `data/static-analysis/user-info-djid.json` proves the 7.2.19 builder, exact absent/success shapes, `djprofile.nxs` path and validation, 32-byte source plus 128-byte zero padding; CDJ-3000 source proves the post-load ticket lifecycle | **Static complete; 142-case live matrix armed as `as18` behind the active queue:** ten authority executions cover ordinary RX3/CDJ identities, argument/type/context boundaries, and absent, valid, checksum-invalid, short, long, wrong-extension, and directory profile states with exact guest backup/restore, fresh-process repeat, health, blob hashes, receipts, and cleanup |
| Location-2 malformed-history timing conflict | The first 47 ordered pairs are promoted; the next pair produced matched precursor replies but a Delivery probe total of 13 in record and 0 in repeat | **Mechanism complete:** 28/28 timing observations prove zero rows only under immediate replacement. The 24/24 routing matrix directly captures identical transaction-1 `0x4000 [0x2602, 0]` orphan replies in all four immediate malformed-blob runs, no frame in all 20 delayed/blob or valid controls, and correct 13-row same/fresh probes throughout. Static dispatch proves player-keyed asynchronous routing; final receipts bind clean health, tests, baseline restoration, zero identities, and stopped VM. Mixed-player `z20` remains rejected evidence |
| Authentic CDJ-2000nexus status | 13 variants / 249 cases, fresh fixture/process repeat, hash-bound receipt for every golden | **Complete:** strict reducer accepted 13/13 variants and 249/249 cases; all 13 semantic envelopes match the derived CDJ-3000 controls, while the sole raw mismatch is the Display baseline's declaration-level pagination of the same ordered 16 rows |
| Every persisted secondary column in legacy setup | 15 selections / 30 cases; identical fixture and case IDs; exact 12-field prefix of each 16-field extended row; repeat receipts | **Complete:** strict reducer accepted 15/15 variants and 30/30 cases; every Sort menu and track result matches its extended partner, and every legacy row is the exact 12-field prefix of the corresponding 16-field row |
| RX3 active track sort x six-argument render | All 11 visible sorts, exact six-argument request shape, all 88 rows and fields 0/5/6/12-15, fresh fixture/process repeat, retained physical request evidence | **Complete:** all 33 renders retain final value 12 while Default uses persisted Column and every non-default sort materializes its own right-hand role; strict tests bind the golden, row CSV, receipt, decoded physical requests, and source PCAP |
| Exact physical RX3 session envelope on 7.2.19 | Retained packet authority proves legacy setup player 11, context `0x0b010401`, root mask `0x05fdffff`, 19 physical-library root rows, and Default render `[context, offset, count, 0, 4342, 12]`; capture version is unknown | **Armed as `av18` behind `au18`:** two authority-only cases replay the exact root and Default-track shapes with the captured status-backed player-11 identity, fresh fixture/process repeat, health captures, strict physical/live provenance split, and final cleanup receipt |
| Exhaustive track compatibility inputs | 382 deterministic rows: complete FileType byte domain, wide-value narrowing, exact SampleRate boundaries for bytes 5/6/11/12, and BitDepth invariance; extended and legacy record/repeat plus strict prefix/predicate reducer | **Complete:** both setup widths return all 382 rows and repeat exactly with clean health; 298 rows are supported and 84 unsupported; only FileType bytes 5/6 reject unconditionally, 11/12 require exact 44100/48000 Hz, wide values narrow to a byte, and BitDepth is invariant. Every legacy row equals the first 12 extended fields; setup and finalization receipts bind the goldens, summaries, health, baseline restore, zero identities, and stopped VM |
| BPM tolerance inclusion boundaries | 43 tracks bracket the zero-percent whole-BPM bucket and every lower/upper ±1–6% edge around 120.00 BPM by one hundredth; seven `0x1206` requests, fixture reset, application restart, and exact repeat | **Complete:** strict reducer accepted all seven cases and exact independent repeat; zero percent is inclusive 119.50–120.49 around 120.00, nonzero endpoints are inclusive, immediate outside neighbors are excluded, and totals nest 5/11/17/23/29/35/41 |
| Extended setter mutable fields | 56 isolated extrema/encoding/comment cases; fresh fixture/process record and repeat; getter plus logical base/WAL/SHM snapshot after each setter | **Complete:** strict reducer accepted 56/56 variants and 112 fixture/process executions; every axis returns status zero with identical database state; the lone surrogate persists exact invalid UTF-8 bytes, and the maximum Comment has strict 8,192-byte response-prefix, 65,656-byte declared-record, complete 32,766-character database, and repeat validation |
| Extended setter seek descriptor | 17 available-byte/declared-length/validity controls x two cold-process runs; process/Application health and logical base/WAL/SHM state | **Complete:** strict reducer accepted 17/17 variants and 34/34 cold-process runs; 14 variants return the canonical status-zero response, while the 82-byte out-of-bounds copy and both nonzero inbound-validity controls durably mutate seek strings, time out, and overlap the faulting process with its replacement |
| Queue closure | Ten strict reducers, focused tests, full Rust tests, baseline fixture marker, zero identity units, stopped isolated VM, hash-bound final receipt | **Complete:** repaired finalizer generation `s7` revalidated all ten reducers, focused Python and pinned Rust tests, the baseline marker, zero identity units, and stopped isolated VM; `real-rekordbox-queue-finalization.json` binds every summary and executable hash |
| Artwork/analysis/cue payloads | 196 fileless semantic requests, 96 malformed probes, 31 database-path controls, 15 baseline generated-asset success requests, 60 matched-status/setup success observations, 57 focused observations across 30 parser-boundary asset profiles, and 114 successful/database-boundary cue observations; all 16 exact dispatch kinds, track types 0-6, zero/maximum content IDs or complete contexts as applicable, representative locations, specified-atom gates, malformed axes, missing/empty/null paths, deterministic JPEG/PMAI inputs, genuine RX3/CDJ setup crosses, exact parser gates, `djmdCue` counts 0/1/3/255/256, all serialized legacy/extended cue fields, null/deleted rows, and isolated seek-parser states | **Fileless, malformed, missing-path, and baseline generated-asset stages complete; later stages handed off:** 196/196 fileless cases repeat as 176 replies and 20 healthy timeouts; 96/96 malformed probes repeat as 80 replies and 16 healthy timeouts; all 31 missing/empty/null database-path controls return their service-specific envelopes; all 15 valid-asset requests return direct replies, with 12 payload-bearing and ordinary-identity `2204`/`2504`/`2804` empty or scalar. Hash-bound receipts confirm exact repeats, clean health, asset cleanup, zero active synthetic identities, and stopped isolated VMs. The serial recovery continues through identical-request history and track compatibility before status/setup payloads, parser boundaries, and cue success/boundaries |

The authoritative live values are the partial reducer outputs and user-service
states, not this prose snapshot. `CLEANUP.md` names every service and candidate
artifact.

## Complete menu-serving surfaces

The following areas meet the Complete definition for the tested AppSync
database path and recorded client/status controls:

- all 95 declared request kinds have one non-overlapping machine-readable
  classification across 47 database-path families: 74 completed live
  menu-oracle kinds, 16 exact static-dispatch kinds, and five recognized
  log-only kinds, including tables, predicates, ordering, results, mutations,
  buffer reads, filesystem dependencies, and explicit no-builder paths;
- the generated navigation graph assigns the same 95 kinds to named menu
  stages, hierarchy or recursive selection edges, and one of list-buffer,
  render, direct-response, or error/no-reply terminal classes; all 20
  configured root choices and every implemented direct browse route remain
  distinct;
- the complete known namespace is enumerated as 185 unique kinds, including
  all 173 CDJ-3000 request/reply names, the physical RX3 `0x0001` client
  control, conformance probes, and Rekordbox-only static arms; exact
  switch/direct dispatch distinguishes 74 live menu-oracle kinds, 54 static
  dispatches, 27 static rejections, eight recognized log-only arms, one
  physical-client control, zero source-only requests, and 21 replies; all 102
  request kinds with direct named XDJ-RR callers have terminal Rekordbox
  evidence;

- root menu masks, persisted category visibility/order, special disable bits,
  empty state, and both setup widths;
- every known category/hierarchy path, returned-selector chaining, wildcard
  rows, deleted-row predicates, and deterministic ordering;
- the database-interface boundary: `SetSharedDBInfo` installs AppSync for the
  shared Link Export library, while Master is selected only by the non-index-3
  FilterSettingManager/TrackFilter arms in the complete x86-64 vtable audit;
- the generated device-behavior matrix binds eight ordinary identities, four
  invariant suite hashes, seven status-backed serving surfaces, eight separate
  serving dimensions, the genuine 13-variant CDJ-2000nexus authority, three
  recovered serving decisions, and explicit native-status provenance tiers;
- the inbound seek-info process exit, localized to the AppSync getter freeing
  its parser-advanced UTF-16 cursor instead of the allocation base, with the
  same dormant defect in the inbound-gated outbound branch;
- ordinary Search and Search Track dispatch, text semantics, sorts, signed
  argument boundaries, pagination, and 1,000/5,000/10,005-row ceilings;
- persisted Sort visibility/order and requested sort IDs `0..17`;
- all 15 persisted secondary selections in extended setup, missing/multiple
  selection, render selectors, formatting, numeric boundaries, and string
  width limits;
- all 11 visible RX3 track sorts crossed with six-argument rendering, including
  exact cached secondary values, composite types, extended Key/BPM metadata,
  and the fixed final render value `12`;
- Classic/Alphanumeric key notation, including Camelot roots, distance labels,
  composite BPM/Key columns, Song Info, and local `DEVSETTING.DAT` control;
- ordinary and Smart playlists, complete Smart XML/operator/property/date/text/
  My Tag semantics, serving crosses, pagination, and row widths;
- ordinary track rows, compatibility flags, filename formatting, exact field
  widths, null/dangling/invalid values, and soft deletion;
- Play Count, Prepare, Date Added, My Tag, Matching, History lifecycle, and Hot
  Cue Bank catalog/cue/mutation families described in their oracle chapters;
- Display, Play, Delivery, and recognized sibling Song Info requests, including
  render selectors, pagination, malformed state, field boundaries, and setup
  widths;
- packed requester/location/slot/type behavior across all list families,
  ordinary identities, the authentic RX3 status control, and the derived
  CDJ-3000 control;
- framing errors, connection behavior, twelve-session concurrency, fixture
  fingerprints, repeat promotion, and isolated-network enforcement.

`CONFORMANCE_COVERAGE.md` is the case-level ledger. A row in this summary does
not supersede a narrower pending cell there.

## Remaining dynamic evidence

These experiments remain necessary for the broadest possible server
characterization. Rows marked handed off are in the guarded serial queue.

| Gap | Existing boundary | Evidence still required |
| --- | --- | --- |
| Windows static device-predicate ownership | Exact stripped-PE `0x2002` dispatch, AppSync formatter and `isAIO` `0x1423815c0`; Disconnect `0x142380930` with inline AIO-map erase; map-only helper `0x142381700`; AppSync row builder `0x14238c720` with inline compatibility predicate; standalone predicate `0x14227e200`; six pinned direct calls; zero absolute pointers to all five addresses; `device-semantic-audit.json` scans all 174,813 runtime-function records and finds the compatibility sequence exactly twice plus one direct bare-`XDJ` literal reference in the known helper; `model-literal-owner-audit.json` classifies the symbol-rich slice as 19 audio-device, 6 controller-mapping, 2 application-UI, 1 anonymous helper, and exactly 2 database-serving references, both in `isAIO`; complete Windows runtime Display and 382-row compatibility authority | Computed function pointers, dynamically constructed model strings, cached state written through an unrecognized path, and semantically different classifiers remain bounded static gaps; pursue them when a new runtime, string, or xref lead identifies another serving decision |
| Native status shapes for modern models | Authentic RX3 and CDJ-2000nexus; two exact 292-byte corroborating XDJ-XZ/player-1 status fixtures with incomplete parent-capture provenance; one exact OPUS-QUAD kind-`0x10` non-status fixture; derived XDJ/CDJ controls; pinned audit of nine public source/capture repositories, one inaccessible physical XDJ-XZ parent-capture lead, and one rejected CDJ-3000 Stagehand control-plane lead | **Declared and handed off:** generation `af18` will run a 13-variant, 249-case corroborating XDJ-XZ matrix across ordinary, Display, Play, class-2, and Hot Cue catalog/getter surfaces under extended and legacy setup, with fresh-fixture/process repeats and four health captures per variant; then obtain captured-verbatim XDJ-XZ provenance plus XDJ-AZ, XDJ-1000MK2, XDJ-RR/RX2, OPUS-QUAD, and CDJ-3000 status packets with complete provenance |
| Status-backed replacement across native generations | RX3 rejoin and RX3-to-derived-CDJ replacement preserve Delivery state | At least one authentic non-RX3 replacement pair with packet-level provenance |
| Song Info location-2 malformed-history state machine | Sixteen immediate malformed precursors, reconnect/shared-socket controls, the direct blob-valued Play/Delivery rule, and the delayed player-routed response mechanism are repeat-verified | **Active lifecycle-aware authority run:** every connection retains setup, drains 1200 ms of no-send traffic into a separate field, and then sends its declared request. A blob-valued Delivery is followed by a measured 3000 ms interval with no matching client before the next connection. The historical 47 pairs and pair-48 conflict remain immutable in their original roots. The partial reducer verifies 224/256 promoted pair receipts and 672 request executions. Generation `z34` completed all 16 successors after blob-valued Play and all 16 successors after zero-context Play. The blob-valued-Play row always transfers delayed `0x4000 [0x2102, 0]`; the zero-context row is silent except when its successor is blob-valued Play, whose own delayed frame reaches the health drain. Blob-valued Delivery instead observes the measured 3000 ms no-client interval and leaves the health drain silent. The complete alternate-location-Play, argumentless-Delivery, missing-content-Delivery, extra-argument-Delivery, string-context-Delivery, and blob-context-Delivery rows each preserve every successor's ordinary result. In each row, blob-content Play queues its exact delayed `0x2102` frame into the health drain; every other drain is silent, including blob-content Delivery after its measured interval, and every health request returns 13 rows. Every extra-argument-Delivery precursor returns 13 rows. Pair 135's blob-content successor reproduced the health-connection admission race in `z34`; `z35` then promoted two fresh runs that both drained the successor's exact delayed `0x2102` frame before 13-row health. Pair 141's three pre-authority activation/readiness/guard attempts remain hash-bound; `z38` promoted its wholly fresh record/repeat. Pair 194's unmatched `z38` record candidate and exhausted repeat activation are quarantined separately; `z39` promoted a wholly fresh pair. Pair 199's `z39` run and pair 215's `z40`, `z41`, and `z42` runs preserve nondeterministic health-connection admission of the delayed blob-Play frame. Generation `z43` promoted pair 215 from two wholly fresh runs that both admitted the frame, then completed the remaining blob-context-Delivery successors. Pair 111's earlier race attempts remain quarantined provenance; bounded successors remain gated on lifecycle finalization. |
| Five-argument active-sort rendering | Default-sort five-argument rendering and all eleven six-argument active-sort cases are complete | **Declared and handed off:** generation `al18` follows the two-player Link-played finalization and records the complete eleven-sort five-argument matrix twice from fresh fixture/process state |
| Seven-argument active-sort rendering | Exact x86-64 decoder thresholds predict the seventh argument is unread; five/six/eight shapes are otherwise covered | **Declared and handed off:** generation `am18` follows the five-argument finalization and records 33 cases twice, crossing every visible sort with zero/one/`UINT32_MAX` in the otherwise-unread position |
| Track render argument-count domain | Ordinary valid-header goldens contain 5/6/8 arguments and the queued seven-argument cross; malformed framing covers count 33 | **Declared and handed off:** generation `an18` records every total count 3-32 under Default and crosses all visible non-default sorts at 3/4/9/32; generation `ao18` then records initialized-list counts 0-2 with raw outcomes and health controls, completing the correctly framed count domain 0-32 without constraining response class |
| Track render argument-type domain | Existing Track renders use numeric arguments; the pinned decoder resolves tags 2/3/6, preceding-length constraints, pointer-valued variable-width slots, and untyped render reads | **Declared and handed off:** `render-argument-types` generation `ap18` changes exactly one of all eight normal render positions to string or blob across 16 independent cold-process probes, each with same-connection Track warmup, exact repeat, and process/Application health evidence |
| Track render numeric fields | Position 4 and 5 had never varied; position 6 used only five values; static decoding proves a low-word character seek, unread client total, and low-word sparse category map | **Declared and handed off:** `render-numeric-fields` generation `aq18` records 42 cases twice, covering character classes and wrap/high-word aliases, client-total boundaries, and every `DBCommon_GetCateKind` equivalence range without treating static equality as a live expectation |
| Track render override controls | Eight-argument rows cover gates zero/one and selectors zero plus 2-17, but no selector 1, out-of-range selector, high-word alias, or non-boolean gate value; static decoding proves split low-byte/full-width selector use | **Declared and handed off:** `render-override-controls` generation `ar18` follows `aq18` and records 17 cases twice, covering boolean gate boundaries and every selector-width class while preserving authority-only outcomes |
| XDJ-RR source-defined location 9 | Generic Rekordbox location domain `1..8` is exhausted; a generated 304-call-site XDJ-RR inventory proves functional uses for every location `1..8`; `dbcl_GetDeliverySongInfo` fixes `2602` to location 9, while no direct XDJ-RR caller survives | **Declared and handed off:** six suites declare 36 cases across ordinary, genuine RX3-status, and derived CDJ-status envelopes under both setup widths; distinguishable-track location-1/2/9 current and stale-buffer sequences receive independent cold record/repeat, health captures, hash receipts, and a strict identity/prefix reducer in generation `ad18`, after cue-payload generation `ac18` |
| XDJ-RR old-Key and CueTrack browser | Static analysis resolves `100B` to `getKey_Root`, `110B` to `getTrack_Key`, and `130C` to a recognized arm with no builder or reply | **Declared and handed off:** six suites declare 48 cases across ordinary, genuine RX3-status, and derived CDJ-status envelopes under both setup widths; locations 1/2 cover root and concrete Key IDs, and each bounded CueTrack timeout has an immediate fresh-connection old-Key health control; generation `ae18` waits behind location-9 generation `ad18` |
| Hot Cue buffer database lifetime | Process restart clears uninitialized contexts; fresh TCP connections and a 40-second discovery disappearance/rejoin preserve initialized contexts | **Declared and handed off:** generation `ag18` uses the supported same-process LINK deactivate/reactivate transition in two control and two toggle runs, proves port 12523 absent while inactive, requires one responsive Rekordbox PID throughout each run, and renders distinguishable old-location/current-location buffers after reactivation |
| Link-played row state | Static ownership is complete: desktop and Link-history producers, per-track/global clearers, `AnotherHistories.xml` option gates, `RowDataTrack` bit `0x10`, the `PSvDBMain` snapshot, row bit `0x100`, and `0x3b03` value `2`; a physical Rekordbox 7.2.11/CDJ-3000 observation corroborates cross-list presentation | **Active:** `ah18` records mutation timing, `ai18` crosses both persistence options over clean restart, `aj18` crosses same-process LINK refresh, and `ak18` resolves two-player ownership. Live promotion and interpretation remain pending |
| Streaming-provider modes | SoundCloud/Tidal/Spotify/Apple Music forms are filtered in ordinary serving; a pinned manager audit proves Beatport is always constructed and uses a login-independent `/v4/catalog/tracks/` substring predicate, while Beatsource has a null slot and constant-false helper; all known `5000..5202` provider-browser commands are terminal `4003` rejections in this build | **Production-shaped path matrix armed as `at18` behind the authority queue:** seven cases cross exact, URL, mid-string, case, delimiter, URI-syntax, and near-match controls through six ordinary serving surfaces plus History with fresh-process repeat. Record account-conditioned application roots/categories and another Rekordbox version if it supports Beatsource or the rejected provider-browser command family |
| Play Song Info cloud-path configuration | The value-1 nonzero path has a complete 14-track real oracle; a pinned audit proves `CLSSyncMethod` is a raw integer with one zero/nonzero decision, distinguishes the DBID/regular-file nonzero path from the any-object/download-root zero path, and closes all other integer values statically | **`CLSSyncMethod=0` matrix armed as `au18` behind `at18`:** ten authority-only cases cover local bypasses, original file/directory, moved-root success/miss, and service IDs 1/2/5/6 with exact settings backup/restore and fresh-process repeat. Authenticated provider share roots remain a separate environment dimension |
| Player-hosted Song Info siblings | `player-hosted-song-info.json` proves XDJ-RX builders for generic metadata `0x2202` and six-row summary `0x2302`; XDJ-RX, RR, RX2, XZ, and RX3 clients expect `0x4802` from `0x2402` and emit `0x2502` register track length one-way, while all five local servers stub both kinds; hash-bound scans of 26,862 CDJ-3000/XDJ-AZ/OMNIS-DUO/CDJ-1500X C sources confine every exact `0x2402`/`0x2502`/`0x4802` literal to name/format tables and find no literal implementation; Rekordbox returns kind-specific `0x4003` for all four | Capture exact native-player `0x2202`/`0x2302` rows. Pursue computed/table-driven or decompiler-omitted newer-generation implementations only when a new call-graph, runtime, or packet lead exists; identify another generation with a successful `0x2402` server if one appears |
| Metadata/art/blob service errors | Exact static dispatch/loader map; handed-off 196-case fileless, 96-case malformed, 31-case missing/empty/null, 15-case generated-success, 60-observation status/setup, 57-case parser-boundary, and 114-case cue-success/boundary matrices | Complete the guarded real-Rekordbox queue and interpret exact response transitions; any newly observed crash or silent truncation becomes a narrower follow-up |

Media files remain unnecessary for the menu oracle. The Play-path fixture
already proves the server's file-presence and size predicates with arbitrary
sentinels. A future test should add playable audio only if a specific service
demonstrates content decoding rather than metadata/path inspection.

## Safety exclusions

The physical RX3 is excluded from synthetic discovery and active protocol
experiments. Client-UI questions such as whether a particular touchscreen path
emits Search Track remain capture questions, not permission to expose the lab
identity to the hardware LAN. Existing physical captures may be analyzed
offline.

Account-conditioned provider-root experiments require user-supplied account
state and must not weaken network isolation. Native device-status gaps require captures
or public evidence; RX3-template mutation remains useful classifier evidence
but cannot be promoted to native hardware behavior.

## Completion rule

Finishing the active queue closes its declared surfaces, not this entire
ledger. The overall research can be called exhaustive only when every dynamic
row above is either Complete or carries a documented, evidence-backed boundary
explaining why the behavior is unreachable in Rekordbox's serving role. Source
needed and Excluded rows remain visible limitations in the final report.
