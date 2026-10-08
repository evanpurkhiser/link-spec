# Artwork and analysis payload services

This chapter describes the binary-payload half of Rekordbox 7.2.19 Link
Export: artwork (`0x2003`, `0x2103`) and song-analysis requests
(`0x2004..0x2d04`). These commands are adjacent to menu serving but do not use
the menu-header/render/footer protocol. They return a binary or scalar reply
directly.

The machine-readable authority is
`data/static-analysis/adjacent-payload-services.json`. Regenerate it with:

```sh
.venv/bin/python tools/generate_adjacent_payload_service_map.py
```

The backend-neutral live declaration is
`conformance/suites/adjacent-payload-fileless.json`. Its 196 fresh-connection
cases cross all 16 services with packed track types 0 through 6 and zero/maximum
content IDs or complete contexts as applicable, add representative location-byte controls, and exercise both
specified-atom kinds across admitted, rejected, and short-circuit tag/extension
forms. Regenerate it with:

```sh
.venv/bin/python conformance/generate_adjacent_payload_suite.py
```

The suite has an exact real-Rekordbox record/repeat covering all 196 cases.
`conformance/record_adjacent_payload_fileless.sh` performed independent
fixture-reset/process phases, captured guest health before and after each
phase, restored the `play-paths` baseline, and wrote a hash-bound receipt.
`tools/summarize_adjacent_payload_fileless.py` requires format-2 direct-response
provenance, the embedded fixture fingerprint, all ordered IDs, and the exact
20 silent versus 176 reply case oracle. It also asserts every reply message and
wire length before emitting `summary.json` and `matrix.csv`.

Both phases began and ended with one Rekordbox process and no new Windows
Application events. The complete golden is byte-identical across processes.
The malformed and database-path matrices are also complete. Generated-success,
status, parser-boundary, and cue matrices continue behind these validated
stages.

## Physical XDJ-RX3 request cadence

The retained physical RX3 session supplies native client-side request evidence
for the adjacent services. Its serving Rekordbox version is unknown, so these
packets establish what the player sent and what the capture contains; the
controlled 7.2.19 suites remain the authority for version-specific server
behavior **[CAP]**.

The RX3 used three packed contexts for this part of the workflow:

| Context | Location | Captured use |
| --- | ---: | --- |
| `0x0b010401` | 1 | specified analysis atoms |
| `0x0b030401` | 3 | selected-track list-buffer offset |
| `0x0b080401` | 8 | artwork, waveform, cues, VBR, beat grid, and content artwork |

All three retain requester 11, Rekordbox media slot 4, and track type 1. For
the twelve tracks visible on the first page, the player interleaved a one-row
Display preview with this native atom request:

```text
2c04 [0x0b010401, content_id, PWV4, EXT]
```

Thirteen captured replies, including one repeat of the first track, are
`4f02` status-zero payloads of exactly 7,228 bytes. Each payload begins with a
`PWV4` atom and has a track-specific SHA-256.

The selected content `193883336` then receives this captured sequence:

| Request | Native arguments | Captured reply |
| --- | --- | --- |
| `2004` | `[0x0b080401, 4, content, 0, <omitted blob>]` | `4402`, status 0, 904 bytes |
| `2d04` | `[0x0b010401, content, PWV6, 2EX]` | `4f02`, status 0, 3,624 bytes, count 1 |
| `2c04` | `[0x0b010401, content, PSSI, EXT]` | `4f02`, status 50, empty |
| `2b04` | `[0x0b080401, content, 0]` | `4e02`, status 1, empty |
| `3100` | `[0x0b030401, content, 0, 0]` | no correlated reply in the retained stream |
| `2504` | `[0x0b080401, content]` | `4502`, status 0, 1,604 bytes |
| `2204` | `[0x0b080401, content]` | `4602`, status 0, 12,948 bytes |
| `2c04` | `[0x0b010401, content, PQT2, EXT]` | `4f02`, status 50, empty |
| `2103` | `[0x0b080401, content, 1]` | no correlated reply in the retained stream |
| `2c04` | `[0x0b010401, content, PWV5, EXT]` | `4f02`, status 0, 83,148 bytes, count 1 |

Artwork prefetch separately sent seventeen
`2003 [0x0b080401, content_id, 1]` messages over twelve unique tracks. Four
captured replies contain JPEG blobs, seven are status-50 empty replies, and six
requests have no correlated response in the retained stream. Five artwork
transactions also contain a client-originated `0001 []` under the same
transaction ID. These reports arrive 21,098 to 126,329 microseconds after the
artwork request. Three follow captured `4002` replies, while two follow requests
without a correlated response in the retained stream. Capture absence is not
classified as a timeout. RX3 `RecvFromCommTask` constructs `0001` when
`CheckCanceledRequest` accepts a GUI cancellation, so these packets cancel the
outstanding artwork transactions rather than report invalid artwork content.

Every payload length, hash, prefix, transaction, and request argument is in
`data/experiments/physical-rx3-session/navigation-transcript.json`; the ordered
interpretation is in `PHYSICAL_RX3_SESSION.md`.

### Fileless wire oracle

The `full` fixture has no payload files and no deterministic cue rows for the
selected content. The exact response classes are:

| Request | Fileless live result | Wire bytes |
|---:|---|---:|
| `2003` | type 1 and ID/location controls: `4002(request, 50, 0, empty)`; types 0 and 2-6: silence | 39 or 0 |
| `2103` | type 1 and ID controls: `4002(request, 50, 0, empty)`; types 0 and 2-6: silence | 39 or 0 |
| `2004` | `4402(request, 50, 0, empty)` for every control | 39 |
| `2104` | empty legacy-cue `4702` with status 1 and zero records | 64 |
| `2204` | `4602(request, 50, 0, empty, 0)` | 45 |
| `2304`, `2404`, `2604`, `2704` | ordinary type controls: `4003(request)`; all-zero/all-ones contexts: silence | 26 or 0 |
| `2504` | `4502(request, 0, 0, empty)` | 39 |
| `2804` | `4000(request, 0)` | 32 |
| `2904` | `4a02(request, 50, 0, empty)` | 39 |
| `2a04` | `4c02(request, 50, 0, empty)` | 39 |
| `2b04` | empty extended-cue `4e02` with status 1 and zero records | 45 |
| `2c04`, `2d04` | `4f02(request, 50, 0, empty, 0)` for every tag, extension, type, ID, and location control | 45 |

The 20 silent cases end in `WouldBlock` without response bytes. Silence does
not terminate Rekordbox or poison later fresh connections. The `4003` replies
show that a source handler returning internal `-2` can still acquire a wire
response from the outer dispatcher; source-level “no builder” and wire-level
“no reply” are separate claims **[OBS, RB-DEC]**.

The 96 generated suites under
`conformance/suites/generated/adjacent-payload-malformed/` add six
missing-argument, wrong-tag-type, extra-argument, or declared-tag-slot probes
for every service. Each suite contains one case so every probe can receive an
independent Rekordbox process and receipt. The matrix index is
`conformance/data/adjacent-payload-malformed-matrix.json`. Regenerate both with:

```sh
.venv/bin/python conformance/generate_adjacent_payload_malformed_suite.py
```

`conformance/record_adjacent_payload_malformed.sh` records and repeats each
one-case suite in a fresh process, refuses ambiguous partial evidence, and
writes one health-bound receipt per case. The aggregate reducer
`tools/summarize_adjacent_payload_malformed.py` validates all 96 suite,
fixture, golden, and receipt hashes before emitting the readable matrix. The
guarded `run_adjacent_payload_malformed_after_fileless.sh` starts only after
the fileless finalization receipt and stops the isolated VM after validation.

### Malformed artwork `0x2003`

The first complete malformed family has six independently repeated cold-
process observations **[OBS]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4002(2003, 50, 0, empty)` | 39 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string identifier | `4002(2003, 50, 0, empty)` | 39 |
| numeric context, numeric identifier, extra number | `4002(2003, 50, 0, empty)` | 39 |

The lone-context result is consistent with a missing identifier becoming a
zero/default value before the ordinary empty-artwork response. A string
identifier reaches the same response, while trailing arguments do not alter
it. Wrong tag types in the first required slot instead produce the generic
empty message before a kind-specific reply appears. All twelve record/repeat processes remained responsive,
and every before/after health capture contained zero Windows Application
events. The per-case goldens and health-bound receipts are under
`conformance/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-malformed/`
and `data/experiments/adjacent-payload/malformed/repeats/`.

### Malformed waveform artwork `0x2103`

The adjacent waveform-artwork handler has the same six-way malformed shape,
with the request kind preserved in its kind-specific response **[OBS]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4002(2103, 50, 0, empty)` | 39 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string identifier | `4002(2103, 50, 0, empty)` | 39 |
| numeric context, numeric identifier, extra number | `4002(2103, 50, 0, empty)` | 39 |

All six final record/repeat pairs have one responsive Rekordbox process and no
Windows Application events before or after either request. The string-
identifier repeat also exercises the recorder's interruption boundary: a
transport-side `WouldBlock` from an earlier attempt produced no receipt, the
complete record candidate was retained, the partial repeat health was
quarantined, and a new cold repeat matched the candidate before promotion.
The quarantine remains provenance and is excluded from the canonical pair.

### Malformed preview waveform `0x2004`

`CMD_GET_WAVEDATA` normally declares five tag slots: packed context, constant
`4`, ContentID, zero, and an omitted zero-length blob. Its malformed family
shows which tag positions gate `PSvDBMain::GetWave` **[OBS, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments and no fixed tag declaration | silence ending in `WouldBlock` | 0 |
| numeric packed context only in a five-slot declaration | `4402(2004, 50, 0, empty)` | 39 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context and constant 4 plus string ContentID and zero | generic empty `0100()` | 20 |
| ordinary four numeric arguments plus numeric fifth slot | `4402(2004, 50, 0, empty)` | 39 |

The fixed five-slot context-only request reaches the builder with defaulted
numeric values, whereas a string ContentID fails before the kind-specific
response. Replacing the normally omitted final blob with a numeric tag does
not change the empty-wave response. Each canonical record/repeat pair has one
responsive Rekordbox process and zero Windows Application events before and
after the request.

### Malformed legacy cue retrieval `0x2104`

`CMD_GET_USB_CUE` takes a packed context and ContentID, then serves the AppSync
cue callback or undeleted `djmdCue` rows through `PSvDBMain::GetUsbCue`. Its
six malformed shapes produce three exact response classes **[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | empty legacy-cue `4702`, status 1 | 64 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID | empty legacy-cue `4702`, status 1 | 64 |
| numeric context, numeric ContentID, extra number | empty legacy-cue `4702`, status 1 | 64 |

The `0x4702` message contains request kind `0x2104`, status 1, both empty
blobs, fixed cue-record width 36, and zero record/count fields. A missing or
wrong-type ContentID therefore becomes an empty/default lookup after the
numeric context gate, while a trailing numeric argument is ignored. Every
canonical pair has one responsive Rekordbox process and zero Windows
Application events before and after both requests.

### Malformed VBR information `0x2504`

`CMD_GET_VBR_INFO` resolves the analysis path through database-interface offset
`+0x180` and loads fixed 1,604-byte DAT `PVBR` data through `MstLoadVBR`. Its
argument gate matches other two-argument analysis builders, but its empty
response uses status zero **[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4502(2504, 0, 0, empty)` | 39 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID | `4502(2504, 0, 0, empty)` | 39 |
| numeric context, numeric ContentID, extra number | `4502(2504, 0, 0, empty)` | 39 |

Missing or wrong-type ContentID therefore reaches the VBR builder as an
empty/default lookup, and trailing arguments are ignored after a valid numeric
context. The status-zero envelope is distinct from quantize data's status-50
failure. Every pair retains one responsive Rekordbox process and zero Windows
Application events before and after both requests.

### Malformed disc-eject log-only command `0x2604`

`CMD_INFO_DISC_EJECT` is the third recognized log-only arm in this adjacent
range. It reads only the packed context's track-type byte, logs the request,
returns internal `-2`, and has no recovered payload builder, database query,
or filesystem dependency. Its six independently repeated cold-process probes
match the complete `0x2304`/`0x2404` parser policy **[OBS, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| string packed context | generic empty `0100()` | 20 |
| blob packed context | generic empty `0100()` | 20 |
| numeric context plus extra number | `4003(2604)` | 26 |
| numeric context plus extra string | `4003(2604)` | 26 |
| numeric context with 32 declared tag slots | generic empty `0100()` | 20 |

The two trailing-tag types are ignored after a valid numeric context and reach
the outer dispatcher's kind-specific error mapping. The 32-slot header is
rejected before the command arm despite carrying a valid numeric context. All
six canonical pairs have one responsive Rekordbox process and zero Windows
Application events before and after both requests.

### Malformed disc-ID registration-status command `0x2704`

`CMD_ASK_DISCID_REGSTAT` is another recognized log-only arm. It reads the
packed context's track-type byte, logs, returns internal `-2`, and has no
recovered payload builder, database query, or filesystem dependency. Its six
cold-process record/repeat pairs establish the same complete parser policy as
the three preceding log-only commands **[OBS, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| string packed context | generic empty `0100()` | 20 |
| blob packed context | generic empty `0100()` | 20 |
| numeric context plus extra number | `4003(2704)` | 26 |
| numeric context plus extra string | `4003(2704)` | 26 |
| numeric context with 32 declared tag slots | generic empty `0100()` | 20 |

Trailing numeric and string tags are ignored once the numeric packed context
passes the first-slot gate. A 32-slot declaration is rejected before the arm.
All six canonical pairs retain one responsive Rekordbox process and zero
Windows Application events before and after both requests.

### Malformed quantize offset `0x2804`

`CMD_GET_QTZ_OFFSET` shares `PSvDBMain::GetQtzInf`, database-interface
analysis-path lookup, and DAT `PQTZ` parsing with beat-grid request `0x2204`.
Its wire result is different: it returns one four-byte quantize value through
the ordinary `0x4000` response instead of a `0x4602` beat-grid blob
**[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4000(2804, 0)` | 32 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID | `4000(2804, 0)` | 32 |
| numeric context, numeric ContentID, extra number | `4000(2804, 0)` | 32 |

The first numeric tag gates the handler. Missing or wrong-type ContentID is
treated as a default lookup whose offset is zero, while the trailing number is
ignored. All six canonical pairs retain one responsive Rekordbox process and
zero Windows Application events before and after both requests.

### Malformed partial waveform `0x2904`

`CMD_GET_PAR_WAVE` resolves the analysis path through database-interface
offset `+0x180`, replaces the analysis filename with its EXT sibling, and has
`PSvDBMain::LoadParWav` scan for `PWV3`. Successful data uses a 20-byte header
followed by one packed height/color byte per 1/150-second segment. Its malformed
forms establish the empty `0x4a02` envelope **[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4a02(2904, 50, 0, empty)` | 39 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID and zero | `4a02(2904, 50, 0, empty)` | 39 |
| ordinary three numeric arguments plus extra number | `4a02(2904, 50, 0, empty)` | 39 |

The numeric packed context is the early gate. Missing or wrong-type ContentID
becomes a default lookup after that gate, and a fourth numeric argument is
ignored. All six canonical pairs retain one responsive Rekordbox process and
zero Windows Application events before and after both requests.

### Malformed segmented-key information `0x2a04`

`CMD_GET_KEY_INFO` resolves the analysis path through database-interface
offset `+0x180`, substitutes the EXT sibling filename, and has
`PSvDBMain::LoadKeyInf` scan for `PKEY`. Successful data uses a 24-byte header
followed by 12 bytes per segmented-key entry. The malformed matrix establishes
its empty `0x4c02` envelope **[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4c02(2a04, 50, 0, empty)` | 39 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID | `4c02(2a04, 50, 0, empty)` | 39 |
| numeric context, numeric ContentID, extra number | `4c02(2a04, 50, 0, empty)` | 39 |

The numeric context tag gates the handler. Missing or wrong-type ContentID is
treated as a default lookup after that gate, and a third numeric argument is
ignored. All six canonical pairs retain one responsive Rekordbox process and
zero Windows Application events before and after both requests.

### Malformed disc-cue log-only command `0x2404`

`CMD_GET_DISC_CUE` is a second recognized log-only arm. Like `0x2304`, it
reads only the packed context's track-type byte, logs, returns internal `-2`,
and has no recovered payload builder, database query, or filesystem path. All
six outcomes reproduce the preceding policy after substituting the echoed
request kind **[OBS, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| string packed context | generic empty `0100()` | 20 |
| blob packed context | generic empty `0100()` | 20 |
| numeric context plus extra number | `4003(2404)` | 26 |
| numeric context plus extra string | `4003(2404)` | 26 |
| numeric context with 32 declared tag slots | generic empty `0100()` | 20 |

Thus the trailing-tag tolerance and 32-slot framing rejection are shared by
both adjacent log-only commands. Every pair retains one responsive Rekordbox
process and zero Windows Application events before and after both requests.

### Malformed recognized log-only command `0x2304`

This arm has no recovered payload builder, database query, or filesystem path.
It reads only the packed context's track-type byte, logs the request, and
returns internal `-2`. Its malformed probes separate argument dispatch from
the message tag-list-width guard **[OBS, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| string packed context | generic empty `0100()` | 20 |
| blob packed context | generic empty `0100()` | 20 |
| numeric context plus extra number | `4003(2304)` | 26 |
| numeric context plus extra string | `4003(2304)` | 26 |
| numeric context with 32 declared tag slots | generic empty `0100()` | 20 |

Both trailing-tag types are ignored after the valid numeric context and reach
the recognized arm's ordinary error mapping. A 32-slot header is rejected
before that arm even though its sole supplied argument has the correct type.
Every pair retains one responsive Rekordbox process and zero Windows
Application events before and after both requests.

### Malformed quantize data `0x2204`

`CMD_GET_QUANTIZE_DATA` takes the same context/ContentID shape, resolves the
analysis path through database-interface offset `+0x180`, and parses DAT
`PQTZ` through `MstLoadBeatGrid` or `MstLoadBeatGridWithHeader`. Its malformed
gate matches the legacy-cue command, while its reply is builder-specific
**[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4602(2204, 50, 0, empty, 0)` | 45 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID | `4602(2204, 50, 0, empty, 0)` | 45 |
| numeric context, numeric ContentID, extra number | `4602(2204, 50, 0, empty, 0)` | 45 |

The accepted malformed forms therefore enter `GetQtzInf` with a default or
coerced lookup value; the first argument's numeric tag is the earlier gate.
The successful-data response is a 20-byte header plus 16 bytes per beat and
rejects more than 6,248 beats, which the separate boundary assets exercise.
Every malformed pair retains one responsive Rekordbox process and zero Windows
Application events before and after both requests.

### Malformed extended cue retrieval `0x2b04`

`CMD_GET_EXTENDED_CUE` takes the same packed context and ContentID pair as the
legacy cue service, but serializes variable-width extended cue records through
reply `0x4e02`. Its six cold-process record/repeat pairs establish the empty
extended-cue envelope and the same first-slot type gate **[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | empty extended-cue `4e02`, status 1 | 45 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID | empty extended-cue `4e02`, status 1 | 45 |
| numeric context, numeric ContentID, extra number | empty extended-cue `4e02`, status 1 | 45 |

The empty `0x4e02` contains request kind `0x2b04`, status 1, byte count zero,
an omitted zero-length blob tag, and count zero. After a numeric context passes
the outer gate, a missing or wrong-type ContentID becomes a default lookup and
a trailing numeric argument is ignored. Each record and repeat retains one
responsive Rekordbox process and zero new Windows Application events.

### Malformed specified-atom retrieval `0x2c04`

`CMD_GET_SPECIFIED_ANALYSIS_DATA` normally accepts packed context, ContentID,
a four-byte atom tag, and a three-character extension. The malformed family
uses shorter two-argument-style probes to separate the common context gate from
the defaulted atom and extension values **[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4f02(2c04, 50, 0, empty, 0)` | 45 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID | `4f02(2c04, 50, 0, empty, 0)` | 45 |
| numeric context, numeric ContentID, extra number | `4f02(2c04, 50, 0, empty, 0)` | 45 |

A valid numeric context is sufficient to enter the handler. Missing or
wrong-type ContentID and missing tag/extension fields therefore reach the
empty status-50 reply; the third numeric argument does not make the default
extension eligible for loading. Wrong tag types in the first slot instead
produce the generic empty message before the service reply. All twelve health
captures retain one responsive process and no Windows Application events.

### Malformed specified-atom retrieval `0x2d04`

`CMD_GET_SPECIFIED_ANALYSIS_DATA2` reaches the same
`PSvDBMain::GetSpecifiedAtomInfo` handler as `0x2c04`, while preserving its own
request kind in the reply. Its six independently recorded malformed shapes
produce the following real-Rekordbox results **[OBS, DB, RB-DEC]**:

| Shape | Exact result | Wire bytes |
|---|---|---:|
| no arguments | silence ending in `WouldBlock` | 0 |
| numeric packed context only | `4f02(2d04, 50, 0, empty, 0)` | 45 |
| string in the packed-context position | generic empty `0100()` | 20 |
| blob in the packed-context position | generic empty `0100()` | 20 |
| numeric context plus string ContentID | `4f02(2d04, 50, 0, empty, 0)` | 45 |
| numeric context, numeric ContentID, extra number | `4f02(2d04, 50, 0, empty, 0)` | 45 |

The dynamic result matches the handler alias established by the pinned
disassembly: a valid numeric context reaches the status-50 service reply,
wrong first-slot types stop at the generic empty reply, and the no-argument
form remains silent. Record and repeat retain one responsive Rekordbox process
with no new Windows Application events.

The generator joins the command vocabulary to two pinned disassemblies and
refuses to emit a map when the required database queries, loaders, size gates,
or handlers disappear. `conformance/test_adjacent_payload_services.py` checks
byte-identical regeneration and the important path distinctions. The service
map is static Rekordbox evidence. Its fileless cross and all 96 malformed cases
across the 16 exact dispatch kinds are complete. The malformed matrix contains
80 replies and 16 healthy timeouts; file-backed crosses remain in the guarded
queue.

## Missing, empty, and null database paths

The `payload-paths` fixture crosses the ten filesystem-backed services with a
nonempty path to an absent file, an empty string, and SQL `NULL`. Artwork also
includes the playlist-artwork lookup path. Rekordbox returns a service-specific
reply for every one of the 31 cases; no path state times out **[OBS, DB]**:

| Request | Exact reply for all tested path states | Wire bytes |
|---:|---|---:|
| `2003`, `2103` | `4002(request, 50, 0, empty)` | 39 |
| `2004` | `4402(request, 50, 0, empty)` | 39 |
| `2204` | `4602(request, 50, 0, empty, 0)` | 45 |
| `2504` | `4502(request, 0, 0, empty)` | 39 |
| `2804` | `4000(request, 0)` | 32 |
| `2904` | `4a02(request, 50, 0, empty)` | 39 |
| `2a04` | `4c02(request, 50, 0, empty)` | 39 |
| `2c04`, `2d04` | `4f02(request, 50, 0, empty, 0)` | 45 |

The playlist-artwork nonempty-missing path returns the same 39-byte `0x4002`
envelope as the three content-artwork path states. Thus the wire protocol does
not distinguish an absent filename, an empty path, and a database null for
these handlers. This is an observed response equivalence, not a claim that the
internal lookup and filesystem branches are identical.

Record and repeat start from the deterministic encrypted fixture in separate
cold Rekordbox processes. The final receipt binds all 31 replies, the fixture
fingerprint, summary, CSV, post-request process health, baseline restoration,
zero active synthetic identities, and the stopped isolated VM.

## Generated valid payloads

The `payload-valid` fixture points the first track and primary playlist at a
deterministic 373-byte JPEG and generated PMAI DAT, EXT, and 2EX files. All
four guest files are hash-verified before both cold-process phases. The 15
requests produce 15 direct replies, but only 12 contain payload bytes
**[OBS, DB]**:

| Request/case | Returned payload bytes | Reply |
|---|---:|---:|
| `2003` content artwork | 373 | `4002`, status 0 |
| `2003` playlist artwork | 373 | `4002`, status 0 |
| `2103` content artwork | 373 | `4002`, status 0 |
| `2004` generated analysis | 904 | `4402`, status 0 |
| `2204` generated analysis | 0 | `4602`, status 50 |
| `2504` generated analysis | 0 | `4502`, status 0 |
| `2804` generated analysis | 0 | `4000(request, 0)` |
| `2904` VBR information | 35 | `4a02`, status 0 |
| `2a04` segmented-key information | 48 | `4c02`, status 0 |
| `2c04`/`2d04` PWV3 from EXT | 44 each | `4f02`, status 0, count 1 |
| `2c04`/`2d04` PKEY from EXT | 48 each | `4f02`, status 0, count 1 |
| `2c04`/`2d04` PWV7 from 2EX | 76 each | `4f02`, status 0, count 1 |

The staged file's existence is therefore insufficient to predict a nonempty
reply for `0x2204`, `0x2504`, or `0x2804` under the ordinary player-11
identity. This is real-Rekordbox evidence: the first reducer rejected the
three empty/scalar replies because it assumed every valid-asset probe was
payload-bearing. Record and repeat had already matched exactly, so the
reducer was corrected to report observed payload widths without imposing that
assumption. The status/setup cross tests whether authentic player state changes
this split.

The final receipt binds the exact golden, 15-case declaration, generated asset
manifest, fixture and identity, record/repeat asset inventories, four clean
health captures, baseline restoration, guest-asset removal, zero active
synthetic identities, and a stopped isolated VM.

## Shared request context

The first numeric argument is the packed `D/M/S/T` context used elsewhere in
the protocol: device, menu location, media slot, and track type occupy one byte
each. Artwork and ordinary graphical data conventionally use menu location
eight. Detailed/extended analysis requests commonly use location one. The
server forwards the complete value for logging and response ownership, while
the artwork dispatcher also extracts media slot and track type.

The direct-response wire rule matters for empty payloads. A response carries a
numeric byte count immediately before its blob. When the count is zero, the
blob tag itself is omitted. This is valid framing, not a truncated packet.

## Artwork dispatch

`OnImgCmd` recognizes only two request kinds:

| Kind | Arguments | Accepted track types | Target |
|---:|---|---|---|
| `2003` | packed context, image/row ID | type 1; types 3/4 return error 1, type 2 and other values return error 2 | database interface `+0x190` |
| `2103` | packed context, content ID | type 1; every other value returns error 3 | database interface `+0x198` |

Both successful paths return `0x4002`. Lookup, file, type, size, and dimension
failures emit a protocol error and an empty `0x4002`, so a client must consume
both messages rather than treating the error as the end of the exchange.

### Active AppSync path

The shared Link Export library installs `PSvAppSyncDBIF`. Its `0x2003` method
runs this query first against `djmdContent`, then against `djmdPlaylist`:

```sql
select ImagePath
from __TABLE_NAME__
where rb_local_deleted = 0 and ID = %lu
```

`0x2103` is a thin wrapper that passes the content ID to that same method. It
does not traverse `djmdContent.ImageID` on the active AppSync path. A nonempty
`ImagePath` is rooted beneath the Rekordbox cloud analysis-share path before it
enters the common loader.

### Master fallback path

`PSvMasterDBIF` has different semantics. `0x2103` calls
`DsqlContent_GetImageID`; both forms ultimately call `DsqlImg_GetPath` and then
the same common loader. This is why the database-interface selection boundary
must accompany any claim about artwork tables.

### Common JPEG loader

The common loader:

1. maps `/PIONEER` paths beneath the analysis-share root;
2. chooses the requested/original or derived artwork candidate;
3. may create medium artwork when the request shape asks for it;
4. requires a file understood by JUCE's JPEG decoder;
5. rejects files larger than 1,048,576 bytes;
6. calls `CheckImgSize_XYE` before returning the original bytes.

`CheckImgSize_XYE` walks JPEG markers to a start-of-frame record and accepts
only nonzero width and height values no greater than 800 pixels. JFIF and
JFXX APP0 markers are skipped explicitly. It does not impose an 80- or
240-pixel artwork size.

No audio file is read.

## Analysis dispatch

`OnSongAnlzCmd` is a bounded high-byte switch from `0x2004` through `0x2d04`.
The exact request and reply contracts are:

| Kind | Request arguments after setup | Reply | Builder and output |
|---:|---|---:|---|
| `2004` | context, `4`, content ID, `0`, declared-but-omitted empty blob | `4402` | `GetWave`; fixed 904-byte preview allocation containing 800 loud-wave bytes and 100 dot-wave bytes plus framing |
| `2104` | context, content ID | `4702` | `GetUsbCue`; legacy cue rows and counts |
| `2204` | context, content ID | `4602` | `GetQtzInf`; 20-byte header plus 16 bytes per beat |
| `2304` | packed context | none | reads the track-type byte, logs, then returns internal `-2` |
| `2404` | packed context | none | reads the track-type byte, logs, then returns internal `-2` |
| `2504` | context, content ID | `4502` | `GetVbrInf`; fixed 1,604-byte payload or empty reply |
| `2604` | packed context | none | reads the track-type byte, logs, then returns internal `-2` |
| `2704` | packed context | none | reads the track-type byte, logs, then returns internal `-2` |
| `2804` | context, content ID | `4000` | same beat-grid parser as `2204`, reduced to one four-byte quantize value |
| `2904` | context, content ID, `0` | `4a02` | `LoadParWav`; 20-byte header plus one packed height/color byte per segment |
| `2a04` | context, content ID | `4c02` | `LoadKeyInf`; 24-byte header plus 12 bytes per segmented-key entry |
| `2b04` | context, content ID, `0` | `4e02` | `GetUsbCueExt`; variable-width extended cue records plus count |
| `2c04` | context, content ID, atom tag, extension | `4f02` | requested analysis atoms |
| `2d04` | same as `2c04` | `4f02` | exact alias of `GetSpecifiedAtomInfo` |

For the database-backed analysis requests other than cue requests, the content
ID is passed to database-interface vtable slot `+0x180` to obtain the analysis
path. In cloud/AppSync mode the path is rebased below the configured
shared-database root. The four log-only arms do not read a content ID or query
the database.

### Beat-grid ceiling

`GetQtzInf` first loads the beat count, then loads a header and entries. It
rejects counts above `0x1868` (6,248) before allocating the wire payload. For
`0x2204`, each accepted beat becomes a 16-byte entry after a 20-byte header.
For `0x2804`, the same parse is reduced to the header's quantize value and sent
through the scalar reply helper.

### Detailed waveform and key paths

`LoadParWav` derives a sibling analysis filename, calls `MstLoadZoomWave`
twice (size, then data), and scans the sibling for a `PWV3` section. It packs
each source entry into one byte: the low
five bits are height and the remaining bits carry color. The output header
records 150 segments per second.

`LoadKeyInf` similarly derives the `.EXT` sibling and calls
`MstLoadSegmentedKey` twice. That loader scans PMAI sections for `PKEY`; its
header supplies a big-endian entry width and count. The Link Export wire
header declares 12-byte entries, followed by the returned segmented-key
records.

### Specified atoms

For `0x2c04` and `0x2d04`, the third number is interpreted as four raw ASCII
bytes and the fourth as a three-character extension. Extension matching is
case-insensitive after conversion to a JUCE string.

- `EXT` and `2EX` are the only extensions that may reach `MstLoadAtomInfo`.
- Other extensions immediately produce an empty `0x4f02`.
- Tags `PCP2`, `PCPT`, and `PMAI` are also explicitly short-circuited to an
  empty `0x4f02`.
- Other tags, including the documented waveform and phrase tags, reach the
  atom loader.

The nonempty reply concatenates each returned memory block including its
four-byte length prefix, and adds the trailing numeric argument required by
`RetBinPlusToClient`.

## Cue database paths

`0x2104` and `0x2b04` are database payload services rather than analysis-file
services. AppSync can obtain cue objects from its callback interface. The
ordinary database path selects `djmdCue` by `ContentID`; the extended builder
also calls cue-option lookups and has a separate shared-content serializer.
Neither recovered builder reads audio or an analysis file.

The `full` fixture's first content row has no deterministic `djmdCue` record,
so its fileless cases establish empty framing rather than successful cue
serialization. The dedicated encrypted `adjacent-payload-cues` fixture closes
that distinction with 19 content IDs and 530 controlled cue rows. It isolates:

- zero, one, three, 255, and 256 live records;
- timing/MPEG extrema, cue kind, loop state, color, and color-table index;
- empty, ASCII, Unicode, embedded-NUL, and SQL-null comments;
- beat-loop and cue-microsecond values;
- soft-deleted-only and mixed live/deleted results;
- valid inbound seek, outbound-only seek, and malformed inbound seek strings.

The safe suite crosses both `0x2104` and `0x2b04` through track types 0-6,
locations 0/1/2/3/7/8/255, and all non-crashing content profiles. The three
seek-bearing `0x2b04` requests each have a one-case suite and an independent
cold record/repeat process, so a process exit cannot hide another state. Four
additional suites cross representative 0/1/3/255/256/Unicode results through
genuine RX3 player 11 and matched CDJ-3000 player 1 status under both setup
widths.

The reducer decodes `0x4702` into fixed 36-byte cue records plus eight-byte
timing extensions. It decodes `0x4e02` into aligned variable-width records,
including timing, MPEG, color, microseconds, beat-loop words, UTF-16 comments,
and optional seek blocks. It requires exact fixture/suite/identity/golden/
health/receipt hashes, exact record counts for every safe profile, and
track-type/location invariance for both request kinds while preserving the
three risky outcomes as observations.

## Live conformance matrix

The guarded live queue records each direct response twice against three
database/file fixture conditions:

| Fixture condition | Purpose |
|---|---|
| unresolved content/image/path | canonical lookup failure and empty-reply framing |
| database row with missing file | distinguish database success from filesystem failure |
| minimal valid JPEG/ANLZ/cue data | successful payload bytes and exact response layout |

The declarations include zero, maximum, and unresolved IDs for database-backed
commands; complete-context boundaries for context-only arms; applicable track
types; both setup widths; `EXT`/`2EX` case variants; unsupported extensions;
short-circuited and supported atom tags; malformed argument types/arities; and
file-size, dimension, count, stride, and alignment boundaries. The
direct-response harness supports fixed tag-slot declarations, which is
required for the peculiar `0x2004` missing-blob request.

The fileless matrix uses the `full` profile to establish unresolved-ID and
null-path empty/error envelopes before any payload bytes are introduced. The
separate `payload-paths` fixture and 31-case
`adjacent-payload-missing-files.json` suite cross each of the ten
filesystem-backed kinds through a nonempty path whose file is absent, an empty
path, and a SQL-null path. `0x2003` additionally exercises the playlist artwork
lookup with a nonempty missing path. Both suites require independent
cold-process record and repeat captures with guest-health and hash-bound
receipts. The fileless receipt and summaries live under
`data/experiments/adjacent-payload/fileless/`; the canonical golden lives at
`conformance/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-fileless.json`.
The path-state equivalents live under
`data/experiments/adjacent-payload/missing-files/` and
`conformance/goldens/rekordbox-7.2.19/xdj-rx3/adjacent-payload-missing-files.json`.
The encrypted `payload-paths` database has SHA-256
`e76d36efea45461623049798b48f61a17fc436201a192bcf15ebca6e399516ef`
and canonical decrypted fixture fingerprint
`cd963cfacdc6197dcf347df8c5bfebf0400eaf48d1a3f1b0d0bfcc1d234e6fb8`.

Minimal JPEG and ANLZ files are sufficient. Playable media remains outside the
fixture unless a live capture demonstrates a decoder dependency.

## Deterministic success assets

`conformance/generate_payload_assets.py` produces four metadata-only files
under `conformance/payload-assets/generated/`: an 8-by-8 baseline JPEG and
PMAI `DAT`, `EXT`, and `2EX` siblings. The DAT contains controlled `PVBR`,
`PQTZ`, `PWAV`, and `PWV2` sections. The EXT contains `PWV3` and two 12-byte
`PKEY` records. The 2EX contains one `PWV7` atom. The generator manifest binds
every byte to its path, size, and SHA-256; `test_payload_assets.py` regenerates
the files independently and parses every section boundary.

The encrypted `payload-valid` profile points track 10001 and playlist 6002 at
those paths. Its database SHA-256 is
`c66100041113db7c6ca41d739f6766a3f09c44377e6f3e16c8df7e222d5abf2a`;
its canonical decrypted fingerprint is
`b8c22f232e17d6157c25fc25c65af29eb77bebef4aede6027c7407cc22461dfa`.
`adjacent-payload-success.json` declares 15 fresh-connection requests across
all ten filesystem-backed kinds. The guarded recorder stages the four files
under the guest's local `%APPDATA%\Pioneer\rekordbox\share`, verifies their
sizes and SHA-256 values before both cold-process passes, restores the
`play-paths` database, and removes only the two research-owned
`deterministic` directories. The completed record/repeat and finalization
receipts bind all assets, requests, replies, health captures, and cleanup. The
ordinary identity returns 12 payload-bearing replies and three empty/scalar
replies, as tabulated above.

Four generated status/setup suites repeat those 15 successes under the genuine
RX3 player-11 status control and matched CDJ-3000 player-1 status control, each
with extended and legacy setup. Their packed contexts use requester 11 and 1
respectively. The strict aggregate reducer validates every reply and reports
per-case normalized response hashes; it preserves model/setup differences
rather than requiring invariance. This 60-observation cross follows the ordered
malformed-history campaign in the guarded serial chain.

## Parser-boundary assets

`generate_payload_boundary_assets.py` derives 30 four-file profiles from the
deterministic baseline. The profiles change one loader-controlled axis at a
time:

| Family | Profiles | Requests |
|---|---:|---|
| JPEG byte length | 1,048,576 and 1,048,577 bytes | content and playlist `2003`; content `2103` |
| JPEG dimensions | width and height 800/801 | content and playlist `2003`; content `2103` |
| `PQTZ` beat count | 6,248 and 6,249 | `2204`, `2804` |
| `PWAV`/`PWV2` preview counts | 399/400/401 and 99/100/101 | `2004` |
| `PVBR` stored words | 399/400/401 | `2504` |
| `PWV3` | count 0/1/65,535; stride 0/1/2 | `2904`, specified-atom `2c04` |
| `PKEY` | count 0/1/65,535; stride 0/11/12/13 | `2a04`, specified-atom `2c04` |
| repeated `PWV7` atoms | two aligned and two unaligned sections | `2c04`, alias `2d04` |

The 57 requests are split across 30 suites so each asset profile is activated
in an independent cold Rekordbox process and then repeated from another cold
process. `record_adjacent_payload_boundary_matrix.sh` reuses the successful
payload recorder with explicit asset, suite, count, and evidence overrides.
The recorder verifies all four files inside Windows before both passes,
restores `play-paths`, and removes the exact two research-owned directories
after every profile.

`summarize_adjacent_payload_boundaries.py` requires the complete declaration,
suite, asset, fixture, identity, golden, health, and receipt hash chain. Its
CSV preserves outcomes, reply kinds, blob lengths, scalar values, and a
normalized response hash for each boundary. It does not turn parser failures
or process disconnects into assumed empty replies. The guarded successor runs
after the status/setup success cross, validates all Python and pinned Rust
tests, checks guest cleanup, and stops the isolated VM before writing its
finalization receipt.
