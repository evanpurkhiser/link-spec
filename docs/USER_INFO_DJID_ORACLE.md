# User-info and DJ-ID oracle

Request `0x3006` is the Link Export user-info request named
`CMD_GET_USER_INFO` by CDJ-3000 firmware. Rekordbox routes it through
`PSvDBMain::OnUserCmd` and returns `0x4d02` (`CMD_RET_USER_INFO`). This exchange
is part of the player's post-load browsing lifecycle: the CDJ-3000 asks for
user info before it requests Delivery Song Info for the loaded track **[DEC,
CDJ-DEC]**.

The generated audit is:

```text
data/static-analysis/user-info-djid.json
data/static-analysis/user-info-djid.disasm.txt
tools/audit_user_info_djid.py
conformance/test_user_info_djid.py
```

It binds the symbol-rich Rekordbox 7.2.19 x86-64 Mach-O and the retained
CDJ-3000 3.20 client analysis by SHA-256. The two sources prove different
halves of the exchange; neither is silently promoted to a live 7.2.19 wire
observation.

## Rekordbox reply construction

`OnUserCmd` accepts exactly kind `0x3006`. It allocates 160 bytes, zeroes all
five 32-byte blocks, then calls `PSvDBMain::GetDJID` **[DEC]**.

When a DJ ID is loaded, `GetDJID` copies exactly 32 bytes into the beginning of
that buffer. Rekordbox returns:

```text
0x4d02 [0x3006, 0, 0xa0, blob(160)]
```

The blob's first 32 bytes are the DJ ID and its remaining 128 bytes are zero.
When no DJ ID is loaded, Rekordbox still returns kind `0x4d02`, declares
length zero, and supplies the command format's zero-length blob field
**[DEC]**:

```text
0x4d02 [0x3006, 0, 0, blob(0)]
```

This field count comes from `DBCFmt_GetCmdPrmFmt`, which declares four
parameters for `0x4d02`: three numbers followed by a blob. The null pointer
passed by `OnUserCmd` controls the blob's zero length; it does not remove the
typed argument.

An unrecognized kind reaching `OnUserCmd` returns internal status
`0xfffffffe`; normal top-level unknown-command handling is documented in
`LINK_EXPORT_REQUEST_VOCABULARY.md`.

## Configuration source

The macOS build constructs this path **[DEC]**:

```text
<user Application Support>/Pioneer/rekordbox6/djprofile.nxs
```

`common::PropertyPath` supplies the `Application Support/Pioneer/rekordbox6`
directory. The `KuvoService::nxsName` static initializer assigns the exact
filename `djprofile.nxs`, and `KuvoService::nxsFile` joins the two.

`KuvoService::isValid` admits a file only when all of these conditions hold:

1. It exists as a regular file.
2. Its lowercased extension is `.nxs`.
3. Its length is exactly 160 bytes.
4. The big-endian unsigned 32-bit value at offset 28 equals the modulo-`2^32`
   sum of the little-endian value at offset 0 and the big-endian values at
   offsets 4, 8, and 12.

`UiProDJLink::run` calls `nxsFile`, validates and loads the file, requires at
least 32 loaded bytes, allocates a 32-byte copy of bytes 0-31, and passes that
pointer into `PSvDBServer::Start`. The server forwards it to
`PSvDBMain::Start`, which owns a private 32-byte copy at member offset `+0x5e8`.
An absent or invalid file causes the server to start with a null DJ-ID pointer
**[DEC]**.

The two byte orders are bound to the concrete `juce::FileInputStream` vtable:
virtual slot `+0x48` is `InputStream::readInt`, while `+0x50` is
`InputStream::readIntBigEndian`. The checksum covers only five values in the
first 32 bytes. The other values in that prefix and bytes 32-159 are not part
of the recovered comparison. Their product semantics are outside this static
result.

## CDJ-3000 post-load sequence

The retained CDJ-3000 firmware analysis records this sequence after loading a
track from a Rekordbox source **[CDJ-DEC, CDJ-OBS]**:

```text
3006 [context]
  -> 4d02 [3006, 0, 0xa0, blob(160)]
2602 [context, ContentID]
  -> 4000 [2602, row_count]
3000 [context, 0, row_count, 0, row_count, 0, 0, 0]
  -> 4001, 4101*, 4201
```

The player accepts the `0x4d02` blob when the declared and actual lengths
agree and at least 32 bytes are present. It retains only the first 32 bytes,
then advances to Delivery Song Info. A short or mismatched reply logs a
parameter error but also advances. Reply `0x4003` finishes the ticket cleanly.

No reply is operationally worse than an explicit unsupported reply. The
observed CDJ-3000 ticket waited about 18 seconds, retried twice, and serialized
later browsing behind the request. A Link Export implementation can therefore
serve every visible menu correctly and still appear hung after track load if
it omits `0x3006`.

## Evidence boundary and live matrix

The reply builder, configuration filename, validation predicate, 32-byte
startup copy, and 160-byte zero-padded construction are static Rekordbox 7.2.19
evidence. The request arguments, post-load order, timeout, retry, and player
parsing behavior are CDJ-3000 firmware evidence cross-checked by that source
against Rekordbox 7.2.11.

A real-Rekordbox 7.2.19 oracle declares 142 cases across ten executions, or
284 fresh-process record/repeat case executions. It covers:

- ordinary RX3 and CDJ status identities;
- zero, one, and extra request arguments plus typed context variants;
- the normal absent-file state;
- controlled valid, checksum-invalid, short, and wrong-extension
  `djprofile.nxs` states with exact guest backup and restoration;
- exact `0x4d02` typed arguments and blob bytes;
- fresh fixture/process repeat, health, receipt, and cleanup evidence.

Those live outcomes must be recorded rather than inferred from this static
path or from another backend. The guarded handoff runs after the render-control
queue and produces a canonical golden, independent repeat, profile and health
evidence, and a receipt for every execution.
