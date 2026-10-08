# Key notation and Camelot oracle

This oracle separates three inputs that Rekordbox exposes under similar names:

1. the desktop View > Display key preference;
2. the local CDJ device-setting file used by Link Export; and
3. the spelling stored in `djmdKey.ScaleName`.

Only the second input controls Classic versus Alphanumeric/Camelot text in the
measured Link Export responses. The distinction is proven by two independent
real-Rekordbox matrices and by the serving implementation in both the Windows
and macOS binaries.

## Result

Rekordbox 7.2.19 reads the local CDJ key-category display style from:

```text
C:\Users\Research\AppData\Roaming\Pioneer\rekordbox6\DEVSETTING.DAT
```

Changing its key-style field produces the following complete protocol change
**[OBS]**:

| Device style | File value | Key root | First-track Key | Key + BPM |
| --- | ---: | --- | --- | --- |
| Classic | 1 | `Abm, B, ... Am, C, ... E` | `Am` | `Am - 120.0 bpm` |
| Alphanumeric | 2 | `1A, 1B, ... 8A, 8B, ... 12B` | `8A` | `8A - 120.0 bpm` |

Every changed field is either key text or the UTF-16 byte length belonging to
that text. Numeric Key IDs, BPM values, request outcomes, row counts, row
ordering, pagination, packed contexts, and all unrelated metadata are
identical. Both 13-case states were captured from fresh Rekordbox processes and
repeat-verified after another fixture reset and process restart.

The controlled first track demonstrates every row surface:

| Surface | Classic | Alphanumeric |
| --- | --- | --- |
| Key root `0x1014` | `Am`, `C` | `8A`, `8B` |
| Key distance labels `0x1114` | `Abm, B` | `1A, 1B` |
| Collection, Key secondary | `Am - 120.0 bpm`; tertiary `Am` | `8A - 120.0 bpm`; tertiary `8A` |
| Collection, BPM secondary | numeric BPM; tertiary `Am` | numeric BPM; tertiary `8A` |
| Smart playlist, Key secondary | `Am - 120.0 bpm`; tertiary `Am` | `8A - 120.0 bpm`; tertiary `8A` |
| Smart playlist, BPM secondary | numeric BPM; tertiary `Am` | numeric BPM; tertiary `8A` |
| Display Song Info, Key selector | `Am` in the selected row and Key detail | `8A` in the selected row and Key detail |
| Display Song Info, BPM selector | numeric BPM; Key detail `Am` | numeric BPM; Key detail `8A` |
| Delivery Info, Key selector | selected row `Am` | selected row `8A` |
| Delivery Info, BPM selector | numeric BPM; tertiary `Am` | numeric BPM; tertiary `8A` |

A render-time BPM override over a persisted Key setting has an empty argument 5
and composite type `0x0d04`; BPM is carried numerically in arguments 0 and 15
while Key is carried in tertiary argument 14. A player may render that
numeric-plus-tertiary data as a BPM/Key pair.

A persisted BPM secondary setting changes the same `0x0d04` row to include the
literal server-authored composite in argument 5. Fresh ordinary and Smart
captures return `120.0 bpm - Am` in Classic and `120.0 bpm - 8A` in
Alphanumeric, with the standalone Key repeated in argument 14 **[OBS]**. The
Key-selected row analogously carries `Am - 120.0 bpm` or
`8A - 120.0 bpm` under type `0x0f04`.

The RX3 six-argument sort cross adds the active-sort rule. With Classic device
style, active Key sort returns `Am - 120.0 bpm`, while active BPM sort returns
`120.0 bpm - Am`; both retain standalone `Am` in argument 14. The same
formatter call chain applies the device style to each key component, so the
Alphanumeric forms are `8A - 120.0 bpm` and `120.0 bpm - 8A`. Artist and Album
sorts return only their own text. A mismatching eight-argument BPM override has
an empty argument 5, while a mismatching Key selection returns only the key
spelling; composites are preserved cached list-builder output, not a universal
render-time concatenation **[OBS, DEC]**.

## Desktop preference cross

The separate desktop matrix changes `KeyStringSetting` and `ShowOriginalKey`
in Rekordbox's preferences:

| Desktop state | `KeyStringSetting` | `ShowOriginalKey` | Link Export result |
| --- | ---: | ---: | --- |
| Classic, normalized | 1 | 0 | Classic |
| Classic, database | 1 | 1 | Classic |
| Alphanumeric, normalized | 2 | 0 | Classic |
| Alphanumeric, database | 2 | 1 | Classic |

All four 13-case response envelopes are byte-identical after provenance is
removed, with behavior SHA-256
`339d9c825fd448a4d9b1924aeb2fd0500eb131d7bfb11f15016ff8fb7b401ecf`
**[OBS]**. Each state was restart-isolated and independently repeated.

This cross establishes that the desktop preference does not directly select
the Link Export notation for the measured process state. It does not contradict
the device-setting result: all four runs retained a Classic `DEVSETTING.DAT`,
while only the new matrix changes the file that the serving path reads.

Desktop code can synchronize preferences into device settings during other
workflows. That synchronization is a state transition, not evidence that the
serving formatter reads `KeyStringSetting` for each response.

## Device-setting format

The retained baseline and generated variants are:

```text
data/experiments/key-notation/device-settings/baseline/DEVSETTING.DAT
data/experiments/key-notation/device-settings/generated/classic.DAT
data/experiments/key-notation/device-settings/generated/alphanumeric.DAT
```

The complete file is 140 bytes:

| File offset | Width | Meaning |
| ---: | ---: | --- |
| `0x00` | 4 | little-endian header size `0x60` |
| `0x64` | 4 | little-endian payload size `0x20` |
| `0x68` | 4 | payload magic `0x12345678` |
| `0x74` | 1 | key-category display style: 1 Classic, 2 Alphanumeric |
| `0x88` | 4 | uint32 field containing the 16-bit payload CRC |

The CRC is CRC-CCITT over the 32 bytes at `0x68..0x87`, initial value zero.
Python's `binascii.crc_hqx(payload, 0)` reproduces it exactly.

| Variant | SHA-256 | CRC |
| --- | --- | ---: |
| Baseline / Classic | `68fea233ec9dcc077204687ddc108cbe9f4272e003d789a0534857eaf4c9c85d` | `0x98e1` |
| Alphanumeric | `62fabc001fc2ee0747fca9a44e589c29f9b6f5d29b1166537bf7f26a9679e1ff` | `0xc634` |

`tools/mutate_device_setting.py` validates the sizes, magic, style range, and
CRC before producing a variant. It modifies only the style byte and checksum.
`conformance/test_device_key_style.py` locks those invariants into the suite.

## Serving implementation

The Windows AppSync track formatter calls function `0x14235e5e0` for Key text
**[DEC]**. Its behavior matches the symbolized macOS function:

```text
exchangeKeyNameIfNeed(unsigned short **, bool, bool)
  -> getMusicKeyNotaion(forceRefresh)
  -> cdjDeviceSetting::DeviceSettingFile::isLocalKeyCatDispStyleNormal()
```

The local predicate returns true unless a valid loaded device-setting object
contains style byte 2. `getMusicKeyNotaion` maps true to notation 1 (Classic)
and false to notation 2 (Alphanumeric). It caches the result, but refreshes it
when its caller requests a fresh setting. The Windows formatter's Key call and
the real cold-process matrix agree with this control flow.

The formatter then parses the input Key into one of 24 normalized harmonic
positions and chooses the Classic or Alphanumeric label table. It replaces the
UTF-16 allocation only when the selected label differs. Raw database spelling
therefore does not pass through unchanged.

Retained evidence:

```text
data/static-analysis/windows/exchange-key-name.disasm.txt
data/static-analysis/windows/local-key-style.disasm.txt
data/static-analysis/device-key-style.disasm.txt
```

The first two artifacts come from the exact installed Windows PE:

```text
C:\Program Files\rekordbox\rekordbox 7.2.19\rekordbox.exe
SHA-256 c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37
```

The third retains the symbolized macOS functions, file validation, CRC body,
style setters/getters, and preference-to-file synchronization path.

`@AlphanumericKeyEnable` is a separate device-profile capability string. No
captured setup field or identity mutation has connected it to this local style
byte. It may describe whether a player supports an Alphanumeric option, while
`DEVSETTING.DAT` selects the current local presentation. The lab keeps those
dimensions separate until a controlled response proves otherwise.

## Database spelling

`conformance/fixtures/generated/key-notation/` is an encrypted deterministic
eight-track database. Its database SHA-256 is
`b3865491d069e8cd2caf3884af6d6b3c08ab53692e2003fc86f1f997ff746701`;
its canonical decrypted fingerprint is
`a9286ce12410b25001a324480ba4923986027b51ec4b9e4d51bff54063e0851a`.

The fixture deliberately stores `08A` and `08B` in `djmdKey.ScaleName` for Key
IDs 5001 and 5002 **[DB]**. The Alphanumeric oracle emits canonical `8A` and
`8B`, without the stored leading zero. The Classic oracle emits `Am` and `C`.
This proves that raw database text, normalized harmonic identity, and selected
display notation are distinct values.

The Smart rule returns the same eight Content IDs as the ordinary collection,
which allows the two row builders to be compared without media files.

## Declared matrix

Each device-setting state uses the same concise 13-case suite. Two focused
Alphanumeric suites additionally cross the persisted BPM selection through
ordinary and Smart row builders:

| Cases | Requests and purpose |
| --- | --- |
| 3 | Key root `0x1014`, distance `0x1114`, tracks `0x1214` |
| 3 | Ordinary collection with BPM, Key, and Key sort |
| 3 | Smart playlist with BPM, Key, and Key sort |
| 2 | Display Song Info with BPM and Key selectors |
| 2 | Delivery Info with BPM and Key selectors |
| 3 | Persisted BPM Sort/ordinary rows (2) and Smart rows (1) |

The exact root sequences are:

```text
Classic:
Abm, B, Ebm, F#, Bbm, Db, Fm, Ab, Cm, Eb, Gm, Bb,
Dm, F, Am, C, Em, G, Bm, D, F#m, A, Dbm, E

Alphanumeric:
1A, 1B, 2A, 2B, 3A, 3B, 4A, 4B, 5A, 5B, 6A, 6B,
7A, 7B, 8A, 8B, 9A, 9B, 10A, 10B, 11A, 11B, 12A, 12B
```

Notation does not change Key sort order. Collection order remains
`10001,10003,10005,10007,10002,10004,10008,10006`; Smart order remains
`10001,10003,10005,10007,10002,10004,10006,10008`.

## Deferred backend comparison

These suites currently stop at canonical expectations captured from real
Rekordbox. They are deliberately backend-neutral so they can later run without
changes against rbxport, but that replay is outside the present research phase.
No rbxport result is part of this device-style oracle.

The machine-readable binding is
`data/experiments/key-notation/device-setting-summary.json`. It records both
setting files, CRCs, suite/golden hashes, fixture identity, exact roots, sort
orders, static evidence, and repeats.

## Reproduction

Generate and validate the device settings and suites:

```sh
tools/mutate_device_setting.py \
  data/experiments/key-notation/device-settings/baseline/DEVSETTING.DAT \
  data/experiments/key-notation/device-settings/generated/classic.DAT \
  --style classic
tools/mutate_device_setting.py \
  data/experiments/key-notation/device-settings/baseline/DEVSETTING.DAT \
  data/experiments/key-notation/device-settings/generated/alphanumeric.DAT \
  --style alphanumeric
conformance/generate_device_key_style_suites.py
../rekordbox-windows/.venv/bin/python -m unittest \
  conformance.test_device_key_style
```

Record both states from the isolated guest:

```sh
conformance/record_device_key_style_matrix.sh
conformance/record_device_key_style_matrix.sh --resume
```

The recorder refuses to overwrite a golden. Its EXIT trap restores the
baseline device setting and activates the `play-paths` fixture. Real-Rekordbox
execution remains behind `../rekordbox-windows/vmctl isolation-check`, so the
synthetic identity cannot be emitted from the physical-LAN VM.

Summarize the real-Rekordbox evidence:

```sh
../rekordbox-windows/.venv/bin/python \
  tools/summarize_device_key_style.py
```

The older desktop-preference matrix remains reproducible with
`conformance/record_key_notation_matrix.sh` and
`tools/summarize_key_notation.py`.

The Windows guest needs no media files for either matrix. Rekordbox constructs
these menu and metadata responses entirely from database and setting data
**[OBS]**.
