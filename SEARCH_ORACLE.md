# Search oracle

This report combines real rekordbox 7.2.19 recordings, deterministic encrypted
fixtures, and the pinned x86-64 implementation of `djeplGetNewSearchResult`.
The canonical oracle contains 160 cases: 44 general Search cases against the
`full` fixture, four cases against each of the Artist-, Album-, Track-, and
File-Name-disabled settings fixtures, 16 ceiling/pagination cases against a
1,005-track fixture, and 19 Unicode/NUL cases against an eight-track text
fixture. Search Track adds 34 request/sort/error cases, 12 pagination and
ceiling cases against 5,005 tracks, and 19 cache-independent sort cases against
10,005 tracks. Every case was immediately repeated against the same Rekordbox
process **[OBS, DB, DEC]**.

## Request and response

Search uses request `0x1300`:

```text
[packed context, sort, declared UTF-16 byte length, query string, trailing field]
```

The declared length includes the UTF-16 NUL terminator. `FIXTURE` therefore has
length 16. Lengths 0, 1, 2, 14, and 15 returned argumentless `0x0100`; lengths
16, 17, 18, and 256 were accepted. Acceptance is a lower-bound check rather
than equality. Values 0, 1, and `0xffffffff` in the trailing field produced the
same Beta result. Sort IDs 0, 1, 3, and 17 produced the same `FIXTURE` result
and order in this fixture **[OBS]**.

Successful requests return an ordinary `0x4000` menu header, `0x4101` rows,
and the extended 16-argument row shape. Entity and content rows share the menu:

| Domain | Primary ID | Primary text | Row discriminator |
| --- | --- | --- | ---: |
| Artist | `djmdArtist.ID` | `djmdArtist.Name` | argument 6 = `0x07` |
| Album | `djmdAlbum.ID` | `djmdAlbum.Name` | argument 6 = `0x02` |
| Track title | `djmdContent.ID` | `djmdContent.Title` | argument 6 = `0x0f04` with Key selected |
| File name | `djmdContent.ID` | `djmdContent.FileNameL` | argument 6 = `0x0f04` with Key selected |

Content rows otherwise use the normal track renderer, including selected
secondary-column text and compatibility fields. Artist and Album rows precede
matching content rows in every mixed-domain observation **[OBS]**.

## Matching algorithm

The implementation performs these steps **[DEC]**:

1. Reject a null query pointer or zero internal character count.
2. Split on UTF-16 space (`0x0020`), ignoring repeated, leading, and trailing
   spaces.
3. Uppercase ASCII `a` through `z` by subtracting `0x20`. BMP code units
   outside that range are compared without Unicode normalization or case
   folding; supplementary pairs do not produce live matches.
4. Require every nonempty token to occur as a contiguous substring in a
   candidate value. Token order is irrelevant.
5. Scan only domains enabled by the current `djmdCategory` rows.
6. Apply `dsqlIsLinkExportVisibleTrack` to every content candidate.
7. Deduplicate content IDs with a bitmap for IDs through 100,000.
8. Stop at the wrapper's fixed maximum of 1,000 inserted results.

Live results confirm ASCII case insensitivity: `FIXTURE`, `fixture`, and
`FiXtUrE` are identical. `ALPHA ONE`, `ONE ALPHA`, `ALPHA  ONE`, leading
spaces, and trailing spaces all return only Alpha One. The symbol query `Ω`
finds Unicode Ω Search, while ASCII `OMEGA` does not. A spaces-only query and
an empty query return zero rows **[OBS]**.

The implementation contains an additional internal content-column branch, but
changing the fifth protocol argument did not enable it. In particular, every
fixture track has `BETA` in `djmdContent.SearchStr`, while all three tested
trailing values still returned only Beta Artist and Beta One. Comments and the
DOS short file-name column are not searched in this path **[OBS, DEC]**.

## Unicode and embedded NUL

The `search-text` fixture distinguishes representations that ordinary ASCII
tests cannot **[OBS, DB]**:

| Query | Result |
| --- | --- |
| `PRECOMPOSED ÉCLAIR` | only `Precomposed Éclair` |
| `PRECOMPOSED éCLAIR` | only `Precomposed éclair` |
| `COMBINING ÉCLAIR` or `COMBINING éCLAIR` | both decomposed-base rows |
| precomposed accent against a decomposed title, or the reverse | zero rows |
| `SHARP ß` | only `Sharp ß Search` |
| `SHARP ẞ` or `SHARP SS` | zero rows |
| `DOTTED İ` | only `Dotted İ Search` |
| `DOTTED i` | zero rows |
| `🙂`, `🙃`, or `emoji 🙂` | zero rows |

The decomposed pair shares a combining acute code unit; its ASCII `E/e` base
still receives ordinary ASCII folding. Rekordbox performs neither canonical
composition nor non-ASCII case expansion. Exact supplementary-plane symbols
do not match the same symbols stored in titles. A one-symbol emoji request
with the correct six-byte declared length is a valid zero-row menu; declaring
four bytes returns argumentless `0x0100`, proving the field length counts the
surrogate pair as two UTF-16 units plus the terminator.

An embedded `U+0000` terminates the effective query. NUL alone behaves as an
empty query and returns zero rows. `EMOJI<NUL>` and
`EMOJI<NUL>🙂` both return the two `Emoji` title rows, while
`🙂<NUL>` returns zero. Bytes after the first NUL are accepted on the wire but
do not participate in matching **[OBS]**.

## Category-controlled domains

`djeplGetNewSearchResult` reads `djmdCategory` before it scans searchable
tables. Its 15-entry jump table maps four enabled menu items to four independent
domain flags **[DEC]**:

| `MenuItemID` | UI category | Search domain |
| ---: | --- | --- |
| 2 | Artist | every `djmdArtist.Name`, including artists referenced as Remixer or Original Artist |
| 3 | Album | `djmdAlbum.Name` |
| 4 | Track | `djmdContent.Title` |
| 16 | File Name | `djmdContent.FileNameL` |

The live fixture cross proves each gate independently **[OBS, DB]**:

| Disabled category | `ALPHA` | `ALBUM` | `FIXTURE` | `BETA` |
| --- | ---: | ---: | ---: | ---: |
| None | 3 | 4 | 10 | 2 |
| Artist | 2 | 4 | 8 | 1 |
| Album | 3 | 1 | 10 | 2 |
| Track | 1 | 3 | 10 | 1 |
| File Name | 3 | 4 | 2 | 2 |

The removals are exact. Artist-disabled `FIXTURE` removes Fixture Remixer and
Fixture Original but retains eight file-name rows. Album-disabled `ALBUM`
retains only the track titled Unknown Album. Track-disabled `ALPHA` retains
only Alpha Artist. File-Name-disabled `FIXTURE` retains only the two artist
entities.

This coupling means a Category UI change alters both the root navigation menu
and Search's database domains. Search does not merely query a fixed global
index.

## Search Track `0x1500`

Search Track is a genuine server command distinct from ordinary Search. Its
wire declaration is exactly four arguments:

```text
0x1500 [packed context, sort, declared UTF-16 byte length, query string]
```

The formatter writes an argument count of four with type tags `number,
number, number, string`. The second number is a sort ID, not a search-domain or
mode selector. `PSvDBMain::OnOtherListCmd` dispatches both Search commands to
the same virtual search interface, but passes a 1,000-row budget for `0x1300`
and a 5,000-row budget plus the new-command flag for `0x1500`. The resolved
backend is `PSvAppSyncDBIF::getNewSearchResult`; the separate new-command body
is retained in `search-result-implementation.disasm.txt` **[DEC]**.

Live requests establish the following validation rules **[OBS]**:

- sort IDs 0 through 17 are accepted and all return eight fixture matches;
- the sort value is consumed as a signed low byte: 256 aliases 0, while 127,
  128, and 255 return `0x4000` with total `0xffffffff`;
- a declared length of zero or shorter than the query returns argumentless
  `0x0100`;
- omitting the string produces an empty `0x4000` menu;
- appending ordinary Search's fifth argument is tolerated and ignored;
- empty and unmatched queries return valid zero-row menus;
- the same uppercase/lowercase non-ASCII distinction observed for `0x1300`
  remains visible.

All 18 sort IDs were recorded over the same eight-row result. They produce
eight distinct exact orders. IDs 0, 1, 9, 11, and 14 share default title order;
2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 15, 16, and 17 exercise the remaining seven
orders. The canonical golden retains the complete typed rows, so equivalence
classes do not replace field-level assertions.

The query ceiling depends on the selected sort path **[OBS, DB, DEC]**:

| Request | Sort | Eligible rows | Reported total |
| --- | ---: | ---: | ---: |
| ordinary Search `0x1300` | 0 | 5,005 / 10,005 | 1,000 |
| Search Track `0x1500` | 0 | 5,005 / 10,005 | 5,000 |
| Search Track `0x1500` | 17 | 5,005 | 5,005 |
| Search Track `0x1500` | each of 1-17 | 10,005 | 10,005 |

The 10,005-row profile places a distinct `SORT00` through `SORT17` token in
every title and issues each sort with its own token. This prevents an earlier
query's cached rowset from supplying the next result. A separate SearchStr-only
profile returned zero for both `0x1300` and every `0x1500` sort, proving
`djmdContent.SearchStr` is not directly searched by this path. Those negative
column probes remain experimental evidence; the cache-independent title probe
is canonical.

## Pagination

Search uses the same list-buffer rendering normalization as other menus
**[OBS]**:

- overlapping windows preserve the repeated row;
- `(offset=0, count=0)` returns the first row;
- an offset at or beyond the total clamps to the final row;
- a zero-count request at the total returns the final row;
- an overrun window is shifted backward to preserve its requested count when
  the result contains enough rows.

The `search-ceiling` fixture contains 1,005 visible title matches with IDs
20,001 through 21,005. The broad `CEILING` query reports exactly 1,000 rows,
and a complete paged render returns `Ceiling Match 0001` through
`Ceiling Match 1000` in order. Narrow queries independently return
`Ceiling Match 1001` and `Ceiling Match 1005`, proving those source rows exist
and that the broad result was truncated by the wrapper. Five-row requests
starting at offsets 995, 996, 998, 999, or 1000 all return the right-aligned
window 0996 through 1000. Single-row offsets 999, 1000, and 1001 all return row
1000 **[OBS, DB, DEC]**.

Search Track applies the same normalization at its 5,000-row default-sort
ceiling. A five-row window crossing that ceiling is shifted to rows 4996-5000;
offsets 5000 and 5001 both return row 5000. A complete render retrieves exactly
rows 0001-5000 in ten pages, while narrow queries independently retrieve rows
5001 and 5005. Explicit sort 17 reports all 5,005 rows **[OBS, DB]**.

The canonical suite retains all render request and reply arguments, not only
the normalized row list.

## Canonical artifacts

```text
conformance/suites/search.json
conformance/suites/search-ceiling.json
conformance/suites/search-text.json
conformance/suites/search-track.json
conformance/suites/search-track-ceiling.json
conformance/suites/search-track-large-title-sort.json
conformance/suites/generated/search-category-{02,03,04,21}-disabled.json
conformance/fixtures/generated/search-ceiling/
conformance/fixtures/generated/search-text/
conformance/fixtures/generated/search-track-ceiling/
conformance/fixtures/generated/search-track-large-title/
conformance/goldens/rekordbox-7.2.19/xdj-rx3/search*.json
conformance/record_search_category_matrix.sh
data/experiments/search/
data/static-analysis/search-query.disasm.txt
data/static-analysis/request-1500-immediates.txt
data/static-analysis/request-1500.disasm.txt
data/static-analysis/search-result-implementation.disasm.txt
tools/promote_search_oracle.py
tools/summarize_search_oracle.py
```

`data/experiments/search/` preserves the exploratory declarations and their
independently repeated responses. `tools/promote_search_oracle.py` verifies
their suite hashes and emits exact total/row-count expectations before a fresh
canonical recording. `tools/summarize_search_oracle.py` validates the canonical
hashes, fixture fingerprints, expected boundary outcomes, Category matrix,
static-analysis artifact, and rbxport replay counts, then writes
`data/experiments/search/summary.json`.

## rbxport replay

The same ten suites were replayed against the pinned rbxport tree. Across 160
cases, 23 are field-exact and 61 preserve outcome, total, and row count. The
principal differences are **[RBX]**:

- an empty query returns all eight tracks instead of zero rows;
- populated searches return tracks rather than Rekordbox's mixed Artist,
  Album, title, and file-name rows;
- multiple tokens use different membership semantics;
- Category settings do not gate search domains;
- declared-length rejection and Search pagination normalization differ;
- rbxport exposes all 1,005 broad-query matches instead of applying the 1,000
  row cap, and it does not right-align overrun windows;
- rbxport normalizes/folds the accent pairs, equates `ß`, `ẞ`, and `SS`,
  equates dotted `İ` with ASCII `i`, and treats emoji-only and NUL-only queries
  as empty filters that return all tracks;
- track Key strings and extended row fields retain the general serialization
  differences.
- rbxport accepts `0x1500` but routes it through the same track-only search as
  `0x1300`, ignores its sort ID, and does not reproduce the signed-byte errors,
  sort-specific 5,000/default ceiling, explicit-sort uncapping, or exact sort
  orders.

Readable diffs and actuals are under
`conformance/results/rbxport/c144f19+tree.80e87ec8aace/xdj-rx3/search*`.

## Remaining coverage

The server-side `0x1500` request, validation, sorting, ceiling, and pagination
paths are covered. A physical RX3 was deliberately excluded from the isolated
network, so the exact touchscreen actions and discovery/status conditions that
cause the RX3 to emit `0x1500` remain a client-UI capture question. Additional
fixtures are needed only for sort tie-breakers beyond the exact eight-row
orders and for an explicit-sort population above 10,005 rows.
