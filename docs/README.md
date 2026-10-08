# Documentation

The documents here separate observed behavior, recovered implementation
details, experiment history, and open research questions.

## Project status and process

- [Research summary](RESEARCH_SUMMARY.md): current findings and reading guide.
- [Conformance design](CONFORMANCE.md): fixtures, recording, verification, and safety boundaries.
- [Conformance coverage](CONFORMANCE_COVERAGE.md): requirement-to-suite ledger.
- [Research gaps](REKORDBOX_RESEARCH_GAPS.md): unfinished Rekordbox experiments.
- [Sources](SOURCES.md): source inventory, versions, hashes, and evidentiary roles.
- [Experiments](EXPERIMENTS.md): chronological lab notebook.
- [Publishing](PUBLISHING.md): public Git boundary and release checklist.
- [Cleanup](CLEANUP.md): retained artifacts and machine state.

## Protocol and data model

- [Protocol reference](PROTOCOL_REFERENCE.md): messages, fields, request families, and database behavior.
- [Link Export navigation](LINK_EXPORT_NAVIGATION.md): server-side navigation tree.
- [Request vocabulary](LINK_EXPORT_REQUEST_VOCABULARY.md): known client commands and Rekordbox dispatch behavior.
- [Request shapes](REQUEST_SHAPES.md): generated request signatures by family and stage.
- [Observed response shapes](OBSERVED_RESPONSE_SHAPES.md): inverse request-to-response index.
- [Database queries](DATABASE_QUERIES.md): request families mapped to database operations.
- [Database field reference](DATABASE_FIELD_REFERENCE.md): 389 fields across 22 AppSync tables and a 95-row inverse request-kind index.
- [SQL literal index](SQL_LITERAL_INDEX.md): SQL recovered from the executable.
- [Item type reference](ITEM_TYPE_REFERENCE.md): represented `0x4101` item types and provenance.
- [Row layout](ROW_LAYOUT.md): list-buffer construction and wire serialization.
- [Configuration](CONFIGURATION.md): categories, sorts, columns, masks, and refresh behavior.
- [Secondary columns](SECONDARY_COLUMNS.md): secondary sort IDs and rendering behavior.
- [Control and mutation reference](CONTROL_AND_MUTATION_REFERENCE.md): write and control command routes.

## Behavioral oracles

- [Adjacent payload services](ADJACENT_PAYLOAD_SERVICES.md): artwork, waveform, beat-grid, cue, and analysis payloads.
- [Boundary and lifecycle oracle](BOUNDARY_INVALID_LIFECYCLE_ORACLE.md): invalid values, limits, and lifecycle cases.
- [Category oracle](CATEGORY_ORACLE.md): category visibility and ordering.
- [Display Song Info oracle](DISPLAY_SONG_INFO_ORACLE.md): `0x2002` rows and request behavior.
- [Hot Cue Bank oracle](HOT_CUE_BANK_ORACLE.md): catalog, cue, mutation, and parser behavior.
- [Key notation oracle](KEY_NOTATION_ORACLE.md): Classic, Camelot, and stored key names.
- [Link Export visibility oracle](LINK_EXPORT_VISIBILITY_ORACLE.md): `FolderPath` and streaming-provider filtering.
- [Packed context oracle](PACKED_CONTEXT_ORACLE.md): context bytes and track-type routing.
- [Play Song Info path oracle](PLAY_SONG_INFO_PATH_ORACLE.md): local and cloud path construction.
- [Search oracle](SEARCH_ORACLE.md): validation, matching, result rows, and pagination.
- [Secondary column oracle](SECONDARY_COLUMN_ORACLE.md): persisted columns and render overrides.
- [Settings experiments](SETTINGS_EXPERIMENTS.md): reproducible settings tests.
- [Settings refresh oracle](SETTINGS_SESSION_REFRESH_ORACLE.md): same-process settings refresh.
- [Smart Playlist oracle](SMART_PLAYLIST_ORACLE.md): parsing, rules, and membership behavior.
- [Song Info siblings oracle](SONG_INFO_SIBLINGS_ORACLE.md): Play, Delivery, and adjacent request families.
- [Sort and color oracle](SORT_AND_COLOR_ORACLE.md): sort visibility, ordering, and color labels.
- [User info and DJ ID oracle](USER_INFO_DJID_ORACLE.md): DJ-ID exchange and profile configuration.

## Device and client evidence

- [Device compatibility](DEVICE_COMPATIBILITY.md): setup width, capabilities, and per-track checks.
- [Device matrix oracle](DEVICE_MATRIX_ORACLE.md): model identities, generations, masks, and reconnects.
- [Device predicate audit](DEVICE_PREDICATE_AUDIT.md): peer-identity and capability predicates.
- [Device status provenance](DEVICE_STATUS_PROVENANCE.md): captured and derived status packets.
- [Physical RX3 session](PHYSICAL_RX3_SESSION.md): ordered XDJ-RX3 session transcript.
- [Public status source audit](PUBLIC_STATUS_SOURCE_AUDIT.md): public packet-source inventory.
- [Static analysis](STATIC_ANALYSIS.md): pinned binaries, tools, addresses, and confidence limits.
- [XDJ-RR adjacent commands](XDJ_RR_ADJACENT_COMMANDS.md): client-side write and modification commands.
- [XDJ-RR client navigation](XDJ_RR_CLIENT_NAVIGATION.md): client call sites and menu locations.

## Implementation comparisons

- [Dysentery crosswalk](DYSENTERY_CROSSWALK.md): mapping to Dysentery and Beat Link concepts.
- [Gap matrix](GAP_MATRIX.md): implementation and evidence gaps by surface.
- [rbxport audit](RBXPORT_AUDIT.md): historical implementation coverage.

## Evidence labels

- `OBS`: observed in the UI, packets, logs, or a reproducible live test.
- `CAP`: derived from an existing packet capture.
- `DB`: derived from a copied Rekordbox database or configuration file.
- `DEC`: derived from static inspection of the Rekordbox executable.
- `RX3DEC`: derived from static inspection of pinned XDJ-RX3 firmware.
- `RBX`: behavior or intent found in rbxport.
- `DYS`: behavior documented by Dysentery or Beat Link.
- `INF`: an inference combining named evidence.
- `OPEN`: an unresolved question or planned experiment.

Dates use America/New_York unless a capture or source explicitly uses UTC.
