# Song-information sibling oracle

Rekordbox 7.2.19 dispatches request kinds `0x2002` through `0x2602` through
`PSvDBMain::OnSongInfCmd`. Display Song Info (`0x2002`) has its own chapter.
This chapter records the adjacent Play Song Info (`0x2102`), Rekordbox-local
no-builder arms (`0x2202` through `0x2502`), and Delivery Info (`0x2602`)
surfaces. Those middle request kinds have distinct client and player-hosted
meanings; Rekordbox's rejection describes only its own database-server role.

The evidence combines eight repeated ordinary-identity goldens, ten repeated
status-backed goldens, ordered malformed-state experiments, fifteen
twice-recorded row-order experiments, four two-phase discovery-identity
lifecycles, deterministic encrypted fixtures, and disassembly of every
Play/Delivery builder in the pinned executable. All live runs used the isolated
VM network. Ordinary captures use XDJ-RX3 player 1; the status matrix uses an
authentic RX3 player-11 packet and an RX3-template-derived CDJ-3000 player-1
control. Evidence labels follow `README.md`.

## Proven scope

| Suite | Cases | Coverage |
| --- | ---: | --- |
| `song-info-siblings` | 24 | Six request kinds crossed with populated, deleted, zero, and unknown content IDs |
| `song-info-sibling-render` | 42 | Both builders with render arities 5/6/8, gate 0/1, database selection, and selectors 2-17 |
| `song-info-sibling-pagination` | 18 | One-row, exact, last, zero, end, past-end, overrun, overlap, and maximum-offset plans |
| `song-info-sibling-errors` | 17 | Deterministic malformed arity, type, extra-argument, zero-context, and alternate-location forms |
| `song-info-sibling-legacy` | 8 | Both builders crossed with populated and three missing-content states under legacy setup |
| `song-info-delivery-boundaries` | 8 | Null, empty, dangling ComposerID, ASCII 126/127/128, UTF-16 126/127/128, and DeliveryControl case behavior |
| `song-info-delivery-wide-strings` | 8 | Direct Delivery strings at ASCII 254/255/256 and UTF-16 252/254/255/256/257 |
| `song-info-play-paths` | 14 | Local/cloud identity, null/empty/Unicode paths, signed/unsigned sizes, file/directory/missing state, ContentLink, and HotCueAutoLoad |
| RX3 status matrix | 106 | Baseline, render, pagination, 14 stable malformed type/arity cases, and legacy under genuine player-11 status |
| CDJ-3000 status matrix | 106 | The same stable surface under an RX3-template-derived player-1 control |

All 351 canonical cases were recorded from Rekordbox and matched an independent
repeat before promotion. The two field-boundary suites and the status malformed
suites reset the fixture and restart Rekordbox between phases; the other suites
use immediate repeats. The path suite uses arbitrary file sentinels; actual
media files were absent.

| Fixture | Database SHA-256 | Semantic fingerprint |
| --- | --- | --- |
| `full` | `e8c45a7020a70103d6a15d5cf9aaa32a3d8c758c6c1f3f33b2a8d80872f7c812` | `c7b0b834a1a1320faaa3526c4792f0d31430c617ea9b8b6008521c514b67853c` |
| `delivery-boundaries` | `2c7e70747e1d02921cd3a542f9539c3acc215ddbbf071c9394baf30acfd4df49` | `1a83481657d837d5af8e5ba996d6a1acbf4c89a65daf9cfaff8783254cbc2c21` |
| `delivery-wide-strings` | `578c7df2d3960ccf496e72a2aced72a2fb192c09f11ab40e403e43c3d1b8381a` | `2fb974d7b0362478ef5630be46dac815f9889e84bd02f8be6dc6427f58985ae6` |
| `play-paths` | `8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6` | `c24aff6c06466a647d09e60f8cf5c872f6db8ae5d482a72cb31ef1d270db6f1a` |

## Family dispatch

The request envelope is the same two-number form as Display Song Info:

```text
kind [packed_context, content_id]
```

The observed family behavior is:

| Kind | Pinned static action | Populated live result | Missing-content result |
| ---: | --- | --- | --- |
| `0x2002` | `GetDispSongInf` | 16-row Display Song Info menu | zero-row menu |
| `0x2102` | `GetPlaySongInf` | 7-row Play Song Info menu | zero-row menu |
| `0x2202` | log and return without a builder | `4003 [0x2202]` | `4003 [0x2202]` |
| `0x2302` | log and return without a builder | `4003 [0x2302]` | `4003 [0x2302]` |
| `0x2402` | log and return without a builder | `4003 [0x2402]` | `4003 [0x2402]` |
| `0x2502` | log and return without a builder | `4003 [0x2502]` | `4003 [0x2502]` |
| `0x2602` | `GetDeliveryInf` | 13-row Delivery Info menu | zero-row menu |

Deleted content ID `10999`, numeric zero, and unknown ID `0xfffffffe` produce
the same zero-row menu for both real builders. The four no-builder kinds return
an error for every one of those IDs; they do not inspect content existence on
this server path **[OBS, DEC]**.

### Player-hosted meanings of `0x2202` through `0x2502`

The four Rekordbox-local no-builder arms are not one globally unsupported
family. Hash-pinned Dysentery, alphatheta-connect, and readable XDJ-RX firmware
sources establish these opposite-role contracts:

| Kind | Player/client meaning | Player-hosted behavior |
| ---: | --- | --- |
| `0x2202` | Generic or non-Rekordbox track metadata for media-slot type 2 or audio-CD type 5 | The XDJ-RX server returns a cached metadata list or starts an asynchronous source fetch |
| `0x2302` | Player unit/track summary root | The XDJ-RX server builds Title, Artist, Album, Time, BPM, and Key rows |
| `0x2402` | Track decode information for a track ID | Five recovered XDJ generations expect `0x4802` with a scalar and length/blob outputs, but each local server dispatches to an unsupported stub |
| `0x2502` | One-way register track length command | Five recovered XDJ generations send context, track ID, and length, but each local server dispatches to an unsupported stub |

Thus `0x2202` and `0x2302` have statically proven successful player-hosted
builders. XDJ-RX, XDJ-RR, XDJ-RX2, XDJ-XZ, and XDJ-RX3 all carry both later
client contracts, while their local `0x2402` and `0x2502` server functions log
unsupported and mark the command complete. The generated
`data/static-analysis/player-hosted-song-info.json` audit binds all 23 source
hashes and checks each recovered contract. CDJ-3000, XDJ-AZ, OMNIS-DUO, and
CDJ-1500X retain the two request names and all three wire-format entries. A
whole-tree scan covers 3,289, 7,857, 7,236, and 8,480 decompiled C sources,
respectively. Every exact `0x2402`, `0x2502`, and `0x4802` literal is confined
to each device's command-name and parameter-format files. The tables declare
two numeric request arguments for `0x2402` and three for `0x2502`; no literal
client caller, reply wait, or server handler exists elsewhere. Computed command
values, table-driven function pointers, and decompiler omissions remain the
bounded static uncertainty **[SRC, DEC]**.

The successful response header echoes its request kind:

```text
4000 [00002102, 00000007]
4000 [00002602, 0000000d]
```

Rendering uses ordinary `0x3000`, then `4001`, `4101` rows, and `4201`.

## Play Song Info rows

The seven extended rows are fixed for the populated fixture. The table gives
the complete distinguishing arguments; all rows have 16 arguments, argument
13 is numeric `2`, and arguments not shown are zero or empty.

| # | Item type | Static source | Arg 0 | Arg 1 | Text in arg 3 |
| ---: | ---: | --- | ---: | ---: | --- |
| 1 | `0x04` | `djmdContent.FileType` | 0 | 1 | empty |
| 2 | `0x0b` | `djmdContent.Length` | 0 | 59 | empty |
| 3 | `0x0d` | `djmdContent.BPM` | 0 | 12000 | empty |
| 4 | `0x23` | `djmdContent.Commnt` | 0 | 10001 | `comment-1` |
| 5 | `0x00` | file delivery path and size | 8864 | 10001 | `Z:/tracks/link-export-fixture/fixture-01.wav` |
| 6 | `0x2f` | `djmdContent.HotCueAutoLoad` | 0 | 1 | empty |
| 7 | `0x0f` | `djmdContent.KeyID` / `djmdKey.ScaleName` | 0 | 5001 | `Am` |

The path row proves that Rekordbox can describe the database path and stored
file size without the referenced media file existing. The focused fourteen-
track oracle now covers local/cloud path selection, matching and mismatched
database identities, null/empty paths, file/directory/missing states, 32-bit
size conversion, `ContentLink`, and `HotCueAutoLoad`. Tiny arbitrary sentinels
exercise the existence branches; audio media is unnecessary. The complete
matrix is in `PLAY_SONG_INFO_PATH_ORACLE.md` **[OBS, DEC]**.

All 21 render-control cases return these same seven rows in the same order and
with the same fields. Play Song Info ignores the tested secondary gate and
selector inputs **[OBS]**.

## Delivery Info rows

The active AppSync database interface builds 13 rows. This is distinct from
the 19-insertion `PSvDBMain::GetDeliveryInfDB` fallback recovered in the same
binary; the fallback was not selected by the live Windows configuration.

| # | Item type | Static source | Arg 0 | Arg 1 | Arg 3 | Arg 5 |
| ---: | ---: | --- | ---: | ---: | --- | --- |
| 1 | `0x36` | `ComposerID` lookup | 0 | 0 | empty | empty |
| 2 | `0x0d` | `BPM` | 0 | 12000 | empty | empty |
| 3 | `0x23` | `DeliveryComment` | 0 | 10001 | empty | empty |
| 4 | `0x0f` | `KeyID` lookup | 5001 | 15 | empty | `Am` |
| 5 | `0x12` | `FileType` | 0 | 1 | empty | empty |
| 6 | `0x06` | `GenreID` lookup | 0 | 3001 | `Fixture House` | empty |
| 7 | `0x0e` | `LabelID` lookup | 0 | 4001 | `Fixture Label One` | empty |
| 8 | `0x07` | `ArtistID` lookup | 0 | 1001 | `Alpha Artist` | empty |
| 9 | `0x37` | `Lyricist` | 0 | 10001 | empty | empty |
| 10 | `0x4f` | `DeliveryControl` / `ISRC` | 10001 | 0 | empty | empty |
| 11 | `0x0f04` | composite Title / selected Key | 5001 | 10001 | `Alpha One` | `Am` |
| 12 | `0x02` | `AlbumID` lookup | 0 | 2001 | `Album One` | empty |
| 13 | `0x0b` | `Length` | 0 | 59 | empty | empty |

The baseline fixture leaves DeliveryControl, ISRC, DeliveryComment, ComposerID,
and Lyricist at their database defaults. The focused profiles below establish
their populated, null, dangling, case, and exact string-limit behavior.

## Delivery-only fields and limits

The Delivery-only columns are nullable `VARCHAR(255)` fields in `djmdContent`.
Their exact observed wire placement is:

| Source | Item type | ID/content field | String field | Length field | Limit |
| --- | ---: | --- | --- | --- | --- |
| ComposerID -> `djmdArtist.Name` | `0x36` | arg 1 | arg 3 | arg 2 | 127 UTF-16 units |
| DeliveryComment | `0x23` | content ID in arg 1 | arg 3 | arg 2 | 255 UTF-16 units |
| Lyricist | `0x37` | content ID in arg 1 | arg 3 | arg 2 | 127 UTF-16 units |
| DeliveryControl / ISRC | `0x4f` | content ID in arg 0 | ISRC in arg 5 | arg 4 | 255 UTF-16 units |

The length field is the UTF-16 byte count including the terminating NUL:
126/127/128 ASCII units produce 254/256/258 before a limit applies;
254/255/256 units produce 510/512/512 at the 255-unit path. Null and empty
values both become an empty string with byte length 2. A dangling ComposerID
`999999` remains in arg 1 while its lookup text is empty **[OBS]**.

At 128 input units, Composer and Lyricist retain 127. At 256 input units,
DeliveryComment and ISRC retain 255. When the boundary falls between a
surrogate pair, the wire decoder exposes U+FFFD: 128 supplementary units become
63 complete characters plus U+FFFD on the 127-unit path, and 256 units become
127 complete characters plus U+FFFD on the 255-unit path **[OBS]**.

DeliveryControl is not returned as text. Arg 8 of the `0x4f` row is 1 only when
the database value equals `ON` case-insensitively. `ON` and `on` set it;
`OFF`, `Off`, empty, and null clear it. The literal comparison and live values
agree **[OBS, DEC]**.

## Delivery render controls

Unlike Play Song Info, Delivery Info applies ordinary secondary-column
composition to its Title row. Its heterogeneous metadata order is controlled
by process/list-buffer state rather than by that selector. The following table
is the complete wire result from the original ordered suite, where all 21 Play
cases preceded these 21 Delivery cases. `Order` lists argument-6 item types as
they appeared at each suite position.

| Control | Composite arg 0 | Arg 5 | Composite type | Order |
| --- | ---: | --- | ---: | --- |
| arity 5 | 10001 | empty | `0004` | `0036 000d 0023 000f 0012 0006 000e 0007 0037 004f 0004 0002 000b` |
| arity 6 | 10001 | empty | `0004` | `0036 000d 0023 000f 0012 0006 000e 0007 0037 004f 0004 0002 000b` |
| gate 0, selector 0 | 10001 | empty | `0004` | `0036 000d 0023 000f 0012 0002 000e 0004 0037 0006 004f 0007 000b` |
| gate 0, selector 7 | 10001 | empty | `0004` | `004f 0006 0036 0037 0002 000e 0023 0012 0004 000f 000b 000d 0007` |
| gate 1, selector 0 | 5001 | `Am` | `0f04` | `0036 0006 004f 0f04 0002 000e 0023 0012 0037 000f 000b 000d 0007` |
| selector 2 | 1001 | `Alpha Artist` | `0704` | `0036 000d 0023 000f 0012 0006 000e 0007 0037 004f 0704 0002 000b` |
| selector 3 | 2001 | `Album One` | `0204` | `0036 000d 0023 000f 0012 0002 000e 0204 0037 0006 004f 0007 000b` |
| selector 4 | 12000 | empty | `0d04` | `004f 0006 0036 0037 0002 000e 0023 0012 0d04 000f 000b 000d 0007` |
| selector 5 | 0 | empty | `0a04` | `0036 0006 004f 0a04 0002 000e 0023 0012 0037 000f 000b 000d 0007` |
| selector 6 | 3001 | `Fixture House` | `0604` | `0036 000d 0023 000f 0012 0006 000e 0007 0037 004f 0604 0002 000b` |
| selector 7 | 10001 | `comment-1` | `2304` | `0036 000d 0023 000f 0012 0002 000e 2304 0037 0006 004f 0007 000b` |
| selector 8 | 59 | empty | `0b04` | `004f 0006 0036 0037 0002 000e 0023 0012 0b04 000f 000b 000d 0007` |
| selector 9 | 1003 | `Fixture Remixer` | `2904` | `0036 0006 004f 2904 0002 000e 0023 0012 0037 000f 000b 000d 0007` |
| selector 10 | 4001 | `Fixture Label One` | `0e04` | `0036 000d 0023 000f 0012 0006 000e 0007 0037 004f 0e04 0002 000b` |
| selector 11 | 1004 | `Fixture Original` | `2804` | `0036 000d 0023 000f 0012 0002 000e 2804 0037 0006 004f 0007 000b` |
| selector 12 | 5001 | `Am` | `0f04` | `004f 0006 0036 0037 0002 000e 0023 0012 0f04 000f 000b 000d 0007` |
| selector 13 | 0 | empty | `1004` | `0036 0006 004f 1004 0002 000e 0023 0012 0037 000f 000b 000d 0007` |
| selector 14 | 0 | empty | `0004` | `0036 000d 0023 000f 0012 0006 000e 0007 0037 004f 0004 0002 000b` |
| selector 15 | 1 | `Pink` | `1404` | `0036 000d 0023 000f 0012 0002 000e 1404 0037 0006 004f 0007 000b` |
| selector 16 | 0 | empty | `2a04` | `004f 0006 0036 0037 0002 000e 0023 0012 2a04 000f 000b 000d 0007` |
| selector 17 | 10001 | `2021-02-02` | `2e04` | `0036 0006 004f 2e04 0002 000e 0023 0012 0037 000f 000b 000d 0007` |

The selector values match the ordinary secondary-column map. Three focused
Delivery-only suites separate selector identity from request position. Each
suite was recorded twice from a cold process and matched byte-for-byte:

| Suite | Cases | Behavior SHA-256 |
| --- | ---: | --- |
| repeated identical request | 16 | `a640b7472b8e2fa9e694ece1f82bc069e1480e1b598ca6d99f91a407b162d97a` |
| controls forward | 21 | `3ad97d44b1ffda4ccefd84a0c6edac051e3e968ba19c472a041fa09811aa7039` |
| controls reversed | 21 | `e1c83e5c589e6502cdd9a9caa7902ba6c9f5ec59332a58e720ec87d56361be71` |

With only populated Delivery requests, cold requests 1-3 use order A, request
4 uses B, request 5 uses C, request 6 uses D, and subsequent requests cycle
A/B/C/D. Fresh TCP connections do not reset this state:

```text
A 0036 000d 0023 000f 0012 0006 000e 0007 0037 004f 0f04 0002 000b
B 0036 000d 0023 000f 0012 0f04 000e 0006 0037 0007 0002 004f 000b
C 004f 000f 0007 0002 0023 0037 000b 000e 0f04 0012 000d 0036 0006
D 0036 0006 004f 0f04 0002 000e 0023 0012 0037 000f 000b 000d 0007
```

Reversing the controls makes each selector inherit the pattern at its new
position while preserving its own composite value and type. The selector does
not select the permutation **[OBS]**.

The first same-process boundary verification was rejected because its second
pass continued the same cycle at positions 9 and 10. Resetting the fixture and
restarting Rekordbox reset the cold prefix and reproduced the complete original
envelope. The original combined Play-then-Delivery table above has additional
permutations, proving prior Play activity reaches the shared ordering state.
The rejected pair, all thirty cold order runs, and eight identity-lifecycle
phase recordings are retained under
`data/experiments/song-info-delivery-{boundaries,order}/` **[OBS]**.

Six cold-process family-interaction suites then alternated a precursor request
with a populated Delivery probe eight times. Each 16-case run matched its
second cold-process recording byte-for-byte:

| Precursor | Precursor response | Probe pattern |
| --- | --- | --- |
| missing Delivery | zero-row menu | `AAABCDAB` |
| recognized no-builder `0x2202` | `4003` error | `AAABCDAB` |
| missing Display | zero-row menu | `AAAAAAAA` |
| missing Play | zero-row menu | `AAAAAAAA` |
| populated Play | 7-row menu | `AAAAAAAA` |
| populated Display | 16-row menu | `AAEAEAEA` |

Here A-D are the normalized patterns above and E is:

```text
E 0002 0f04 0023 000f 004f 0037 0007 000e 0006 0012 000d 0036 000b
```

Missing Delivery and the no-builder error do not consume or reset the
standalone populated sequence. Missing Display, missing Play, and populated
Play make the immediately following Delivery response use A on every
iteration. Populated Display gives A for its first two following probes and
then alternates E/A. This rules out a single family-independent counter. The
observable state belongs to reused builder/list storage and is affected by the
preceding builder's successful or empty path **[OBS]**. Exact behavior hashes
and a reproducible summarizer are in
`data/experiments/song-info-delivery-order/README.md`.

The same six precursor suites were then recorded twice with one TCP connection
held from setup through all 16 cases. For every family, the complete case array
is byte-for-byte equal to the corresponding suite that replaces the client
connection before every case. Connection reuse/replacement does not alter the
precursor response, Delivery row payload, or A-E pattern sequence **[OBS]**.

Discovery identity expiry also leaves the state intact. Two cold processes
each ran six populated Delivery calls (`AAABCD`), removed the XDJ-RX3 identity,
waited through discovery expiry, reintroduced that RX3, and ran eight more
calls. Two more cold processes replaced RX3 with CDJ-3000. All four post-rejoin
phases return `ABCDABCD`, the exact continuation after call six. Warm-up and
post behavior hashes are identical across repeats and model replacement.
Identity loss/rejoin and XDJ/type-7 to CDJ/class-1 replacement therefore do not
reset or select Delivery ordering **[OBS]**.

In all four automated lifecycles, port query still timed out after the initial
40-second absence and eight seconds of renewed emission. Thirty more seconds
and another emission reopened Link Export without a Rekordbox restart. The
successful phase recordings are separated by 98 seconds; the manually
recovered first run is separated by 108 seconds. This bounds observed recovery
without assigning Rekordbox's exact internal expiry interval **[OBS]**.

## Pagination

Both builders use the same normalization algorithm, scaled to their own total
`N` (`7` or `13`) **[OBS]**:

| Request | Returned behavior |
| --- | --- |
| each offset `0..N-1`, count 1 | exactly that row and offset |
| offset 0, count `N` | all `N` rows from offset 0 |
| offset `N-1`, count 1 | final row |
| offset 0, count 0 | one row at offset 0 |
| offset `N` or `N+1`, count 1 | final row at offset `N-1` |
| offset `N-1`, count `N+2` | all `N` rows from offset 0 |
| windows `0:3` then `2:3` | both windows, including duplicate row 2 |
| offset `0xffffffff`, count 1 | render timeout |

## Malformed arguments and parser state

The deterministic independent-case results are identical for both builders
except the alternate-location Delivery request:

| Arguments | Play `0x2102` | Delivery `0x2602` |
| --- | --- | --- |
| none | timeout | timeout |
| context only | zero-row menu | zero-row menu |
| context, content, extra number | populated 7-row menu | populated 13-row menu |
| string context | generic `0100 []` | generic `0100 []` |
| blob context | generic `0100 []` | generic `0100 []` |
| string content ID | zero-row menu | zero-row menu |
| blob content ID | generic `0100 []` | generic `0100 []` |
| numeric zero context | zero-row menu in the canonical ordered suite | excluded from the canonical suite; see below |
| location-2 context | populated 7-row menu | zero-row menu |

Numeric zero context is order-dependent. A cold 20-case audit alternated Play
and Delivery zero-context requests ten times; all 20 timed out. Valid Play,
Delivery, and Display requests inserted between zero-context attempts did not
change that result. A 28-case prefix bisection then paired each malformed form
with an immediate zero-context request. Only a blob-valued content ID changed
the following zero-context request into a zero-row menu, for both builders.

The complete prefix behavior repeated from a fresh Rekordbox process with
canonical behavior SHA-256
`ed06d4efe39c1eb6f088822d0474b70dc2c6e46b119f0ec11f3cd1afe2e468fb`.
The first broad error recording also caught Delivery zero context as a timeout,
then as a menu on repeat. Both envelopes are retained. This is observable
connection-independent server/parser state; it is deliberately represented as
ordered experiment evidence rather than weakened golden equality **[OBS]**.

## Status-backed device classification

Five suites were repeated under each status-backed control: authentic RX3
player 11 at context `0x0b010301` and the RX3-template-derived CDJ-3000 player
1 at `0x01010301`. After replacing
only the requester byte in the RX3 request/page contexts, all 106 stable cases
per identity are byte-identical. The baseline, render, pagination, and legacy
cases are also identical to the ordinary no-status XDJ-RX3 oracle **[OBS]**:

| Suite | Cases per identity | Normalized case SHA-256 | Ordinary result |
| --- | ---: | --- | --- |
| baseline | 24 | `839f7795e4aea6af341c041e1edad33eec6f49e5a16f86814758b8ea9473b6ee` | exact |
| render | 42 | `cf46eb6381af1f3c6085e7381205193016bfb2ac04be8455ec898e7d922508c4` | exact |
| pagination | 18 | `89eee438685439081eb7d80ea2f186d3d012965664879ee998a2672783bdb3d1` | exact |
| stable malformed | 14 | `9b0bd2d3f771e722d10c5e12e7d58303c67e8b75b825ce76620fb3a966f77522` | one dispatch difference |
| legacy | 8 | `4a8aa182c7b422f7a26c215acf7322abeada3eaebc8ac67453a5241d7aa6b3e1` | exact |

The stable malformed difference is argumentless Delivery. The ordinary
identity times out. Both status identities return a zero-row menu whose header
unexpectedly echoes Play kind `0x2102`, even though the request kind is
Delivery `0x2602`. The other thirteen stable malformed cases match ordinary
behavior after context normalization. This is a status-presence branch, not an
RX3-versus-CDJ distinction **[OBS]**.

Zero context and alternate menu location remain ordered experiment evidence.
Two cold CDJ runs are exact: zero-context Play is an empty menu, location-2
Play has 7 rows, and location-2 Delivery has 13. Two matched-player RX3 runs
both give 7-row Play at `0x0b020301`; zero-context Play is timeout then empty,
and Delivery at that location is 13 rows then empty. With the inherited
player-1 location-2 context, RX3 Play times out and Delivery is empty in both
runs. This separates requester mismatch from the remaining RX3 lifecycle
variation without assigning either effect to the AIO field-order branch
**[OBS]**.

`tools/summarize_status_siblings.py` validates the canonical equality, expected
ordinary divergence, and retained cold-run outcomes. Display Song Info remains
the only stable populated builder here whose row order changes with the AIO
classifier recovered from the executable **[OBS, DEC]**.

### Packed type under status-backed controls

A focused 28-case matrix crosses Play Song Info types `0x00..0x06`, both setup
widths, matched RX3 player-11 status/requester 11, and matched CDJ-3000
player-1 status/requester 1. Only type `0x01` returns the seven Play rows; the
other six types return `0x4000` with total `0xffffffff`. After requester-byte
normalization, RX3 and CDJ-3000 response envelopes are identical within each
setup. Legacy rows are exact 12-argument prefixes of extended rows **[OBS]**.

The four goldens and their immediate repeats are summarized by
`tools/summarize_context_play_status.py` under
`data/experiments/packed-context/play-status-cross/`. This closes the packed
type x matched-status x setup cross for Play without finding an AIO branch.

The companion 140-case class-2 matrix covers Delivery and every recognized
no-builder kind under the same identities and widths. Delivery admits only
type `0x01`, returning 13 rows; other types return `0x4000` with total
`0xffffffff`. Requests `0x2202..0x2502` return their kind-specific `0x4003`
for every type. Normalized RX3/CDJ envelopes are identical, and legacy
Delivery rows are exact extended prefixes **[OBS]**. The evidence and validator
are under `data/experiments/packed-context/class2-status-cross/` and
`tools/summarize_context_class2_status.py`.

### RX3 status menu-location-2 state

A dedicated cold-process matrix resolves the earlier location-2 ambiguity.
Seven precursor families run eight iterations per process, and every suite was
recorded twice. The 208 header-only executions are byte-identical across
repeats. Every matched `0x0b020301` Delivery probe returns 13 rows after no
precursor, zero-context Play timeouts, primary or location-2 Play, primary or
location-2 Display, and primary Delivery **[OBS]**.

A 32-case prefix suite then crosses all sixteen preceding malformed forms with
that same Delivery probe. It also repeats exactly. Only a blob-valued content
ID sent to Play or Delivery makes the immediately following location-2
Delivery menu empty; all fourteen other precursors leave it at 13 rows. This
is the same typed-input/parser-state family that controls zero-context behavior,
but the target response is now independently isolated **[OBS]**.

The earlier broad sequence remains a wider-history boundary. Its final
Delivery-blob/Delivery-location-2 pair returns 13 in the cold run where prior
zero-context Play times out and 0 in the run where zero context returns empty.
The direct blob precursor is therefore deterministic in the focused suite,
while longer malformed history can alter whether the effect is applied.

The malformed content type reaches a concrete transaction-state edge in the
pinned 7.2.19 x86-64 implementation **[DEC]**. `DBCFmt_GetCmdPrmFmt` declares
`0x2602` as two numeric tags, but `GetDeliveryInf` reads the second generic
argument slot as a 32-bit ContentID without checking its decoded tag. A blob
slot therefore contributes the low 32 bits of its allocated payload pointer.
`GetDeliveryInfDB` first calls `DsqlListBuf_Clear(context, 0)`, which disables
autocommit, and then performs the content lookup. A failed lookup jumps to the
return epilogue before `DsqlListBuf_InsEnd(1)`. The skipped tail normally
commits the transaction, restores autocommit, and opens the left-buffer index
when necessary. This proves a Delivery-specific unbalanced transaction edge.
Play reaches its normal finalizer even for the corresponding missing-content
path, while both Play-blob and Delivery-blob have produced the live follow-up
effect. The transaction edge is therefore not a complete explanation of that
shared behavior **[DEC, OBS]**.

The connection lifecycle supplies a separate, directly testable mechanism.
The empty `0x0100` observed for these malformed commands is the
`transaction = 0xfffffffe` close sentinel constructed by
`PSvDBConnection::Listen`, not a correlated Song Info response. Incoming
commands execute synchronously on the `PSvDBMain::run` queue, but their real
responses pass through `RequestToSendData` and the separate `PSvDBComm` queue,
keyed by player number rather than originating socket. This is the same routing
architecture that delivered delayed Hot Cue setter replies to replacement
connections. The complete timing oracle now bounds the live effect: four of
four immediate replacement probes receive zero rows, while four of four probes
at every tested delay from 50 through 3000 ms receive the correct 13 rows. A
focused routing oracle locates the response directly. All 24 replacement setup
exchanges contain only the normal setup reply. In each of four zero-delay blob
runs, the following no-send read receives the identical transaction-1 frame
`0x4000 [0x2602, 0]`; both the same-socket valid Delivery issued after draining
that frame and a later fresh-socket health request return 13 rows. At 50 and
100 ms, all eight blob no-send reads time out and both valid probes still
return 13. All twelve valid-extra-argument controls time out on the no-send
read and return 13 from both probes, including four immediate replacements
**[OBS]**.

The wrapper marks the pointer-derived missing-content result sendable and
passes its zero count to `Ret4ByteToClient`; `RequestToSendData` then targets
the player-keyed communications queue rather than the originating socket
**[DEC]**. The zero row in the original immediate follow-up is therefore a
late response from the malformed request, not the response to the valid probe
or persistent list-buffer corruption. When no replacement is registered by
the time that reply is dispatched, the absence of any later frame is
consistent with it being dropped; the exact drop point remains an inference
rather than a traced instruction **[OBS, DEC inference]**.

The lifecycle-aware ordered-pair rerun records setup and a 1200 ms no-send
drain independently for each of its three connections. Its first 221 promoted
pairs include all 16 successors after blob-valued Play. Every second
connection drains the identical transaction-1 `0x4000 [0x2102, 0]` before
sending its own request, across all nine malformed Play successors and all
seven malformed Delivery successors. Those successors themselves cover
timeouts, zero, seven, and 13 rows, plus headers without totals. The second
blob-valued Play queues one more identical response, which appears in the
health-probe drain; the other 15 health drains time out. All 16 health Delivery
requests return 13 rows. The delayed response therefore follows the count of
blob-valued Play requests and player-keyed connection admission, not the next
request's kind, result shape, or retained list contents **[OBS]**.

The string-context-Delivery/blob-content-Play pair reproduced that same
admission boundary. One quarantined record/repeat attempt split only on whether
the health connection received the delayed frame. Two wholly fresh processes
then agreed on the raw `0x4000 [0x2102, 0]` drain before the same 13-row health
response, establishing the promoted result without treating either side of the
earlier race as authority **[OBS]**.

The next sixteen promoted pairs complete the zero-context-Play precursor row.
That precursor times out in all sixteen; argumentless Play then times out,
missing-content Play returns zero rows, and extra-argument Play returns seven
rows, string- and blob-context Play return headers without totals, and
string-content Play returns zero rows. The first six pairs have eighteen timed-
out drains. With blob-content Play as successor seven, its own drain still
times out but the health connection receives exactly one delayed
`0x4000 [0x2102, 0]` from that second request before returning 13. A second
zero-context Play is another silent timeout with three timed-out drains.
Alternate-location Play returns its ordinary seven-row menu and also leaves
all three drains silent. Argumentless Delivery is a silent timeout in the
tenth pair, with another 13-row health result; unlike the standalone
status-backed argumentless-Delivery capture, this lifecycle produces no
immediate or drained frame. Missing-content Delivery returns its ordinary
zero-row menu, again with three silent drains. Extra-argument Delivery returns
13 rows and also leaves every drain silent. String- and blob-context Delivery
each return a header without a total and three more silent drains.
String-content Delivery returns zero rows. Blob-content Delivery returns a
header without a total; after its measured three-second no-client interval,
the health drain remains silent. All sixteen health Delivery requests return
13. These controls separate a
silent timeout from blob-valued Play's delayed player-routed header while
preserving each successor's independent result across the complete row
**[OBS]**.

All sixteen pairs in the alternate-location-Play precursor row are promoted.
They
return seven rows from that valid precursor, then either an argumentless Play
timeout, a zero-row missing-content Play menu, or a seven-row extra-argument
Play menu; string- and blob-context Play return their ordinary headers without
totals, string-content Play returns zero rows, zero-context Play times out, and
alternate-location Play returns seven rows. The first six successors plus the
zero-context and alternate-location successors have three silent drains
apiece. Argumentless Delivery times out, missing- and string-content Delivery
return zero rows, extra-argument Delivery returns 13 rows, and string-context,
blob-context, and blob-content Delivery return headers without totals.
Blob-content Delivery
is followed by the measured three-second no-client interval; its health drain
still times out. All fifteen successors other than blob-content Play have three
silent drains. Blob-content Play also returns a header without a total, but
queues one transaction-1 `0x4000 [0x2102, 0]` frame into the health drain. All
sixteen health Delivery requests return 13. The valid location-2 menu therefore
neither queues a transferable frame nor changes any successor's ordinary
result **[OBS]**. The reducer now verifies 151 pairs; 105
ordered pairs remain active authority work.

The complete argumentless-Delivery precursor row begins
with the same silent timeout. Argumentless Play then times out, while
missing-content Play returns zero rows, extra-argument Play returns seven, and
string- and blob-context Play return headers without totals. String-content
Play returns zero rows. All eighteen pre-request drains time out and all six
matched health Delivery requests return 13. Blob-content Play returns a header
without a total and queues its own delayed transaction-1
`0x4000 [0x2102, 0]` frame into the health drain before the same 13-row result.
The first timeout therefore queues no transferable frame and does not change
either successor or health result. Zero-context Play also times out with three
silent drains and 13-row health. Alternate-location Play preserves its ordinary
seven-row menu with three silent drains and 13-row health, completing all nine
Play-shaped successors. The first two Delivery-shaped successors preserve the
ordinary argumentless timeout and missing-content zero-row menu. Both have
three silent drains and 13-row health. Extra-argument Delivery preserves its
full 13-row menu, also with three silent drains and 13-row health **[OBS]**.
String- and blob-context Delivery preserve headers without totals, each with
three silent drains and 13-row health. String-content Delivery preserves its
zero-row menu with three silent drains and 13-row health. Blob-content Delivery
preserves a header without a total after the measured no-client interval, with
three silent drains and 13-row health **[OBS]**.

The first nine promoted pairs in the missing-content-Delivery precursor row
return zero rows for the precursor. They preserve the argumentless-Play
successor's silent timeout, missing-content Play's zero-row menu, and
extra-argument Play's seven-row menu. String- and blob-context Play preserve
their headers without totals, while string-content Play preserves its zero-row
menu. Those six pairs have three silent drains and 13-row health. Blob-content
Play returns a header without a total and queues its own delayed transaction-1
`0x4000 [0x2102, 0]` frame into the health drain before the same 13-row result
**[OBS]**. Zero-context Play remains a silent timeout with three silent drains
and 13-row health. Alternate-location Play preserves its seven-row menu with
three silent drains and 13-row health, completing all nine Play-shaped
successors. The first Delivery-shaped successor is argumentless Delivery; it
remains a silent timeout with three silent drains and 13-row health. A second
missing-content Delivery returns zero rows with three silent drains and 13-row
health. Extra-argument Delivery preserves its full 13-row menu with three
silent drains and 13-row health. String- and blob-context Delivery preserve
headers without totals, each with three silent drains and 13-row health
**[OBS]**. String-content Delivery preserves its zero-row menu with three
silent drains and 13-row health. Blob-content Delivery preserves its header
without a total after the measured no-client interval, with three silent drains
and 13-row health, completing the row **[OBS]**.

The complete extra-argument-Delivery precursor row returns the full 13-row
precursor menu in all sixteen pairs. Each successor preserves its ordinary
result: Play covers two timeouts, two zero-row menus, two seven-row menus, and
three headers without totals; Delivery covers one timeout, two zero-row menus,
one 13-row menu, and three headers without totals. Blob-content Play queues its
exact delayed transaction-1 `0x4000 [0x2102, 0]` frame into the health drain.
Every other drain is silent, including blob-content Delivery after its measured
three-second no-client interval. All sixteen health requests return 13 rows
**[OBS]**.

The first six promoted string-context-Delivery precursors return headers
without totals. Argumentless Play then times out, missing-content Play returns
a zero-row menu, extra-argument Play returns seven rows, string- and
blob-context Play return headers without totals, and string-content Play
returns zero rows. All six pairs have three silent
pre-request drains and 13-row health **[OBS]**.

The next blob-content-Play successor has one quarantined record/repeat
divergence. Both runs preserve the seven-row alternate-location precursor, the
successor's header without a total, and 13-row health. The record health drain
times out, while the repeat health drain receives the exact delayed transaction-1
`0x4000 [0x2102, 0]` frame queued by the successor. Neither divergent side was
promoted. A wholly fresh record and repeat both received that frame in the
health drain and now form the canonical pair. The hash-bound attempt remains
direct evidence that admission of the health connection can race this
player-routed frame **[OBS]**.

Two additional eight-case controls request the menu at location 2 and render
with the default location-1 context. Every header advertises 13 rows and every
render times out. Menu construction and rendering must use the same packed
location; the runner does not implicitly copy the request context into a
later render **[OBS]**.

The same seven families were recorded twice more with one persistent dbserver
connection per suite. All 208 case results and setup exchanges exactly equal
the reconnect controls, including recovery after every zero-context Play
timeout. The malformed suite terminates differently: in two cold attempts,
the wrong-typed Play context is followed by a dbserver close before the next
Delivery probe completes **[OBS]**.

The seventeen declarations, thirty-two successful recordings, 496 completed
executions, two expected-failure transcripts, exact behavior hashes, and
artifact roles are documented in
`data/experiments/song-info-status-location2/README.md`.
`tools/summarize_status_location2.py` validates every suite hash, paired
behavior envelope, reconnect/shared-socket equality, malformed cutoff,
precursor result, probe total, and render control.

## Legacy setup

Legacy setup preserves the seven- and thirteen-row memberships and values but
returns 12 arguments per populated `4101` row. Deleted, zero, and unknown IDs
remain exact zero-row menus. Setup width therefore changes serialization width,
not builder membership, for both request kinds **[OBS]**.

## Database and executable paths

The active live path is:

```text
PSvDBMain::OnMAnlzClientCmd                    0x101d2e6b0
  -> PSvDBMain::OnSongInfCmd                  0x101d2edc0
     -> GetPlaySongInf                        0x101ab8f70
        -> PSvAppSyncDBIF::getPlaySongInf     0x1016c14e0
     -> GetDeliveryInf                        0x101ab8f10
        -> PSvAppSyncDBIF::getDeliveryInf     0x1016cdc00
```

Both AppSync builders begin with:

```sql
select * from djmdContent
where rb_local_deleted = 0 and ID = %lu
```

Play Song Info additionally reads `ContentsLink`, `FolderPath`,
`OrgFolderPath`, `FileSize`, `ServiceID`, `MasterDBID`, and local `DBID`; cloud
path selection queries `select DBID from djmdProperty` and invokes cloud share,
sync-method, and download-root helpers. Delivery Info queries
`select DBID from djmdProperty where rb_local_deleted = 0` and resolves lookup
IDs with dynamically constructed `select Name` or `select ScaleName` queries
against `djmdArtist`, `djmdAlbum`, `djmdGenre`, `djmdKey`, and `djmdLabel`.

The wrapper accepts only its expected database location, calls the database
interface through vtable offsets `0x178` (Play) and `0x220` (Delivery), marks
the response as a four-byte result, and passes the returned row count to
`Ret4ByteToClient`. Static fallback builders are
`GetPlaySongInfDB` at `0x101ab8320` and `GetDeliveryInfDB` at `0x101ab8700`.
The retained disassembly is
`data/static-analysis/song-info-siblings.disasm.txt` **[DEC]**.

## Historical rbxport comparison

The eight ordinary canonical suites add 139 backend cases. Rbxport results are:

| Suite | Cases | Exact | Same outcome/total/row count |
| --- | ---: | ---: | ---: |
| sibling baseline | 24 | 6 | 8 |
| render controls | 42 | 0 | 42 |
| pagination | 18 | 0 | 8 |
| malformed arguments | 17 | 7 | 7 |
| legacy | 8 | 6 | 8 |
| Delivery-only 127-unit boundaries | 8 | 0 | 8 |
| DeliveryComment/ISRC 255-unit boundaries | 8 | 0 | 8 |
| Play path/cloud/file-presence matrix | 14 | 0 | 12 |

Rbxport serves the correct 7- and 13-row populated totals and exact missing-ID
menus. Its populated row fields differ. It converts `0x2202` through `0x2502`
from Rekordbox `4003` errors into empty menus, uses conventional pagination for
the ten normalized/timeout edge cases, and regularizes ten malformed forms.
Readable field diffs and actual envelopes are under the canonical result
directory **[RBX]**.

The ten status-backed suites add 212 backend cases: 36 are field-exact and 146
preserve outcome, total, and row count. Each status-backed malformed suite has
six exact cases and seven same-shape cases. Rbxport does not reproduce the
status-only argumentless Delivery header behavior **[RBX]**.

## Reproduction

```sh
cd /home/evan/workspace/rx3-research/rekordbox-link-export-research

conformance/record_song_info_siblings.sh
conformance/record_song_info_sibling_matrix.sh
conformance/record_song_info_delivery_boundaries.sh
conformance/record_song_info_delivery_wide_strings.sh
conformance/record_song_info_play_paths.sh
conformance/record_song_info_status_matrix.sh
conformance/record_song_info_status_error_experiments.sh
conformance/record_context_play_status_matrix.sh
conformance/record_context_class2_status_matrix.sh
python3 tools/summarize_play_paths.py

tools/summarize_status_siblings.py
tools/summarize_context_play_status.py
tools/summarize_context_class2_status.py
```

The ordered parser-state suites and their independent recordings are under
`data/experiments/song-info-sibling-errors/`. Direct audit retries must run
fixture activation before `start_oracle_ui.sh`; otherwise a prior headless
single-instance process can make the scheduled launch return a null process
status.

## Remaining matrix

1. Record the one missing `getCLSSyncMethod=0` equivalence class with
   controlled `MovedFromCloudDir` and filesystem sentinels. The pinned builder
   proves every nonzero integer follows the already recorded value-1 path;
   authenticated provider share roots remain an environment dimension.
2. Capture genuine status shapes from additional player models before extending
   the negative RX3/CDJ classification result to them.
3. Complete the active lifecycle-aware 16-by-16 ordered-pair rerun. Its
   per-connection setup/drain model supersedes guessed attribution from longer
   mixed sequences; 228 promoted pairs currently include the complete
   rows and all sixteen successors after argumentless, missing-content,
   extra-argument, string-context, and blob-context Delivery, plus the first
   four string-content Delivery successors.
4. Capture exact native-player `0x2202` and `0x2302` response rows. Identify any
   generation outside the five audited XDJ firmwares that successfully answers
   the `0x2402` client contract with `0x4802`; all five emit the `0x2502`
   register track length command one-way but stub both local server arms. Four
   newer firmwares provide vocabulary and format evidence only.
