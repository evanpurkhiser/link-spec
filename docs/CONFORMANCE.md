# Link Export conformance lab

The conformance lab records real rekordbox as the behavioral oracle. Test
intent, fixture state, transport, and golden responses are separate artifacts,
and declarations remain backend-neutral for a later implementation phase.

## Current phase

Rekordbox 7.2.19 is the behavioral oracle. The recording queue remains isolated
from backend implementations, and `test_real_rekordbox_phase_boundary.py`
enforces that every script in the active serial queue, including its finalizer,
contains no backend invocation. The safe replay catalog can be evaluated
independently against rbxport or another adapter. Mutation and
lifecycle suites stay deferred until a backend-specific disposable-state
contract is defined.

## Architecture

```text
fixture profile + settings variant
              |
              v
       encrypted master.db
              |
       +------+------+
       |             |
  rekordbox       rbxport
       |             |
       +------v------+
         wire runner
              |
       canonical JSON result
              |
        record or verify
              |
          golden corpus
```

The runner talks to the port-query service and dbserver over their real TCP
protocol. It does not call either backend's catalog internals. A golden recorded
from rekordbox can therefore be compared byte-semantically at the typed-message
level against `rbxport`.

## Fixture profiles

`conformance/build_fixture.py` makes an encrypted copy of a known-good schema,
deletes Link Export library rows, inserts deterministic fixtures, and writes a
manifest. It refuses to overwrite an output directory.

| Profile | Purpose |
| --- | --- |
| `empty` | Zero-track roots, factory My Tag definitions, lookup leakage, valid empty menus, and error behavior |
| `full` | Every known category, hierarchy, wildcard, relation, secondary value, playlist, persisted history, and populated Hot Cue Bank |
| `payload-paths` | Artwork and analysis paths split into nonempty missing-file, empty-string, and SQL-null controls, plus a playlist artwork path whose file is absent |
| `payload-valid` | One content row and the primary playlist point at deterministic generated JPEG and PMAI DAT/EXT/2EX assets for successful payload-service captures |
| `adjacent-payload-cues` | Nineteen content rows isolate zero/one/three/255/256 `djmdCue` counts, every legacy/extended cue field, null/deleted rows, and three seek-parser states |
| `hot-cue-banks` | Recursive tree, membership boundaries/count limits, and unique deterministic `djmdCue` rows for cue-info work |
| `hot-cue-bank-pagination` | Seventy ordered memberships crossing two full 32-row render pages, with deterministic boundary content IDs |
| `hot-cue-bank-cue-fields` | Paired AppSync memberships with mapped timing/MPEG values, conflicting cue rows, and ignored-field controls |
| `hot-cue-bank-extended-fields` | Isolated new-format timing, MPEG, color, comment, beat-loop, microsecond, and seek-info controls |
| `hot-cue-bank-mutation` | Disposable two-row same-slot state for before/set/after mutation experiments; the duplicate satisfies the observed AppSync resolver invariant |
| `hot-cue-bank-legacy-mutation` | Disposable two-row `TrackNo=4` state for `0x2201`; isolates AppSync's unadjusted D ordinal and duplicate-row resolver requirement |
| `hot-cue-bank-legacy-ordinals` | Duplicate writable rows at `TrackNo` 4/5/6 with distinct ContentIDs for the complete D/E/F mapping and response-source cross |
| `hot-cue-bank-legacy-ordinal-boundaries` | Paired writable rows at eleven outside-gate ordinals from 0 through 65535, distinguishing acknowledged cue replies from database mutation |
| `hot-cue-bank-deleted-bank-member` | Soft-deleted bank with a live membership/cue for the tree-versus-direct-ID predicate cross |
| `boundaries` | BPM rounding, time/year bounds, zero/null-like values, deletion, and maximum accepted values |
| `unicode-boundaries` | Comment and Date Added values bracketing 255/256 UTF-16 code units with supplementary characters |
| `filename-boundaries` | Null/empty, dots/extensions, literal separators, embedded NUL, Unicode normalization pairs, and 254/255/256-unit filenames |
| `invalid` | Null/empty fields, dangling foreign keys, invalid enums, negative values, and malformed dates |
| `scalar-boundaries` | Stored rating 99, bitrate `INT32_MAX`, unassigned color 0, and dangling color ID for root/direct selector distinctions |
| `smart-playlists` | Attribute 4 rule-only and contradictory-membership rows, malformed/null rules, and an Attribute 0 rule-bearing control |
| `smart-rule-matrix` | All operator codes over text and decimal BPM values, all/any, ignored nested nodes, empty groups, invalid conditions, and root-attribute parser defaults |
| `smart-numeric-matrix` | Stored-scale BPM, Rating, Play Count, Duration, and Year comparisons, ordered/reversed ranges, empty/invalid text, signed negatives, and values above `INT32_MAX` |
| `smart-property-matrix` | All 23 written SmartList property names, lookup/scalar/date source mappings, raw and signed My Tag IDs, and alias controls |
| `smart-date-matrix` | Fixed-date operators 1-5 over Date Added, Date Created, and Date Released, including leap-day, reversed-range, blank, and malformed controls |
| `smart-relative-date-matrix` | Clock-controlled operators 6-7 over all three date properties, singular/plural/unknown units, count coercion, leap/month/year boundaries, future dates, and ignored right values |
| `smart-date-format-matrix` | Exact-length date parsing, ignored separator positions, Unicode and malformed characters, calendar overflow normalization, epoch/range failures, embedded NUL, and SQL `NULL` across all three date properties |
| `smart-text-matrix` | Operators 1/2/8-11 over Comments with ICU case/accent/width/kana behavior, canonical composition direction, expansions, scripts, punctuation, whitespace, supplementary characters, entities, empty/null, and embedded NUL |
| `smart-string-property-matrix` | Operators 1/2/8-11 crossed over nine lookup-backed and four direct string properties, with case/accent/width variants, substring boundaries, empty lookup names, missing relations, empty strings, and SQL `NULL` |
| `smart-mytag-matrix` | Operators 1-11, signed 32-bit parsing boundaries, blank/invalid/decimal-prefix forms, ignored right/unit fields, and all/any multi-tag membership logic |
| `smart-xml-matrix` | XML document/root/child structure, case and namespace handling, declarations/comments/entities, malformed/trailing data, duplicate/missing attributes, and integer parsing |
| `smart-serving-crosses` | Rule-only populated playlist crossed with sort IDs 0-17, every render/secondary override, pagination boundaries, and packed requester/location/slot contexts |
| `smart-serving-legacy` | The same rule result through legacy 12-field setup serialization |
| `compatibility` | File type, sample rate, and bit depth combinations used by player compatibility checks |
| `compatibility-exhaustive` | All 256 FileType bytes, wide narrowing controls, SampleRate equality boundaries, and BitDepth invariance for the exact compatibility predicate |
| `display-strings-254/255/256` | Every Display Song Info string source set to an exact ASCII threshold |
| `display-strings-unicode-256` | Every Display Song Info string source set to 128 supplementary characters / 256 UTF-16 units |
| `delivery-boundaries` | Delivery-only null/empty/dangling fields, `ON` case behavior, and 126/127/128-unit strings |
| `delivery-wide-strings` | Delivery direct strings at ASCII 254/255/256 and supplementary UTF-16 252/254/255/256/257 boundaries |
| `search-ceiling` | 1,005 visible title matches with stable IDs around row 1,000 for Search truncation, ordering, and pagination |
| `search-text` | Precomposed/decomposed accents, non-ASCII case pairs, supplementary symbols, and embedded-NUL Search inputs |
| `search-track-ceiling` | 5,005 visible title matches for Search Track's 5,000-row default ceiling, pagination, and explicit-sort control |
| `search-track-large` | 10,005 rows with sort tokens only in `SearchStr`, proving that column is not directly queried |
| `search-track-large-title` | 10,005 title matches with distinct per-sort tokens for cache-independent default/explicit sort ceilings |
| `settings` | Full data plus a named category/sort/secondary/color mutation |

No media files are generated. Content paths and file metadata are populated,
which is sufficient unless a controlled run demonstrates an existence check.
The deleted fixture track and deleted Matching relation test soft-deletion
filters without relying on absence alone.

Every profile includes rekordbox's required root playlist ID `200000`, named
`CUE Analysis Playlist`. A clean 7.2.19 startup creates that row when it is
absent and shifts the other root playlist sequences. Encoding it in the
baseline makes the reachable empty state deterministic: zero tracks and one
system playlist. Folder rows render before playlist rows; sequence ordering is
then applied within the playlist rows.

The empty profile also contains rekordbox's 28 factory My Tag definitions:
four root groups and 24 leaves. When `djmdMyTag` is truly empty, 7.2.19 writes
those rows on first startup. Encoding the observed IDs, names, parents,
attributes, and sequences prevents that provisioning mutation while preserving
the exact empty-library menu. The focused `search-ceiling` profile also embeds
the factory tree so its otherwise relation-free database remains stable at
startup. Other populated profiles use their explicit fixture tree.

Stable symbolic IDs live in every `manifest.json`, for example
`$fixture.track.first`, `$fixture.genre.house`, and
`$fixture.playlist.primary`. Suite declarations use those names rather than
opaque decimal IDs.

### Build examples

From `/home/evan/workspace/rx3-research`:

```sh
PY=rekordbox-windows/.venv/bin/python
BUILDER=rekordbox-link-export-research/conformance/build_fixture.py
SOURCE=rekordbox-windows/shared/library/master.db
OPTIONS=/mnt/documents/multimedia/djing/rekordbox/options.json

"$PY" "$BUILDER" empty "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/empty

"$PY" "$BUILDER" full "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/full

"$PY" "$BUILDER" adjacent-payload-cues "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/adjacent-payload-cues

"$PY" "$BUILDER" boundaries "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/boundaries

"$PY" "$BUILDER" invalid "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/invalid

"$PY" "$BUILDER" compatibility "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/compatibility

"$PY" "$BUILDER" compatibility-exhaustive "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/compatibility-exhaustive

"$PY" "$BUILDER" search-ceiling "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/search-ceiling

"$PY" "$BUILDER" search-text "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/search-text

"$PY" "$BUILDER" smart-playlists "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-playlists

"$PY" "$BUILDER" smart-rule-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-rule-matrix

"$PY" "$BUILDER" smart-numeric-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-numeric-matrix

"$PY" "$BUILDER" smart-property-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-property-matrix

"$PY" "$BUILDER" smart-date-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-date-matrix

"$PY" "$BUILDER" smart-relative-date-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-relative-date-matrix

"$PY" "$BUILDER" smart-date-format-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-date-format-matrix

"$PY" "$BUILDER" smart-text-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-text-matrix

"$PY" "$BUILDER" smart-string-property-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-string-property-matrix

"$PY" "$BUILDER" smart-mytag-matrix "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/smart-mytag-matrix

"$PY" "$BUILDER" filename-boundaries "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/filename-boundaries

"$PY" "$BUILDER" hot-cue-banks "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/hot-cue-banks

"$PY" "$BUILDER" hot-cue-bank-extended-fields "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/hot-cue-bank-extended-fields

"$PY" "$BUILDER" hot-cue-bank-mutation "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/hot-cue-bank-mutation-duplicate-slot

"$PY" "$BUILDER" hot-cue-bank-legacy-mutation "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/hot-cue-bank-legacy-mutation

"$PY" "$BUILDER" hot-cue-bank-legacy-ordinals "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/hot-cue-bank-legacy-ordinals

"$PY" "$BUILDER" hot-cue-bank-legacy-ordinal-boundaries "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/hot-cue-bank-legacy-ordinal-boundaries

"$PY" "$BUILDER" hot-cue-bank-deleted-bank-member "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/hot-cue-bank-deleted-bank-member

"$PY" "$BUILDER" settings "$SOURCE" "$OPTIONS" \
  rekordbox-link-export-research/conformance/fixtures/generated/secondary-comment \
  --settings-file rekordbox-link-export-research/conformance/settings/generated/secondary-comment.json
```

The source database is opened read-only. The output manifest records profile,
fixture version, stable IDs, integrity result, live track count, settings, a
byte-level encrypted-file SHA-256, and a canonical decrypted
`fixture_fingerprint`. SQLCipher uses a random file salt, so independently built
files can have different byte hashes while the canonical fingerprint proves
their schema and row values are identical. The SQLCipher key remains in memory.

## Declarative suites

A case contains only:

- stable ID and description;
- request kind and typed arguments;
- whether to render the resulting menu;
- optional page size;
- concise structural expectations, including exact or allowed numeric values at
  any row-argument index.

Cases may additionally declare exact render windows, override the suite's
render arguments, request a fresh connection, run in a parallel-connection
suite, set a suite-level `read_timeout_ms`, or provide raw frame bytes.
Raw probes normalize their result to `raw_reply`, `disconnect`, or `timeout`
and retain all returned bytes plus any messages the normal codec can decode.
Normal requests preserve `timeout`/`disconnect`; render failures preserve the
successful header plus `render_timeout`/`render_disconnect` and the exact page
arguments. Parallel connection setup can similarly yield
`connection_timeout`/`connection_disconnect`.

Parallel suites may set `canonicalize_parallel`. The golden then compares a
sorted multiset and outcome counts with worker labels removed, while the result
retains raw worker cases under `observations`. This makes concurrency equality
independent of thread scheduling without discarding the original evidence.

The runner saves every typed header, render page, row, string, number, blob,
and outcome in the golden. Inline expectations catch a wrong fixture or gross
protocol failure during recording; the golden supplies the exhaustive equality
assertion during verification. `outcome: "any"` is reserved for discoveries
whose current rekordbox behavior is intentionally being recorded.

Supported argument declarations are:

```json
{"number": "$context"}
{"number": "$fixture.track.first"}
{"number": "0xffffffff"}
{"utf16_bytes": "FIXTURE"}
{"string": "FIXTURE"}
{"blob_hex": "01020304"}
```

`utf16_bytes` calculates UTF-16 byte length including the terminating NUL. The
standard render tail is declared once per suite, so 5-, 6-, and 8-argument
render forms are independent matrix cases. A case may set `render_context` to
override the suite default for its `0x3000` follow-up; this keeps the query and
render location bytes independently declarative for location-routing tests.

Expectations can assert the complete ordered values of a numeric row argument,
or constrain every row to a small allowed set:

```json
"expect": {
  "outcome": "menu",
  "row_argument_values": {
    "12": ["$fixture.key.am", "$fixture.key.c"]
  },
  "row_argument_any_of": {
    "10": ["0x00000100", "0x00000101"]
  }
}
```

The map key is the zero-based `4101` argument index. Exact-value arrays must
match row order and cardinality; `any_of` applies the same allowed set to every
returned row. Symbolic fixture IDs and hexadecimal numbers use the same
resolver as request arguments.

## Current corpus

The checked-in corpus contains 5,730 declarations across 933 suite files. This
is the recursive count of every JSON suite under `conformance/suites`; the
Python test gate validates that same complete set:

| Area | Coverage |
| --- | --- |
| Full navigation | 47 cases across every captured family and hierarchy level |
| Chained navigation | 16 genre, artist, album, and label paths using selectors returned by the backend |
| Empty state | 21 category, error, and independence cases |
| Setup width | Legacy 12-field and extended 16-field rows |
| Root mask | Zero, each menu-item bit, legacy mask, controlled lab mask, physical RX3 mask, and all bits |
| Sort request | IDs 0 through 17, including hidden and reserved IDs |
| Packed context | Player 1-6, generic menu locations 1-8, the XDJ-RR source-defined location-9 Delivery context, slots 0-4, an exhaustive ordinary-Track final-byte sweep over `0x00..0xff`, all 47 list families x seven known client values, complete seven-value crosses over Song Info and Hot Cue Bank, a 256-case eight-identity x two-setup interaction matrix, a 42-case requester-keyed Display AIO/status/setup cross, a 28-case matched RX3/CDJ Play status/setup cross, a 140-case matched-status Delivery/no-builder/setup cross, a 112-case Hot Cue direct-getter/status/setup cross, 56 cases each for the extended and legacy setters with post-write database reads, an 84-case Hot Cue catalog/status/setup cross, 36 location-9/current/stale-buffer declarations, and 48 old-Key/CueTrack/location/liveness declarations across ordinary/RX3/CDJ identities and both row widths |
| Render shape | Recorded common 5/6/8 forms plus declared total arities 0-32; counts 0-2 follow initialized lists with health controls, complete visible-sort crosses are recorded for six and declared for five/seven, 3/4/9/32 cross all visible sorts, 16 independently isolated probes substitute string/blob tags into every normal position, 42 cases vary the first-row character seek, unread client total, and category-ID fields, and 17 cases cross override-gate and full-width selector boundaries |
| Secondary columns | 15 concrete settings variants, no/multiple selection states, and 42 string/UTF-16 boundary cases |
| User info / DJ ID | 142 authority-only cases across three identities, argument counts 0-32, typed substitutions, packed-context boundaries, and seven controlled profile-path states; live recording is queued |
| Boundary values | 30 cases covering BPM, year/decade, duration, play-count width, direct out-of-root selectors, and soft deletion |
| Invalid values | 15 roots over null/empty fields, dangling references, invalid enums, negatives, and malformed dates |
| Track compatibility | 2 observed views over 8 sampled metadata combinations plus 2 declared extended/legacy views over 382 rows exhausting the FileType byte domain, wide narrowing, SampleRate boundaries, and BitDepth invariance |
| Category configuration | Every one of 21 persisted rows disabled alone, reversed order, and special disable-bit predicates |
| Sort configuration | Every one of 17 persisted rows visibility-toggled alone, reversed order, and hidden-selected behavior |
| Search | 160 cases covering mixed domains, Category gates, token/case/Unicode/NUL behavior, both `0x1300` and `0x1500`, all Search Track sort IDs, malformed arity/lengths, pagination, 1,000/5,000 default ceilings, and explicit-sort results through 10,005 rows |
| Smart playlists | 839 canonical executions covering Attribute 4 activation, rule/membership precedence, every operator code, numeric/string/date/My Tag properties, SQL null/REAL/wide-integer storage, missing numeric attributes, signed conversion, collation, direct-condition/ignored-node structure, XML document and attribute boundaries, malformed/unknown semantics, all sort IDs, every secondary render selector, all persisted secondary states, pagination, packed contexts, both row widths, key-notation states, root rows, folder dispatch, and populated/empty results across all eight ordinary device identities |
| Key notation | Four desktop Classic/Alphanumeric x normalized/database preference states plus two local CDJ Classic/Alphanumeric `DEVSETTING.DAT` states, each with 13 key-root/distance/track, collection, Smart, sort, Display, and Delivery cases |
| File Name | 18 all-sort cases over literal formatting, embedded NUL, Unicode, and 254/255/256-unit boundaries |
| Custom colors | Renamed endpoint colors plus color secondary-column rendering |
| Pagination | 9 exact plans covering one-row, edge, zero, past-end, overrun, overlap, and maximum offsets |
| Request errors | 9 unknown-kind, missing/extra-argument, wrong-type, and out-of-sequence requests |
| Display Song Info | Ordinary/AIO order, category flags, render/pagination/errors, both row widths, 24 boundary/invalid tracks, every string field at exact ASCII/non-BMP limits, and four mutated-status model controls |
| Song Info siblings | 351 canonical cases covering ordinary identity, authentic RX3 status, the derived CDJ-3000 control, Play and Delivery rows, recognized no-builder kinds, render controls, pagination normalization, malformed parser state, missing content, both row widths, exact Delivery-only field limits, and Play path/cloud/file-presence inputs; retained experiments cover Delivery ordering, six precursor families, connection reuse/replacement, discovery rejoin, RX3-to-CDJ replacement, 496 RX3-status location-2 executions, and two expected socket-close transcripts; 256 cold-process suites declare every ordered pair of the 16 malformed precursors followed by a location-2 Delivery probe, and seven focused timing suites resolve a newly observed 13-versus-zero repeat conflict |
| Malformed framing | 6 bad-magic, truncated, count, tag-list, field-tag, and oversized-length probes |
| Concurrency | 12 simultaneous sessions across player and menu-location contexts |
| History lifecycle | 10 ordered root, insert, drilldown, append, remove, delete, and final-state cases |
| Extended request families | 30 full/empty cases for Play Count, Prepare, New Key, Date Added, and My Tag |
| Hot Cue Bank | 92 catalog/count/location-render/state cases plus legacy/extended cue getters, setters, field layouts, ordinal gates, and deleted-bank predicates |
| Adjacent payload services | 196 fileless semantic requests, 96 independent malformed-process probes, 31 database-path controls distinguishing nonempty missing files, empty strings, SQL nulls, and playlist artwork lookup, 15 successful deterministic JPEG/PMAI requests across all ten filesystem-backed kinds, a 60-observation genuine RX3/CDJ status x setup-width success cross, 57 parser-boundary observations across 30 independently staged JPEG/PMAI profiles, and 114 successful/database-boundary cue observations across eight independently repeated suites |

`conformance/generate_matrices.py` deterministically regenerates capability,
context, render, secondary-column, per-category, and per-sort suites and their
settings. Focused generators own the exhaustive track-compatibility and Song
Info malformed-history declarations. Hand-authored suites hold semantic,
boundary, and special-predicate cases.

## Device and capability matrix

`conformance/device-matrix.json` covers CDJ-2000NXS2, CDJ-3000, XDJ-RX3,
XDJ-XZ, XDJ-AZ, XDJ-1000MK2, and an unknown control identity; player numbers
1-6; CDJ, mixer, DJM, and type-7 device classes; generations 0, 2, and 3;
both setup forms; three root masks; and all render arities.

Model identity is learned through Pro DJ Link discovery/keepalive state, not the
dbserver setup message. `conformance/identity_adapter.py` emits the 54-byte
keepalive with independently configurable model, player number, device class,
generation, MAC, and IP. Its encoder is tested byte-for-byte against captured
packet shapes; the CDJ-3000 status control derives from the RX3 template. The
direct TCP runner varies setup, request mask,
context, sort, and rendering. The default plan uses pairwise combinations plus
the full crosses named in `device-matrix.json`. Every model also runs menu,
sort, track-row, unsupported-command, and format-compatibility smoke cases.

The model matrix is gated on an isolated L2 network. No synthetic discovery
packet may reach `lan0` or the physical RX3.

## Record and verify

Test the runner:

```sh
make test
```

Run the Python fixture and synthetic-identity tests from the workspace root.
The fixture builder uses the SQLCipher environment shared with the Windows
lab; the research `.venv` is reserved for LIEF/Capstone static analysis.

```sh
PYTHONPATH=rekordbox-link-export-research/conformance \
  rekordbox-windows/.venv/bin/python -m unittest discover \
  -s rekordbox-link-export-research/conformance -p 'test_*.py' -v
```

Completed recording campaigns retain their accepted runner binaries and hashes
as local evidence outside the public Git tree. New recording work uses the
checked-in Python runner. Backend implementation code is never imported into
the recorder, so capture and validation remain independent of later backend
changes.

Record a golden from real Rekordbox after installing the matching fixture:

```sh
python3 protocol_runner.py record \
  --host 172.31.96.96 \
  --suite suites/full.json \
  --manifest fixtures/generated/full/manifest.json \
  --identity runs/cdj-3000-player-1.json \
  --backend rekordbox \
  --backend-version 7.2.19 \
  --golden goldens/rekordbox-7.2.19-full-extended.json
```

### Deferred rbxport comparison

This section is retained as the design for a later implementation-comparison
phase. Do not run it while real rekordbox is the only system under test. The
replay program exits before building or inspecting rbxport unless a future run
explicitly supplies the phase opt-in flag.

Once Evan explicitly starts that phase, replay every retained oracle suite
against the selected `rbxport` checkout with:

```sh
cd /home/evan/workspace/rx3-research/rekordbox-link-export-research
conformance/replay_rbxport.py --enable-rbxport-replay
```

The command requires no media, sudo, SSH agent, VM, synthetic discovery, or
physical network. Its adapter binds port query and RemoteDBServer only to
`127.0.0.1`; it does not start a Pro DJ Link beacon or NFS. It derives a source
tree fingerprint from every `rbxport` file in the compiled dependency closure,
then writes results under:

```text
conformance/results/rbxport/<commit>+tree.<fingerprint>/
```

Each directory contains `rbxport-source.json`, server logs, an actual envelope,
a semantic `*.diff.txt`, and a complete runner log for every suite, plus
`summary.json` and `SUMMARY.md`. The canonical current replay is
`c144f19+tree.80e87ec8aace`. It runs all 211 retained goldens: RX3 navigation,
capability, sort, context, render, pagination, error, framing, concurrency,
empty, legacy, extended-family, Search including the 1,000-result ceiling,
secondary settings, category settings, sort
settings, custom-color, smart-playlist precedence, rule, numeric, property,
fixed-date, relative-date, date-format, text-collation, cross-property string,
My Tag, XML-parser, SmartList serving and persisted-secondary matrices, the
four-state key-notation matrix, filename-boundary, invalid-data,
compatibility, and History lifecycle suites, CDJ-3000 full and legacy, eight
Display Song Info identity
recordings, the dedicated Display Song Info render, pagination, error, legacy,
invalid, numeric, and string-boundary matrices, the eight ordinary and ten
status-backed Play/Delivery baseline/render/pagination/error/legacy matrices,
two Delivery-only field boundary matrices, the Play path/cloud/file-state
matrix, and the seven-case cross-surface `FolderPath` visibility matrix. The adapter
uses each fixture's effective secondary column and visible sort order. Its
mandatory Comment control for the no-selection fixture records rbxport's
missing absent-secondary state as an explicit diff.

Direct verification remains available for a separately started endpoint:

```sh
./target/release/link-export-conformance verify \
  --host 127.0.0.1 \
  --suite suites/full.json \
  --manifest fixtures/generated/full/manifest.json \
  --identity runs/cdj-3000-player-1.json \
  --backend rbxport \
  --backend-version <source-fingerprint> \
  --golden goldens/rekordbox-7.2.19/cdj-3000/full.json \
  --expectations compare \
  --actual results/rbxport/<source-fingerprint>/cdj-3000/full.actual.json \
  --diff results/rbxport/<source-fingerprint>/cdj-3000/full.diff.txt
```

`--expectations strict` is the default and stops at the first concise suite
assertion failure. It is the recording and oracle-repeat gate.
`--expectations compare` reports those failures but completes every case so an
alternate backend produces a comprehensive result and diff. If a backend omits
a row required by a later `case_item` reference, compare mode records
`dependency_unavailable` with the unresolved source case/row/argument and
continues; strict mode treats the same condition as fatal. Classified socket
timeouts and disconnects are protocol outcomes. Unclassified transport,
decoding, fixture, unsafe response-size, and missing-artifact failures remain
fatal in both modes.

On mismatch, the runner lists differing case IDs and exact nested JSON paths
with compact expected/actual values. Explicit `--actual` and `--diff` paths
retain both forms; without them, the actual result is written beside the
golden. Format-2 goldens separate provenance from behavior. The
provenance records backend/version, Unix time, suite and fixture fingerprints,
paths, and the complete synthetic identity. Verification compares only the
behavior envelope, allowing the identical golden to test another backend.
Per-case transactions and socket ports are omitted from canonical output
because they do not describe behavior. The fixed `fffffffe` setup transaction
is retained with its request and response because setup kind and arguments are
part of the compatibility contract.

The runner treats a `4000` count of `ffffffff` as the protocol's unavailable
sentinel and does not render it. Automatic full-menu rendering is limited to
100,000 rows; larger tests must declare bounded `render_pages`. Undecoded input
is limited to 16 MiB and a render transaction to 100,000 messages. These are
harness safety limits, not claims about rekordbox's database capacity.

Create a run identity without transmitting anything:

```sh
python conformance/identity_adapter.py \
  --model CDJ-3000 --player 1 --device-type cdj --generation 3 \
  --manifest conformance/runs/cdj-3000-player-1.json --manifest-only
```

Status-backed identities can use either the captured RX3 template or an exact
hex artifact. Hex artifacts are validated for the known 284/292-byte status
lengths, player-status magic/kind, ASCII model, and both player-number fields
before transmission. `conformance/status-packets/README.md` records capture
provenance for each retained packet. The CDJ-2000nexus declaration uses this
path; its raw status bytes are never relabeled or padded.

After the matching fixture is active in Windows, the guarded oracle helper
checks isolation, starts the identity as a bounded transient user service,
activates the LINK source through the already-connected noVNC session, records
the golden, and immediately verifies a second query run against it:

```sh
conformance/oracle_record.sh \
  conformance/suites/full.json \
  conformance/fixtures/generated/full/manifest.json \
  conformance/runs/cdj-3000-player-1.json \
  conformance/goldens/rekordbox-7.2.19-full-extended.json
```

The helper never sends a packet unless `vmctl isolation-check` succeeds.
The browser session must already be connected to the noVNC canvas; reloading
the page immediately before a coordinate click can leave the canvas without
keyboard/mouse forwarding. Each rekordbox application start receives a fresh
synthetic identity service. Reusing a departed identity against the same
application process can leave the player visually stale while port query no
longer becomes available.
Suites that mutate backend state declare `repeat_strategy` as
`fixture-reset-and-restart`. Run the helper with phase `record`, reinstall the
same fixture and restart rekordbox, then run phase `repeat`; the second phase
verifies against the existing golden instead of overwriting it.

## VM fixture switch

Prepare the real oracle once. The script preserves the factory Groove Circuit
preset, creates an empty guarded preset directory, and denies only writes and
child deletion beneath `GROOVE CIRCUIT`. This prevents rekordbox from importing
eight bundled sampler tracks into every fixture. It is reversible with
`-Remove` and refuses non-empty or ambiguous states.

```sh
guest-control/guestctl copy-to conformance/prepare-oracle.ps1 \
  C:/Users/Research/link-export-conformance/prepare-oracle.ps1
guest-control/guestctl powershell \
  '& "C:/Users/Research/link-export-conformance/prepare-oracle.ps1"'
```

Activate a generated fixture entirely over the dedicated lab key:

```sh
conformance/activate_fixture.sh conformance/fixtures/generated/full
```

`activate_fixture.sh` copies the database, manifest, and switcher to
`C:\Users\Research\link-export-conformance`, executes the switcher, retrieves
the guest activation marker, and verifies its encrypted-file SHA-256. It does
not use the Dockur SMB share, which is absent on the isolated network.

Activation invokes the switcher first with `-StopOnly`, waits for guest SSH,
then installs with `-SkipStop`. This separates desktop-process shutdown from
the critical database transaction. A standalone switch still closes rekordbox
itself unless `-SkipStop` is explicitly supplied. The process set includes
`rekordbox.exe`, `rekordboxAgent.exe`, and `edb_streamd.exe`; the last helper can
otherwise retain a live handle to `master.db`. The switcher verifies the
manifest SHA-256 before and after copying,
makes one persistent backup named `link-export-conformance-original.db`,
atomically replaces `master.db`, removes stale WAL/SHM files, and writes the
active manifest beside the database and an activation marker in the staged host
share. It never overwrites the original backup. The oracle helper refuses to
run unless that marker's encrypted-file SHA-256 matches its requested manifest.
If closing rekordbox interrupts the SSH command status, activation retrieves
the freshly recreated marker and accepts the switch only when its SHA-256
matches. The staging marker is removed before every attempt, so a stale marker
cannot satisfy this recovery path.

Restore before leaving the lab:

```sh
guest-control/guestctl powershell \
  '& "C:/Users/Research/link-export-conformance/switch-fixture.ps1" -Restore'
guest-control/guestctl powershell \
  '& "C:/Users/Research/link-export-conformance/prepare-oracle.ps1" -Remove'
```

## Isolation gate

Start the private VM and validate its containment before starting an identity:

```sh
cd /home/evan/workspace/rx3-research/rekordbox-windows
./vmctl isolated-start
./vmctl isolation-check
```

The root check fails unless the physical-LAN service is stopped, the private
bridge has exactly one end of the named carrier-only veth pair as its sole
member, the unattached peer has no master or address, IPv4 forwarding and IPv6
are disabled on the bridge and peer, both forwarding drops exist, the
synthetic addresses exist, and
the Podman network uses the macvlan driver with only the private bridge as its
`NetworkInterface`. The check uses formatted fields supported by Podman 6,
rather than a version-specific JSON path. It also requires the host-side
`rbx-lab-host` macvlan, its `172.31.96.50/32` address, and the exact guest-only
route through that shim. It also requires fixed MAC `02:00:00:60:00:50`, which
keeps checked-in discovery identities stable across network recreation. The
unit's exit status is the oracle batch gate.
It allows up to ten seconds for Podman to register the named container, then
requires it to be running and repeats both the container and service checks
after a two-second stability interval. Inspect details with
`./vmctl isolation-check-logs 20`.

## Oracle discipline

1. Build a fixture and retain its manifest.
2. Install it with rekordbox stopped.
3. Start rekordbox and confirm the expected fixture count in Export mode.
4. Start the isolated discovery identity required by the matrix row.
5. Click the large `LINK` source after the synthetic player appears. Before
   this UI gate, port query returns `0xffff` and no dbserver is available.
6. Record the suite once; never hand-edit a golden to make another backend pass.
7. Repeat the same run to establish oracle determinism.
8. Treat nondeterministic fields as an explicit normalizer change reviewed in
   both the suite schema and documentation.
9. Restore the original VM database and stop the isolated network.

Backend comparison is a separate workflow documented in
`conformance/BACKENDS.md`; it never shares the oracle recording queue or writes
canonical goldens.

## Recorded oracle baseline

On September 30, 2026, rekordbox 7.2.19 recorded and repeat-verified:

| Identity | Fixture | Suite | Cases | Golden |
| --- | --- | --- | ---: | --- |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `full.json` | 47 | `goldens/rekordbox-7.2.19/xdj-rx3/full.json` |
| XDJ-RX3, player 11, captured type-7 shape | `empty` | `empty.json` | 21 | `goldens/rekordbox-7.2.19/xdj-rx3/empty.json` |
| CDJ-3000, player 1, CDJ type | `full` | `full.json` | 47 | `goldens/rekordbox-7.2.19/cdj-3000/full.json` |
| CDJ-2000NXS2, player 2, CDJ type | `full` | `full.json` | 47 | `goldens/rekordbox-7.2.19/cdj-2000nxs2/full.json` |
| XDJ-XZ, player 3, type 7 | `full` | `full.json` | 47 | `goldens/rekordbox-7.2.19/xdj-xz/full.json` |
| XDJ-AZ, player 4, type 7 | `full` | `full.json` | 47 | `goldens/rekordbox-7.2.19/xdj-az/full.json` |
| XDJ-1000MK2, player 5, CDJ type | `full` | `full.json` | 47 | `goldens/rekordbox-7.2.19/xdj-1000mk2/full.json` |
| UNKNOWN-FIXTURE, player 6, mixer type | `full` | `full.json` | 47 | `goldens/rekordbox-7.2.19/unknown-mixer/full.json` |
| UNKNOWN-FIXTURE, player 6, DJM type | `full` | `full.json` | 47 | `goldens/rekordbox-7.2.19/unknown-djm/full.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `legacy.json` | 2 | `goldens/rekordbox-7.2.19/xdj-rx3/legacy.json` |
| CDJ-3000, player 1, CDJ type | `full` | `legacy.json` | 2 | `goldens/rekordbox-7.2.19/cdj-3000/legacy.json` |
| Six additional identity controls | `full` | `legacy.json` | 12 | corresponding model directories |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `extended-families-full.json` | 21 | `goldens/rekordbox-7.2.19/xdj-rx3/extended-families-full.json` |
| XDJ-RX3, player 11, captured type-7 shape | `empty` | `extended-families-empty.json` | 9 | `goldens/rekordbox-7.2.19/xdj-rx3/extended-families-empty.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `chained-navigation.json` | 16 | `goldens/rekordbox-7.2.19/xdj-rx3/chained-navigation.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `generated/root-capabilities.json` | 31 | `goldens/rekordbox-7.2.19/xdj-rx3/root-capabilities.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `generated/sort-ids.json` | 18 | `goldens/rekordbox-7.2.19/xdj-rx3/sort-ids.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `generated/contexts.json` | 19 | `goldens/rekordbox-7.2.19/xdj-rx3/contexts.json` |
| XDJ-RX3, player 1, keepalive | `full` | `context-track-types.json` | 256 | `goldens/rekordbox-7.2.19/xdj-rx3/context-track-types.json` plus before/after health evidence |
| XDJ-RX3, player 1, keepalive | `full` | `context-track-type-families.json` | 329 | `goldens/rekordbox-7.2.19/xdj-rx3/context-track-type-families.json` plus before/after health evidence |
| XDJ-RX3, player 1, keepalive | `full` | `context-analysis-track-types.json` | 49 | `goldens/rekordbox-7.2.19/xdj-rx3/context-analysis-track-types.json` plus before/after health evidence |
| XDJ-RX3, player 1, keepalive | `hot-cue-banks` | `context-hot-cue-track-types.json` | 21 | `goldens/rekordbox-7.2.19/xdj-rx3/context-hot-cue-track-types.json` plus before/after health evidence |
| Eight ordinary discovery identities | `full` | `context-device-setup-{extended,legacy}.json` | 256 | 16 model/setup goldens plus immediate repeats and a canonical cross-model summary |
| Genuine RX3/CDJ status plus RX3 requester mismatch | `full` | `context-display-status*.json` | 42 | Six deferred goldens plus immediate repeats and a requester-keyed AIO summary |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `generated/render-{5,6,8}.json` | 3 | `goldens/rekordbox-7.2.19/xdj-rx3/render-{5,6,8}.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `generated/render-secondary-controls.json` | 19 | `goldens/rekordbox-7.2.19/xdj-rx3/render-secondary-controls.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `pagination.json` | 9 | `goldens/rekordbox-7.2.19/xdj-rx3/pagination.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `request-errors.json` | 9 | `goldens/rekordbox-7.2.19/xdj-rx3/request-errors.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `malformed-framing.json` | 6 | `goldens/rekordbox-7.2.19/xdj-rx3/malformed-framing.json` |
| XDJ-RX3, player 11, captured type-7 shape | `full` | `concurrent.json` | 12 | `goldens/rekordbox-7.2.19/xdj-rx3/concurrent.json` |
| XDJ-RX3, player 11, captured type-7 shape | 15 `settings` variants | `generated/secondary-*.json` | 30 | `goldens/rekordbox-7.2.19/xdj-rx3/secondary-*.json` |
| XDJ-RX3, player 11, captured type-7 shape | 2 invalid `settings` variants | no/multiple selection | 2 | `goldens/rekordbox-7.2.19/xdj-rx3/{no-secondary-selection,multiple-secondary-selections}.json` |
| XDJ-RX3, player 11, captured type-7 shape | 21 category-disable variants | `generated/category-*-disabled.json` | 21 | `goldens/rekordbox-7.2.19/xdj-rx3/category-*-disabled.json` |
| XDJ-RX3, player 11, captured type-7 shape | category order reversal | `generated/category-order-reversed.json` | 1 | `goldens/rekordbox-7.2.19/xdj-rx3/category-order-reversed.json` |
| XDJ-RX3, player 11, captured type-7 shape | category special bits | `category-special-bits.json` | 2 | `goldens/rekordbox-7.2.19/xdj-rx3/category-special-bits.json` |
| XDJ-RX3, player 11, captured type-7 shape | 17 sort-visibility variants | `generated/sort-*-toggled.json` | 17 | `goldens/rekordbox-7.2.19/xdj-rx3/sort-*-toggled.json` |
| XDJ-RX3, player 11, captured type-7 shape | sort order reversal | `generated/sort-order-reversed.json` | 1 | `goldens/rekordbox-7.2.19/xdj-rx3/sort-order-reversed.json` |
| XDJ-RX3, player 11, captured type-7 shape | hidden selected Comment | `hidden-selected-comment.json` | 2 | `goldens/rekordbox-7.2.19/xdj-rx3/hidden-selected-comment.json` |
| XDJ-RX3, player 11, captured type-7 shape | custom color labels | `custom-colors.json` | 2 | `goldens/rekordbox-7.2.19/xdj-rx3/custom-colors.json` |
| XDJ-RX3, player 11, captured type-7 shape | `boundaries` | `boundaries.json` | 30 | `goldens/rekordbox-7.2.19/xdj-rx3/boundaries.json` |
| XDJ-RX3, player 11, captured type-7 shape | `boundaries` | three secondary boundary suites | 10 | `goldens/rekordbox-7.2.19/xdj-rx3/secondary-*-boundaries.json` |
| XDJ-RX3, player 11, captured type-7 shape | `invalid` | `invalid.json` | 15 | `goldens/rekordbox-7.2.19/xdj-rx3/invalid.json` |
| XDJ-RX3, player 11, captured type-7 shape | `compatibility` | `compatibility.json` | 2 | `goldens/rekordbox-7.2.19/xdj-rx3/compatibility.json` |
| XDJ-RX3, player 11, captured type-7 shape | reset `full` | `history-lifecycle.json` | 10 | `goldens/rekordbox-7.2.19/xdj-rx3/history-lifecycle.json` |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-bank-legacy-mutation` | `hot-cue-bank-legacy-track-cues.json` | 3 | `goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-legacy-track-cues.json` |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-banks` | `hot-cue-bank-count-boundaries.json` | 6 | `goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-count-boundaries.json` |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-banks` | three single-case `hot-cue-bank-count-{int32-max,high-bit,uint32-max}.json` suites | 3 | matching `goldens/rekordbox-7.2.19/xdj-rx3/` files plus before/after process-health evidence |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-banks` | `hot-cue-bank-location-renders.json` | 10 | matching XDJ-RX3 golden plus before/after process-health evidence |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-banks` | `hot-cue-bank-location-cross.json` | 32 | matching XDJ-RX3 golden plus before/after process-health evidence |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-banks` | `hot-cue-bank-location-state.json` | 8 | matching XDJ-RX3 golden plus before/after process-health evidence |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-bank-pagination` | `hot-cue-bank-pagination.json` | 15 | matching XDJ-RX3 golden, exact immediate repeat, and machine-validated pagination summary |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-bank-legacy-ordinals` | `hot-cue-bank-legacy-ordinals.json` | 3 | `goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-legacy-ordinals.json` |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-bank-legacy-ordinal-boundaries` | `hot-cue-bank-legacy-ordinal-boundaries.json` | 11 | `goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-legacy-ordinal-boundaries.json` |
| XDJ-RX3, player 11, isolated type-7 shape | `hot-cue-bank-deleted-bank-member` | `hot-cue-bank-deleted-bank-member.json` | 4 | `goldens/rekordbox-7.2.19/xdj-rx3/hot-cue-bank-deleted-bank-member.json` |
| XDJ-RX3, player 1, keepalive | ten smart evaluator profiles | rule/numeric/property/fixed/relative/date-format/text/cross-property/My Tag/XML matrices | 616 | `goldens/rekordbox-7.2.19/xdj-rx3/smart-*-matrix.json` |
| XDJ-RX3, player 1, keepalive | SmartList serving crosses | all sorts/render selectors/pagination/contexts plus legacy width | 66 | `goldens/rekordbox-7.2.19/xdj-rx3/smart-serving-*.json` |
| Eight ordinary discovery identities | `smart-rule-matrix` | populated/empty SmartList device cross | 16 | `goldens/rekordbox-7.2.19/*/smart-device-cross.json` |
| XDJ-RX3, player 1, keepalive | 17 persisted-column profiles | every Smart secondary state | 17 | `goldens/rekordbox-7.2.19/xdj-rx3/{smart-secondary-*,smart-*-secondary-selection*}.json` |
| XDJ-RX3, player 1, cold process per state | `key-notation` | four 13-case preference-state suites | 52 | `goldens/rekordbox-7.2.19/xdj-rx3/key-notation-*.json` |
| XDJ-RX3, player 1, cold process per state | `key-notation` | two 13-case local CDJ device-style suites | 26 | `goldens/rekordbox-7.2.19/xdj-rx3/key-device-setting-*.json` |
| XDJ-RX3, player 1, cold process per state | ordinary/Smart persisted BPM settings | Alphanumeric BPM composite controls | 3 | `goldens/rekordbox-7.2.19/xdj-rx3/device-key-style-alphanumeric-*.json` |
| XDJ-RX3, player 1 and player 11 keepalive controls | `full` | `display-song-info.json` | 8 | `goldens/rekordbox-7.2.19/{xdj-rx3,xdj-rx3-player-1}/display-song-info.json` |
| XDJ-RX3, player 11, captured status | `full` | `display-song-info-aio-player-11.json` | 1 | `goldens/rekordbox-7.2.19/xdj-rx3-status/display-song-info-aio-player-11.json` |
| CDJ-3000, player 1, status control | `full` | `display-song-info.json` | 4 | `goldens/rekordbox-7.2.19/cdj-3000-status/display-song-info.json` |
| RX3 player 11, CDJ-3000 player 1, and RX3-status/requester-1 | `full` | `context-display-status*.json` | 42 | six status/setup packed-context goldens and exact repeats |
| Authentic RX3 player 11 and derived CDJ-3000 player 1 status controls | `full` | `context-play-status*.json` | 28 | four status/setup packed-context goldens and exact repeats |
| Authentic RX3 player 11 and derived CDJ-3000 player 1 status controls | `full` | `context-class2-status*.json` | 140 | four Delivery/no-builder status/setup packed-context goldens and exact repeats |
| Authentic RX3 player 11 and derived CDJ-3000 player 1 status controls | `hot-cue-banks` | `context-hot-cue-getter-status*.json` | 112 | four legacy/extended direct-getter status/setup goldens and exact repeats |
| Authentic RX3 player 11 and derived CDJ-3000 player 1 status controls | `hot-cue-bank-mutation` | `context-hot-cue-setter-status*.json` | 56 | four extended-setter packed-type/status/setup goldens, post-write getters, and exact fixture-reset repeats |
| Authentic RX3 player 11 and derived CDJ-3000 player 1 status controls | `hot-cue-bank-legacy-ordinals` | `context-hot-cue-legacy-setter-status*.json` | 56 | four legacy-setter packed-type/status/setup goldens, six-slot post-write getters, and exact fixture-reset repeats |
| Authentic RX3 player 11 and derived CDJ-3000 player 1 status controls | `hot-cue-banks` | `context-hot-cue-catalog-status*.json` | 84 | four root/populated/empty catalog packed-type/status/setup goldens and exact repeats |
| XDJ-RX3, player 1, keepalive | `full` | `generated/display-song-info-render.json` | 21 | `goldens/rekordbox-7.2.19/xdj-rx3/display-song-info-render.json` |
| XDJ-RX3, player 1, keepalive | `full` | `generated/display-song-info-pagination.json` | 9 | `goldens/rekordbox-7.2.19/xdj-rx3/display-song-info-pagination.json` |
| XDJ-RX3, player 1, keepalive | `full` | `generated/display-song-info-errors.json` | 9 | `goldens/rekordbox-7.2.19/xdj-rx3/display-song-info-errors.json` |
| XDJ-RX3, player 1, keepalive | `full` | `generated/display-song-info-legacy.json` | 4 | `goldens/rekordbox-7.2.19/xdj-rx3/display-song-info-legacy.json` |
| XDJ-RX3, player 1, keepalive | boundary/Unicode/invalid | three generated Display Song Info suites | 24 | `goldens/rekordbox-7.2.19/xdj-rx3/display-song-info-{boundaries,unicode-boundaries,invalid}.json` |
| XDJ-RX3, player 1, keepalive | four Display string profiles | four generated threshold suites | 4 | `goldens/rekordbox-7.2.19/xdj-rx3/display-song-info-strings-*.json` |
| XDJ-XZ/AZ/1000MK2, player 11, mutated RX3 status | `full` | three generated status suites | 12 | `goldens/rekordbox-7.2.19/{xdj-xz,xdj-az,xdj-1000mk2}-status/display-song-info.json` |
| Unknown model, player 1, mutated RX3 status | `full` | generated unknown-model status suite | 4 | `goldens/rekordbox-7.2.19/unknown-mixer-status/display-song-info.json` |
| XDJ-RX3, player 1, keepalive | `full` | `generated/song-info-siblings.json` | 24 | `goldens/rekordbox-7.2.19/xdj-rx3/song-info-siblings.json` |
| XDJ-RX3, player 1, keepalive | `full` | `generated/song-info-sibling-render.json` | 42 | `goldens/rekordbox-7.2.19/xdj-rx3/song-info-sibling-render.json` |
| XDJ-RX3, player 1, keepalive | `full` | `generated/song-info-sibling-pagination.json` | 18 | `goldens/rekordbox-7.2.19/xdj-rx3/song-info-sibling-pagination.json` |
| XDJ-RX3, player 1, keepalive | `full` | `generated/song-info-sibling-errors.json` | 17 | `goldens/rekordbox-7.2.19/xdj-rx3/song-info-sibling-errors.json` |
| XDJ-RX3, player 1, keepalive | `full` | `generated/song-info-sibling-legacy.json` | 8 | `goldens/rekordbox-7.2.19/xdj-rx3/song-info-sibling-legacy.json` |
| XDJ-RX3, player 1, keepalive | `delivery-boundaries` | `generated/song-info-delivery-boundaries.json` | 8 | `goldens/rekordbox-7.2.19/xdj-rx3/song-info-delivery-boundaries.json` |
| XDJ-RX3, player 1, keepalive | `delivery-wide-strings` | `generated/song-info-delivery-wide-strings.json` | 8 | `goldens/rekordbox-7.2.19/xdj-rx3/song-info-delivery-wide-strings.json` |
| XDJ-RX3, player 1, keepalive | `play-paths` | `generated/song-info-play-paths.json` | 14 | `goldens/rekordbox-7.2.19/xdj-rx3/song-info-play-paths.json` |
| XDJ-RX3, player 1, keepalive with `CLSSyncMethod=0` | `cloud-sync-zero` | `generated/song-info-cloud-sync-zero.json` | 10 | Pending guarded real-Rekordbox record/repeat |
| XDJ-RX3, player 11, authentic status | `full` | five generated status sibling suites | 106 | `goldens/rekordbox-7.2.19/xdj-rx3-status/song-info-sibling-*.json` |
| CDJ-3000, player 1, RX3-template-derived status | `full` | five generated status sibling suites | 106 | `goldens/rekordbox-7.2.19/cdj-3000-status/song-info-sibling-*.json` |

All runs passed the isolation gate, traversed the real port-query and dynamic
dbserver sockets, and matched on an immediate independent replay. The XDJ-RX3
and CDJ-3000 behavior envelopes are identical within both extended and legacy
setup modes. Each golden retains the exact typed setup exchange.
The current real-Rekordbox corpus totals 288 goldens and 4,058 case executions.
The earlier rbxport comparison remains frozen at its historical 211-golden,
2,403-case boundary and is outside the current research phase.

## Remaining implementation work

- Capture genuine status packet shapes from XDJ-XZ, XDJ-AZ, and XDJ-1000MK2;
  the RX3-shape model-mutation rejection matrix is complete.
- Extend semantic paths with decoded row-field and database-entity names after
  every menu item's argument schema has been confirmed.
- Cross authenticated cloud runtime modes beyond the active database-controlled
  Play path/file-presence matrix. Extend the Delivery row-order matrix from
  the completed cold-process, field, render, precursor-family, TCP, and
  discovery-identity controls to irregular request sequences.
- Record production-shaped Beatport `/v4/catalog/tracks/` substring and
  near-match controls through the `FolderPath` matrix. Authentication is not
  an input to the 7.2.19 path classifier, and its Beatsource service slot is
  permanently null; account-conditioned application roots remain separate.
