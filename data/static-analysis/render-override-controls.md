# Track render override-control decoder audit

This generated audit is pinned to Rekordbox 7.2.19 x86-64 executable SHA-256
`07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244` and validates 24 exact instructions across the render,
row-builder, and secondary-extractor functions.

Eight-argument rendering reads argument 7 as a 32-bit value and immediately
canonicalizes it with `setne`; every nonzero bit pattern reaches the row builder
as the same one-byte true value. Argument 8 remains a full 32-bit value. When
the gate is true, selector zero retains the database-selected column and a
nonzero selector replaces it.

The effective selector has two widths downstream. `ReturnIconID` receives its
signed low byte, while `Get_SubCategoryValue` receives all 32 bits. The latter
subtracts two and admits only the unsigned interval 2 through 17. Consequently,
a high-word value whose low byte resembles a valid selector is not statically
equivalent to that selector: icon comparison and value extraction can disagree.

The live matrix crosses boolean-boundary gate values, selector zero and one,
the reserved 14 hole, the upper valid selector, the first out-of-range value,
low-byte wrap cases, a high-word Artist lookalike, and signed/unsigned 32-bit
boundaries. Returned `0x4101` rows remain authority observations rather than
predictions from this decoder audit.
