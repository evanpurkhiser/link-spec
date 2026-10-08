# XDJ-RR adjacent Link Export commands

This chapter joins decompiled XDJ-RR client call sites to the exact terminal
paths in Rekordbox 7.2.19 for commands that previously had only a firmware
name. It covers the old Key browser, Cue Track root, analysis-file writers,
cue writers, track-rating update, quantize-offset writer, and specified-atom
writers.

The result is static server evidence. A named target and reply constructor
establish what this Rekordbox build can execute; they do not substitute for a
recorded success, failure, malformed-input, and lifecycle matrix. Mutating
commands remain outside the live queue until their declarations use a fresh
fixture and capture database, filesystem, process-health, and restart state.

## Evidence boundary

The client is the pinned XDJ-RR decompilation at AlphaTheta documentation
commit `a70aeefb202ffddd2900e7b40e339a47ac077057`. The generated inventory retains
the SHA-256 of all six source chunks and every direct named caller. The server
is the symbol-rich Rekordbox 7.2.19 x86-64 Mach-O with SHA-256
`07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244`.

Canonical artifacts:

```text
data/static-analysis/xdj-rr-client-navigation.json
data/static-analysis/link-export-request-vocabulary.json
data/static-analysis/link-export-dispatch-tables.json
data/static-analysis/source-only-client-handlers.disasm.txt
data/static-analysis/source-only-client-db-effects.disasm.txt
```

The inventory has 102 request kinds with direct XDJ-RR call sites. Every one
now has a terminal Rekordbox classification; none remains
`source-vocabulary-only`.

## Old Key and Cue Track browser

The XDJ-RR contains both the old Key browser (`0x100B`/`0x110B`) and the newer
Key browser already exercised by the lab (`0x1014` and descendants). Left-side
old-Key calls pass a dynamic browser location, while right-side calls use
literal location 2.

| Kind | XDJ-RR wrapper | Direct callers | Rekordbox terminal path | Result |
|---:|---|---|---|---|
| `100B` | `dbcl_GetKey_Root` through `dbcl_GetRoot` | `GetLeftKeyList`, `GetRightKeyList` | `OnKeyListCmd` -> DB interface `+0xE8` -> AppSync `getKey_Root` | list total in `4000`; rows use the location buffer |
| `110B` | `dbcl_GetTrack_Key` through `dbcl_GetULong` | `GetLeftKeyList`, `GetRightKeyList` | `OnKeyListCmd` -> DB interface `+0xF0` -> AppSync `getTrack_Key` | list total in `4000`; selector is the Key ID |
| `130C` | `dbcl_GetCueTrack_Root` through `dbcl_GetRoot` | `GetLeftCueList`, `GetRightCueList` | special `OnListClientCmd` arm | command log only; internal return `-2`, no builder or reply |

`getKey_Root` clears the requested location buffer and executes:

```sql
SELECT *
FROM djmdKey
WHERE rb_local_deleted = 0;
```

It extracts ID and scale name, inserts Key rows, terminates the buffer, and
returns the list count. The routine contains an additional mode-byte branch;
live probes must preserve the XDJ request shape instead of borrowing the newer
`0x1014` contract.

`getTrack_Key` passes the selected Key ID into the common AppSync track-query
builder and ordinary sort/row insertion machinery. It inherits the undeleted
content predicate, secondary-column behavior, compatibility fields, and row
width rules. Corresponding Master-interface methods exist, while
`SetSharedDBInfo` installs AppSync for this isolated Link Export library.

The `0x130C` branch is intentionally asymmetric with its player wrapper. The
XDJ-RR waits for the ordinary numeric root reply; Rekordbox logs the exact kind,
sets no cache entry, builds no buffer, sends no `4000`, and returns `-2` to its
internal dispatcher. A live request is therefore a bounded timeout probe, not
an empty menu.

## Write dispatcher

`OnMAnlzClientCmd` routes every `2x05` request to `OnWriteCmd`. Its ten-entry
switch accepts exactly `0x2005..0x2905`. Three accepted kinds are explicit
log-only compatibility arms.

| Kind | Client name | XDJ-RR location | Rekordbox target | Reply/transport | Persistent effect |
|---:|---|---:|---|---|---|
| `2005` | `CMD_SAV_WAVE` | 8 | `SavWave` | asynchronous | writes 400 loud-wave samples and 100 dot-wave bytes to the analysis path |
| `2105` | `CMD_SAV_USB_CUE` | 8 | `SavUsbCue` | `4702`; cue-update notification | inserts, updates, or deletes legacy cue and cue-option rows |
| `2205` | `CMD_SAV_VBR_INFO` | 8 | `SavVbrInf` | asynchronous | constant-success stub; message is not inspected |
| `2305` | `CMD_SAV_DISC_CUE` | 8 | log-only arm | no reply | none |
| `2405` | `CMD_DEL_ALL_DISC_CUE` | 8 | log-only arm | no reply | none |
| `2505` | `CMD_REG_DISCID` | 8 | log-only arm | no reply | none |
| `2605` | `CMD_SAV_QTZ_OFFSET` | 1 | `SavQtzOfs` | `4000` | writes the analysis offset and mirrors its state into `ContentLink` bit zero |
| `2705` | `CMD_SAV_USB_CUE2` | 8 | `SavUsbCueExt` | `4E02`; cue-update notification | applies the extended cue/cue-option mutation |
| `2805` | `CMD_SAV_SPECIFIED_ATOM_INFO` | 1 | `SaveSpecifiedAtomInfo` | `4000` | writes a validated atom through `MstSaveAtomData` |
| `2905` | `CMD_UPD_SPECIFIED_ATOM_INFO` | 1 | `UpdateSpecifiedAtomInfo` | `4000` | updates a PQT2 atom through `MstUpdateAtomData` |

### Wave write (`2005`)

The XDJ-RR has SD/USB and disc-shaped constructors. Both set location 8 and the
streamed-data flag, declare 900 bytes, and place the payload pointer in the
final message field. The disc form also carries a media/file selector; the
SD/USB form uses the connected device number and direct content identifier.

`SavWave` requires at least 900 bytes and a non-null stream. For its accepted
wave type it expands the first 800 bytes into 400 `LoudWaveInfo` samples and
writes them with `MstStoreLoudWave`, then sends the remaining 100 bytes to
`MstStoreDotWave`. The destination comes from AppSync
`getAnalysisDataPathFromContentID`:

```sql
SELECT AnalysisDataPath
FROM djmdContent
WHERE rb_local_deleted = 0 AND ID = <content-id>;
```

The operation writes analysis data and does not decode playable audio.

### Cue writes (`2105`, `2705`)

The legacy constructors distinguish register and delete with an operation
flag, carry a 36-byte cue record, and attach an eight-byte auxiliary record.
`SavUsbCue` mutates the cue state and builds a `4702` reply from the resulting
rows.

The extended constructor sends content ID, declared payload length, extended
record pointer, and a mode value. `SavUsbCueExt` replies through
`RetNewCueToClient`, whose constructor hard-codes `0x4E02`. This path is
distinct from the `0x2401` Hot Cue Bank setter even though both eventually use
AppSync cue callbacks.

### VBR and compatibility arms (`2205..2505`)

The complete `SavVbrInf` body returns one. It reads no payload and writes no
file, making `0x2205` a successful compatibility sink.

The XDJ-RR also contains complete `0x2305`, `0x2405`, and `0x2505`
constructors and waits for cue, numeric, or disc-ID responses. Rekordbox logs
each kind, assigns internal result `-2`, and invokes no target. Their silent
behavior differs from a status-zero or empty reply.

### Quantize offset (`2605`)

The client sends location 1, content ID, and offset. `SavQtzOfs` resolves the
analysis path, passes the low 16 bits to `MstSaveQtzOffset`, and then calls
AppSync `setQtzOffsetFlg`. That method reads:

```sql
SELECT ContentLink
FROM djmdContent
WHERE rb_local_deleted = 0 AND ID = <content-id>;
```

It preserves all other bits, sets bit zero from `offset != 0`, and persists the
row through `CloudAgentAPI::ContentIf`.

### Specified atoms (`2805`, `2905`)

Both client wrappers send location 1, content ID, packed four-character atom
and extension identifiers, numeric positioning/length fields, and a stream
pointer. Rekordbox resolves `AnalysisDataPath`, derives a sibling analysis
file, and returns a numeric `4000` result.

`SaveSpecifiedAtomInfo` validates its atom/extension combination and calls
`MstSaveAtomData`. `UpdateSpecifiedAtomInfo` admits PQT2 and calls
`MstUpdateAtomData`. Exact parser boundaries belong to the guarded generated
payload campaign already in the serial queue.

## Database modification dispatcher

`OnDbModCmd` accepts exactly two kinds:

| Kind | Client/source status | AppSync target | Reply | Effect |
|---:|---|---|---:|---|
| `2107` | XDJ-RR `SetRateValue2Track`, location 1 | `modTrackRate`, vtable `+0x2A0` | `4000` | update `djmdContent.Rating` and emit a rating notification |
| `2507` | Rekordbox-only static arm | `modTrackBPM`, vtable `+0x2A8` | `4000` | update `djmdContent.BPM` and emit a BPM notification |

The player name `CMD_MOD_TRACK_RATE` uses “rate” to mean star rating. Its
constructor sends content ID and one rating value. AppSync reads:

```sql
SELECT Rating
FROM djmdContent
WHERE rb_local_deleted = 0 AND ID = <content-id>;
```

It returns success without writing when the low byte already matches. A change
is persisted through `CloudAgentAPI::ContentIf::updateById`; the previous value
is copied through the handler output pointer. The BPM arm follows the same
pattern with `BPM`.

AlphaTheta's named `0x2207` KUVO-status request reaches `OnDbModCmd` by its low
byte but falls outside the two-kind switch and is statically rejected.

## Device and location implications

- Location 8 carries player-side analysis and cue persistence associated with
  removable/disc workflows.
- Location 1 carries track-property and analysis-offset/atom updates.
- The old Key browser uses the caller-selected left location or right location
  2.
- Cue Track uses the same left/right locations even though Rekordbox has no
  builder for its root kind.

These are client workflow choices, not recovered Rekordbox model-string
predicates. Model-dependent behavior can still arise from setup width, status
ownership, requester number, or the client selecting a different family.

## Live-test boundary

The read-only follow-up is declared and handed off as guarded recovery
generation `ae18`.
Six suites contain 48 cases across ordinary RX3, authentic RX3-status, and
derived CDJ-status identities under both setup widths. Locations 1 and 2 each
exercise old-Key root and track selection. Each bounded `130C` timeout uses a
fresh connection and is immediately followed by a known-good old-Key root on
another fresh connection, distinguishing a silent command from a dead
dbserver. Record/repeat health captures and hash-bound receipts remain pending
behind the location-9 matrix.

Write follow-up requires one fresh encrypted fixture per observation. Each
case must retain request bytes, process/Application health, logical
base/WAL/SHM snapshots, relevant analysis-file hashes, immediate reply or
timeout, and a same-database restart control. Log-only arms require before and
after database/filesystem hashes because their clients expect responses that
this server never constructs.
