# Track render numeric-field decoder audit

This generated audit is pinned to Rekordbox 7.2.19 x86-64 executable SHA-256
`07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244` and validates 30 exact instructions plus the complete
51-entry `DBCommon_GetCateKind` table.

The normal eight render positions are consumed as follows:

| Position | Width read | Role |
| ---: | ---: | --- |
| 1 | 64 | packed list-buffer context |
| 2 | 64 | requested offset, narrowed downstream |
| 3 | 32 | requested count |
| 4 | 16 | first-row character seek key |
| 5 | 0 | client-reported total; unread by `GetListBufContents` |
| 6 | 16 | category ID passed through `DBCommon_GetCateKind` |
| 7 | 32 | nonzero secondary-override gate |
| 8 | 32 | secondary selector override |

Argument 4 is therefore not reserved. Zero follows ordinary offset pagination.
A nonzero low word enters `GetListBuf1stRow`'s normalized first-character scan;
ASCII lowercase is promoted to uppercase and `U`/`Unknown` has a dedicated
path. Low word `0xffff` wraps the internal increment and rejoins the ordinary
path. High 16 bits are never read.

Argument 5 is sent by clients as the menu total but has no read in the complete
renderer body. Argument 6 is also truncated to its low word. Its exact category
map is: 1-24 map identically; 25-29 map to zero; 30-32 map identically; 33-39 map to zero; 40 maps identically; 41-49 map to zero; and 50-51 map identically. Values outside 1-51 map to zero.

The checked-in live matrix tests representative character classes, wrap and
high-word aliases, client-total boundaries, and every category-map range. The
static findings constrain interpretation but do not predict returned rows;
the queued real-Rekordbox record/repeat remains authoritative.
