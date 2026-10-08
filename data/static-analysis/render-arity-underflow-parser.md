# Track render arity-underflow decoder audit

This generated audit is pinned to Rekordbox 7.2.19 x86-64 executable SHA-256
`07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244` and validates 22 exact instructions.

`PSvDBConnection::ReceiveCommand` allocates a `0x98`-byte command object and
zeroes the complete allocation before decoding the argument count, tag list,
or values. The zero-count branch skips the field loop. Each decoded value slot
starts at offset `0x18` and advances by eight bytes.

`PSvDBMain::GetListBufContents` reads offsets `0x18`, `0x20`, and `0x28`
before its first count comparison, which tests for six arguments. Missing
mandatory slots therefore contain zero rather than prior-message state.

The source-derived projection is:

| Total arguments | Context slot | Offset slot | Count slot |
| ---: | --- | --- | --- |
| 0 | `0` | `0` | `0` |
| 1 | supplied argument 1 | `0` | `0` |
| 2 | supplied argument 1 | supplied argument 2 | `0` |

This proves storage initialization and field projection, not the response
class or connection lifecycle. The queued real-Rekordbox oracle remains the
behavioral authority.
