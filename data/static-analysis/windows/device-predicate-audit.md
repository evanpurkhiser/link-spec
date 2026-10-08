# Windows device-predicate audit

Source: Rekordbox 7.2.19 PE `c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37`.

| Role | Address | Direct calls/jumps | Result |
| --- | --- | ---: | --- |
| Display `isAIO` | `0x1423815c0` | 1 | Called by the AppSync Display formatter |
| Disconnect with inline AIO clear | `0x142380930` | 1 | Erases player key from the `0x790` map under the `0x7a0` lock |
| Map-only AIO clear helper | `0x142381700` | 0 | Same keyed erase, retained without a direct caller |
| Standalone content compatibility | `0x14227e200` | 1 | Called by the Master-interface row path |
| `GetListBufRowContent` | `0x14238c720` | 3 | AppSync path inlines the content predicate |

Windows therefore differs from the macOS call graph without differing in the
observed decisions. The active AppSync track-row path reads `FileType` and
`SampleRate` itself, rejects bytes 5 and 6, conditionally admits bytes 11 and
12 only at 44,100 or 48,000 Hz, and never reads BitDepth. Its alternate Master
path calls the standalone predicate at `0x14227e200`. Disconnect performs the
AIO-cache erase inline; it does not directly call the separately emitted
map-only helper.

The direct-reference count is exhaustive for x86-64 `call rel32` and `jmp
rel32` instructions targeting these five recovered functions. A full-image
search also finds zero little-endian 64-bit absolute pointers to any of the
five addresses, excluding ordinary PE pointer-table and vtable storage for
these exact functions. Computed pointers and semantically duplicated inline
code require separate proof; the two known inline decisions above are retained
as disassembly slices.
