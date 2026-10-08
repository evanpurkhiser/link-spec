# Database-interface selection audit

This generated report inventories constructor-style x86-64 `__text` LEA
references into the complete `PSvAppSyncDBIF` and `PSvMasterDBIF` tables.
Constructor-style object vptrs use the Itanium ABI table offset `+0x10`.

Binary SHA-256: `07dcecbaf304f777e435539c83c7dcc02e41de1eaf2e0a75e8a9852e4411a244`.

| Interface | Vtable | Bytes | LEA refs | Base refs | Exact `+0x10` refs |
| --- | ---: | ---: | ---: | ---: | ---: |
| `appsync` | `0x105656d30` | `0x328` | 6 | 4 | 2 |
| `master` | `0x1056f54a8` | `0x328` | 3 | 3 | 0 |

## appsync

- `0x100f901b3` in `__ZN20FilterSettingManagerC2ERKN4juce6StringEP9PSvDBMain9RbDBIndex`: `lea rax, [rip + 0x46c6b76]` -> vtable `0x0`.
- `0x100f92555` in `__ZN20FilterSettingManager10setDBIndexE9RbDBIndex`: `lea rcx, [rip + 0x46c47d4]` -> vtable `0x0`.
- `0x100f92d8b` in `__ZN11TrackFilterC2E9RbDBIndexRKN4juce10OwnedArrayI15FilterConditionNS1_20DummyCriticalSectionEEEP9PSvDBMain`: `lea rax, [rip + 0x46c3f9e]` -> vtable `0x0`.
- `0x1016dccf4` in `__ZN14PSvAppSyncDBIFD1Ev`: `lea rax, [rip + 0x3f7a045]` -> vtable `0x10`.
- `0x1016dcd19` in `__ZN14PSvAppSyncDBIFD0Ev`: `lea rax, [rip + 0x3f7a020]` -> vtable `0x10`.
- `0x102520708` in `__ZN9PSvDBMain15SetSharedDBInfoEbPKhS1_jS1_`: `lea rcx, [rip + 0x3136621]` -> vtable `0x0`.

## master

- `0x100f901ed` in `__ZN20FilterSettingManagerC2ERKN4juce6StringEP9PSvDBMain9RbDBIndex`: `lea rax, [rip + 0x47652b4]` -> vtable `0x0`.
- `0x100f92596` in `__ZN20FilterSettingManager10setDBIndexE9RbDBIndex`: `lea rcx, [rip + 0x4762f0b]` -> vtable `0x0`.
- `0x100f92dd5` in `__ZN11TrackFilterC2E9RbDBIndexRKN4juce10OwnedArrayI15FilterConditionNS1_20DummyCriticalSectionEEEP9PSvDBMain`: `lea rax, [rip + 0x47626cc]` -> vtable `0x0`.

## Boundary

A reference to vtable offset zero followed by an add of `0x10` is also a
constructor-style selection; inspect the attributed function disassembly.
A zero reference count is a bounded negative result for RIP-relative LEA
selection in the pinned x86-64 text slice. It does not exclude computed
addresses, non-LEA or non-text initializers, arm64-only behavior, or
construction by dynamically loaded code.
