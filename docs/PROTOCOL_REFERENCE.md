# Rekordbox Link Export menu protocol

This document describes the Link Export database menus served by Rekordbox
7.2.19, using a live Rekordbox session and its matching `master.db`. It is
intended both as a protocol reference and as an implementation guide for a
headless server.

The live source was Rekordbox at `10.0.0.119:61074` on 2026-09-28. The
read-only database was
`/mnt/documents/multimedia/djing/rekordbox/master.db`. Both contained 4,342
tracks and 2,203 referenced artists, which establishes that the database and
the Link Export source were the same library.

The machine-readable capture is
[`data/source-menu-tree.json`](data/source-menu-tree.json). It contains 90
bounded menu nodes and retains every typed argument of every captured row.
It was limited to 64 rows per menu, two branches per node, and four drilldown
levels; header counts still record the full size of each menu.

## Evidence notation

- **Observed**: received directly from the live Link Export socket.
- **Database**: verified against the matching `master.db` schema or values.
- **RE**: corroborated by Rekordbox 7.2.19 symbols or decompiled behavior.
- **Inference**: the evidence is consistent, but the exact contract remains
  unverified.
- **Unknown**: a question that needs another controlled capture or deeper
  reverse engineering.

Numeric protocol values are hexadecimal unless a table labels them otherwise.
The request examples omit the transaction ID, which is part of every message
but is not a request argument.

## Connection and menu transaction

1. A player connects to TCP port 12523 and asks for the `RemoteDBServer` port.
   Rekordbox returns the database server's two-byte TCP port.
2. The player connects to that port, exchanges the protocol greeting, and sends
   setup `0000`.
3. A menu request receives `4000 [request_kind, count]`.
4. The player asks for one window with `3000`; this capture used 32-row pages.
5. Rekordbox replies with `4001`, zero or more `4101` rows, then `4201`.
6. The player repeats step 4 with another offset until it has the requested
   rows.
7. `0100` closes the session. The polite close uses transaction
   `ffffffff`-minus-one (`fffffffe`).

TCP is a byte stream: message boundaries do not necessarily align with
`recv(2)` calls. Rekordbox keeps process-wide materialized menus keyed by the
packed context, including its menu-location byte. The state survives the TCP
connection that populated it. A client must query and render with the same
context unless it deliberately intends to read an older initialized buffer;
rendering a context that has never been populated can time out **[OBS, RE]**.

The observed render request shape was:

```text
3000 [context, offset, requested_count, 0, total_count, 12, 1, 0]
```

The fourth value is a first-row character seek key, not a reserved word. Its
low 16 bits are passed to `GetListBuf1stRow`; zero selects ordinary offset
pagination. The fifth value is the client's reported menu total and is unread
by `GetListBufContents`. The sixth value is a category ID whose low 16 bits are
mapped through `DBCommon_GetCateKind`. The final two values are the secondary-
override gate and selector. Static field ownership and the pending boundary
oracle are detailed under **Track render numeric fields** below **[DEC]**.

The bounded capture used 32-row pages. A 37-row menu arrived as 32 + 5; menus
capped by the probe at 64 arrived as two full pages. Every response matched its
requested count. Zero-count valid menus required no render request. The JSON
records the render requests and menu rows but not the arguments of `4001` and
`4201`, so those exact arguments need a raw second capture.

`4003` is an explicit query error. A `4000` count of `ffffffff` is another
failure/unavailable result seen by existing clients.

### Setup variants

**Observed.** Setup uses transaction `fffffffe` and request kind `0000`. The
isolated 7.2.19 oracle returned two distinct reply shapes for controlled query
device 1:

```text
extended request: 0000 [1, 14]
extended reply:   0000 [11, 14]
legacy request:   0000 [1]
legacy reply:     4000 [0, 11]
```

These are hexadecimal values. The legacy reply agrees with Dysentery's
documented common-success form; the extended reply retains setup kind `0000`.
The complete typed exchanges, including transaction IDs, are retained as
`behavior.setup_exchange` in every format-2 oracle golden.

A two-argument setup selects the extended row form and rekordbox returns all
16 arguments. The one-argument setup selects a 12-argument legacy form. Legacy
rows are the first 12 arguments of the same row; rekordbox does not erase the
secondary text or replace the item type.

The controlled device-matrix suites use query device 1 and context `01010301`
for every discovery identity. The XDJ-RX3 discovery packet advertises player
11, so those suites deliberately isolate discovery/model classification from
the client number in the TCP protocol.

The retained physical RX3 session establishes the native query number
separately. It sent legacy setup `fffffffe:0000 [0x0b]`, received
`fffffffe:4000 [0, 0x29]`, and used requester byte `0x0b` in every packed
context. Its root context was `0x0b010401`: player 11, menu location 1,
Rekordbox media slot 4, track type 1, and root capability mask `0x05fdffff`.
The complete session also used locations 3, 5, and 8 while retaining slot 4
and track type 1. The
capture does not establish the serving Rekordbox version, so its `0x29` setup
reply must not be attributed to 7.2.19. Fresh
7.2.19 status-backed player-11 goldens use the same setup request and legacy
row width; their recorded behavior identifies setup width but the current
golden format does not retain the setup reply fields **[CAP, OBS]**.

This distinction exposed a server bug: its legacy path blanked argument 5 and
changed a composite track type to title-only before truncation. The corrected
path only truncates the row. A live legacy track row looked like:

```text
206733291, "Abandon All Hope Here", "3A - 112.2 bpm", type 0x0f04
```

### Client cancellation `0001`

The retained physical RX3 emits five zero-argument `0001` messages after
artwork requests, preserving the preceding `2003` transaction ID. Dysentery
names this message "invalid data." In the RX3 firmware,
`RecvFromCommTask` builds the zero-argument kind `0001` from the outstanding
request ID when `CheckCanceledRequest` accepts a GUI cancellation. It is absent
from the CDJ-3000 command-name table and is not classified as an ordinary
Rekordbox menu request **[CAP, DYS, RX3DEC]**.

The reports follow their artwork requests by 21,098 to 126,329 microseconds.
Three occur after a captured `4002` response: one status-zero 28,040-byte JPEG
and two status-50 empty replies. Two have no correlated server reply in the
retained stream. No separate response to `0001` is captured. The command means
cancel the outstanding transaction; it is not evidence that the RX3 rejected
JPEG bytes. The timing evidence is machine-readable in
`data/experiments/physical-rx3-session/navigation-transcript.json`.

## Common request arguments

Most requests begin with a packed context and a sort ID:

```text
[context, sort, selectors...]
```

The captured context was `01010301`. Existing protocol work describes its
bytes as requester/player, menu location, media slot, and media/track type. A
fresh-connection sweep established these live acceptance rules for the first
three bytes: requester/player 1 returns the menu and values 2-6 time out;
menu-location values 1-8 all return the same track list; media-slot candidates
0-4 all return it. The menu-location byte participates in the complete
process-wide list-buffer key rendered by a later `3000` request **[OBS, RE]**.
The decompiled XDJ-RR client independently supplies direct callers at every
literal location 1-8 and fixes Delivery Info `2602` to location 9. Location 9
is a source-defined specialized context, not part of the ordinary-Track sweep;
its 36-case real-Rekordbox matrix is queued behind the cue-payload oracle
**[RR-DEC]**.

The final byte was then exhausted over `0x00..0xff` for ordinary Track request
`1004`, holding the other bytes at `010103`. Exactly `0x03` and `0x04` time out
before a header. Each of the other 254 values returns the same eight-track menu.
Only `0x01` preserves argument-10 bit `0x100`; all eight rows from every other
successful value carry zero there, with every other field identical. Dysentery
names `0x00` no track, `0x01` rekordbox track, `0x02` unanalyzed track, `0x05`
audio CD track, and `0x06` streaming track. The renderer statically gates its
cache/`HotCueAutoLoad` enrichment path on `track_type == 1`, explaining the row
delta **[OBS, RE, DYS]**.

The same seven client values were crossed over all 47 canonical list-family
requests. Root and Search populate only for `0x01`; direct category and leaf
queries work for the other successful values. Genre, Artist, Album, Label,
Original Artist, Remixer, and Playlist track leaves copy `TT << 24` into row
argument 7. `PSvDBMain::OnClientReq` explains the exceptional values exactly:
for request class `0x1xxx`, it diverts low bytes `0x03` and `0x04` before
`OnListClientCmd`. The same values reach the `0x2xxx` dispatcher. Display,
Play, and Delivery Song Info then reject every type except `0x01` with total
`0xffffffff`; Hot Cue Bank instead advertises 50 rows and times out during
render for every non-`0x01` type. The binary does not assign semantic names to
`0x03` or `0x04` **[OBS, RE]**. See `PACKED_CONTEXT_ORACLE.md`.

The root request was:

```text
1000 [01010301, 00000000, 05cfffff]
```

The final root argument is a category capability mask. For ordinary menu item
ID `n`, bit `n - 1` is required. Date Added (menu item 22) instead requires bit
24. Rekordbox intersects this mask with `djmdCategory.Disable`, including
special handling for Date Added and Matching, then suppresses Folder. The exact
predicate and complete bit map are in `CONFIGURATION.md` **[RE, DB]**.

`ffffffff` is the wildcard/ALL selector in hierarchy requests. Rekordbox also
sends an ALL row with ID `ffffffff` and item type `a0` where a hierarchy may be
collapsed.

The exact extended ALL row is:

```text
[0, ffffffff, 12, "\ufffaALL\ufffb", 2, "", a0,
 0, 0, 0, 0, 0, 0, 2, "", 0]
```

In this capture Rekordbox inserted ALL only when a level had more than one
concrete child. Single-artist Acoustic, single-album Above & Beyond, and the
single-artist Ablazing label omitted it. Database album ID 0 displayed as
`Unknown` is a concrete row and is distinct from ALL.

## Render ranges and pagination

The nine-case live pagination sweep exposes nonstandard range normalization:

| Offset | Count | Observed rows |
| ---: | ---: | --- |
| automatic one-row pages | 1 each | all eight in order |
| 0 | 8 | all eight |
| 7 | 1 | final row |
| 0 | 0 | first row |
| 8 | 1 | final row |
| 9 | 1 | final row |
| 7 | 10 | all eight from the beginning |
| 0 then 2 | 3 then 3 | six rows with the overlap repeated |
| `ffffffff` | 1 | no reply; read timeout |

Thus zero count is normalized to one, ordinary offsets at or past the end clamp
to the final row, and an overrun larger than the list wraps to the full list.
Only the maximum unsigned offset is silently ignored. All results repeated
exactly **[OBS]**.

## Invalid requests and framing

The normal-message error suite produced these exact 7.2.19 outcomes **[OBS]**:

- unknown kind and a track request with no arguments timed out;
- a missing sort argument and an extra third argument both returned the normal
  eight-row track header;
- string or blob context values returned a zero-argument `0x0100` response;
- a root request missing capabilities returned a valid zero-row root;
- string root capabilities returned `0x0100`;
- sending render kind `0x3000` as the first menu request returned the normal
  two-zero-argument `0x4001` render header.

At the raw framing layer, bad magic, too many declared arguments, and an unknown
field tag each returned a zero-argument `0x0100` message. A truncated header, a
short tag list, and the oversized-blob probe produced no reply before timeout.
Connections were isolated per malformed case, so one decoder state could not
affect the next.

## Concurrent sessions

Twelve identical player-1 track sessions released from a barrier all completed
with eight rows when setup reads were allowed ten seconds. The runner stores
the raw worker observations but compares a canonical outcome multiset, avoiding
thread-scheduling labels in the oracle. The immediate repeat again produced
12 menus. The ten-second deadline is part of the suite because a three-second
burst deadline caused transport setup timeouts rather than a stable server
capacity limit **[OBS]**.

## Menu row layout (`4101`)

Extended menu rows contain 16 typed arguments:

| Index | Shape | Meaning established by this capture |
| ---: | --- | --- |
| 0 | number | Row-dependent auxiliary ID. On track rows it is the effective right-column key: lookup ID, numeric value, or content ID for Comment/Date Added. It is a distance/tolerance on some selector rows. |
| 1 | number | Primary row ID: content, artist, album, lookup, playlist, or selector ID. |
| 2 | number | UTF-16 byte length of argument 3, including the terminating NUL. |
| 3 | string | Primary display text. Root labels are wrapped in U+FFFA/U+FFFB for player localization. |
| 4 | number | UTF-16 byte length of argument 5, including the NUL. An empty string has length 2. |
| 5 | string | Secondary display text. Track rows use the configured secondary column. |
| 6 | number | Item type. For track rows the low byte is title (`04`) and the high byte identifies the secondary column. |
| 7 | number | Scope/state flags. Bit 0 marks Prepare membership; `01000000` is materialized list/scope metadata. See `ROW_LAYOUT.md`. |
| 8 | number | Row-dependent repeated ID. Album rows repeat their album ID here; track rows repeat their content ID from argument 1. |
| 9 | number | Position or track number, depending on the menu. Playlist/folder rows carry their position under the parent; SmartList track rows retain persisted membership sequence even when rule evaluation supplies the candidate set. |
| 10 | number | Track compatibility and hot-cue-auto-load flags. Bit 0 marks an unsupported compatibility result; bit 8 marks nonempty `HotCueAutoLoad`. |
| 11 | number | Converted/new-key ID on the New Key/Key-category path; zero where that path does not populate it. |
| 12 | number | Original `djmdContent.KeyID` on content track rows, independent of the secondary-column selection. |
| 13 | number | UTF-16 byte length of argument 14, including the NUL. |
| 14 | string | Tertiary text; the live track rows contain a key spelling. |
| 15 | number | BPM multiplied by 100 on track rows. |

Arguments 0 and 12 happen to match when Key is the effective right column, but
they come from different stages. Argument 0 follows the selected right-column
field; argument 12 is always the content row's original KeyID. Argument 8 was
consistently the content ID on tracks and the album ID on albums. A headless
implementation must still model layouts by item type rather than assign the
track meanings universally. `ROW_LAYOUT.md` provides the complete track path.

### Item types and the secondary column

Simple row item types observed in this capture include album `02`, title `04`,
genre `06`, artist `07`, playlist `08`, rating `0a`, duration `0b`, tempo `0d`,
label `0e`, key `0f`, bitrate `10`, release year `11`, and remixer `29`. Other
corroborated layouts use history `24`, original artist `28`, and date added
`2e`. These wire meanings matter more than names in an existing constants file:
this live capture proves that `10` is bitrate and `11` is release year. Color
rows are a special case, using one type per color (`14` through `1b`) rather
than a single generic color type.

`ITEM_TYPE_REFERENCE.md` is the complete corpus-wide catalog: it covers all 85
represented simple, menu, synthetic, Song Info, and composite values across
51,148 `0x4101` row representations and preserves their producing requests,
samples, occurrence counts, and source goldens.

`OBSERVED_RESPONSE_SHAPES.md` supplies the inverse request-to-response index
for the complete canonical Rekordbox 7.2.19 golden corpus. It attributes
selection headers and direct replies to their declared request, while treating
each later page as a distinct `0x3000` transaction. This keeps list selection,
rendering, timeouts, and asynchronous pre-request drain frames in their proper
protocol stages. Exact argument-type vectors, counts, item types, and source
goldens are retained in `data/observed-response-shapes.json`. Every request
also points to exact identity profiles carrying model, player, device class,
generation, presence, model code, setup width, keepalive hash, and optional
status-packet provenance. This preserves the distinction between ordinary
identity coverage and status-backed model classification. The readable index
lists every one of the 17 exact profiles and reports profile/model counts,
status-backed coverage, and setup widths per request. Its separate declaration
snapshot binds the five classified kinds still lacking a canonical response to
222 declared cases across 36 suite files; declaration readiness is not counted
as observed behavior. Setup exchanges and asynchronous drains carry their own
exact identity-profile and setup-width coverage. This preserves provenance
without reassigning a delayed frame to the request that follows it **[OBS]**.

Track-list rows use a composite type:

```text
(secondary-column item type << 8) | 04
```

The current live library returned `0f04` and secondary values such as
`3A - 112.2 bpm`, so its selected column was key. An older capture used `2304`
with the same human-readable key/BPM summary while the secondary item type was
comment. This proves that clients key presentation behavior off the type, but
also warns that the string is not necessarily a raw copy of the named database
column.

Rekordbox USB exports store the user's choice in the `sort` table as
`isSelectedAsSubColumn`. The desktop `master.db` encodes the same choice in
`djmdSort.Disable` bit 1. The row renderer selects
`WHERE (Disable & 2) = 2`; the copied database selects sort ID 12 (Key). Bit 0
independently controls sort-menu visibility **[RE, DB]**. Exact extractor and
wire-type mappings are in `SECONDARY_COLUMNS.md`.

The controlled extended-row matrix is complete for all 15 selectable rows
**[OBS, DB]**. Artist, Album, Genre, Remixer, Label, Original Artist, Comment,
Color, Date Added, Key, and BPM carry server-authored argument-5 text; Rating,
Time, Bitrate, and DJ Play Count leave it empty for player-side formatting.
Key selection produces `<key> - <bpm>`, type `0x0f04`; BPM selection produces
`<bpm> - <key>`, type `0x0d04`. Argument 0 remains the raw lookup ID or numeric
database value, while arguments 12/14/15 continue to carry original KeyID, key
spelling, and BPM independently of the selected column. A database with no
selected row emits title-only `0x0004`; a deliberately invalid two-selection
database consumes row zero from the unordered query and reproducibly chooses
Comment for that fixture. `SECONDARY_COLUMN_ORACLE.md` gives every exact value,
the numeric sweeps, missing/multiple-selection evidence, and Sort-menu effects.
The Preferences settings reader is a separate `Seq`-ordered path; it reports
the first selected ID and logs multiple selections without determining which
row the Link Export builder or fallback renderer consumes **[DEC]**.

`data/secondary-column-semantics.json` provides the canonical same-track join
across 63 persisted, six-argument active-sort, eight-argument control, and
active-sort eight-argument persisted-fallback profiles, containing 504 row
projections. Fields 12-15 are path-invariant for
each track across the join. Persisted and explicit
override results agree for every selectable column except BPM alone: dynamic
BPM override over a Key-materialized list retains BPM and type `0x0d04` but
has empty argument 5 instead of cached `BPM - Key`. Persisted and active-sort
profiles retain the same text/type; six shared lookup/date paths differ only
in argument 0 **[OBS]**.
The all-track comparison includes nonzero numeric values and confirms that BPM
argument 5 is the only persisted/override difference.
With eight-argument gate `1` and selector `0`, Default and active Key preserve
the cached `Key - BPM` value. Each other active sort forces persisted Key to be
re-extracted as Key alone. The matching six-argument rows therefore agree for
Default and Key and differ exactly in fields 0, 5, and 6 for every row under
the other nine shared visible sorts **[OBS]**.
The matching legacy record/repeat matrix is complete across all 15 selectable
columns. Every Sort menu and secondary value matches its extended partner, and
each legacy row is the exact first-12-argument prefix of its 16-argument
extended row **[OBS]**.

The optional render arguments are active controls only in the eight-argument
form: argument 7 is an override gate and argument 8 is a nonzero selector
override. When the gate is zero, argument 8 is ignored. With the gate enabled,
a zero override reads the persisted Column selection and a nonzero override
selects that sort ID. A type mismatch against the materialized list-buffer
column regenerates the requested value through the dynamic extractor.

Six-argument RX3 rendering instead preserves the preceding list request's
right column. The complete visible Sort-menu cross held every render at
`[context, offset, count, 0, total, 12]`: Default used persisted Key; Alphabet
used Title; Artist, Album, BPM, Rating, Genre, Label, Key, Date Added, and DJ
Play Count each used the active sort's type and value. Thus the final value
`12` does not select Key in this form. The earlier five/six/eight arity capture
used only Default sort and could not expose this distinction. String extractors
cap lookup-backed values at 127 characters. Comment and Date Added preserve at
most 255 UTF-16 code units; an input that reaches 256 units yields the menu
header but stalls the render response **[OBS, DEC]**.

Five-argument rendering omits that final value entirely. Default-sort behavior
is recorded, but the corresponding eleven-sort cross is a queued declaration,
not yet an observed rule. Its real-Rekordbox reducer compares every complete
row with the six-argument oracle and reports equality or divergence without
using the six-argument result as an expectation.

Seven-argument rendering is accepted by the pinned parser but falls between
its two optional-field thresholds. `GetListBufContents` decodes argument 6 at
an argument count of six or greater, while the gate and selector are decoded
together only at eight or greater. The supplied seventh value is therefore
unread in the recovered x86-64 body. A queued real-Rekordbox matrix crosses all
11 visible sorts with seventh values zero, one, and `UINT32_MAX`; until those
record/repeat artifacts exist, ignoring it remains a static prediction **[DEC,
OBS plan]**.

### Track render arity boundary sweep

The checked-in `render-arity-boundaries.json` declaration covers every total
argument count from 3 through the protocol framing limit of 32 after a valid
Track header. Default sort supplies the complete 30-count sweep. Arity 3, 4,
9, and 32 additionally cross all ten non-default sorts visible on RX3, for 70
cases total. Three arguments are the runner's mandatory context, offset, and
count; arity 32 is the largest ordinary typed-message argument list. The
existing malformed-framing suite separately proves that a declared count of
33 is rejected at the framing layer.

Counts above eight retain valid first-eight controls and use distinct numeric
sentinels in each trailing position. Every case has an unconstrained outcome:
reply, error, timeout, or disconnect will be recorded from Rekordbox rather
than inferred from the nominal eight-field format. Generation `an18` records
and repeats this matrix after the five- and seven-argument crosses **[OBS
plan]**.

### Track render arity underflow

`render-arity-underflow.json` closes the valid-framing domain below the normal
three-field render prefix. For each total argument count zero, one, and two, a
fresh connection first materializes the Default Track list, then sends a
correctly encoded `0x3000` on that same connection with respectively no fields,
`context`, or `context, offset`. A fresh-connection Track request follows each
probe as a process-health control.

The three render declarations accept any raw reply, timeout, or disconnect and
retain the exact decoded bytes when present. They do not treat an argumentless
render sent before list creation as equivalent to an underlength read of an
initialized list buffer. Generation `ao18` records and independently repeats
all nine sequence cases after the 3-32 sweep **[OBS plan]**.

The pinned decoder allocates and zeroes the complete `0x98`-byte command before
reading its argument count, tags, or values. A zero count skips the value loop;
each supplied value otherwise occupies an eight-byte slot beginning at
`0x18`. `GetListBufContents` reads slots `0x18`, `0x20`, and `0x28` before its
first count comparison. The source-derived projections are therefore
`[0, 0, 0]`, `[context, 0, 0]`, and `[context, offset, 0]`. This establishes
storage and field projection, while response and connection behavior remain
live-authority questions **[DEC, OBS plan]**.

### Track render argument types

`render-argument-type-matrix.json` crosses all eight positions of the normal
eight-argument `0x3000` request with protocol string tag `0x02` and blob tag
`0x03`. Each of the 16 probes runs in its own cold Rekordbox process, first
materializes a valid Default Track list on the same connection, changes
exactly one argument's tag and value, and accepts any raw reply, timeout, or
disconnect. Record and repeat retain process and Application-event health in
addition to the wire result **[OBS plan]**.

The pinned `ReceiveCommand` decoder explains why argument type cannot be
treated independently from its position. String and blob tags both require a
preceding decoded numeric slot as their allocation/read length. String rejects
lengths at or above `0x201`; blob rejects lengths at or above `0x500000`.
Neither variable-width type can occupy position one because it has no preceding
slot. When decoding succeeds, the current eight-byte value slot contains an
allocation pointer. `GetListBufContents` reads the same slots as render values
without consulting their semantic tags **[DEC]**.

The live declarations intentionally leave every neighboring numeric value at
its normal render value. They therefore measure the combined framing, decoder,
dispatch, render, transport, and process behavior of a one-field wire
substitution. They do not change a preceding field merely to admit the new
type. The static projection does not determine which probes reach render
dispatch or what Rekordbox returns; generation `ap18` records those answers
after the arity-underflow oracle **[DEC, OBS plan]**.

### Track render numeric fields

The complete `GetListBufContents` body reads render positions 1-8 with widths
64, 64, 32, 16, 0, 16, 32, and 32 bits respectively. Positions 1-3 are context,
offset, and count. Position 4 is a first-row character seek key. Position 5 is
the client-reported total but has no read in the renderer. Position 6 is a
category ID passed through `DBCommon_GetCateKind`; positions 7-8 are the
secondary override gate and selector **[DEC]**.

For position 4, zero follows normal offset pagination. Other low-word values
enter a first-character scan that normalizes ASCII lowercase to uppercase and
contains dedicated handling for `U`/`Unknown`. Low word `0xffff` wraps the
internal increment back to zero. High 16 bits are never read. The 42-case
`render-numeric-fields.json` matrix covers representative characters, search
boundaries, `0xffff`, and high-word aliases **[DEC, OBS plan]**.

The 51-entry category map is exact: IDs 1-24 map identically; 25-29 map to
zero; 30-32 map identically; 33-39 map to zero; 40 maps identically; 41-49 map
to zero; and 50-51 map identically. Zero and IDs above 51 map to zero. Position
6 is also truncated to 16 bits. The matrix selects every equivalence range and
boundary while holding the override fields constant **[DEC, OBS plan]**.

Generation `aq18` records all 42 cases twice after the argument-type stage.
Every declaration accepts Rekordbox's authority outcome, and the reducer
reports row identities, titles, and equality with the normal control rather
than using the static prediction as a promotion gate **[OBS plan]**.

### Track render override controls

The eight-argument form reads argument 7 as a 32-bit override gate and
canonicalizes it to one bit with `setne`. Argument 8 is not narrowed at the
request boundary. The row builder uses its signed low byte for `ReturnIconID`,
but passes the complete 32-bit selector to `Get_SubCategoryValue`. That
extractor subtracts two and admits only the unsigned interval 2 through 17.
A value such as `0x00010002` can therefore resemble Artist to icon dispatch
while remaining out of range for secondary-value extraction **[DEC]**.

Earlier live controls covered gate zero and one, selector zero, and selectors
2 through 17. They did not establish selector 1, values above 17, high-word
aliases, or whether every nonzero gate value is live-equivalent. The focused
`render-override-controls.json` matrix adds five gate boundaries and eleven
selector boundaries while holding the materialized Default track list and all
other render fields fixed. Generation `ar18` records its 17 cases twice after
the numeric-field stage; response rows and transport outcomes remain real-
Rekordbox authority questions **[DEC, OBS plan]**.

The Rekordbox track-row builder independently establishes these secondary
column type bytes and backing values:

| Secondary | Type byte | Backing value |
| --- | ---: | --- |
| Genre | `06` | `GenreID` |
| Artist | `07` | `ArtistID` |
| Album | `02` | `AlbumID` |
| BPM | `0d` | `BPM` |
| Rating | `0a` | `Rating` |
| Remixer | `29` | `RemixerID` |
| Label | `0e` | `LabelID` |
| Original artist | `28` | `OrgArtistID` |
| Key | `0f` | `KeyID` |
| Color | `13` plus a color-specific discriminator | `ColorID` |
| Duration | `0b` | `Length` |
| Bitrate | `10` | `BitRate` |
| Comment | `23` | `Commnt` |
| DJ play count | `2a` | `DJPlayCount` |
| Date added | `2e` | `StockDate` |

Color's `13` here is a secondary-column base type; the Color category selector
rows remain the distinct palette types `14`-`1b`. The secondary jump table and
the independent icon-type table both assign DJ Play Count type `2a`.

For the captured key-secondary mode, the track row is well correlated:

| Argument | Key-secondary track value |
| ---: | --- |
| 0 | `djmdContent.KeyID` |
| 1 | `djmdContent.ID` |
| 3 | `Title`, except `FileNameL` in the filename menu |
| 5 | `"<Classic key> - <BPM with one decimal> bpm"` |
| 6 | `0f04` |
| 7 | Scope/state flags |
| 8 | Content ID, repeating argument 1 |
| 9 | Scope-specific position/track number |
| 10 | `0100` in all 708 captured rows because `HotCueAutoLoad` was nonempty |
| 11 | Converted/new-key ID populated by the key-category path |
| 12 | Original `djmdContent.KeyID`, independently populated |
| 14 | Classic key text |
| 15 | BPM ×100 |

For the first live track, arguments 0/12 were `3441880869`, exactly its
database `KeyID`; arguments 1/8 were `206733291`, exactly its content ID. The
match between arguments 0 and 12 is a consequence of Key being selected and
does not hold for other right columns.

Argument 9 is zero in unordered top-level/filter results. It matches
`djmdSongPlaylist.TrackNo` in playlist results and the album track number in a
concrete album. An artist's ALL-albums result used zero, while its concrete
album result used the track number. The Matching sample carried track number
15.

### Flags

The live track capture contained `00000000`, `00000001`, `01000000`, and
`01000001` in argument 7. `01000000` occurred in artist, album, genre, label,
remixer, and playlist track lists, but not in Track, Key, BPM, Rating, Time,
Bitrate, Color, Year, File Name, or Matching results. The low bit was stable for
the same content ID across every captured scope.

Static analysis maps the high nibble to materialized column 12 shifted into
bits 24-27. Bit 0 is set when a content ID has at least one matching
`djmdSongTagList` row (or the equivalent cloud-query result). Bit 8 is the
Link-played marker. `UiProDJLink` snapshots every cached `RowDataTrack` whose
status word at `+0x3f8` has bit `0x10`, and
`PSvDBServer::NotifyLibraryUpdatedPlayed` swaps those ContentIDs into the
critical-section-protected `PSvDBMain` array at `+0x6d8`. The renderer and
`0x3b03` `CMD_GET_PLAYSTATE` search that same array; the former emits argument-7
bit `0x100`, while the latter returns scalar `2` for membership and zero for
absence **[DEC, RR-DEC]**. These flags are distinct from argument 10's
compatibility and hot-cue-auto-load flags. The Windows UI transition and cache
refresh timing remain a controlled before/after capture target.

## Root menu

### Display Song Info

Request `2002 [context, content_id]` creates a 16-row metadata list for one
live content row. Rekordbox replies with `4000 [0x2002, total]`; an ordinary
`3000` render then returns `4001`, 16-argument `4101` rows, and `4201`.
Deleted, zero, and unknown IDs return a valid zero-row menu **[OBS]**.

For positive `ServiceID`, Play Song Info reads `CLSSyncMethod` as an integer
with default 1 and branches only on zero versus nonzero. The recorded value-1
path prefers an existing regular `OrgFolderPath` only when local DBID equals
`MasterDBID`, then falls back through the service share root. The zero path
does not require DBID equality, accepts any existing filesystem object at
`OrgFolderPath`, and otherwise consults `MovedFromCloudDir` through the
download-root helper. Its default is special-location kind 3 plus
`PioneerDJ/Moved from Cloud`, normalized as a unified path. The share-root
switch maps ID 0 to empty, 1 to the
current master-database directory plus `/share`, 2 to Dropbox, 3 to Google
Drive, and 4 to OneDrive; the three provider roots append `/rekordbox` and must
be nonempty absolute paths. Download roots admit IDs 0 and 2-5. Only the
`CLSSyncMethod=0` class remains a live-oracle gap **[DEC, OBS]**.

Extended and legacy setup both return the same 16 fields; their rows contain
16 and 12 arguments respectively. This API's render control differs from an
ordinary track list: 5/6-argument renders and an eight-argument render with
gate zero produce a title-only composite first row. Gate one plus selector zero
loads the persisted column; selectors 2-17 override it. Count zero returns the
first row, offsets at or just beyond total clamp to the last row, an overrun
resets to the full list, and offset `0xffffffff` times out. Wrong typed
arguments can return generic `0100 []`, while missing/zero values generally
return a zero-row menu **[OBS]**.

Primary Title and the simple lookup-backed metadata strings cap at 127 UTF-16
code units; Comment and Date Added cap at 255 UTF-16 units. Either path can
split a surrogate pair and expose U+FFFD. The composite Title row's secondary
Key string instead caps at 127 Unicode characters. All tested null, dangling,
negative, out-of-range, 254/255/256-character, and supplementary-string rows
retain the complete 16-field menu **[OBS]**.

The ordinary item-type order is:

```text
0f04 0007 0002 000b 000d 000f 000a 0014
0006 002e 0023 0010 0011 000e 0028 0029
```

For a status-backed `XDJ-RX3` client, Comment (`0023`) moves from position 11
to position 6. The matched `CDJ-3000` status control retains ordinary order.
RX3-shaped status packets relabeled XDJ-XZ, XDJ-AZ, or XDJ-1000MK2 time out;
the relabeled unknown-model/player-1 control retains ordinary behavior. This
is a packet-shape/model-consistency boundary rather than a native-hardware
claim.
`DISPLAY_SONG_INFO_ORACLE.md` gives every complete row, selector and pagination
table, malformed-request result, field-limit matrix, the SQL and lookup paths,
model-cache lifecycle, sibling request kinds, provenance, and remaining matrix
**[OBS, DEC]**.

### Play and Delivery Song Info

Request `2102 [context, content_id]` produces seven rows in this order:

```text
0004 000b 000d 0023 0000 002f 000f
```

They carry FileType, Length, BPM, Comment, delivery path/file size,
HotCueAutoLoad, and Key. Request `2602 [context, content_id]` produces thirteen
rows in this order under the baseline render:

```text
0036 000d 0023 000f 0012 0006 000e
0007 0037 004f 0f04 0002 000b
```

They carry Composer, BPM, Delivery Comment, Key, FileType, Genre, Label,
Artist, Lyricist, DeliveryControl/ISRC, composite Title/secondary, Album, and
Length. Deleted, zero, and unknown content IDs return zero-row menus. Recognized
kinds `2202` through `2502` have no builder in this server path and return
`4003 [request_kind]` for both populated and missing IDs **[OBS, DEC]**.

That rejection is specific to Rekordbox's serving role. XDJ-RX firmware has
successful player-hosted builders for `2202` generic/non-Rekordbox metadata and
`2302` six-row track summary data. The clients in XDJ-RX, XDJ-RR, XDJ-RX2,
XDJ-XZ, and XDJ-RX3 use `2402` for track decode information, expecting reply
`4802`, and emit `2502` as a one-way register track length command. All five
local servers dispatch those latter two to unsupported stubs. See
`data/static-analysis/player-hosted-song-info.json` for the hash-pinned role
audit. CDJ-3000, XDJ-AZ, OMNIS-DUO, and CDJ-1500X still name both requests and
recognize their formats plus `4802`. Hash-bound whole-tree scans cover 26,862
decompiled C sources and find every exact literal confined to the command-name
and parameter-format files. No literal caller, reply wait, or server handler is
present; computed or decompiler-omitted paths remain possible **[SRC, DEC]**.

Play's path row requires nonempty `FolderPath`; null or empty makes the whole
menu zero-row. Its size is the low 32 bits of `FileSize`. Positive `ServiceID`
enters cloud selection: a matching local/property DBID and an existing regular
`OrgFolderPath` select that original path. A zero-byte file qualifies, while a
directory does not. `HotCueAutoLoad` is 1 for every nonempty string and 0 for
null or empty. `PLAY_SONG_INFO_PATH_ORACLE.md` gives the fourteen-case matrix,
cloud fallback strings, static control flow, and backend delta **[OBS, DEC]**.

Play ignores the tested render gate and selectors. Delivery applies selectors
2-17 to its composite Title row. Its heterogeneous row order follows shared
process/list-buffer state independently of the selector. Both
builders use the same non-conventional pagination normalization as Display
Song Info, scaled to totals 7 and 13, including count-zero first-row behavior,
end clamping, overrun reset, and maximum-offset timeout. Both also expose a
repeat-verified parser-state dependency: a blob-valued content ID closes its
socket before its correlated zero-row response is delivered. That transaction-
1 `4000 [2602, 0]` is posted by player identity and can arrive on an immediate
replacement socket. A no-send drain exposes the orphan directly; the following
valid Delivery request returns 13. Delays of 50 ms or more avoid the observed
race. Extended and legacy setup preserve membership while changing rows from
16 to 12 arguments. `SONG_INFO_SIBLINGS_ORACLE.md` contains every field,
selector order, malformed form, query path, lifecycle capture, experiment
hash, and replay delta **[OBS, DEC]**.

Authentic RX3 player-11 status and the RX3-template-derived CDJ-3000 player-1
control produce identical stable Play/Delivery responses after normalizing the
requester byte. Baseline,
render, pagination, and legacy results also equal the ordinary no-status
identity. Argumentless Delivery is the stable exception: ordinary times out,
while both status identities return `4000 [0x2102, 0]` to the `0x2602`
request. Zero context and location 2 are state-sensitive under RX3 status and
remain ordered experiment evidence rather than canonical equality **[OBS]**.

The focused RX3 location-2 matrix makes the latter precise. Valid Play,
Display, Delivery, no precursor, and repeated zero-context Play timeouts all
leave the following matched location-2 Delivery total at 13. Of sixteen
malformed direct precursors, only a blob-valued content ID to Play or Delivery
makes an immediate replacement receive the prior zero-row response. The actual
next Delivery remains 13 once that orphan is drained. The seven regular
families also produce identical cases when an entire suite shares one dbserver
socket; zero-context Play timeouts do not prevent the next request. A wrong-
typed Play context is followed by socket closure before the next Delivery
probe in both cold attempts.
A location-2 menu followed by a render using location 1 advertises 13 and then
times out, proving that the packed location must be preserved across the
menu/render pair **[OBS]**.

The active lifecycle-aware ordered-pair rerun makes that routing rule
connection-explicit. Every connection performs setup and a 1200 ms no-send
drain before sending its declared request. In all 16 promoted pairs whose
first request is blob-valued Play, the second connection's drain receives the
same transaction-1 `0x4000 [0x2102, 0]` before the second request is sent. The
successors span every malformed Play and Delivery form, with timeout,
zero-row, seven-row, 13-row, and
header-without-total outcomes; none changes the delayed frame. When the second
request is another blob-valued Play, the health-probe connection drains a
second identical frame before returning the normal 13-row Delivery. Every
other 15 completed health-probe drains time out and their Delivery still returns
13. This is direct promoted evidence for one player-routed delayed header per
blob-valued Play, consumed by the next admitted connection independently of
that connection's subsequent request. The reducer currently verifies 158 of
256 ordered pairs; the remaining pairs stay an explicit active boundary
**[OBS]**.

All sixteen completed pairs in the following zero-context-Play row are
direct negative controls. Zero-context Play times out; argumentless Play then
times out, missing-content Play returns zero rows, and extra-argument Play
returns seven rows, while both string- and blob-context Play return headers
without totals; string-content Play returns zero rows. All eighteen no-send
drains time out and all six health Delivery requests return 13.
Zero-context Play therefore neither queues the delayed `0x2102` header nor
changes the successor's own response or later location-2 Delivery result in
these lifecycles **[OBS]**.

The seventh successor, blob-content Play, makes the ownership boundary visible
from the other direction. The precursor and successor drains time out; the
health connection then drains exactly one `0x4000 [0x2102, 0]` queued by that
second Play request before its Delivery returns 13. Delayed frames therefore
follow each blob-valued Play request independently of whether it occupies the
first or second position. The eighth successor, a second zero-context Play,
again produces only a
timeout: all three drains time out and health remains 13. Alternate-location
Play then returns its ordinary seven-row menu with all three drains silent and
health still 13. Argumentless Delivery is also a silent timeout in the tenth
pair, followed by normal 13-row health. That lifecycle result is distinct from
the standalone status-backed argumentless-Delivery reply described above; the
ordered-pair runner observes no immediate or drained frame on any of its three
connections. Missing-content Delivery then returns its ordinary zero-row menu
with three more silent drains and 13-row health. Extra-argument Delivery then
returns 13 rows, again with three silent drains and 13-row health.
String- and blob-context Delivery each return a header without a total and
likewise leave all drains silent. String-content Delivery returns zero rows.
Blob-content Delivery returns a header without a total; the measured
three-second no-client interval after it leaves the health drain silent rather
than transferring an orphaned frame. The zero-context precursor is therefore
silent across all sixteen successors, while each successor preserves its own
independent result **[OBS]**.

The following alternate-location-Play row is complete across all sixteen
successors. Its valid
location-2 Play precursor returns seven rows; argumentless Play then times out,
missing-content Play returns zero rows, extra-argument Play returns seven rows,
string- and blob-context Play return headers without totals, and string-content
Play returns zero rows. Zero-context Play times out, while a second
alternate-location Play returns seven rows. The first six successors plus the
zero-context and alternate-location successors leave all three no-send drains
silent. Argumentless Delivery times out, missing- and string-content Delivery
return zero rows, extra-argument Delivery returns 13 rows, and string-context,
blob-context, and blob-content Delivery return headers without totals.
Blob-content Delivery
is followed by the measured three-second no-client interval and still leaves
the health drain silent. All fifteen successors other than blob-content Play
have three silent drains, and every health Delivery request returns 13. These
direct controls show the valid alternate-location menu does not transfer queued
traffic or change any successor's ordinary result **[OBS]**.

The seventh alternate-location-Play pair, with blob-content Play as successor,
hit the independently established connection-admission race. Its record health
drain timed out; its cold repeat drained the exact transaction-1
`0x4000 [0x2102, 0]` successor reply. The precursor, successor outcome, and
13-row health result were otherwise equal. Both envelopes remain quarantined.
A wholly fresh record and repeat then both drained that delayed frame and were
promoted, proving the successor independently queues one reply while retaining
normal health **[OBS]**.

The complete argumentless-Delivery precursor row has sixteen promoted
pairs whose precursor is a silent timeout. Argumentless Play then times out,
while missing-content Play returns zero rows, extra-argument Play returns
seven, and string- and blob-context Play return headers without totals.
String-content Play returns zero rows. All eighteen pre-request drains time
out, and all six matched health Delivery requests return 13. Blob-content
Play returns a header without a total and queues exactly one delayed
transaction-1 `0x4000 [0x2102, 0]` frame into its health drain before the
same 13-row result. These direct controls show the precursor timeout queues no
transferable frame and leaves each successor's independently established
behavior and location-2 health unchanged. Zero-context Play also times out
with three silent drains and 13-row health. Alternate-location Play preserves
its ordinary seven-row menu with three silent drains and 13-row health,
completing every Play-shaped successor. A second argumentless Delivery is also
a silent timeout, while missing-content Delivery returns zero rows. Both have
three silent drains and 13-row health. Extra-argument Delivery returns the full
13-row menu, also with three silent drains and 13-row health **[OBS]**.
String- and blob-context Delivery preserve headers without totals, each with
three silent drains and 13-row health. String-content Delivery preserves its
zero-row menu with three silent drains and 13-row health. Blob-content Delivery
preserves a header without a total after the measured no-client interval, with
three silent drains and 13-row health **[OBS]**.

The missing-content-Delivery precursor row begins with nine zero-row
precursors. Its argumentless-Play successor remains a silent timeout,
missing-content Play returns its ordinary zero-row menu, and extra-argument
Play returns seven rows. String- and blob-context Play return headers without
totals, while string-content Play returns zero rows. All six pairs have three
silent drains and 13-row health. Blob-content Play returns a header without a
total and queues exactly one delayed transaction-1 `0x4000 [0x2102, 0]` frame
into its health drain before the same 13-row result. Zero-context Play remains
a silent timeout, while alternate-location Play preserves its seven-row menu.
Both have three silent drains and 13-row health, completing all nine
Play-shaped successors. The first Delivery-shaped successor is argumentless
Delivery; it remains a silent timeout with three silent drains and 13-row
health. A second missing-content Delivery returns zero rows with three silent
drains and 13-row health. Extra-argument Delivery preserves its full 13-row
menu with three silent drains and 13-row health. String- and blob-context
Delivery preserve headers without totals, each with three
silent drains and 13-row health. String-content Delivery preserves its zero-row
menu with three silent drains and 13-row health. Blob-content Delivery
preserves its header without a total after the measured no-client interval,
with three silent drains and 13-row health, completing the row **[OBS]**.

The extra-argument-Delivery precursor row begins with three ordinary 13-row
precursor menus. Argumentless Play remains a silent timeout, while
missing-content Play returns zero rows and extra-argument Play returns seven.
All three pairs have three silent drains and 13-row health **[OBS]**.

Composer lookup text and Lyricist cap at 127 UTF-16 units. DeliveryComment and
ISRC cap at 255 units. Both paths can split a supplementary character and
expose U+FFFD at their boundary. Null and empty values serialize as empty;
dangling ComposerID remains numeric with empty text. The string length fields
are UTF-16 byte counts including the NUL. DeliveryControl is represented by
arg 8 of item `0x4f` and is 1 exactly when its database string equals `ON`
case-insensitively **[OBS, DEC]**.

Delivery-only cold requests 1-3 use order A; request 4 uses B; requests 5 and 6
use C and D; subsequent requests repeat A/B/C/D. Reversing all 21 controls
makes each selector inherit its new position's order without changing its
composite field. Fresh TCP connections do not reset the counter; Rekordbox
restart does. Interleaving proves this is list-buffer state rather than one
counter: missing Delivery and `0x2202` errors preserve the standalone sequence;
missing Display, missing Play, and populated Play make every following probe
use A; populated Display produces `AAEAEAEA`, where E is
`0002 0f04 0023 000f 004f 0037 0007 000e 0006 0012 000d 0036 000b`.
Every family sequence repeated exactly from a second cold process **[OBS]**.
Repeating all six family sequences on one persistent dbserver TCP connection
produces case arrays exactly equal to the per-case reconnect recordings. The
ordering state is process/builder scoped, not connection scoped **[OBS]**.
Six calls before discovery identity loss produce `AAABCD`; eight calls after
the same RX3 rejoins or RX3 is replaced by CDJ-3000 produce `ABCDABCD`. Both
lifecycles repeat exactly. Discovery expiry, model/class replacement, and Link
reactivation preserve the process-scoped sequence **[OBS]**.

The live root returned these 20 entries in this exact order:

| # | Label | Row ID | Item type | First request | Live count |
| ---: | --- | ---: | ---: | --- | ---: |
| 1 | TRACK | `04` | `83` | `1004 [ctx, sort]` | 4,342 |
| 2 | KEY | `0c` | `8b` | `1014 [ctx, sort]` | 24 |
| 3 | BPM | `06` | `85` | `1006 [ctx, sort]` | 84 |
| 4 | GENRE | `01` | `80` | `1001 [ctx, sort]` | 27 |
| 5 | ARTIST | `02` | `81` | `1002 [ctx, sort]` | 2,203 |
| 6 | ALBUM | `03` | `82` | `1003 [ctx, sort]` | 765 |
| 7 | MATCHING | `1a` | `aa` | `1017 [ctx, sort, track]` | seed-dependent |
| 8 | SEARCH | `12` | `91` | `1300` | query-dependent |
| 9 | PLAYLIST | `05` | `84` | `1105 [ctx, sort, id, kind]` | 8 root rows |
| 10 | HISTORY | `16` | `95` | `1012 [ctx, sort]` | 0 current sessions |
| 11 | BITRATE | `14` | `93` | `1011 [ctx, sort]` | 12 |
| 12 | COLOR | `0f` | `8e` | `100d [ctx, sort]` | 8 |
| 13 | FILE NAME | `15` | `94` | `1013 [ctx, sort]` | 4,342 |
| 14 | HOT CUE BANK | `17` | `98` | `2001 [ctx, selector, mode, count]` | fixture-dependent |
| 15 | LABEL | `0a` | `89` | `100a [ctx, sort]` | 353 |
| 16 | ORIGINAL ARTIST | `0b` | `8a` | `1302 [ctx, sort]` | 0 referenced |
| 17 | RATING | `07` | `86` | `1007 [ctx, sort]` | 2 |
| 18 | REMIXER | `09` | `88` | `1602 [ctx, sort]` | 540 |
| 19 | TIME | `13` | `92` | `1010 [ctx, sort]` | 12 |
| 20 | YEAR | `08` | `87` | `1008 [ctx, sort]` | 5 decades |

The root labels are protocol localization tokens, not authoritative display
strings. A player recognizes the item type and renders its localized label.
The row ID in this table is `djmdCategory.ID`; it is distinct from
`djmdCategory.MenuItemID`. The latter selects the label/class and capability
bit. `GetRootMenu` always skips menu item 24 (Folder), leaving it available only
inside Playlist navigation. With the exact legacy mask `00ffffff`, it appends
category ID 23 / menu item 18 (Hot Cue Bank) when that item was absent from the
normal query **[RE, DB]**.

## Sort menu

The observed sort menu contains 11 rows in this order. The row ID is the sort
argument subsequently sent with a track-list query.

| # | Sort | ID | Item type | Database basis |
| ---: | --- | ---: | ---: | --- |
| 1 | default | `00` | `a1` | Context-defined order |
| 2 | track name/alphabet | `01` | `a2` | `djmdContent.Title` |
| 3 | artist | `02` | `81` | `djmdArtist.Name` |
| 4 | album | `03` | `82` | `djmdAlbum.Name` |
| 5 | BPM | `04` | `85` | `djmdContent.BPM` |
| 6 | rating | `05` | `86` | `djmdContent.Rating` |
| 7 | key | `0c` | `8b` | `djmdContent.KeyID` / `djmdKey` |
| 8 | label | `0a` | `89` | `djmdContent.LabelID` / `djmdLabel` |
| 9 | genre | `06` | `80` | `djmdContent.GenreID` / `djmdGenre` |
| 10 | date added | `11` | `8c` | `djmdContent.StockDate` |
| 11 | DJ play count | `10` | `97` | `djmdContent.DJPlayCount` |

The server may advertise a configured subset, but IDs must retain these wire
values. Sort availability and secondary-column selection are separate settings.

## Complete menu graph

`sort` below is the selected sort ID. Each selector after it is an ID returned
by the preceding menu. `ALL` means `ffffffff`.

| Browser path | Requests |
| --- | --- |
| All tracks | `1004 [ctx, sort]` |
| Key → related range → tracks | `1014 [ctx, sort]` → `1114 [ctx, sort, key]` → `1214 [ctx, sort, key, distance]` |
| BPM → tolerance → tracks | `1006 [ctx, sort]` → `1106 [ctx, sort, bpm]` → `1206 [ctx, sort, bpm, distance]` |
| Genre → artist → album → tracks | `1001` → `1101 [ctx, sort, genre]` → `1201 [ctx, sort, genre, artist|ALL]` → `1301 [ctx, sort, genre, artist|ALL, album|ALL]` |
| Artist → album → tracks | `1002` → `1102 [ctx, sort, artist]` → `1202 [ctx, sort, artist, album|ALL]` |
| Album → tracks | `1003` → `1103 [ctx, sort, album]` |
| Matching tracks | `1017 [ctx, sort, seed_track]` |
| Search | `1300 [ctx, sort, utf16_bytes, text, 0]` |
| Folder / playlist | `1105 [ctx, sort, parent_id, 1]`; playlist tracks use the same kind with `[ctx, sort, playlist_id, 0]` |
| History → tracks | `1012` → `1112 [ctx, sort, history]` |
| Bitrate → tracks | `1011` → `1111 [ctx, sort, bitrate]` |
| Color → tracks | `100d` → `110d [ctx, sort, color]` |
| File name | `1013 [ctx, sort]` |
| Hot Cue Bank folder/bank tree | `2001 [ctx, parent_id, 1, 0]`; root uses parent 0 |
| Hot Cue Bank tracks | `2001 [ctx, bank_id, 0, requested_count]` |
| Label → artist → album → tracks | `100a` → `110a` → `120a` → `130a` with the accumulated selectors |
| Original artist → album → tracks | `1302` → `1402` → `1502` |
| Rating → tracks | `1007` → `1107 [ctx, sort, rating]` |
| Remixer → album → tracks | `1602` → `1702` → `1802` |
| Time → tracks | `1010` → `1110 [ctx, sort, minute_bucket]` |
| Release year → decade/year → tracks | `1008` → `1108 [ctx, sort, decade]` → `1208 [ctx, sort, year]` |

The populated request families in this table were observed live. History and
Original Artist returned valid empty roots in the original bounded capture.
The deterministic full fixture subsequently proved the populated Original
Artist hierarchy: one referenced artist, an album menu containing ALL plus
three albums, and three tracks beneath a concrete album selector. The empty
fixture independently records a zero-row root. Hot Cue Bank was similarly
proven with a dedicated populated fixture. Search was captured with a separate
focused probe rather than by the bounded tree walker.

### Observed request signatures

`C` is context, `S` is sort, and all other IDs are values returned by the
parent menu.

| Kind | Arguments | Result row type |
| ---: | --- | ---: |
| `1000` | `C,S,05cfffff` | root-specific |
| `1001` | `C,S` | genre `06` |
| `1002` | `C,S` | artist `07` |
| `1003` | `C,S` | album `02` |
| `1004` | `C,S` | track `0f04` |
| `1006` | `C,S` | BPM `0d` |
| `1007` | `C,S` | rating `0a` |
| `1008` | `C,S` | release year `11` |
| `100a` | `C,S` | label `0e` |
| `100d` | `C,S` | color `14`–`1b` |
| `1010` | `C,S` | duration `0b` |
| `1011` | `C,S` | bitrate `10` |
| `1012` | `C,S` | history `24`; empty in the bounded capture, populated by the lifecycle oracle |
| `1013` | `C,S` | track `0f04`, filename primary |
| `1014` | `C,S` | key `0f` |
| `1017` | `C,S,seed_track` | track `0f04` |
| `1018` | `C,S` | rejected guessed route; `4003` error |
| `1101` | `C,S,genre` | artist `07` / ALL `a0` |
| `1102` | `C,S,artist` | album `02` / ALL `a0` |
| `1103` | `C,S,album` | track `0f04` |
| `1105` | `C,S,node,folder_flag` | folder `01`, playlist `08`, or track `0f04` |
| `1106` | `C,S,bpm_x100` | BPM distance `0d` |
| `1107` | `C,S,rating` | track `0f04` |
| `1108` | `C,S,decade` | release year `11` / ALL `a0` |
| `110a` | `C,S,label` | artist `07` / ALL `a0` |
| `110d` | `C,S,color` | track `0f04` |
| `1110` | `C,S,minute_bucket` | track `0f04` |
| `1111` | `C,S,bitrate` | track `0f04` |
| `1112` | `C,S,history` | track `0f04` in insertion order |
| `1114` | `C,S,key` | related key `0f` |
| `1201` | `C,S,genre,artist` | album `02` / ALL `a0` |
| `1202` | `C,S,artist,album` | track `0f04` |
| `1206` | `C,S,bpm_x100,distance` | track `0f04` |
| `1208` | `C,S,decade,year` | track `0f04` |
| `120a` | `C,S,label,artist` | album `02` / ALL `a0` |
| `1214` | `C,S,key,distance` | track `0f04` |
| `1300` | `C,S,utf16_bytes,text,0` | mixed typed search results |
| `1301` | `C,S,genre,artist,album` | track `0f04` |
| `1302` | `C,S` | original artist `07`; empty in the bounded capture, populated by the full fixture |
| `130a` | `C,S,label,artist,album` | track `0f04` |
| `1402` | `C,S,original_artist` | album `02` / ALL `a0` |
| `1502` | `C,S,original_artist,album` | track `0f04` |
| `1602` | `C,S` | remixer `29` |
| `1702` | `C,S,remixer` | album `02` |
| `1802` | `C,S,remixer,album` | track `0f04` |
| `2001` | `C,selector,mode,count` | folder `01`, bank `2b`, or track `0f04` |

## Category details and database mapping

Unless a section says otherwise, content predicates include
`djmdContent.rb_local_deleted = 0`. Lookup, membership, and relation rows must
also be live before joining them back to live content; otherwise stale deleted
relationships leak into menus. Rekordbox sends the actual `master.db` IDs for
lookup entities, not a dense per-process index.

### Track and File Name

`1004` returns one track row per live `djmdContent` record. Its primary text is
`Title`. `1013` returns the same content IDs and track-row shape but labels the
row with `FileNameL`. Both accept a sort ID. Default Track order is
title-alphabetic; File Name order follows `FileNameL`.

Before row insertion, ordinary track surfaces reject a row exactly when the
active streaming-provider registry recognizes its `FolderPath` protocol.
Collection, File Name, ordinary playlist, Smart playlist, and Search share the
measured filter. Windows AppSync persisted History uses a separate direct
content-row builder with no `FolderPath` read and returns the controlled
streaming rows; the pinned macOS History function instead applies the helper.
This gate neither tests media-file existence nor sets the later compatibility
bit; `LINK_EXPORT_VISIBILITY_ORACLE.md` contains the fourteen-path matrix and
both platform code paths **[OBS, DEC]**.

The 20-row filename fixture records all sort IDs 0-17 and nine exact order
classes. Every sort retains `FileNameL` as primary text. Extensions, leading
dots, trailing dots, multiple dots, forward slashes, and backslashes are
literal; neither `FileNameS` nor any path basename replaces the value. Embedded
NUL truncates the visible string. Null and empty both serialize as an empty
string with byte-length argument 2 **[OBS, DB]**.

The primary string is capped at 255 UTF-16 code units. Inputs of 254 and 255
units survive exactly; a 256-unit ASCII value is truncated to 255. A 256-unit
value made from 128 supplementary characters is cut after the high surrogate
of its final pair, which JUCE serializes as U+FFFD. Argument 2 is always twice
the rendered UTF-16-unit count plus its terminating NUL. The exact order and
row payloads are retained in `filename-boundaries.json` **[OBS]**.

The content table supplies the fields needed to build a track row:
`ID`, `Title`, `FileNameL`, `ArtistID`, `AlbumID`, `GenreID`, `BPM`, `Length`,
`BitRate`, `Rating`, `ReleaseYear`, `RemixerID`, `LabelID`, `OrgArtistID`,
`KeyID`, `StockDate`, `ColorID`, `DJPlayCount`, `Commnt`, and deletion state.
Only live content rows should be served.

### Key

`1014` normalizes the library to 24 harmonic positions even though this database
contains 42 historical or spelling variants in `djmdKey`. The first menu row's
ID is the normalized key ID. `1114` returns three widening choices with
distances 0, 1, and 2; `1214` uses the selected distance to return tracks.
Distance 0 is the selected key only; distance 1 adds its relative major/minor;
distance 2 adds the neighboring wheel keys for four categories total.

**Database.** Join `djmdContent.KeyID` to `djmdKey.ID`, normalize its musical
value/spelling, then compare in harmonic-wheel space. Raw database IDs are opaque and
must not be mistaken for the 1–24 wire key index carried later in a track row.
The controlled 7.2.19 LAN labels follow the local CDJ key-category display
style in `DEVSETTING.DAT`. Style 1 yields Classic (`Abm`, `B`, through `E`);
style 2 yields canonical Alphanumeric/Camelot (`1A`, `1B`, through `12B`). The
style changes roots, distance labels, Key/BPM composite text, tertiary Key,
Display Song Info, and Delivery Info, but does not change numeric IDs or sort
order. Four restart-isolated desktop preference states separately prove that
`KeyStringSetting` and `ShowOriginalKey` do not directly alter these responses.
The exact crosses and file format are in `KEY_NOTATION_ORACLE.md`.

### BPM

`1006` returns distinct nonzero BPM values rounded half-up to whole BPM and
sent ×100. The database-equivalent normalization is
`((BPM + 50) / 100) * 100` using integer division. This exactly produces the 84
live rows; raw distinct values produce 272 and flooring produces 92. Rekordbox
accepts raw values through 49,949 for this root and excludes zero. `1106`
returns tolerance IDs 0 through 6 for a chosen BPM. Rekordbox's range table
labels these as ±0 through ±6 percent. `1206` uses a special zero case: it
rounds the selected value to a whole BPM and accepts the inclusive interval
`[rounded - 50, rounded + 49]`. Nonzero tolerance `p` uses signed integer bounds
`(100 - p) * BPM / 100` and `(100 + p) * BPM / 100`, truncating toward zero,
and accepts both endpoints **[DB, DEC]**.

The selector rows rely on item type `0d` and numeric values; their visible
labels can be blank because the player formats BPM and range text itself. The
43-track below/exact/above dynamic edge matrix is complete **[OBS]**.
Tolerance zero includes `119.50..120.49` around 120.00 BPM; tolerances 1
through 6 include both integer-truncated endpoints and exclude the immediate
one-hundredth outside neighbors. The nested totals are
`5, 11, 17, 23, 29, 35, 41`.

### Genre

The full path is genre → artist → album → track. Genre rows come from referenced
`djmdGenre` records. Artist and album rows are constrained through
`djmdContent.GenreID`; selecting ALL at either intermediate level leaves that
dimension unconstrained. Empty/deleted content and unreferenced lookup rows do
not belong in the live menu.

### Artist and Album

Artist rows are the distinct referenced `djmdArtist` records. An artist's album
menu contains the distinct `djmdAlbum` rows referenced by that artist's content
and prepends ALL only when there is more than one. Album root similarly includes
referenced albums, and `1103` filters `djmdContent.AlbumID` directly.

The live artist count, 2,203, exactly matched distinct referenced ArtistIDs in
the database. Album named rows repeat their ID in row argument 8. Default
album-specific track lists are ordered by `djmdContent.TrackNo`, which is also
sent in track-row argument 9. This behavior carries through artist, genre,
label, and remixer paths after selecting a concrete album. ALL-albums scopes
send zero in argument 9.

### Matching

`1017 [ctx, sort, seed_track_id]` directly returns tracks related to the seed.
For seed `245834041`, the live response contained the single content ID
`264286423`, “Martini’s & Mixed Feelings.”

**Database.** The relationship is `djmdRecommendLike(ContentID1, ContentID2,
LikeRate, ..., rb_local_deleted)`. It is not the similarly named
`djmdRelatedTracks` feature, which stores Rekordbox UI related-track presets.
The local database contained eight live recommendation pairs.

Reverse engineering confirms a bidirectional scan: if either endpoint equals
the seed, the other endpoint is returned. `LikeRate` is not read. The related
content IDs then go through the ordinary requested sort; default uses title and
creation order. **Unknown:** whether another Rekordbox version supplements the
stored pairs with computed matches.

### Search

The observed request was:

```text
1300 [ctx, sort, utf16_byte_length_including_nul, uppercase_text, 0]
```

`ABITAN` therefore has length 14, not 12. Sending the length without the NUL
caused Rekordbox to reject/close the session.

Search results are heterogeneous. `ABITAN` returned an artist heading followed
by track rows. Those track rows used filenames as primary text, key as the
secondary column, and composite type `0f04`. A search implementation must not
assume every result is a track.

Rekordbox splits the UTF-16 query on spaces and stops at the NUL. Its visible
category mask enables Artist (menu ID 2), Album (3), Track/Content (4), and File
Name (16), producing genuine mixed rows of types `07`, `02`, and `04`/composite
track. Filename search/display mode strips the extension, unlike the standalone
File Name category captured above. The 160-case Search oracle proves token
intersection, mixed-domain grouping order, ASCII-only folding, Unicode and NUL
behavior, all sort IDs, category gates, pagination, and result ceilings. The
fifth request argument is tolerated and ignored for tested values 0, 1, and
`0xffffffff`; it does not enable `SearchStr`, Comment, or the DOS short-name
column. Tie-breakers beyond the deterministic eight-row orders and populations
above the tested 10,005-row explicit-sort result remain unmeasured. See
`SEARCH_ORACLE.md` **[OBS, DB, DEC]**.

### Playlist

`1105 [ctx, sort, parent_id, 1]` returns children of a folder, starting with
parent 0. Folder rows have item type `01`; playlist rows have type `08`.
Argument 9 carries their ordering position. A folder is opened recursively with
kind 1. A playlist is opened with the same request kind and kind 0, returning
tracks. The database contained 121 live folder/playlist records and eight root
children.

**Database.** Hierarchy and ordering come from `djmdPlaylist`. Ordinary
playlist membership and default track order come from
`djmdSongPlaylist.TrackNo`. Preserve explicit sequence numbers rather than
alphabetizing the default view.

`djmdPlaylist.Attribute = 4` switches track serving to the `SmartList` rule.
The deterministic smart fixture proves this independently of ordinary
membership: a rule-only House playlist returns all four House tracks; a second
House rule returns the same four rows despite materialized membership that
contains only Techno tracks. Malformed or null rules return empty even when
`djmdSongPlaylist` contains rows. An `Attribute = 0` playlist with the same
valid rule is also empty without membership. The database remains byte-for-byte
unchanged after Rekordbox startup and both oracle runs, so this is not a
persisted rematerialization side effect **[OBS, DB]**.

Smart rows at the root use the same item type `08` and sequence field as
ordinary playlists. The request's final `folder_flag`, rather than the stored
attribute, still chooses child-list (`1`) versus track-list (`0`) dispatch.
`smart-playlists.json` records all twelve controls and an immediate repeat.

The independent 39-case `smart-rule-matrix.json` records exact ordered results
for codes 1-11 over Genre and decimal BPM inputs, root all/any, nested-node controls,
empty groups, invalid operators/properties, multiple roots, and missing or
unknown root metadata. Genre confirms equal/not-equal and
contains/not-contains/starts-with/ends-with for codes 1, 2, and 8-11; codes 3-7
return empty on text. Empty all and any groups both return empty. Nested nodes
are ignored; only direct `CONDITION` children are evaluated. A condition before the root is ignored, the first
of two roots wins, and missing/unknown `LogicalOperator` behaves as all-of.
`AutomaticUpdate` and root `Id` do not gate serving **[OBS, DB]**.

The 73-case XML matrix and `getSmartlistContentData`/`getSmartlistNode`
disassembly define the parser boundary. Element names are case-insensitive,
attribute names are case-sensitive, duplicate attributes use the first value,
and integer attributes accept signs, surrounding whitespace, and leading
zeroes. Only direct `CONDITION` children are collected. Unknown, wrapped, and
nested elements are skipped; zero collected conditions produce an empty menu.
Declarations, comments, processing instructions, numeric character references,
the first of multiple roots, and trailing text/NUL are accepted. A BOM,
leading text/NUL, namespaces, invalid entities, and the measured incomplete
forms are rejected into the same ordinary empty-menu outcome **[OBS, DB, DEC]**.

For `myTag`, only operators 8 and 9 are applicable. They test membership and
non-membership against the track's tag-ID array; operators 1-7, 10, and 11
return a normal empty menu. The XML value uses signed 32-bit integer parsing:
positive overflow saturates at `INT32_MAX`, negative overflow at `INT32_MIN`,
and negative values address unsigned tag IDs by their 32-bit bit pattern.
Blank differs from malformed text: blank produces empty results for both
operators, while malformed nonblank text becomes zero. `ValueRight` and
`ValueUnit` are ignored. All/any groups compose these predicates normally.
The live 49-case matrix and `db::operate`/parser disassembly agree on these
semantics **[OBS, DB, DEC]**.

The rule result then enters the ordinary track-serving stages. A 65-case live
cross proves all request sort IDs 0-17, the render gate and selectors 2-17,
the complete pagination boundary matrix, and requester/location/slot context
validation on a rule-only eight-track playlist. A separate legacy setup case
proves the same result serializes as 12 rather than 16 row arguments. Exact
orders, item types, and edge outcomes are in `SMART_PLAYLIST_ORACLE.md`
**[OBS, DB]**.

Search is not a child operation of `0x1105`: ordinary Search `0x1300` and
Search Track `0x1500` contain query data but no playlist ID, while playlist
request `0x1105` contains a playlist ID but no query field. The server protocol
therefore exposes global Search and playlist serving as separate paths
**[OBS]**.

Decimal BPM values are compared against the stored integer domain. With stored
BPM values 12000-12350, `121.5` yields empty for equality, every track for
not-equal and greater-than, and empty for less-than/range. Do not silently
convert the XML value from display BPM by multiplying it by 100 **[OBS, DB]**.

The 60-case stored-numeric matrix then measures codes 1-5 over BPM, Rating,
Play Count, Duration, and Year. Code 1 is equal, 2 not-equal, 3 strictly
greater, 4 strictly less, and 5 an inclusive range whose endpoints must be in
ascending order; every reversed range returns empty. Empty and malformed
numeric strings coerce to zero. Negative BPM thresholds retain their sign, and
values above signed 32-bit remain positive rather than wrapping. The exact
ordered sets are in `SMART_PLAYLIST_ORACLE.md` **[OBS, DB]**.

The 33-case property matrix covers all 23 written SmartList property names.
Controlled conflicts establish that `dateCreated` uses `DateCreated` rather
than the audit `created_at` field, `mixName` uses `Subtitle`, and `producer`
uses the composer/producer relation. Custom `myTag` values match raw positive
tag IDs; subtracting 2^32 produces empty results for the same memberships.
Lowercase `filename` is accepted alongside `fileName`, while the controlled
`title`, `color`, `playCount`, `remixer`, and `composer` aliases return empty.
The complete property-to-row map is in `SMART_PLAYLIST_ORACLE.md` **[OBS, DB]**.

For `stockDate`, `dateCreated`, and `dateReleased`, codes 1-5 have identical
fixed-date semantics: equal, not-equal, strict later-than, strict earlier-than,
and inclusive ordered range. Reversed ranges return empty. Blank and malformed
track values fail both equal and not-equal; they are excluded before the
comparison operator is applied. Blank or malformed rule values likewise
produce equality-empty and an inequality result containing only parseable
track dates. Exact sets are in `SMART_PLAYLIST_ORACLE.md` **[OBS, DB]**.

Codes 6 and 7 use a single lower boundary for all three date properties. At a
controlled `2032-03-31` clock, singular `month` and uppercase `MONTH` use
calendar-month arithmetic; every other tested unit spelling uses a day count.
`ValueRight` is ignored. Operator 6 includes future dates, operator 7 selects
parseable dates older than the lower boundary, and invalid track dates match
neither. Zero, negative, blank, malformed, and fractional count strings share
the zero-count result. The 56 exact sets and clock provenance are in
`SMART_PLAYLIST_ORACLE.md` **[OBS, DB, DEC]**.

The fixed-date parser has a narrower syntactic gate and a broader semantic
acceptance than ISO 8601. It requires exactly 10 characters, consumes year at
positions 0-3, month at 5-6, and day at 8-9, and ignores positions 4 and 7.
It does not test the consumed characters for ASCII digits. The resulting year,
month, and day are passed through the platform calendar conversion, which
normalizes overflow values. Slash, dot, space, ASCII-letter, Unicode, and
newline separators therefore compare identically to hyphens. Month 0/13/99,
day 0/32/99, invalid leap/calendar days, and `202A-01-31` all survive in the
117-case oracle. Wrong-length strings and conversions yielding a nonpositive
day are excluded before the comparison operator. Embedded NUL and SQL `NULL`
track values match neither canonical equality nor inequality. Exact sets and
the static/live cross-check are in `SMART_PLAYLIST_ORACLE.md` **[OBS, DB, DEC]**.

The 55-case Comments matrix measures codes 1, 2, and 8-11 against 43 controlled
strings. Equality is insensitive to ASCII case, accents, fullwidth forms,
hiragana/katakana, and the tested Angstrom variants. Greek sigma and final
sigma share an equality class; Turkish dotted I joins ASCII I, while dotless I
does not. Sharp-S and AE expansions are pattern-direction-dependent: the
ligature or sharp-S rule admits its expanded spelling, while the expanded rule
does not admit the compact spelling. Punctuation, spaces, tabs, and newlines
remain significant. XML entities decode normally, supplementary emoji work at
prefix/suffix boundaries, and a database string is truncated at an embedded
NUL. Empty equality admits both empty and SQL `NULL`; empty inequality admits
every nonempty row; empty contains/not-contains/starts/ends all return empty.
The ICU 51 US-locale `StringSearch` construction and primary-strength collator
are preserved in `smart-collation.disasm.txt`; exact sets and asymmetric
normalization cases are in `SMART_PLAYLIST_ORACLE.md` **[OBS, DB, DEC]**.

The same string engine applies to all 13 written string properties. A
104-case cross uses identical values for `artist`, `album`, `albumArtist`,
`originalArtist`, `producer`, `genre`, `key`, `label`, `remixedBy`, `comments`,
`fileName`, `mixName`, and `name`; every property returns the same ordered set
for equality, inequality, contains, not-contains, prefix, suffix, empty
equality, and empty inequality. Empty lookup names agree with direct empty
strings, while relation ID zero agrees with direct SQL `NULL`. Lookup absence
therefore enters the same comparison domain rather than excluding the track
before string evaluation **[OBS, DB]**.

### History

`1012` returns Link session histories; `1112` returns the selected session's
tracks. The live root was empty during this capture even though the database
contains 589 ordinary history records.

**Database/RE.** Relevant tables are `djmdHistory` and `djmdSongHistory`, but
Rekordbox also has an active Link-history lifecycle (`djeplMakeNewHistory`,
`djeplInsertSong2History`, deletion, and root/track getters). Players notify the
source when they load tracks. A server therefore needs a current-session
catalog layered over persistence; blindly listing every historical database row
does not reproduce the observed root. The low-level getters themselves do not
show an explicit “active only” predicate, so the distinction is the
Link-facing/materialized database context rather than a query over every
ordinary history row.

The repeat-verified ten-step lifecycle fixes the active behavior **[OBS]**:

1. A fresh process starts with an empty `1012` root.
2. `3001(context, content_id)` creates the current history on the first insert
   and appends later tracks without a reply.
3. The created root is named `LINK HISTORY YYYY-MM-DD`; on 2026-09-30 its row
   had item type `0x24`, an empty secondary string, and a process-generated ID.
4. `1112(context, sort, returned_history_id)` preserves insertion order and
   numbers track rows from one.
5. `3401(context, content_id)` returns a zero-total header, removes that track,
   and closes the ordinal gap in the next `1112` result.
6. `3101(context, returned_history_id)` deletes the current history without a
   reply; the following root is empty.

The same mutation path owns played presentation state. Static control flow
maps Link-history add/remove notifications to `RowDataTrack` bit `0x10`, then
refreshes the DB server's Link-played ContentID snapshot. The declaration in
`conformance/suites/link-played-state.json` observes argument-7 bit `0x100`
and direct `0x3b03` replies before and after `3001`, `3401`, and `3101`.
Expected transitions remain unset until guarded generation `ah18` promotes its
real-Windows record and independent repeat **[DEC]**. The reducer preserves the
observed scalar and row-bit channels without supplying inferred values.

Generation `ai18` then crosses the same two channels over a clean process
restart for all four `PlayedTrackOption`/`LinkPlayedTrackOption` combinations.
It retains the actual `AnotherHistories.xml` tree and separate process IDs, so
the eventual persistence rule will be based on real Rekordbox rather than the
static option-gate interpretation **[DEC]**.

Generation `aj18` isolates Link-server refresh from application restart. It
uses an uninterrupted control plus a same-process LINK deactivate/reactivate
arm, proves listener disappearance and return, and queries the primed and
unprimed ContentIDs through both protocol representations. Expected post-toggle
state remains unset until the real-Windows golden is promoted **[DEC]**.

Generation `ak18` tests ownership across two simultaneous RX3 requester
identities. The four player-correct suites alternate insert and remove
operations while both `0x3b03` and argument-7 bit `0x100` are observed before
and after every mutation. Static storage appears global, but the dynamic oracle
intentionally leaves global, partitioned, and asymmetric outcomes admissible
until real Rekordbox promotes the timeline **[DEC]**.

The complete sequence was repeated after reinstalling the fixture and
restarting Rekordbox. Only the generated history ID was canonicalized. The
remaining lifecycle boundary is narrower: Cross-day rollover, survival across
a Rekordbox restart without first deleting the history, and simultaneous
multi-player ownership/partitioning have not been exercised. No broader
rollover or persistence rule should be inferred from the date-named row.

### Bitrate

`1011` returns distinct `djmdContent.BitRate` values in kbps using item type
`10`; `1111` returns matching tracks. The live library exposed 12 values.
Zero is a real bucket and covered 50 tracks in this database. Numeric rows may
have blank text because the player formats the value. The exact descending set
was 2304, 2116, 1536, 1411, 320, 256, 224, 192, 160, 128, 32, and 0.
The deterministic selector matrix records every fixture bucket: direct values
0, 32, 128, 160, 192, 256, 320, and 1411 each return their equality-matched
track; absent 1 returns zero. A boundary track carrying `INT32_MAX` is omitted
from the root, and direct selector `2147483647` also returns zero despite the
stored match. `0xffffffff` likewise returns zero **[OBS, DB]**.

### Color

`100d` returns the eight fixed color IDs, backed by `djmdColor`. Display text is
`djmdColor.Commnt`, ordered by `SortKey`/ID; it is not the table's `Name` field.
`110d` filters on `djmdContent.ColorID`, and uncolored ID 0 is excluded. The
live row mapping was Pink `14`, Red `15`, Orange `16`, Yellow `17`, Green `18`,
Aqua `19`, Blue `1a`, and Purple `1b`. All eight palette rows are returned even
when a particular color has zero tracks. The player owns their visual
presentation and localization.
Direct selection is broader than root advertisement in one special case:
`110d [..., 0]` returns tracks whose `ColorID` is 0 even though the root never
contains a zero row. IDs 1-8 each select their corresponding tracks. A dangling
stored/reference ID `999999`, direct 9, and `0xffffffff` return empty menus
**[OBS, DB]**.

### Hot Cue Bank

The root advertises HOT CUE BANK with category ID `17` and item type `98`.
Its catalog request is the separate command-family kind `2001`:

```text
2001 [context, selector, mode, requested_track_count]
```

Mode 1 lists the immediate `djmdHotCueBanklist` children of `selector`; selector
0 is the root. Attribute 1 renders item type `01` (folder), while Attribute 0
renders `2b` (bank leaf). Rows carry database ID, Name, and Seq. Deleted nodes
are excluded and leaves used as parents return valid empty menus.

Mode 0 lists a bank's `djmdSongHotCueBanklist` memberships in signed `TrackNo`
order. The fourth argument caps the candidate array but is floored to 3:
0/1/2/3 returned 3, 4 returned 4, 5 returned 5, 8 returned 8, and 16 returned
all 10 resolvable fixture memberships. Duplicate memberships and even a
membership marked locally deleted survive. Soft-deleted or dangling content is
removed when each membership is resolved through the live content getter.
Argument 9 carries membership TrackNo; stored -1 sorts before 0 and renders as
unsigned 65535. Unknown selectors and modes other than 0/1 return normal empty
menus **[OBS, DB, DEC]**.

A 70-membership bank proves ordinary render paging is independent of that
catalog cap. Page sizes 1 and 32 and explicit 32/32/6 windows return the same
ordered rows. Zero render count becomes one; end and past-end offsets clamp to
the final row; overrun windows are right-aligned; overlaps duplicate rows; and
offset `0xffffffff` times out after the successful total header **[OBS]**.

Counts 17, 255, 256, 65535, 65536, and 1048576 also return the same ten rows
and repeat exactly. `0x7fffffff` also returns those ten rows, while
`0x80000000` and `0xffffffff` return successful empty menus; all three repeat
after independent restarts without a new application error or an unresponsive
process. The active AppSync implementation applies unsigned `max(count, 3)`
and then compares the loop index to that word as a signed integer. Thus bit 31
is the exact behavioral boundary. There is no 8-bit/16-bit narrowing, and the
active path does not allocate memory proportional to the requested count
**[OBS, RB-DEC]**.

The old `1018 [context, sort]` probe remains a rejected-route control and
returns `4003`; it does not describe empty Hot Cue Bank behavior. Locations 1,
2, 3, and 7 all return the same header total and matching-location rows. Each
accepts both the legacy render
`3000 [context, offset, limit, 0, total, 0]` and RX3 render
`3000 [context, offset, limit, 0, total, 12, 1, secondary]`. Menu buffers are
process-wide and keyed by location: rendering an uninitialized location times
out, while rendering a previously populated foreign location returns that
location's stale rows across a fresh TCP connection. The current header total
bounds the stale-buffer window. Exact rows, the full 4 x 4 x 2 cross, ordered
state proof, dispatch addresses, XDJ-RR call sites, and fixture hashes are in
`HOT_CUE_BANK_ORACLE.md` **[OBS, DEV-DEC]**.

A matched-status 84-case matrix crosses the `0x2001` root, populated bank, and
empty bank over types `0x00..0x06`, authentic RX3 and derived CDJ-3000 status
controls, and both setup widths. Type `0x01` returns totals 3/8/0; every other
type returns a total-50
header and then times out after emitting no rows for a 32-row render. RX3 and
CDJ-3000 are identical after requester normalization, and legacy rows are exact
12-field prefixes of extended rows **[OBS]**.

Cue information uses the direct-response request `2101 [context, bank_id]` and
returns `4702`. Static handlers resolve cue numbers 1-3 from membership
`TrackNo`; the master-database path follows `CueID` into `djmdCue`, while the
live Windows AppSync path reads `djmdSongHotCueBanklist` directly. A conflicting
paired fixture proves the latter supplies the observed payload. Rekordbox
serializes up to three 36-byte cue records plus 8-byte millisecond extensions.
The nine reply arguments include the echoed
`2101`, status zero, cue-blob length/blob/36-byte stride/count, and extension
status/length/blob. Alpha Bank returns three records, Root Bank returns two,
and empty or invalid selectors return an empty `4702`. Compact/fixed tags,
legacy/extended setup, RX3/RR models, keepalive/status identities, and stateful
catalog navigation have identical decoded payloads. See `HOT_CUE_BANK_ORACLE.md` **[OBS,
DB, DEC]**.

### Label

The four-level path is label → artist → album → track, with ALL sentinels at
the intermediate levels. Labels come from referenced `djmdLabel` rows through
`djmdContent.LabelID`; later levels add `ArtistID` and `AlbumID` constraints.
The live root contained 353 referenced labels.

### Original Artist

`1302`, `1402`, and `1502` form original artist → album → track. The lookup is
the artist table referenced by `djmdContent.OrgArtistID`. The deterministic
full fixture returns one root row (`Fixture Original`, ID 1004), followed by
four album rows: the `0xffffffff` ALL sentinel and albums 2001, 2003, and 2002.
A concrete album selector returns tracks 10001, 10003, and 10004. The empty
fixture returns a valid zero-row root **[OBS, DB]**.

### Rating

`1007` returns distinct `djmdContent.Rating` values in the advertised integer
domain 0-5, descending; the player renders stars from item type `0a`. The
deterministic full fixture records all six root values and every `1107`
drilldown. Ratings 0 and 1 each return two tracks; 2-5 each return one. Root
construction suppresses a stored rating 99, but direct selector 99 still
returns that track. Direct 6 and `0xffffffff` return empty menus when no such
row exists **[OBS, DB]**.

### Remixer

`1602`, `1702`, and `1802` form remixer → album → track. Remixers are artists
referenced by `djmdContent.RemixerID`; albums are constrained through the same
content rows. The original library capture contained 540 referenced remixers.
The deterministic full fixture returns one root row (`Fixture Remixer`, ID
1003), followed by the same ALL-plus-three-album shape and the same three
concrete-album tracks as its deliberately paired Original Artist data. The
empty fixture returns a valid zero-row root **[OBS, DB]**.

### Time

`1010` groups `djmdContent.Length` (seconds) into minute buckets using item type
`0b`; `1110` returns tracks in a bucket. The database-equivalent expression is
integer `floor(COALESCE(Length, 0) / 60)`, ordered descending. It exactly
reproduced the 12 live buckets and their counts, including two tracks in bucket
11 and ten in bucket 10. The Rekordbox implementation ignores lengths above
10,799 seconds (179:59); 0–59 seconds maps to bucket 0 and 60 seconds maps to 1.
The captured counts from bucket 11 down to 0 were 2, 10, 39, 120, 405, 926,
1,454, 976, 327, 51, 17, and 15.

### Year

The observed YEAR root is release year, not date added. Its selector item type
is `11`. `1008` groups `djmdContent.ReleaseYear` into decade rows, `1108`
returns years in a decade, and `1208` returns tracks in a year. The live library
had five non-empty decade buckets. Nonzero years through 2999 are grouped as
`floor(year / 10) * 10`; decades and child years are ordered descending. The
18 zero-year tracks were excluded. The 2020s drilldown exactly matched the
database: 2024→23, 2023→17, 2022→107, 2021→147, 2020→239, and ALL→533.

Rekordbox separately contains a date-added family operating on `StockDate`:
`1708` returns distinct years, `1808 [context, sort, year]` returns months,
`1908 [context, sort, year, month]` returns days, and
`1a08 [context, sort, year, month, day]` returns tracks. The selectors are
derived from `djmdContent.StockDate`; `ffffffff` (`-1`) takes explicit wildcard
branches at the lower levels **[DEC, OBS]**. Date Added appeared in the captured
sort menu, not the captured root menu. It must not be substituted for YEAR
merely because both ultimately filter dates.

The newer client enum also names `1308..1608` as Stock Year/Month requests.
Those numbers do **not** reach the `StockDate` query path in Rekordbox 7.2.19.
All four enter `OnYearListCmd`, select its shared invalid-kind branch, return
`-2` to `OnClientReq`, and receive `4003` from `OnUnknownClientCmd`. The
supported `StockDate` browser is exclusively `1708..1a08` in this build
**[DEC]**.

The populated oracle returned years `2024..2020` descending as numeric selector
rows with item type `0x2e`. Year 2021 returned `ALL`, February, and July; the
February drilldown returned `ALL` and day 2. Concrete month/day rows also use
type `0x2e`; `ALL` is ID `ffffffff`, label `\ufffaALL\ufffb`, type `0xa0`.
Requesting days for wildcard month returned only the `ALL` row, while wildcard
day in February returned the same one track as exact day 2 **[OBS]**.
With zero tracks, the year and track stages returned zero rows, but both the
month and day stages still returned one `0xa0` ALL row **[OBS]**.

## Additional recovered request families

This section concerns additional menu builders. The broader command namespace,
including artwork, waveform, cue, beat-grid, VBR, key-analysis, atom,
history/control, rejected, and reply kinds, is specified in
`LINK_EXPORT_REQUEST_VOCABULARY.md`. A command name recovered from player
firmware is not treated as Rekordbox server support without independent static
or live evidence.

`CONTROL_AND_MUTATION_REFERENCE.md` gives the complete adjacent control plane:
all 54 `0x2x05`, `0x2x07`, and `0x3xxx` requests are joined from Rekordbox
dispatch to 97 direct XDJ-RR caller sites. It distinguishes 20 mutation/state
writes, 12 state queries, ten other recognized routes, eight rejections, three
log-only arms, and list-buffer rendering. Missing XDJ-RR callers remain an
explicit device-source gap rather than a cross-device conclusion.

### User info and DJ ID

Request `0x3006 [context]` is the CDJ-3000 `CMD_GET_USER_INFO` exchange.
Rekordbox 7.2.19 accepts exactly that kind in `OnUserCmd` and constructs reply
`0x4d02`. A valid startup DJ ID produces
`[0x3006, 0, 0xa0, blob(160)]`: the first 32 bytes are copied from
`djprofile.nxs` and the remaining 128 bytes are zero. Without a startup DJ ID,
the same reply kind carries `[0x3006, 0, 0, blob(0)]`; the blob argument is
present with zero length **[DEC]**.

The macOS configuration path is
`<user Application Support>/Pioneer/rekordbox6/djprofile.nxs`. The file must
exist, have a case-insensitive `.nxs` extension, be exactly 160 bytes, and pass
the recovered mixed-endian word checksum. CDJ-3000 firmware places this
exchange before `0x2602` Delivery Song Info after load; omitting the reply can
serialize later browsing behind an approximately 18-second timeout and two retries
**[CDJ-DEC, CDJ-OBS]**. `USER_INFO_DJID_ORACLE.md` and
`data/static-analysis/user-info-djid.json` give the full construction,
configuration, client lifecycle, and live-evidence boundary.

### Unsupported newer-client families

The top-level server dispatcher accepts request classes `1xxx`, `2xxx`, and
`3xxx`. Every other high-nibble class goes directly to
`OnUnknownClientCmd`, which emits `4003`. Consequently the CDJ-3000 enum's
`0100` info-drop request, all nine `5000..5202` Top 100/Genres/Curated/My
Playlist provider-browser requests, and `6100` 64-bit-track-ID request have
exact terminal rejection evidence in Rekordbox 7.2.19 **[DEC]**.

This rejection is specific to those command families. Provider-backed rows can
still be exposed through ordinary `1xxx` roots and track lists. Their
`FolderPath` admission is independent of login state in this build: the fixed
manager registry recognizes five service-specific path forms, including a
Beatport `/v4/catalog/tracks/` substring, while its Beatsource slot is null.
Account-conditioned application roots remain a separate oracle boundary.

`XDJ_RR_ADJACENT_COMMANDS.md` supplies that independent static evidence for
the old-Key `100B/110B` menu family, the silent `130C` Cue Track root, every
`2x05` write arm, and the `2107/2507` Rating/BPM mutations. All request kinds
with direct named XDJ-RR callers now have a terminal Rekordbox classification;
the write paths remain live-oracle gaps until isolated mutation fixtures record
their actual transport and persistence behavior.

The list dispatchers expose several families that were absent from the bounded
RX3 traversal. Their shapes come from executable control flow; the populated
fixture results below were recorded and independently repeated where noted
**[DEC, OBS]**:

| Family | Request | Arguments after the kind | Established operation |
| --- | --- | --- | --- |
| DJ Play Count root | `100e` | `context, sort` | Distinct play-count selector rows; observed IDs 0–7 ascending, type `0x2a`, empty labels |
| DJ Play Count tracks | `110e` | `context, sort, play_count` | Tracks whose `DJPlayCount` equals the one-byte selector; 255 returned an empty menu |
| Prepare | `100f` | `context, sort` | Tracks in `djmdSongTagList`; sort 0 used membership `TrackNo`, Key sort reordered the same members |
| New Key root | `1014` | `context, sort` | Key selectors |
| New Key range | `1114` | `context, sort, key` | Distance/range selectors for one key |
| New Key tracks | `1214` | `context, sort, key, distance` | Tracks within the selected key distance |
| My Tag list | `1015` | `context, sort, selector, mode` | Selector 0/group ID with mode 0 returned hierarchy rows; mode 1 and a leaf selector returned unavailable |
| My Tags on track | `1315` | `context, sort, content_id` | Group and leaf tag rows assigned to one content row; untagged and unknown IDs returned empty menus |

`100f` extracts byte 1 from the packed context before calling the Prepare
getter. That byte-dependent behavior remains a matrix dimension even though
the database membership is global. In the observed default ordering, argument
9 carried membership positions 1 then 2 and argument 7 was `0x01000001`.
Key sort changed argument 0 to converted key values 14 and 15 and reordered the
tracks, while preserving those membership-position fields **[OBS]**.

`1315` is particularly easy to mis-model: its selector is a content ID and its
result domain is tags. Group rows use item type `0x01` with the group ID in
arguments 0 and 1. Leaf rows use type `0x4a`, parent group ID in argument 0,
and leaf ID in argument 1. Root/group browse rows use type `0x4a`; their names
are in argument 3. The observed mode-1 response was `4000` count `ffffffff`,
the unavailable sentinel **[OBS]**.

An otherwise empty `djmdMyTag` table is not a stable database state. On first
startup rekordbox persisted four factory groups and 24 leaves. The empty oracle
root returned the four groups in sequence: `1 Genre`, `2 Components`,
`3 Situation`, and `4 Untitled Column`, all type `0x4a`. The fixture now includes
the complete observed factory tree, so subsequent starts leave the table
unchanged. A tags-on-missing-track request returns a valid zero-row menu
**[DB, OBS]**.

## Rekordbox implementation corroboration

Symbols in the Rekordbox 7.2.19 x86-64 binary independently identify getters
for these families:

| Family | Symbol evidence |
| --- | --- |
| Bitrate | `djeplGetBitrate_Root`, `djeplGetTrack_Bitrate` |
| Track / filename | `djeplGetTrack_Root`, `djeplGetFileName_Root` |
| Playlist | playlist list and track getters |
| Album | album root and track getters |
| Genre | root, artist, album, and track getters |
| Artist | root, album, and track getters |
| Key | root/range/track getters, plus a second “NewKey” family |
| Search | `djeplGetNewSearchResult` |
| Label | root/artist/album/track getters |
| BPM | root/range/track getters |
| Date added | root and track getters |
| Release year | decade/year/track getters |
| History | root/track getters plus create/insert/delete lifecycle |
| Color | root/track getters |
| DJ play count | root/track getters |
| Length | root/track getters |
| Rating | root/track getters |
| Matching | `djeplGetTrack_Matching` |
| Prepare | dispatcher plus `Dsql_GetPrepareList` and `DsqlContent_GetPrepareList` |
| My Tag | dispatcher plus `Dsql_GetMyTag` and `Dsql_GetMyTagOnTrack` |

Function signatures corroborate selector counts and the repeated sort byte, but
they are not treated as a substitute for a wire capture. Hot Cue Bank has no
ordinary `djepl` family; its dedicated `OnCueBnkCmd` / `GetHCBnkList` path is
reached by request `2001` and is independently wire-proven.

The same command family includes legacy setter `2201`, extended getter `2301`,
and extended setter `2401`. Live `2301 [context, bank_id, slot_count]` returns
direct reply `4e02 [2301, status, blob_bytes, blob, record_count]`. Records are
self-sized, start with a 56-byte timing/MPEG header, and carry variable color,
microsecond, beat-loop, UTF-16 comment, and seek-option data. Counts through
eight, empty selectors, fixed/compact tags, and isolated field sources are
wire-proven. Live `2401` returns the same `4e02` envelope with echoed kind
`2401`; its canonical record is byte-identical to the immediate `2301`
readback and persists to the membership row through the WAL. Exactly one
matching bank/slot row returns status 50 because the AppSync resolver rejects
`size() == 1`; the successful deterministic fixture uses two same-slot rows and
updates row zero. A 56-case status-backed cross proves packed type `01` alone
admits `2401`; types 00 and 02-06 return
`4e02 [2401, 50, 0, empty_blob, 0]`, and a type-1 getter after every rejected
request proves the database record remains pristine. RX3/CDJ identity and
extended/legacy setup do not change any decoded response. The active `2401`
parser requires one record, at least 56 actual blob bytes, a
non-null four-byte-aligned pointer, slot 1-8, cue type 1 or 2, time unit 75,
150, or 1000, and a nonzero resolved membership CueID. The record-size word at
offset zero is not read. Nonzero option length is bounded against the actual
blob before nested comment and seek fields are parsed. A short optional region
does not reject the fixed header: it skips or defaults the unavailable option
fields and continues the update. The live 56-byte control returns status zero
and persists a 56-byte fixed-only getter record, confirming that permissive
branch **[RB-DEC, OBS]**.

The repeat-verified actual-length boundary is 56 bytes: 0, 1, and 55 return
status 50 without mutation; 56 succeeds and persists a 56-byte fixed-only
record. Inputs of 123, 124, and 125 bytes all succeed and return the same
canonical 124-byte record, so a missing final padding byte and one trailing
byte do not alter the stored result **[OBS, DB]**.

The request's numeric declared-length argument is distinct from the typed
blob's encoded length. With an actual 124-byte blob, declared lengths 0, 55,
56, and 123 return the argument-free generic reply `0100 []`, not a `4e02`
status reply, and leave the getter record pristine. Declared lengths 124 and
125 both return `4e02 [2401, 0, 124, canonical_record, 1]` and mutate. These
points are repeat-verified and establish a finite lower-bound rule; the
`UINT32_MAX` overflow control instead rejects asynchronously **[OBS, DB]**.
Across three independent zero-delay runs, two first reads returned `0100 []`
and the later status-50 `2401` reply appeared on a newly established socket;
one first read received the status reply directly. A no-send read captured the
late reply without creating another protocol transaction. Both following
`2301` getters in every run returned the pristine 124-byte record. The completed
lifecycle matrix contains 20 topology/delay cells with three independent
cold-process observations each. Every same-connection arm received
`0xfffffffe/0x0100` followed by EOF. Waiting before reconnect produced no late
frame in all 18 observations. When reconnecting first, the queued status-50
`0x2401` reply arrived on the replacement socket in 13 of 21 observations,
including one after 3,000 ms; the remaining eight timed out. Two of 60 initial
setter reads received the correlated rejection directly and 58 received the
close sentinel. Both fresh getters in every observation returned the pristine
record **[OBS, DB]**.

The static parser accounts for both halves of this behavior. The formatter
declares `2401` as six arguments tagged number, number, number, number, blob,
number. In `PSvDBConnection::ReceiveCommand`, the blob branch at
`0x10143b8a8..0x10143b9bf` reads its byte count from the immediately preceding
numeric slot and accepts only `1..0x4fffff`. `UINT32_MAX` takes the rejected
branch, which stops the argument loop without invalidating or freeing the
command. The four preceding numbers remain populated; the zero-initialized blob
pointer and trailing record count are delivered to the handler. Its null-pointer
guard produces `4e02 [2401, 50, 0, empty_blob, 0]`. Separately, the
`PSvDBConnection` Drop/Listen/destructor paths construct transaction
`0xfffffffe`, kind `0100`, and send it before dropping the EDB agent. Thus
`0xfffffffe/0100` is a connection-close sentinel, not the correlated setter
result **[RB-DEC, OBS]**.

This is consistent with the server send path rather than a client-side
artifact. `RetNewCueToClient` preserves the request transaction but passes its
reply to `RequestToSendData` with a player/device byte. The shared send queue is
not given the originating socket, so replacement-connection delivery for the
same identity is an expected routing possibility **[RB-DEC, OBS]**.

An accepted AppSync mutation uses up to three ordered membership updates. The
fixed update writes ContentID, millisecond/frame/MPEG timing, and `Color=-1`.
The parsed-option update writes Color, ColorTableIndex, Comment, BeatLoopSize,
and CueMicrosec. The seek update writes `InPointSeekInfo` and
`OutPointSeekInfo` as comma-separated unsigned triples. A failed phase prevents
later phases. This explains how the 56-byte fixed-only form can succeed without
an option region while a canonical record replaces the temporary color and
persists its option fields **[RB-DEC, DB]**.

Both setter dispatch paths deliver a Hot Cue Bank update only when the setter
returns a nonzero resolved CueID. The installed delivery sink receives
`(class=3, CueID, 0)` behind the server's delivery-enabled flag. This is a
static callback contract; its downstream packet framing and recipients remain
to be captured **[RB-DEC]**.

Live `2201` passes the D/E/F ordinal directly to that resolver,
so D targets `TrackNo=4`; a successful update then returns kind `4702` with the
selected track's unchanged `djmdCue` rows rather than echoing the mutation.
Unknown-bank, unknown-content, and duplicate-`TrackNo=1` controls time out. The
separate D/E/F matrix proves ordinals 4/5/6 update `TrackNo` 4/5/6, with the
response cue count selected independently by ContentID. The handler's exact
flag gate is `0x00040000..0x0006ffff`, so the observed `0x0100` low word admits
only ordinals 4/5/6. Ordinals 0/1/2/3/7/8/255/256/32767/32768/65535 all return
status-zero `4702` track-cue replies but leave every target membership and cue
unchanged. They are acknowledged no-ops because the post-gate ContentID reply
path still runs **[OBS, DB, RB-DEC]**. A matching 56-case status cross proves
packed type `01` alone admits `2201`; types 00 and 02-06 return the nine-field
legacy status-50 envelope, and six-slot getters after every request prove only
the accepted type changes slot 4. RX3/CDJ identity and setup width again have
no effect on decoded responses. The complete layouts, WAL mutation
proofs, and inbound seek-info process-exit edge are in `HOT_CUE_BANK_ORACLE.md`.

The `2201` dispatcher calls the mutation path only when its declared cue length
is exactly 36, its record pointer is non-null and four-byte aligned, and the
flag is in `0x00040000..0x0006ffff`. Extension lengths 0-8 are copied into a
zeroed eight-byte local; larger lengths read the first eight bytes directly.
After a malformed cue-record error, the handler still reads ContentID at
record offset `+0x04` and enters `GetUsbCue`, so malformed probes require an
independent process and explicit timeout/disconnect/process-health evidence
**[RB-DEC]**.

Soft-deleting a bank hides it from its parent tree but does not invalidate its
numeric selector. With one live membership retained beneath deleted bank 9031,
direct catalog `2001`, legacy cue `2101`, and extended cue `2301` requests all
serve that membership. Clients must not infer direct-ID rejection from tree
visibility **[OBS, DB]**.

The common static query pipelines, including rowset helpers, liveness filters,
sorting, and rendering-time lookups, are cataloged in `DATABASE_QUERIES.md`.
`DATABASE_FIELD_REFERENCE.md` then resolves every table-like name to the
physical AppSync fixture schema or to its runtime/alternate-interface role and
joins every table and semantically identified field to its concrete request
kinds. Its inverse 95-row index maps each kind back to the family, operation,
tables, and family-named fields while labeling exact-SQL, semantic-family, and
schema-only evidence separately.
Addresses, hashes, raw disassembly artifacts, and reproduction commands are in
`STATIC_ANALYSIS.md`.

## Headless server requirements exposed by the capture

1. Advertise the exact 20-entry root order and item types.
2. Keep sort visibility/order configurable while preserving fixed wire IDs.
3. Implement selector menus as real database queries, including wildcard ALL
   paths, rather than returning decorative root entries.
4. Keep materialized menus by packed context across client connections and
   implement paged rendering. Querying a context replaces only that context's
   buffer.
5. Count UTF-16 strings in bytes including their NUL.
6. Preserve full track fields when emitting the RX3's 12-argument legacy rows.
7. Select and format the secondary column explicitly; do not hardcode comment
   or blank it for legacy clients.
8. Use live referenced lookup rows and honor Rekordbox deletion markers.
9. Distinguish database IDs from normalized wire values, especially musical
   keys.
10. Treat Link history as mutable session state, not only a static DB query.
11. Keep Matching based on `djmdRecommendLike` and do not conflate it with
    Rekordbox's related-track presets.
12. Return an empty/error result for unsupported paths without corrupting the
    connection's framing.

### Frozen historical implementation audit

This section describes the retained pre-conformance rbxport snapshot. It is
provenance for later replay work, not a gap list for real Rekordbox and not part
of the current real-Rekordbox recording phase.

The current daemon handles Track, Key, Genre, Artist, Album, Playlist, current
Link History, Search, Label, BPM, Rating, Release Year, Color, Time, Bitrate,
File Name, and Matching Tracks. Selector rows, request families, item types,
track filtering, and the captured ordering rules are implemented for those
families.

Additional fidelity gaps found during database correlation:

- Lookup menus currently expose dense interner IDs (`index + 1`) rather than
  the `master.db` entity IDs Rekordbox sends. The dense IDs round-trip inside
  this server but are not wire-identical and complicate cross-feature joins.
- Link-history create/add/remove operations are not implemented by the daemon's
  source, so its History root remains empty.
- Remixer and Original Artist still lack catalog/session paths in the retained
  historical implementation audit. Hot Cue Bank comparison is deferred.
- The separate `1708` StockDate/date-added hierarchy still uses its existing
  year/month/day selectors and needs the stock-year/stock-month correction
  described above.
- Smart playlists need rule evaluation rather than membership lookup alone.
- Color names use Rekordbox's default eight-name palette rather than custom
  `djmdColor.Commnt` values.

## Outstanding second-pass questions

- Capture a genuine player's `2101`/`4702` request and UI transition to recover
  the player-side prerequisite and visible load state. Rekordbox's server reply,
  catalog, getters, setters, and internal-only bank-update callback are already
  characterized; the active queue covers the remaining declared parser and
  mutable-field matrices.
- Capture the physical-client actions and status conditions that emit Search
  Track `0x1500`, plus sort tie-breakers beyond the exact eight-row orders and
  an explicit-sort population above 10,005 rows. The server-side Search and
  Search Track paths are otherwise complete.
- Cross the established context types with additional status/setup and
  mutation families whose builders may consume the low byte differently.
- Cross packed type with additional native status shapes for remaining class-2 mutation
  families. Display, Play, Delivery, recognized no-builder kinds, Hot Cue Bank
  catalog/getters, and both setters are complete for matched RX3/CDJ status and
  both setup widths; only Display takes the requester-keyed AIO branch.
- Compare row flags before and after load, tag, rating, and playlist operations.
  The complete command routes, database/filesystem effects, replies, rejected
  arms, and XDJ-RR caller sites are indexed; the remaining question is the live
  before/after row presentation and refresh boundary.
- Cross the proven Hot Cue Bank matrix with additional genuine device status
  identities beyond the authentic RX3 and completed CDJ-2000nexus sources.

## Reproduction artifacts

- `data/source-menu-tree.json`: structured live tree capture, including all row
  arguments.
- `data/source-findings.md`: short field note created during exploration.
- `data/source-probes/menu-probe-source.txt`: bounded tree/pagination probe.
- `data/source-probes/legacy-menu-probe-source.txt`: RX3-style 12-field setup probe.
- `data/source-probes/search-probe-source.txt`: search request and UTF-16 length probe.
- `artifacts/rekordbox/7.2.19/symbols-x86_64.txt`: Rekordbox symbol inventory.

The tools are exploratory clients. They should be pointed only at a live source
whose library is backed up, and all database correlation should remain
read-only.
