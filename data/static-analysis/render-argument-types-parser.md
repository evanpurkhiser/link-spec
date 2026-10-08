# Track render argument-type decoder audit

This generated audit is pinned to Rekordbox 7.2.19 x86-64 executable SHA-256
`07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244` and validates 27 exact instructions plus the six-entry
`PSvDBConnection::ReceiveCommand` argument-tag jump table.

The command decoder accepts variable-width tag `2` as a UTF-16 array and tag
`3` as a byte blob. Both paths require an earlier argument: its decoded numeric
slot supplies the allocation/read length. A string length must be below
`0x201`; a blob length must be below `0x500000`. Position one therefore cannot
carry either variable-width type through this decoder because it has no
preceding length slot.

Successful string and blob decoding stores the allocation pointer in the same
eight-byte value-slot array used by numeric arguments. `GetListBufContents`
reads those slots directly and does not inspect their tags. A wrong-typed
render may consequently fail in framing/decoding, reach dispatch with a pointer
interpreted numerically, time out, disconnect, or affect process health.

The declared live matrix preserves all normal numeric neighbors and changes
exactly one tag/value. That deliberately measures the combined real parser and
render behavior; it does not rewrite a preceding argument to make the
variable-width value parser-admissible. The live oracle, not this static
projection, determines every response and process outcome.
