# Source ledger

## Exhaustive menu-query classification

- `tools/generate_menu_database_query_map.py` owns the canonical classification
  of every request kind declared by the conformance corpus.
- `data/static-analysis/menu-database-query-map.json` records 47 database-path families
- `data/static-analysis/link-export-navigation-graph.json` joins those 47
  families and all 95 classified request kinds into the complete server-side
  selection/render transition graph
- `REQUEST_SHAPES.md` renders that graph and all 301 conformance argument
  signatures as a family-by-family reference with suite/case provenance
- `OBSERVED_RESPONSE_SHAPES.md` and
  `data/observed-response-shapes.json` invert the canonical Rekordbox 7.2.19
  golden corpus into per-request immediate replies, separately attributed
  `0x3000` page replies, exact type signatures, outcomes, row item types, and
  source-golden provenance, plus per-request setup and packet-hashed identity
  coverage; setup and drain ledgers retain independent identity/setup
  provenance, and a separately hashed suite snapshot binds all declarations
  for the five classified kinds without canonical responses
- `data/device-behavior-matrix.json` binds the canonical ordinary and
  status-backed device/model comparisons to their goldens, summaries, hashes,
  static predicate audits, and provenance tiers
  with their tables, predicates, ordering, result semantics, and evidence.
- `conformance/test_menu_database_query_map.py` derives the request-kind domain
  from all checked-in suites and requires exact, non-overlapping coverage. It
  also prevents a database-backed path from silently losing its table set.

## Complete request vocabulary and server dispatch

- `../alphatheta-docs/devices/cdj-3000/application/remote-database-client.md`
  supplies the complete recovered CDJ-3000 request/reply enum at commit
  `a70aeefb202ffddd2900e7b40e339a47ac077057`; the source file SHA-256 is
  `d3563dc35962b21ba224906f2307f8e7f872368d4b16cdd93c9ee24d9104fa95`.
- `tools/extract_link_export_dispatch_tables.py` decodes ten exact switch
  tables from the pinned Rekordbox 7.2.19 x86-64 Mach-O without loading the
  binary through a native parser. It verifies the executable SHA-256 before
  mapping virtual addresses to file offsets.
- `data/static-analysis/link-export-dispatch-tables.json` retains every decoded
  offset, destination address, semantic label, and direct-dispatch arm.
- `tools/generate_link_export_request_vocabulary.py` joins the firmware enum,
  server tables, 74-kind menu corpus, and Dysentery provenance into
  `data/static-analysis/link-export-request-vocabulary.json`.
- `conformance/test_link_export_request_vocabulary.py` verifies byte-identical
  regeneration and exact inclusion of every source, menu, and static kind.
- `data/static-analysis/adjacent-payload-loaders.disasm.txt` retains the active
  AppSync and fallback Master artwork paths plus detailed waveform, segmented
  key, and extended-cue builders. `tools/generate_adjacent_payload_service_map.py`
  joins those bodies to the adjacent dispatcher and vocabulary in
  `data/static-analysis/adjacent-payload-services.json`.
- `conformance/test_adjacent_payload_services.py` verifies byte-identical map
  regeneration, the full image/analysis dispatch domain, AppSync/Master path
  separation, cue-file independence, and the direction of the atom gate.

Firmware names establish client vocabulary. Rekordbox support is asserted only
when the pinned binary or live oracle supplies independent evidence.

## Played-track state

- `conformance/arm_post_lifecycle_queue.sh` is the fail-closed serial handoff
  from the lifecycle-aware malformed-history authority to generations `aa18`
  through `ar18`. `data/experiments/post-lifecycle-queue-arming.json` binds the
  launcher hash, the live `z27` invocation, all 18 bounded successor services,
  their scripts, runtime ceilings, invocation IDs, and observed active state.

- `data/static-analysis/played-track-cache-member-xrefs.txt`,
  `played-track-cache.disasm.txt`, and `played-track-producers.disasm.txt`
  recover the complete Link-played cache, persistence, producer, clearer, and
  server-refresh path from the pinned Rekordbox 7.2.19 x86-64 Mach-O.
- `../alphatheta-docs/platform/prodjlink/track-metadata.md` records the
  independent physical CDJ-3000 observation against Rekordbox 7.2.11. The
  source file SHA-256 is
  `779a833d1074292e68cefe70a14c8df05df5235573eedf2231f3e4f040eab9d6`.
- `conformance/suites/link-played-state.json` declares the real-Windows
  before/after sequence. It is a pending declaration and supplies no expected
  transition until a canonical record and independent repeat exist.
- `conformance/data/link-played-multiplayer.json`, the four generated
  `link-played-multiplayer-*` suites, and `runs/xdj-rx3-player-2.json` declare
  the two-requester ownership/admission oracle. The generator pins both packed
  contexts and the player-2 discovery-packet hash; player-2 outcomes remain
  open for real Rekordbox.

## Five-argument active-sort rendering

- `conformance/suites/generated/sort-secondary-render-5.json` declares the
  complete visible RX3 sort set with five-argument `0x3000` pagination.
- `conformance/record_sort_secondary_render_5.sh` and
  `conformance/run_sort_secondary_render_5_after_multiplayer.sh` own the fresh
  fixture/process record-repeat lifecycle on isolated networking.
- `tools/summarize_sort_secondary_render_5.py` preserves arguments 0, 5, 6,
  and 12-15 for every row and reports equality or divergence against the
  canonical six-argument golden. It does not encode either outcome as an
  expectation.
- Generation `al18` is a live bounded waiter behind `ak18`. No five-argument
  active-sort result is claimed until its canonical golden and receipts exist.

## Seven-argument active-sort rendering

- `data/static-analysis/client-and-render.disasm.txt` retains the pinned
  `GetListBufContents` body and its exact six/eight argument-count thresholds.
- `conformance/suites/generated/sort-secondary-render-7.json` declares all 11
  visible sorts crossed with seventh values zero, one, and `UINT32_MAX`.
- `conformance/record_sort_secondary_render_7.sh`, its guarded `am18` handoff,
  and `tools/summarize_sort_secondary_render_7.py` own record/repeat, health,
  provenance, complete row extraction, and descriptive six-argument comparison.
- No live result is claimed until the canonical 33-case golden and receipts
  exist; the ignored-seventh-value behavior is currently source-derived.

## Track render arity boundaries

- `conformance/suites/generated/render-arity-boundaries.json` declares every
  total `0x3000` argument count from 3 through 32 after a valid Track header,
  plus the complete visible-sort cross at counts 3, 4, 9, and 32.
- `conformance/suites/malformed-framing.json` retains the independent
  33-argument framing rejection.
- `conformance/record_render_arity_boundaries.sh`, the guarded `an18` handoff,
  and `tools/summarize_render_arity_boundaries.py` retain exact terminal
  outcomes, page argument counts, health, repeat identity, and hashes.
- No response class is declared in advance. The source parser explains why
  the cells matter but is not used as the behavioral oracle.

## Track render arity underflow

- `conformance/suites/generated/render-arity-underflow.json` declares total
  counts zero, one, and two after a valid Default Track list on the same
  connection, followed by a fresh-connection health request.
- `conformance/record_render_arity_underflow.sh`, the guarded `ao18` handoff,
  and `tools/summarize_render_arity_underflow.py` retain raw reply bytes,
  decoded messages, timeout or disconnect outcomes, process health, repeat
  identity, and hashes.
- `tools/audit_render_arity_underflow.py` generates the hash-pinned JSON,
  Markdown, and retained disassembly under `data/static-analysis/`. It proves
  the complete command allocation is zeroed, the zero-count field-loop bypass,
  eight-byte slot stride, and unconditional mandatory-slot reads.
- The declarations remain authority-only for response and transport behavior.
  They do not infer those outcomes from the proven zero-slot projection or the
  existing render-before-list request-error control.

## Public device-status source audit

`PUBLIC_STATUS_SOURCE_AUDIT.md` and its machine-readable companion retain the
pinned source search, the corroborating CDJ-2000nexus fixture, the inaccessible
two corroborating XDJ-XZ status fixtures, a physical XDJ-XZ parent-capture
lead, and the explicitly rejected CDJ-3000 Stagehand
control-plane lead. Protocol-plane rejections remain visible so later searches
do not promote real-hardware evidence that lacks the Link Export status packet.

`PUBLIC_STATUS_SOURCE_AUDIT.md` and
`data/static-analysis/public-status-source-audit.json` pin and classify the
following public repositories as of October 2, 2026:

- <https://github.com/anweiss/prodjlink-rs>
- <https://github.com/chrisle/alphatheta-connect>
- <https://github.com/grantHarris/prolink-cpp>
- <https://github.com/usr-ein/prolink>
- <https://github.com/Deep-Symmetry/beat-link>
- <https://github.com/fiverecords/SuperTimecodeConverter>

The audit reads fixture construction paths and retained capture contents rather
than treating hardware-support claims as packet provenance. Exact revisions,
findings, and the one newly retained corroborating legacy payload are in the
machine-readable audit.

## BPM tolerance boundary fixture

- `data/static-analysis/bpm-tolerance-boundaries.disasm.txt` preserves the two
  relevant functions from the pinned Rekordbox 7.2.19 x86-64 Mach-O whose
  SHA-256 is
  `07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244`.
  `tools/disassemble_symbols.py` generates the instruction listing; the
  artifact's leading comment records the reviewed interpretation and address
  ranges. `conformance/test_bpm_tolerance_static_analysis.py` binds those
  claims to the retained symbols and instructions.
- `conformance/fixtures/generated/bpm-tolerance-boundaries/` contains an
  encrypted 43-track database with logical fingerprint
  `daffd7ce05f2b995a26d6320b577e0f2418eaf15a6199d0668c7bfd30ca55e32`.
- Each lower and upper ±1–6% boundary around 120.00 BPM has a track one
  hundredth below, exactly on, and one hundredth above it. The special
  zero-percent whole-BPM bucket has controls around both 119.50 and 120.49,
  plus the selected 120.00 BPM.
- `conformance/suites/bpm-tolerance-boundaries.json` declares the seven
  `0x1206` requests. `conformance/record_bpm_tolerance_boundaries.sh` records
  and independently repeats them against real Rekordbox only, then restores
  the baseline fixture. The completed golden and summary contain all seven
  exact-repeat cases.

## Persisted secondary columns across setup widths

- `conformance/generate_matrices.py` declares one legacy suite for each of the
  15 persisted secondary-column selections, reusing the matching deterministic
  settings fixture and case IDs.
- `conformance/record_secondary_legacy_matrix.sh` records and independently
  repeats those suites against real Rekordbox 7.2.19 only.
- `tools/summarize_secondary_legacy.py` verifies fixture equality, Sort-menu
  equality, 16-versus-12 argument widths, exact legacy-prefix rows, and
  hash-bound repeat receipts. Its canonical evidence target is
  `data/experiments/secondary-column-legacy/summary.json`.

## Track render argument types

- `conformance/data/render-argument-type-matrix.json` and the 16 suites under
  `conformance/suites/generated/render-argument-types/` cross all eight normal
  `0x3000` positions with string and blob tags after a valid Track-list warmup.
- `data/static-analysis/render-argument-types-parser.{json,md,disasm.txt}` is
  pinned to Rekordbox 7.2.19 executable SHA-256
  `07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244`.
  It validates the six-entry argument-tag dispatch, the tag-2/tag-3 preceding-
  length checks, pointer storage, and the renderer's untyped slot reads.
- `conformance/record_render_argument_type_matrix.sh` gives every probe an
  independent cold process and exact repeat. The reducer and guarded handoff
  preserve wire outcomes, process/Application health, receipts, and readable
  JSON/CSV summaries. Live results remain pending generation `ap18`.

## Track render numeric fields

- `data/static-analysis/render-numeric-fields.{json,md,disasm.txt}` pins
  `GetListBufContents`, `GetListBuf1stRow`, and `DBCommon_GetCateKind` to the
  Rekordbox 7.2.19 executable. It records every field width, proves that the
  client-reported total is unread, and retains the complete 51-entry category
  map.
- `conformance/suites/generated/render-numeric-fields.json` declares 42 normal
  Track renders spanning the first-row character seek, client total, category
  map ranges, and high-word aliases. The recorder, reducer, guarded handoff,
  and focused test preserve real-Rekordbox authority under generation `aq18`.
- The canonical summary accepts all 15 variants and 30 cases, binds every
  independent-repeat receipt, and proves exact 12-field prefix equality for
  every legacy row.

## Track render override controls

- `data/static-analysis/render-override-controls.{json,md,disasm.txt}` pins 24
  instructions across `GetListBufContents`, `GetListBufRowContent`, and
  `Get_SubCategoryValue`, including boolean gate normalization and split
  low-byte/full-width selector dispatch.
- `conformance/suites/generated/render-override-controls.json` declares the 17
  isolated gate and selector boundary cases.
- `conformance/record_render_override_controls.sh`,
  `tools/summarize_render_override_controls.py`, the guarded `ar18` handoff,
  and focused test preserve real-Rekordbox authority after `aq18`.

## Secondary-column controller ownership

- `data/static-analysis/subcolumn-controller-paths.disasm.txt` is a
  byte-reproducible extraction of every `getSortSetting`, `resetSubColumn`, and
  `setSubColumn` implementation on the Dev SQLite, AppSync, and desktop routing
  controllers, plus the low-level Dev/Master mutators, from the pinned
  Rekordbox 7.2.19 x86-64 Mach-O.
- The trace preserves AppSync's `Seq`-ordered settings read, multiple-selection
  diagnostic, exact bit-clear/bit-set SQL, synchronization metadata updates,
  and the desktop controller's database-mode dispatch. The independent Link
  Export fallback query remains in `subcolumn-sql.disasm.txt` and has no
  `ORDER BY`.
- `conformance/test_subcolumn_controller_paths.py` verifies the source binary
  hash, every owning symbol and SQL fragment, the AppSync setter-to-reset
  vtable binding, the documented reader distinction, and byte-identical
  regeneration with `tools/disassemble_symbols.py`.

## Device-status source inventory

The executable-side companion is
`data/static-analysis/model-name-state-path.disasm.txt`, SHA-256
`30575763a1dfa96c6504cd1de22648cfc65780454728114e534acbd0a6944035`.
It is generated from the pinned Rekordbox 7.2.19 x86-64 binary and retains the
player-status parser, stored model record, internal model-change message type
`0x6e`, independent membership path, complete accessor chain, UI notification,
and Display AIO cache. `conformance/test_model_name_state_path.py` validates the
binary hash, resolves the internal jump-table destinations, checks the storage
offsets, and reproduces the artifact byte-for-byte.

- `conformance/status-packets/xdj-xz-player-1-{analyzed,unanalyzed}-status-20260422.hex`
  retains two complete 292-byte kind-`0x0a` packets embedded as real physical
  XDJ-XZ captures in `cinderblock/netBeat` revision
  `399583fff849bddd8c8abd744d1d25e1656ba009`. The dated session notes identify
  the unit and capture conditions, but the parent JSONL, firmware, timestamps,
  address tuple, and paired keepalive are not committed. These are
  corroborating hardware fixtures, not captured-verbatim provenance.
- `conformance/status-packets/opus-quad-first-50002.hex` retains the exact
  36-byte kind-`0x10` UDP 50002 packet published from a physical OPUS-QUAD by
  `kyleawayan/opus-quad-pro-dj-link-analysis` at pinned revision
  `d7459fdc0884b704cdd5540b5bf5ab6d003c4ded`. It is modern physical-device
  corroboration, not a kind-`0x0a` player-status packet and therefore not
  eligible for the status-backed model matrix.
- `xxvw/Conduction` revision
  `07ee2989c5e2363c4c59bba7670864bea65072c2` independently distinguishes its
  Dysentery-derived captured fixtures from transcribed OPUS/export-source
  references. It supplies provenance corroboration but no new native status
  bytes.

- `tools/inventory_device_status_sources.py` scans every bundled Dysentery
  `.pcap`/`.pcapng` byte stream for fixed-width device model fields, hashes each
  capture, and classifies every lab status identity as captured verbatim or
  derived from the captured RX3 template.
- `data/static-analysis/device-status-source-inventory.json` is the generated
  machine ledger. `DEVICE_STATUS_PROVENANCE.md` states the evidence boundary
  and native-packet acquisition gaps.
- The inventory reads local artifacts only. It sends no packets and does not
  invoke Rekordbox or any future comparison backend.

## Local observations and captures

| Source | Role |
| --- | --- |
| `../captures/rekordbox-menus-20260928/LINK_EXPORT_MENUS.md` | Existing decoded menu survey |
| `../captures/rekordbox-menus-20260928/menu-tree.json` | Full captured request/response menu tree |
| `../captures/rekordbox-menus-20260928/findings.md` | Earlier findings and limitations |
| `../captures/real-rekordbox-20260924/eth0.pcap` | Real rekordbox network traffic |
| `../captures/rx3-rekordbox-working-ap-20260927.pcap` | Known-working RX3/rekordbox traffic through the AP |
| `../captures/rx3-rekordbox-lan-20260927.pcap` | RX3/rekordbox LAN capture |
| `../toolkit-source/captures/link-export-20260925T164951Z/` | Multi-interface Link Export capture session |

## rekordbox implementation artifacts

| Source | Role |
| --- | --- |
| `../artifacts/rekordbox/7.2.19/` | Version-pinned installer and extracted-symbol artifacts |
| `../toolkit-source/tools/rekordbox_reverse/analysis/` | Disassembly, strings, symbols and decoded capture summaries |
| `../rekordbox-windows/` | Reproducible Windows 11/QEMU installation and copied library |
| `../alphatheta-docs/devices/cdj-3000/application/remote-database-client.md` | CDJ-3000 `0x3006`/`0x4d02` ticket, post-load Delivery chain, timeout, retry, and reply parsing |

`STATIC_ANALYSIS.md` pins both the symbol-rich universal Mach-O and the exact
Windows PE used by the oracle. Generated disassembly lives under
`data/static-analysis/`; the Windows subset uses `.pdata` and MSVC RTTI to
recover stripped function and vtable boundaries. Static evidence establishes
implementation paths and constants for its named platform and build, but does
not by itself establish runtime reachability.

`data/static-analysis/user-info-djid.json` joins that CDJ-side source with the
hash-pinned Rekordbox 7.2.19 `OnUserCmd`, `GetDJID`, `KuvoService`, and server
startup paths. `USER_INFO_DJID_ORACLE.md` preserves the static/live evidence
boundary; no 7.2.19 wire result is inferred from the 7.2.11 observation named
by the device source.

The VM's historical rootful LAN mode uses the persistent Podman network
`rekordbox-lan`, a macvlan child of host interface `lan0`. Oracle recordings use
the separate host-only `rekordbox-isolated` network documented by
`../rekordbox-windows/systemd/rekordbox-windows-prepare-isolated`.

The preferred lifecycle interface is `../rekordbox-windows/vmctl`, backed by
fixed root-owned systemd units and a four-unit polkit allowlist. The checked-in
unit/helper/rule sources live in `../rekordbox-windows/systemd/`. Host changes
and removal steps are inventoried in `CLEANUP.md`.

The status-backed packed Play, remaining Song Info class-2, and Hot Cue getter
evidence is retained in `data/experiments/packed-context/{play-status-cross,class2-status-cross,hot-cue-getter-status-cross}/`, with canonical goldens
under `conformance/goldens/rekordbox-7.2.19/{xdj-rx3-status,cdj-3000-status}/`
and dedicated machine validators under `tools/`.

## Related implementations retained as historical context

| Source | Role |
| --- | --- |
| `/home/evan/workspace/rbxport/crates/rbl-dbserver/` | `rbxport` dbserver and menu implementation |
| `/home/evan/workspace/rbxport/crates/rbl-prolink/` | `rbxport` PRO DJ LINK protocol types |
| `/home/evan/workspace/rbxport/crates/rbl-link/` | `rbxport` network/link orchestration |
| `/home/evan/workspace/rbxport/crates/rbl-linkd/` | Link service integration and diagnostics |
| `/home/evan/workspace/rbxport/crates/rbl-index/src/smart.rs` | SmartList parser/evaluator and explicitly marked community-derived assumptions used to seed independent oracle cases |
| `/home/evan/workspace/rbxport/src-tauri/src/rx3_link.rs` | RX3-facing application integration |
| `../link-export-activate/` | RX3 Link Export activation work and device behavior |

## External protocol research

`../dysentery/` is the upstream Deep Symmetry Dysentery repository, checked out
at commit `f62a24ba947f9db4c1553bb2dc3ba76de1fecbb4`. Key documentation lives under
`doc/modules/ROOT/pages/`; `menus.adoc` and `track_metadata.adoc` are the primary
Link Export sources, while the remaining pages provide device/network context
or explicitly separate protocols. `data/external/dysentery-docs.json` pins all
14 guide documents, hashes, sizes, and headings, and `DYSENTERY_CROSSWALK.md`
records the complete relevance boundary. Beat Link is consulted for newer enum
coverage and implemented request semantics where Dysentery documents an older
generation.

[Pyrekordbox discussion 110](https://github.com/dylanljones/pyrekordbox/discussions/110)
documents the community operator names, root logical values, and representative
Rekordbox-written XML. It is a case-generation lead, not runtime proof. The
39-case real-Rekordbox golden independently establishes the observed result
sets and parser defaults used in this research.

[Pyrekordbox's SmartList source](https://github.com/dylanljones/pyrekordbox/blob/master/pyrekordbox/masterdb/smartlist.py)
enumerates the 23 written property names and operator families used to seed the
property matrix. The 33-case real-Rekordbox golden independently establishes
the field mappings, accepted alias, and raw My Tag representation reported here.

[Zetetic's SQLCipher API reference](https://www.zetetic.net/sqlcipher/sqlcipher-api/)
documents the random database salt and per-page encryption behavior relevant to
fixture reproducibility. Fixture manifests therefore distinguish the exact
encrypted-file SHA-256 from a canonical decrypted schema/row fingerprint.

[The Rekordbox 7.2.14 manual](https://cdn.rekordbox.com/files/20260409151936/rekordbox7.214_manual_EN.pdf)
defines the View > Display Type key preference as Classic or Alphanumeric and
documents the independent "Display key information on the database" control.
[AlphaTheta's operation FAQ](https://rekordbox.com/en/support/faq/operation-hint/)
gives representative Classic and Alphanumeric spellings. The official
[release notes](https://rekordbox.com/en/support/releasenote/page/7/) record a
past LINK EXPORT defect involving Alphanumeric key ordering, establishing that
the preference is relevant to this protocol surface. These sources define the
configuration matrix; real-Rekordbox goldens establish its wire effects.

## Source-handling rule

Existing prose is treated as a lead, not proof. The final reference cites the
specific capture, code path, symbol/string location or live experiment behind
each substantial claim. Contradictions are retained in the gap matrix until a
targeted experiment resolves them.

## Local derived artifacts

| Source | Role |
| --- | --- |
| `data/source-menu-tree.json` | Immutable local copy of the 90-node traversal |
| `data/summary.json` | Source hash, capture context and traversal limits |
| `data/menu-nodes.csv` | One row per captured logical menu |
| `data/request-signatures.csv` | Request kind, argument types, counts and samples |
| `data/item-types.csv` | Rendered row/item-type inventory |
| `data/secondary-column-semantics.json`, `tools/generate_secondary_column_semantics.py`, and `conformance/test_secondary_column_semantics.py` | Byte-reproducible join of 63 real-Rekordbox persisted-column, six-argument active-sort, eight-argument control, and active-sort persisted-fallback profiles over 504 row projections, retaining exact fields 0/5/6/12-15 and proving the cached-composite boundary |
| `data/static-analysis/item-type-domain.json`, `tools/audit_item_type_domain.py`, and `conformance/test_item_type_domain.py` | Byte-reproducible corpus-wide audit of every represented `0x4101` argument-6 value, resolving Dysentery's upper-two-byte question for the canonical Rekordbox 7.2.19 corpus while preserving it as a cross-version boundary |
| `ITEM_TYPE_REFERENCE.md`, `data/item-type-reference.json`, `tools/generate_item_type_reference.py`, and `conformance/test_item_type_reference.py` | Generated readable and machine-complete catalog of all 85 represented item types, joining 51,148 corpus occurrences to simple/menu/composite encoding, documented meanings, producing request kinds, bounded raw samples, and every source golden without importing backend behavior |
| `OBSERVED_RESPONSE_SHAPES.md`, `data/observed-response-shapes.json`, `tools/generate_observed_response_shapes.py`, and `conformance/test_observed_response_shapes.py` | Generated request-to-response index over every canonical Rekordbox 7.2.19 golden: exact immediate and render reply kinds, ordered argument-type signatures, outcomes, source request kinds, `0x4101` item types, occurrence counts, corpus hash, every source file, a readable 17-profile identity table, and per-request profile/model/status/setup coverage; setup exchanges and pre-request drains retain independent identity/setup provenance, with drains remaining asynchronous evidence, while a distinct declaration-corpus hash binds 222 cases across 36 suite files for the five classified kinds without canonical responses |
| `data/source-findings.md` | Local copy of the concise source-capture findings |
| `data/source-probes/` | Exact local snapshots of the three Rust capture probes |
| `data/database/` | Sanitized menu/category/sort/color rows and schemas from the copied database |
| `data/static-analysis/` | Generated function disassembly for the pinned rekordbox binary |
| `data/static-analysis/model-literal-owner-audit.json`, `tools/audit_model_literal_owners.py`, and `conformance/test_model_literal_owner_audit.py` | Byte-reproducible symbol-rich ownership inventory for all 30 direct exact-`XDJ`/`XDJ-AZ` literal references, separating database serving from audio, controller, UI, and anonymous deck-helper uses while binding the Windows companion counts |
| `data/static-analysis/link-export-dispatch-tables.json` | SHA-verified ten-table Rekordbox request dispatcher extraction, top-level default route, and direct arms |
| `data/static-analysis/link-export-request-vocabulary.json` | Complete 185-kind union of firmware-enum commands, the physical RX3 `0x0001` cancellation control, conformance probes, and Rekordbox-only arms with per-kind coverage and provenance; pins the RX3 `RecvFromCommTask` source that constructs the command |
| `data/static-analysis/year-list-handler.disasm.txt` | Complete pinned Year-handler body proving Release Year, rejected Stock Date, and Date Added routing |
| `data/static-analysis/xdj-rr-client-navigation.json` | Generated six-source, 121-wrapper, 304-direct-call inventory joining XDJ-RR player actions to 102 request kinds and the constructor-derived menu-location expression; all source hashes and the AlphaTheta docs commit are pinned |
| `data/static-analysis/source-only-client-handlers.disasm.txt` | Old-Key/Cue Track, write, database-modification, and reply dispatch used to close every directly called XDJ-RR kind |
| `data/static-analysis/source-only-client-db-effects.disasm.txt` | AppSync old-Key queries plus Rating, BPM, analysis-path, and quantize-flag database effects for adjacent client commands |
| `conformance/data/xdj-rr-location9-matrix.json`, `suites/generated/xdj-rr-location9/`, `record_xdj_rr_location9_matrix.sh`, `run_xdj_rr_location9_after_cues.sh`, and `tools/summarize_xdj_rr_location9.py` | Six-suite, 36-case real-Rekordbox declaration for the XDJ-RR source-defined `2602` location-9 context, including ordinary/RX3/CDJ identities, both row widths, independent cold repeats, and distinguishable-track stale-buffer assertions |
| `data/static-analysis/adjacent-payload-loaders.disasm.txt` | Active AppSync/fallback Master artwork implementations and detailed waveform, segmented-key, and extended-cue payload builders |
| `data/static-analysis/adjacent-payload-parser-loaders.disasm.txt` | Complete pinned x86-64 bodies for the loud/dot waveform, beat-grid, VBR, detailed-waveform, segmented-key, beat-grid-header, arbitrary-atom, and JPEG-dimension parsers; directly proves PMAI validation, the `PWV3`/`PKEY` section scans, and the nonzero 800-by-800 JPEG ceiling |
| `data/static-analysis/adjacent-payload-services.json` | Generated request arguments, replies, database/filesystem dependencies, response shapes, and live state for both artwork and all fourteen analysis-class commands |
| `conformance/fixtures/generated/payload-paths/`, `conformance/suites/adjacent-payload-missing-files.json`, its generator/recorder/reducer, `conformance/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-missing-files.json`, and `data/experiments/adjacent-payload/missing-files/` | Deterministic encrypted nonempty-missing, empty-string, and SQL-null artwork/analysis paths plus playlist artwork; completed cold-process record/repeat proves all 31 cases return service-specific envelopes, with hash-bound fixture, health, summary, matrix, cleanup, and finalization evidence |
| `conformance/payload-assets/`, `conformance/fixtures/generated/payload-valid/`, `conformance/suites/adjacent-payload-success.json`, `conformance/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-success.json`, `record_adjacent_payload_success.sh`, `run_adjacent_payload_success_after_missing_files.sh`, `tools/summarize_adjacent_payload_success.py`, `conformance/test_payload_assets.py`, and `data/experiments/adjacent-payload/success/` | Self-authored deterministic 8-by-8 JPEG and PMAI DAT/EXT/2EX bytes, encrypted database paths, and 15 direct-response declarations across all ten filesystem-backed kinds; completed cold record/repeat returns 12 payload-bearing and three empty/scalar replies, with exact widths, guest-side hashes, four clean health captures, narrowly scoped cleanup, strict real-Rekordbox reduction, and a hash-bound finalization receipt |
| `conformance/suites/generated/adjacent-payload-success-status/`, `record_adjacent_payload_success_status_cross.sh`, `run_adjacent_payload_success_status_after_history.sh`, and `tools/summarize_adjacent_payload_success_status.py` | Four byte-reproducible successful-payload suites crossing genuine RX3 player 11 and matched CDJ-3000 player 1 status with both setup widths; 60 declared observations use requester-correct packed contexts, independent cold repeats, guest-asset verification/cleanup, and a difference-preserving aggregate reducer |
| `conformance/payload-assets/boundaries/`, `conformance/suites/generated/adjacent-payload-boundaries/`, `conformance/data/adjacent-payload-boundary-matrix.json`, and their generator/recorder/reducer/handoff | Thirty byte-reproducible four-file profiles and 57 focused requests cover exact JPEG byte/dimension gates, beat-grid count ceiling, preview/VBR fixed counts, detailed-wave/key count and stride fields, and duplicate aligned/unaligned specified atoms; every profile receives independent cold record/repeat, guest hash verification, health evidence, and exact-path cleanup |
| `conformance/fixtures/generated/adjacent-payload-cues/`, `conformance/suites/adjacent-payload-cue-success.json`, `conformance/suites/generated/adjacent-payload-cues/`, and their generator/recorder/reducer/handoff | Encrypted 19-content/530-cue fixture plus 114 declarations establish successful `2104`/`2b04` framing, exact legacy and extended record decoding, 0/1/3/255/256 counts, all cue option fields, null/deleted rows, type/location behavior, RX3/CDJ setup crosses, and three independently isolated seek-parser states |
| `data/static-analysis/other-client-dispatch.disasm.txt` | Focused symbol-bounded disassembly for the complete recovered `3xxx` server dispatch tree |
| `data/static-analysis/list-buffer-location.disasm.txt` | Complete packed-context list-buffer predicate, render path, insert mapping, and context-selective clear used to explain process-wide menu-location state |
| `data/static-analysis/listbuf-transaction-state.disasm.txt` and `conformance/test_song_info_malformed_transaction.py` | Hash-pinned transaction finalizer and autocommit state machine, cross-checked against the Delivery wrapper/builder and `0x2602` parser declaration; proves that a wrong-type ContentID can bypass the normal commit/autocommit restoration tail |
| `data/static-analysis/song-info-command-lifecycle.disasm.txt`, `dbserver-connection-send.disasm.txt`, and `conformance/test_song_info_command_lifecycle.py` | Hash-pinned synchronous inbound command worker, player-keyed asynchronous response queue, disconnect state cleanup, and `0xfffffffe/0x0100` socket-close sentinel; statically explains the observed malformed Song Info orphan-reply routing |
| `data/static-analysis/player-hosted-song-info.json`, `tools/audit_player_hosted_song_info.py`, and `conformance/test_player_hosted_song_info.py` | Byte-reproducible 23-source role audit separating Rekordbox-local `0x4003` results from player-hosted `0x2202`/`0x2302` builders and five XDJ generations of client/stub-server contracts; four additional hash-bound whole-tree manifests cover 26,862 newer-generation C sources and confine every exact `0x2402`/`0x2502`/`0x4802` literal to name/format tables |
| `data/static-analysis/user-info-djid.{json,disasm.txt}`, `tools/audit_user_info_djid.py`, and `conformance/test_user_info_djid.py` | Byte-reproducible Rekordbox 7.2.19 and CDJ-3000 audit for the `0x3006`/`0x4d02` contract, mixed-endian `djprofile.nxs` validation, 32/160-byte payload construction, server-start ownership, and post-load browsing dependency |
| `conformance/user-info-djid-profiles/`, `conformance/data/user-info-djid-matrix.json`, ten generated user-info suites, `tools/generate_user_info_djid_{profiles,suites}.py`, `conformance/record_user_info_djid_matrix.sh`, `tools/summarize_user_info_djid_matrix.py`, and `conformance/run_user_info_djid_after_render_controls.sh` | Authority-only declaration of 142 `0x3006` cases across three identities, parser boundaries, and eight profile states; deterministic inputs, exact guest backup/restoration, fresh-process record/repeat, health capture, strict reduction, and guarded finalization are established while live results remain pending |
| `data/static-analysis/context-track-type.disasm.txt` | Focused Track dispatch, active AppSync root, renderer extraction, and track-type-one enrichment gate |
| `data/static-analysis/context-track-type-routing.disasm.txt` | Exact `OnClientReq` request-class dispatch and list-only `0x03`/`0x04` interception |
| `data/static-analysis/played-track-cache-member-xrefs.txt`, `played-track-cache.disasm.txt`, and `tools/find_member_offset_references.py` | Reproducible ownership trace for argument-7 bit `0x100`: persisted played-state settings, `RowDataTrack` Link bit, ID snapshot, dbserver cache offsets, renderer membership, and the shared `0x3b03` query |
| `data/static-analysis/bpm-tolerance-boundaries.disasm.txt` | Exact selector-6 integer bound construction, zero-tolerance whole-BPM special case, and inclusive comparison predicate |
| `data/static-analysis/hot-cue-bank.disasm.txt` | `0x2001` catalog and `0x2101` cue-info dispatch/getter/`0x4702` serializer paths |
| `data/static-analysis/hot-cue-bank-{mutations,master-mutations}.disasm.txt` and `hot-cue-setter-reply-target.json` | AppSync/master implementations for legacy setter `0x2201`, extended getter `0x2301`, extended setter `0x2401`, active membership query, variable-record serialization, mutation paths, and reproducible AppSync reply-getter vtable resolution |
| `data/static-analysis/hot-cue-bank-membership-resolver.disasm.txt` | Exact AppSync `HCBnkSong_GetCueID` query and its anomalous rejection of a one-row result |
| `data/static-analysis/hot-cue-bank-legacy-setter.disasm.txt` | Exact AppSync legacy setter and post-update `GetUsbCue` path, including the unadjusted D/E/F ordinal |
| `data/static-analysis/hot-cue-bank-notifications.disasm.txt` | Setter dispatch notification gate plus adjacent delivery classes; Hot Cue Bank invokes the installed sink as class 3 with the resolved CueID and zero extra data |
| `data/static-analysis/hot-cue-bank-notification-callback.disasm.txt` | Complete callback installation and class-3 sink trace; the setter update becomes the in-process call `DatabaseIF::notifyDBUpdated(0x1e, CueID, 0)` rather than a Link Export packet |
| `data/static-analysis/dbserver-command-parser.disasm.txt`, `dbserver-connection-send.disasm.txt`, and `hot-cue-reply-routing.disasm.txt` | Six-field `0x2401` declaration; receive-side `1..0x4fffff` blob bound and partial-command behavior; connection-close sentinel construction; correlated `0x4e02` construction and device-keyed shared-queue routing |
| `data/static-analysis/cue-seek-value-parser.disasm.txt` | Exact unsigned-decimal UTF-16 parsing and separator advancement used by extended cue seek fields |
| `data/static-analysis/cue-time-conversion.disasm.txt` | Exact millisecond-to-150-fps cue/loop conversion body |
| `conformance/fixtures/generated/hot-cue-banks/`, `hot-cue-bank-pagination/`, cue/mutation/legacy/deleted-member Hot Cue fixtures, Hot Cue Bank suites, RX3/RR goldens, and `data/experiments/hot-cue-bank/` | Controlled tree/membership/cue sources plus repeat-verified catalog, 70-row render pagination, complete location/render cross, process-wide location-buffer state, complete count-width/signed-boundary controls, direct responses, both setter mutations, the D/E/F mutation gate, acknowledged no-op ordinal boundaries, and the deleted-bank tree/direct predicate split |
| `data/experiments/packed-context/hot-cue-catalog-status-cross/`, four `context-hot-cue-catalog-status-*.json` goldens, their suites, generator, recorder, and validator | Repeat-verified real-Rekordbox `0x2001` root/populated/empty behavior across all seven packed types, authentic RX3 and derived CDJ-3000 status controls, and both setup widths; backend replay is deferred |
| `data/experiments/hot-cue-bank/` | Machine-validated catalog/cue summary, malformed/crash controls, outbound gating, setter resolver controls, and live base/WAL/SHM durable-mutation captures |
| `conformance/data/track-compatibility-exhaustive-matrix.json`, `fixtures/generated/compatibility-exhaustive/`, its extended/legacy suites and goldens, recorder/reducer/tests, `data/experiments/track-compatibility-exhaustive/`, and `data/static-analysis/device-predicate-bodies.disasm.txt` | Repeat-verified 382-row proof of the complete FileType byte predicate, wide integer narrowing, SampleRate equality boundaries, and BitDepth non-input across both row widths; setup and finalization receipts bind clean health, exact legacy prefixes, and the pinned static predicate |
| `data/experiments/source-library-count-audit.json`, `tools/audit_source_library_counts.py`, and `conformance/test_source_library_count_audit.py` | Hash-bound audit proving that the 2026-09-29 source and relocated databases each contain the same 4,342 live ContentIDs and ContentLink partitions; bounds the screenshot-only 4,356 count without attributing its unretained UI/session source |
| `conformance/data/song-info-location2-malformed-history-matrix.json`, 256 ordered-pair suites, `song-info-delayed-reply-routing-matrix.json`, their recorders/reducers/tests, and `data/experiments/song-info-status-location2/{malformed-history-pairs,malformed-history-timing,delayed-reply-routing,malformed-history-lifecycle}/` | Cold-process RX3 player-11 malformed-history evidence: 47 historical promoted pairs; retained pair-48 conflict; complete 28-observation timing partition; complete 24-observation malformed-versus-valid routing proof; and the active distinct lifecycle-aware 256-pair rerun, which captures setup and a 1200 ms no-send drain before every declared request and leaves a 3000 ms no-client interval after blob-valued Delivery. `summary.partial.json` and `matrix.partial.csv` verify 224 promoted pairs and 672 request executions. Generation `z34` completed all 16 successors after blob-valued Play and all 16 after zero-context Play. The complete alternate-location-Play, argumentless-Delivery, missing-content-Delivery, extra-argument-Delivery, string-context-Delivery, and blob-context-Delivery rows each preserve every successor's ordinary result. In each row, blob-content Play queues delayed `0x4000 [0x2102, 0]` into the health drain before 13-row health; every other drain is silent, including blob-content Delivery after its measured no-client interval. Every health request returns 13 rows, and every extra-argument-Delivery precursor returns 13 rows. Pair 135's divergent `z34` runs independently prove the health connection can race that frame; `z35` promoted two wholly fresh delayed-frame runs. Pair 141's activation, guest-readiness, and stale-work-slot guard attempts, pair 194's unmatched record/exhausted-repeat-activation attempt, and pair 199 and pair 215 delayed-frame admission races are separately hash-bound. `z38` promoted authority through pair 193; `z39` promoted wholly fresh pairs 194 through 198; `z40` promoted pairs 199 through 214 before pair 215's first race; `z41` and `z42` preserved two further pair-215 admission races; `z43` promoted pair 215 from two wholly fresh matching runs and completed the blob-context-Delivery row. Retained pair-16, pair-99, pair-104, pair-106, pair-111, pair-135, pair-199, and pair-215 attempts preserve every observed admission race without changing canonical authority. Mixed-player `z20` remains quarantined rejected evidence |
| `conformance/data/hot-cue-setter-parser-matrix.json`, three lifecycle matrices, their generated suites, recorders/reducers/tests, and `data/experiments/hot-cue-bank/extended-setter-parser/` | Complete 57-variant structural oracle: 54 repeat-golden variants plus strict 60/60 declared-length `UINT32_MAX`, 3/3 slot-8, and 3/3 returned-slot `UINT32_MAX` lifecycle evidence; includes transaction-aware captures, logical base/WAL/SHM state, same-database restart getters, resumable recording, and documented cleanup |
| `conformance/data/hot-cue-legacy-setter-parser-matrix.json`, generated legacy parser suites, recorder/validator/tests, and `data/experiments/hot-cue-bank/legacy-setter-parser/{summary.json,matrix.csv}` | Complete 57-probe `0x2201` safety matrix with a fingerprinted database baseline, 114 isolated process/health/getter/database runs, conditional same-database restart evidence, hash-bound receipts, the exact mutation/crash boundaries, and a dynamically verified fixed-word map |
| `conformance/suites/hot-cue-bank-buffer-disconnect-{warmup,post}.json`, lifecycle recorder/validator/tests, and `data/experiments/hot-cue-bank/buffer-disconnect/` | Repeat-verified control/rejoin experiment proving context-keyed list-buffer persistence across a 40-second device disappearance and same-identity rejoin; static `PSvDBMain::Disconnect` evidence is retained in `device-identity-paths.disasm.txt` |
| `data/rekordbox-mobile-controls.pcap` | Negative baseline; mobile controls, not Link Export |
| `data/rekordbox-windows-lan-startup.pcap` | Early LAN startup/connectivity capture |
| `data/rekordbox-no-player-5min.pcap` | 3,695-packet negative baseline; no PDJL/dbserver ports |
| `data/isolated-rx3-identity-unicast-delivery.pcapng` | Direct isolated RX3-shaped keepalive delivery and rekordbox startup reply |
| `../captures/rx3-rekordbox-working-ap-20260927.pcap` UDP 50002 player-11 payload | Byte-exact 292-byte status template used to populate Rekordbox's AIO model cache |
| `data/seeded-full-master.db` | Fixture database after rekordbox injected eight factory sampler rows |
| `data/rekordbox-provisioned-empty-master.db{,-wal,-shm}` | Pre-baseline empty fixture after rekordbox persisted its 28 factory My Tag rows |
| `data/rekordbox-{xdj-rx3,cdj-3000}-link-enabled.png` | Live UI evidence for identity-dependent Link-panel controls |
| `data/rekordbox-preferences-dj-system-*.png` | Real Category, Sort, and Column preference controls in unlocked and active-Link-locked states |
| `data/session-refresh/` | Same-process Album category removal, Comments sort activation, and KEY-to-COMMENTS declarations and typed results; shared-process lifecycle, UI screenshots, encrypted DB/WAL evidence, and machine-validated summary |
| `conformance/goldens/rekordbox-7.2.19/xdj-rx3/` | 307 real XDJ-RX3 golden files containing 3,040 cases across navigation, capability, render, exhaustive Track context type, all-list-family context types, Song Info and Hot Cue Bank context types, device/setup interaction, pagination, errors, framing, concurrency, empty/legacy/extended families, Search/Search Track, settings, smart playlists, File Name boundaries, source visibility, scalar/numeric/string/UTF-16 boundaries, invalid data, compatibility, History lifecycle, Hot Cue Bank predicates/mutation/state, Display Song Info, and Play/Delivery Song Info including path/cloud/file state, each independently repeated |
| `conformance/suites/context-track-types.json`, its generator/recorder/golden, and `data/experiments/packed-context/track-types/` | Exhaustive 256-value ordinary-Track final-byte oracle, both clean-run health pairs, machine summary, and fixture/artifact fingerprints; future backend replay is deferred |
| `conformance/suites/context-track-type-families.json`, its generator/recorder/golden, and `data/experiments/packed-context/family-cross/` | All 47 canonical list families crossed with client values `0x00..0x06`; exact repeat, health, routing, row-argument, and artifact evidence |
| `conformance/suites/context-analysis-track-types.json`, its generator/recorder/golden, and `data/experiments/packed-context/analysis-cross/` | Seven Song Info request kinds crossed with all seven client values; exact repeat, health, per-header result, and artifact evidence |
| `conformance/suites/context-hot-cue-track-types.json`, its generator/recorder/golden, and `data/experiments/packed-context/hot-cue-cross/` | Hot Cue Bank root, populated, and empty modes crossed with all seven client values; exact post-header render-timeout evidence and health |
| `conformance/suites/context-device-setup-{extended,legacy}.json`, 16 identity/setup goldens, and `data/experiments/packed-context/device-setup-cross/` | Eight ordinary identities x both setup widths over Track, hierarchy, Root, and Search context effects; exact repeats, behavior hashes, validator, and bounded-service journal |
| `conformance/data/cdj-2000nexus-status-matrix.json`, genuine status identity/packet, 13 variants, recorder/reducer/tests, and `data/experiments/device-status/cdj-2000nexus/` | Genuine Dysentery CDJ-2000nexus player-1 status crossed through 249 ordinary, setup, Song Info, and Hot Cue cases; all 13 variants have hash-bound independent-repeat receipts and semantically match the derived CDJ-3000 controls |
| `conformance/suites/context-display-status*.json`, six RX3/CDJ status/requester/setup goldens, and `data/experiments/packed-context/display-status-cross/` | Seven packed types over matched RX3 player-11 AIO, matched CDJ-3000 player-1, and RX3-status/requester-1 mismatch controls; exact repeats, requester-keyed ordering proof, validator, and bounded-service journals |
| `conformance/suites/context-play-status*.json`, four RX3/CDJ status/setup goldens, and `data/experiments/packed-context/play-status-cross/` | Seven packed types over matched RX3 player-11 and CDJ-3000 player-1 contexts under both setup widths; exact repeats, normalized identity equality, legacy-prefix proof, validator, and bounded-service journal |
| `conformance/suites/generated/render-arity-underflow.json`, its recorder/reducer/handoff/tests, and `data/experiments/render-arity-underflow/` | Track render arity underflow declaration: correctly framed counts 0-2 after an initialized Default Track list, with raw outcomes, fresh-connection health controls, and queued real-Rekordbox record/repeat |
| `conformance/suites/context-class2-status*.json`, four RX3/CDJ status/setup goldens, and `data/experiments/packed-context/class2-status-cross/` | Delivery and recognized kinds `2202`-`2502` over seven packed types, matched RX3/CDJ contexts, and both setup widths; exact repeats, normalized identity equality, legacy-prefix proof, validator, and bounded-service journal |
| `conformance/suites/context-hot-cue-getter-status*.json`, four RX3/CDJ status/setup goldens, and `data/experiments/packed-context/hot-cue-getter-status-cross/` | Legacy/extended direct getters over populated/empty banks, seven packed types, matched RX3/CDJ contexts, and both setup shapes; exact repeats, status-50 rejection proof, normalized equality, validator, and bounded-service journal |
| `conformance/suites/context-hot-cue-setter-status*.json`, four RX3/CDJ status/setup goldens, and `data/experiments/packed-context/hot-cue-setter-status-cross/` | Extended setter over all seven packed types, matched RX3/CDJ contexts, and both setup shapes; exact fixture-reset repeats, 24 post-rejection getter controls, accepted mutation readback, response equality, validator, and bounded-service journal |
| `conformance/data/hot-cue-setter-field-matrix.json`, 56 generated suites, recorder/reducer/tests, and `data/experiments/hot-cue-bank/extended-setter-fields/` | Complete real-Rekordbox matrix for every non-seek mutable field boundary: 56/56 variants and 112 fixture/process executions with exact response, database snapshot, and repeat receipts |
| `conformance/data/hot-cue-setter-seek-matrix.json`, 17 generated suites, health-aware recorder/reducer/tests, and `data/experiments/hot-cue-bank/extended-setter-seek/` | Complete available-byte, descriptor-length, inbound-validity, and outbound-only setter matrix: 17/17 variants and 34 cold process/database captures, including the three repeat-verified replacement-overlap fault cases |
| `../dysentery/doc/assets/captures/S05-link-browse/run.pcapng`, `conformance/status-packets/cdj-2000nexus-player-1.hex`, its identity/matrix declarations, and `data/experiments/device-status/cdj-2000nexus/` | Genuine generation-2 CDJ-2000nexus player-1 status source, exact payload provenance, validated raw-packet emitter path, and completed 249-case real-Rekordbox matrix with 13/13 repeat-verified semantic matches to the derived CDJ-3000 controls |
| `conformance/suites/context-hot-cue-legacy-setter-status*.json`, four RX3/CDJ status/setup goldens, and `data/experiments/packed-context/hot-cue-legacy-setter-status-cross/` | Legacy setter over all seven packed types, matched RX3/CDJ contexts, and both setup shapes; exact fixture-reset repeats, 24 pristine D/E/F getter controls, accepted slot-4 mutation, response equality, validator, and bounded-service journal |
| `conformance/goldens/rekordbox-7.2.19/{cdj-3000,cdj-2000nxs2,xdj-xz,xdj-az,xdj-1000mk2,unknown-mixer,unknown-djm}/` | Real full and legacy device-identity goldens, each independently repeated; together with XDJ-RX3 they cover every named model and all four keepalive classes |
| `conformance/goldens/rekordbox-7.2.19/{xdj-rx3-status,cdj-3000-status,xdj-xz-status,xdj-az-status,xdj-1000mk2-status,unknown-mixer-status}/` | Repeated status-backed Display classification/model-consistency recordings plus complete stable Play/Delivery baseline, render, pagination, malformed, and legacy recordings for authentic RX3 status and the RX3-template-derived CDJ-3000 control |
| `data/static-analysis/display-song-info-{dispatch.disasm,direct-xrefs}.txt` | Generated dispatch, database-builder, AIO classifier, and direct-caller evidence for request `0x2002` |
| `data/static-analysis/category-configuration-fields.disasm.txt` | Root-serving `ID`/`MenuItemID`/`Seq`/`Disable` accesses, settings-editor `InfoOrder` persistence, and the boundary proving content emptiness and `InfoOrder` do not affect root serving |
| `data/configuration-behavior-map.json`, `tools/generate_configuration_behavior_map.py`, and `conformance/test_configuration_behavior_map.py` | Deterministic join of the four sanitized configuration tables, root masks and predicates, field ownership, settings refresh, render arities, and all eleven repeat-verified RX3 active-sort/six-argument row observations |
| `SQL_LITERAL_INDEX.md`, `data/static-analysis/sql-literal-index.json`, `tools/generate_sql_literal_index.py`, and `conformance/test_sql_literal_index.py` | Generated index of 36 exact SQL literals across 79 occurrences in 84 retained disassembly artifacts; distinguishes 33 structurally complete literals from three fragments and binds every occurrence to source hash, line, address, function heading, and platform |
| `CONTROL_AND_MUTATION_REFERENCE.md`, `data/static-analysis/control-mutation-command-map.json`, `tools/generate_control_mutation_reference.py`, and `conformance/test_control_mutation_reference.py` | Complete generated join for 54 control/mutation commands: 20 mutation/state writes, 12 state queries, ten other recognized routes, eight rejected arms, three log-only commands, list-buffer rendering, and 97 exact XDJ-RR caller sites with source/line/location provenance |
| `data/static-analysis/device-predicate-audit.{json,md}`, `device-predicate-audit-arm64.{json,md}`, `tools/audit_device_predicates.py`, and `conformance/test_device_predicate_audit.py` | Hash-pinned, byte-reproducible dual-slice inventory of 23 Link peer identity/capability helpers: 67 x86-64/five database-serving and 68 ARM64/six database-serving references; the sole count delta is a duplicate ARM64 compatibility call from the same row builder |
| `data/static-analysis/device-{predicate-bodies,model-callers}.disasm.txt` | Exact predicate bodies, capability bits, model literals, and every direct exact-model caller |
| `data/static-analysis/db-interface-selection.{json,md,disasm.txt}` | Pinned complete x86-64 vtable-selection evidence separating the shared AppSync server object from non-index-3 Master filter wrappers |
| `data/static-analysis/hot-cue-seek-fault.disasm.txt` | Complete active AppSync getter and advancing decimal helpers, localizing both seek-string interior-pointer frees |
| `data/static-analysis/search-query.disasm.txt` | Complete Search implementation and wrapper, including tokenization, four Category domain gates, content visibility/deduplication, and the 1,000-row cap |
| `data/static-analysis/request-1500-{immediates,disasm}.txt` | Validated immediate owners, exact four-argument formatter, cache branches, and Search Track dispatch evidence |
| `data/static-analysis/search-result-implementation.disasm.txt` | Ordinary and new-command Search result implementations, including budget and configured-sort paths |
| `data/static-analysis/playlist-queries.disasm.txt` | Playlist list/track wrappers and lower-level playlist data, membership, and count getters |
| `data/static-analysis/smart-playlist-paths.disasm.txt` | Exported `getRowset_Playlist` path plus desktop smart-list evaluator entry points |
| `data/experiments/search/` | Exploratory Search/Search Track declarations and repeat-verified results for domains, Unicode, tokenization, request fields, all sort IDs, length/arity boundaries, pagination, Category gates, SearchStr exclusion, and 1,000/5,000/10,005-row probes, plus the machine-validated canonical summary |
| `conformance/fixtures/generated/search-ceiling/` | Deterministic encrypted 1,005-track source used to prove the live 1,000-row Search cap and cap-edge rendering |
| `conformance/fixtures/generated/search-text/` | Deterministic encrypted Unicode text source for precomposed/decomposed, non-ASCII case, supplementary-plane, UTF-16 length, and embedded-NUL Search behavior |
| `conformance/fixtures/generated/search-track-{ceiling,large,large-title}/` | Deterministic encrypted 5,005/10,005-track sources for Search Track limits, SearchStr exclusion, and cache-independent sort behavior |
| `conformance/fixtures/generated/scalar-boundaries/` | Deterministic encrypted stored values outside advertised Rating, Bitrate, and Color root domains |
| `data/experiments/scalar-selectors/` | Repeat-verified exploratory declarations, canonical summary, complete valid selector cross, and root/direct hidden-domain evidence |
| `conformance/fixtures/generated/smart-playlists/` and `data/experiments/smart-playlists/` | Contradictory rule/membership fixture, exploratory oracle, unchanged post-startup database copy, canonical summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-rule-matrix/` and `data/experiments/smart-rule-matrix/` | Thirty-nine-playlist operator/group/parser fixture, exact repeated golden, machine-validated summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-numeric-matrix/` and `data/experiments/smart-numeric-matrix/` | Sixty-playlist stored numeric comparison/conversion fixture, exploratory capture, exact repeated golden, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-property-matrix/` and `data/experiments/smart-property-matrix/` | Thirty-three-playlist property vocabulary and source-mapping fixture, exploratory capture, exact repeated golden, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-date-matrix/` and `data/experiments/smart-date-matrix/` | Thirty-playlist fixed-date comparison fixture over all three date properties, exploratory capture, exact repeated golden, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-numeric-boundaries/` and `data/experiments/smart-numeric-boundaries/` | Ten-track SQL null/REAL/wide-integer fixture crossed through five numeric Smart properties and missing XML endpoints; exploratory repeat, exact repeated golden, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-relative-date-matrix/` and `data/experiments/smart-relative-date-matrix/` | Fifty-six-playlist controlled-clock relative-date fixture, repeated exact golden, clock restoration evidence, UI diagnostic screenshots, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-date-format-matrix/` and `data/experiments/smart-date-format-matrix/` | Forty-track/117-playlist exact-length, separator, character-class, calendar-normalization, epoch, embedded-NUL, and SQL-null fixture; exploratory capture, repeated exact golden, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-text-matrix/` and `data/experiments/smart-text-matrix/` | Forty-three-track/55-playlist Comments collation fixture spanning all applicable string operators, case, accents, normalization, expansions, scripts, width, kana, supplementary characters, punctuation, whitespace, XML entities, empty/null, and embedded NUL; repeated exact golden, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-string-property-matrix/` and `data/experiments/smart-string-property-matrix/` | Ten-track/104-playlist cross-property fixture proving identical string semantics for nine lookup-backed and four direct properties, including empty lookup names, missing relations, direct empty strings, and SQL `NULL`; exploratory capture, repeated exact golden, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-mytag-matrix/` and `data/experiments/smart-mytag-matrix/` | Eight-track/49-playlist My Tag fixture covering operators 1-11, zero/high-bit/maximum tag IDs, signed integer parsing boundaries, blank and malformed values, ignored attributes, and multi-condition all/any logic; exploratory capture, repeated exact golden, static cross-check, machine summary, and rbxport comparison |
| `conformance/fixtures/generated/smart-xml-matrix/` and `data/experiments/smart-xml-matrix/` | Eight-track/73-playlist XML document/root/child/attribute matrix; corrected v2 fixture, preserved v1 design control, exploratory repeats, exact repeated golden, machine summary, and rbxport comparison |
| `conformance/suites/smart-serving-{crosses,legacy}.json` and `data/experiments/smart-serving-crosses/` | Rule-only populated SmartList crossed with all sort IDs, render/secondary selectors, pagination edges, packed contexts, and both setup widths; exploratory repeat, exact repeated goldens, static cross-check, machine summary, and rbxport comparison |
| `conformance/suites/smart-device-cross.json`, eight identity goldens, and `data/experiments/smart-device-cross/summary.json` | Populated and empty SmartList results crossed with all ordinary discovery identities; immediate repeats, per-identity provenance hashes, normalized behavior equality, and rbxport comparison |
| `conformance/fixtures/generated/key-notation/`, four `key-notation-*`, two `key-device-setting-*`, and two persisted-BPM suites/goldens, plus `data/experiments/key-notation/` | Desktop-preference null cross plus local CDJ Classic/Camelot control over key menus, ordinary and Smart rows, persisted `BPM - Key`, sorting, Display Song Info, and Delivery Info; exact restart repeats, retained inputs, and machine summaries; backend replay deferred |
| `data/static-analysis/key-notation-settings.disasm.txt`, `data/static-analysis/device-key-style.disasm.txt`, and `data/static-analysis/windows/{exchange-key-name,local-key-style}.disasm.txt` | Desktop `MusicKey` predicates plus the active local-device-setting serving call chain, symbolized file validation, style accessors, cache, and CRC implementation |
| `data/experiments/ui-debug/` | Before/after LINK activation and blocking Mobile Library Sync modal screenshots used to stabilize the real-Rekordbox recorder |
| `data/static-analysis/smart-condition-evaluator.disasm.txt` | Generated `getSmartlistCondition`, date conversion, relative-day/month conversion, and comparison helper evidence |
| `data/static-analysis/smart-xml-parser.disasm.txt` | Generated `getSmartlistContentData` and `getSmartlistNode` bodies proving JUCE document parsing, direct-child-only condition collection, logic fallback, and zero-condition rejection |
| `data/static-analysis/smart-date-conversion.disasm.txt` | Complete generated `dateToDay`, `pastMonthToDay`, and `pastDayToDay` bodies with pinned addresses |
| `data/static-analysis/smart-collation.disasm.txt` | Complete ICU `CollationRule` constructor, equality, contains, starts-with, and ends-with implementations with US locale and primary-strength setup |
| `conformance/fixtures/generated/filename-boundaries/` and `data/experiments/filename/` | Twenty-row FileNameL-exclusive fixture and validated all-sort formatting/UTF-16 summary |
| `data/static-analysis/song-info-siblings.disasm.txt` | Generated Play Song Info and Delivery Info wrapper, active AppSync builder, fallback builder, query, and field-construction evidence |
| `data/static-analysis/play-song-info-cloud-paths.{json,disasm.txt}`, `tools/audit_play_song_info_cloud_paths.py`, and `conformance/test_play_song_info_cloud_paths.py` | Byte-reproducible 7.2.19 audit proving the raw `CLSSyncMethod` default, its sole zero/nonzero Link Export decision, distinct filesystem predicates and roots, exact service-ID domains, and the one missing live equivalence class |
| `data/static-analysis/play-path-conversion.disasm.txt` | Complete `convertToRealPath` helper showing unified-path conversion and conditional drive replacement |
| `data/static-analysis/link-export-visibility.{disasm,xrefs}.txt` | Pinned visibility overloads, `FolderPath` streaming classifier, fixed-provider dispatcher, and nine validated direct call sites |
| `data/static-analysis/streaming-provider-registry.{json,disasm.txt}`, `tools/audit_streaming_provider_registry.py`, and `conformance/test_streaming_provider_registry.py` | Byte-reproducible 7.2.19 provider-manager audit proving five constructed classifier slots, login/path separation, Beatport's `/v4/catalog/tracks/` substring predicate, and the absent/constant-false Beatsource path |
| `conformance/fixtures/generated/streaming-provider-paths/`, `conformance/suites/generated/streaming-provider-paths.json`, `conformance/record_streaming_provider_paths.sh`, `tools/summarize_streaming_provider_paths.py`, and `conformance/run_streaming_provider_paths_after_user_info.sh` | Deterministic ten-track production-shaped provider-path fixture, seven-case real-Rekordbox authority cross, authority-first reducer, and guarded fresh-process record/repeat finalizer |
| `data/static-analysis/windows/`, its `manifest.json`, and `data/experiments/link-visibility/windows-history-summary.json` | Exact Windows PE metadata; `0x1112` History and `0x2002` Display dispatch; RTTI-derived `PSvAppSyncDBIF` vtables; active History/Display builders; Windows XDJ-prefix AIO, inline Disconnect cache clear, inline AppSync and standalone Master compatibility predicates, whole-image semantic signature/literal audit, and local-device Key-style helpers; all 20 extracts hash-bound to exact producer invocations and retained-installer provenance; machine-checked platform comparison |
| `data/experiments/song-info-sibling-errors/` | Cold, sequenced, prefix-bisected, and status-backed malformed parser-state recordings, including matched/mismatched player-location contexts and repeat pairs |
| `data/experiments/song-info-status-location2/` | Seventeen declarations, thirty-two successful real recordings, and two expected-failure transcripts isolating RX3 player-11 location-2 Delivery across valid, zero-context, malformed, reconnect/shared-socket, and render-location behavior |
| `PHYSICAL_RX3_SESSION.md`, `data/experiments/physical-rx3-session/{session-envelope,navigation-transcript}.json`, `tools/summarize_physical_rx3_{session,navigation}.py`, `conformance/suites/generated/physical-rx3-session-envelope.json`, and their recorder/reducer/finalizer | Deterministic complete reduction of the retained physical RX3 RemoteDBServer stream: 106 client messages, 268 captured server messages, 144 menu rows, exact legacy setup player 11 and reply, menu locations 1/3/5/8 with Rekordbox slot 4 and track type 1, root mask `0x05fdffff`, native browse/prefetch/selected-track cadence, compact hashes for 23 binary payloads, and an authority-only 7.2.19 replay that keeps physical requests separate from fresh server responses |
| `data/experiments/song-info-delivery-boundaries/` | Rejected same-process Delivery boundary candidate/repeat pair proving warmed row-order state before cold-process promotion |
| `data/experiments/song-info-delivery-order/` | Seventeen generated suites and 38 real-Rekordbox phase recordings proving Delivery ordinal permutations, six precursor-family effects, persistent/replaced TCP equality, discovery rejoin, and RX3-to-CDJ replacement behavior |
| `conformance/fixtures/generated/{delivery-boundaries,delivery-wide-strings}/` | Deterministic encrypted Delivery-only null/dangling, 126/127/128-unit, and 254/255/256-unit profiles |
| `conformance/fixtures/generated/play-paths/` | Fourteen-track encrypted local/cloud/path/file-state profile with deterministic fingerprint |
| `conformance/fixtures/generated/cloud-sync-zero/`, `conformance/suites/generated/song-info-cloud-sync-zero.json`, `conformance/record_play_song_info_cloud_sync_zero.sh`, and `conformance/run_play_song_info_cloud_sync_zero_after_provider_paths.sh` | Ten-track authority-only zero-branch fixture and guarded fresh-settings/process recorder covering local bypass, original file/directory, moved-root success/miss, helper service domains, exact guest restoration, and cleanup |
| `conformance/fixtures/generated/link-visibility/`, `conformance/goldens/rekordbox-7.2.19/xdj-rx3/link-visibility.json`, and `data/experiments/link-visibility/` | Fourteen-path visibility fixture, seven-case cold-process oracle and repeat evidence, machine summary, and retained invalid-Smart diagnostic |
| `../alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_{0016,0017,0019,001f,0020,0021}.c` | Complete direct named XDJ-RR `dbcl_` call surface: locations 1-8, 121 request wrappers, 304 callers, fixed-location service wrappers, left/right/specialized navigation, reload, Prepare/Tag List, and drag/drop paths; generated inventory in `xdj-rr-client-navigation.json` |
| `DATABASE_FIELD_REFERENCE.md`, `data/database/link-export-schema.json`, `tools/generate_database_field_reference.py`, and `conformance/test_database_field_reference.py` | Reproducible schema-only inventory for every table-like name in the request map: 22 physical AppSync tables, 389 columns, three runtime or alternate-interface names, direct and inverse table/semantic-field joins across all 95 classified wire request kinds, and independent schema, exact-SQL, and semantic-family evidence labels; the SQLCipher key remains memory-only |
| `conformance/results/rbxport/c144f19+tree.80e87ec8aace/` | Canonical replay of all 211 goldens/2,403 cases against the exact dirty `rbxport` source tree; includes per-file source hashes, per-suite adapter configuration, actuals, semantic diffs, logs, and summaries |

`tools/export_link_config.py` reproduces the database files without writing the
SQLCipher key or any track/library records.
