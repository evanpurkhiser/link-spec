# Play Song Info path, cloud, and file-state oracle

This chapter documents how rekordbox 7.2.19 constructs the file-delivery row
and hot-cue row in Play Song Info request `0x2102`. It combines a repeated
fourteen-track Windows oracle with the matching x86-64 executable paths. The
fixture uses tiny sentinel files, not audio media. Rekordbox only tests file
type/existence in these branches; it does not parse the file as media **[OBS,
DEC]**.

## Evidence identity

| Artifact | Identity |
| --- | --- |
| Suite | `conformance/suites/generated/song-info-play-paths.json` |
| Suite SHA-256 | `4aeaf062e04697cb3cc9b55e7df2bf3a476a1e21a61095a2f217affaaf202097` |
| Fixture | `conformance/fixtures/generated/play-paths/` |
| Encrypted database SHA-256 | `8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6` |
| Logical fixture fingerprint | `c24aff6c06466a647d09e60f8cf5c872f6db8ae5d482a72cb31ef1d270db6f1a` |
| Golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/song-info-play-paths.json` |
| Golden behavior SHA-256 | `46f735e9d060f3d00b1280384d8bf8c12126c9f7039667e7b3bc54020ee46108` |
| Rekordbox | Windows 7.2.19, XDJ-RX3 player-1 keepalive |
| Repeat method | fixture reset, Rekordbox restart, sentinel recreation |

The independent cold repeat matched all fourteen complete behavior envelopes.
`tools/summarize_play_paths.py` verifies the suite hash, fixture hashes, case
order, totals, path strings, UTF-16 byte lengths, file sizes, hot-cue flags,
and paired `ContentLink` result directly from the retained golden.

## Database inputs

The active builder starts with:

```sql
select * from djmdContent
where rb_local_deleted = 0 and ID = %lu
```

The path decision reads these `djmdContent` values:

| Column or result key | Use |
| --- | --- |
| `FolderPath` | Initial path; null or empty aborts the whole builder |
| `ContentLink` / executable key `ContentsLink` | Bit 7 disables drive replacement in `convertToRealPath` |
| `FileSize` | Low 32 bits become path-row argument 0 |
| `ServiceID` | Values greater than zero enter cloud path selection |
| `MasterDBID` | Compared with the cached local property DBID |
| `OrgFolderPath` | Candidate original local file for a cloud record |
| `HotCueAutoLoad` | Empty-string test for the separate `0x2f` row |

The local identity is loaded once from:

```sql
select DBID from djmdProperty
```

The fixture's property DBID is `3194974614`. The executable asks the result
object for literal `ContentsLink`, while the database schema names the column
`ContentLink`. Mutating schema `ContentLink` from `0` to `0x80` produced equal
path fields after content-ID normalization. This proves no observable effect
in the active configuration; the name mismatch is a likely explanation, but
the wire result alone does not prove which internal value was read **[OBS,
DEC]**.

## Path normalization

`convertToRealPath(PPt, bool)` first rejects a null UTF-16 pointer. An empty
`FolderPath` becomes that null representation before the call, so null and
empty database values both terminate Play Song Info with a successful
zero-row header. A nonempty path is converted with
`UnifiedFilePath::toUnifiedFilePath` **[DEC, OBS]**.

When its boolean is true, the helper gets AppSync's source and current drive
strings. If both are nonempty and differ, `replaceDrivePath` rewrites the
unified path. The caller passes true when bit 7 of `ContentsLink` is clear.
Allocation or drive-info failure also terminates the builder. The complete
helper is retained in
`data/static-analysis/play-path-conversion.disasm.txt` **[DEC]**.

## Cloud path selection

For `ServiceID <= 0`, the normalized `FolderPath` is returned directly. For a
positive service, the builder also obtains `RekordboxCloud::sharePath`,
`getCLSSyncMethod`, and, on one branch, `downloadFolderPath`.
`getCLSSyncMethod` reads the raw integer setting `CLSSyncMethod` with default
`1`. The Play builder tests that result once with `test eax, eax`; it therefore
has exactly two Link Export equivalence classes, zero and nonzero. Negative and
positive nonzero values take the same branch **[DEC]**.

A complete direct-call scan of the pinned x86-64 `__TEXT,__text` section finds
one call to `RekordboxCloud::getCLSSyncMethod`, at `0x1016c1a79` inside
`PSvAppSyncDBIF::getPlaySongInf`. This bounds the setting's directly observed
Link Export role to Play Song Info **[DEC]**.

The recorded Windows configuration has value `1`. Its nonzero branch behaves
as follows **[DEC, OBS]**:

```text
path = convertToRealPath(FolderPath, !(ContentsLink & 0x80))
if conversion failed:
    return zero rows

if ServiceID > 0:
    if local DBID == MasterDBID and OrgFolderPath existsAsFile:
        path = OrgFolderPath
    else:
        derive a share/download candidate from cloud roots and path
        use that candidate according to its file/existence checks

emit FileSize modulo 2^32 and path
```

The actual fallback includes special handling for paths beginning with
`/Contents` and for an original path already rooted below the cloud share.
The Windows fixture deliberately uses absolute `C:/...` paths. With a DBID
mismatch, or a DBID match whose original path is a directory, the fallback
concatenates the current cloud base and absolute path without inserting a
separator:

```text
C:/Users/Research/AppData/Roaming/PioneerC:/Users/Research/...
```

The zero branch does not compare the local DBID with `MasterDBID`. It first
uses `OrgFolderPath` when `File::exists` accepts any filesystem object,
including a directory. Otherwise it constructs candidates through
`downloadFolderPath(ServiceID)` and tests their existence. That helper accepts
service IDs 0 and 2 through 5, reads `MovedFromCloudDir`, and returns an empty
string for every other ID. The setting default is special-location kind 3's
`PioneerDJ/Moved from Cloud` child, normalized through `UnifiedFilePath`; an
explicit setting replaces that default. The nonzero path's share-root jump
table is exact **[DEC]**:

| `ServiceID` | Share-root source |
| ---: | --- |
| 0 | Empty string |
| 1 | Current master-database directory plus `/share` |
| 2 | Dropbox local public path plus `/rekordbox` |
| 3 | Google Drive local public path plus `/rekordbox` |
| 4 | OneDrive local public path plus `/rekordbox` |
| Outside 0-4 | Empty string |

For IDs 1-4, `sharePath` still returns empty unless the provider result is
nonempty and absolute. The audit retains the five signed jump-table offsets
and resolves every target to its owning call sequence.

The complete accessor, branch, filesystem predicates, helper domains, and call
sites are machine-audited in
`data/static-analysis/play-song-info-cloud-paths.{json,disasm.txt}`. The
remaining dynamic branch is exactly `CLSSyncMethod=0`; recording additional
nonzero integer values cannot exercise another Link Export path **[DEC]**.

That malformed-looking string is the real repeated response. It is not runner
normalization **[OBS]**.

## Fourteen-case oracle

The path row is row 5, item type `0x00`; its distinguishing fields are argument
0 `FileSize`, argument 1 content ID, argument 2 UTF-16 byte length including
NUL, and argument 3 path. The hot-cue row is row 6, item type `0x2f`; argument
1 is the Boolean result.

| Case | Distinguishing input | Total | Size arg | Returned path/result | Hot cue |
| --- | --- | ---: | ---: | --- | ---: |
| 01 | local control, missing original | 7 | `8864` | `.../local-control.wav` | 1 |
| 02 | empty `FolderPath`, size 0, empty hot cue | 0 | - | builder stops | - |
| 03 | link bit 7, service -1, size -1, null hot cue | 7 | `4294967295` | `.../local-high-bit.wav` | 0 |
| 04 | link bits 7+0, service 0, size `INT_MAX`, `OFF` | 7 | `2147483647` | `.../local-high-bits.wav` | 1 |
| 05 | service 1, matching DBID, existing original file | 7 | `1` | `.../org-existing.bin` | 1 |
| 06 | service 1, mismatched DBID, existing original directory | 7 | `2` | AppData prefix + `.../cloud-mismatch-directory.wav` | 1 |
| 07 | service 2, matching DBID, missing original, size `UINT_MAX` | 7 | `4294967295` | `.../cloud-match-missing.wav` | 1 |
| 08 | service `INT_MAX`, null DBID, Unicode path, size `2^32` | 7 | `0` | `.../cloud-null-master-unicode-Ω.wav` | 1 |
| 09 | local path, null size, empty hot cue | 7 | `0` | `.../local-empty-hotcue.wav` | 0 |
| 10 | null `FolderPath`, existing original file | 0 | - | builder stops | - |
| 11 | service 1, matching DBID, existing original directory | 7 | `4` | AppData prefix + `.../cloud-match-existing-directory.wav` | 1 |
| 12 | service 1, matching DBID, existing zero-byte original file | 7 | `5` | `.../org-zero-byte.bin` | 1 |
| 13 | `ContentLink = 0` paired control | 7 | `6` | `.../content-link-pair.wav` | 1 |
| 14 | `ContentLink = 0x80` paired control | 7 | `6` | `.../content-link-pair.wav` | 1 |

The abbreviated prefix in the table is
`C:/Users/Research/link-export-conformance/play-paths`. The canonical golden
retains every full typed message **[OBS]**.

## Derived rules

1. `FolderPath` is a builder precondition, not merely a nullable row field.
   Null and empty values return a zero-row menu even when the content record
   exists and `OrgFolderPath` names an existing file **[OBS, DEC]**.
2. `FileSize` is converted to a 32-bit word. `-1` and `2^32-1` become
   `0xffffffff`; `2^32` becomes zero; SQL null also becomes zero **[OBS,
   DEC]**.
3. `HotCueAutoLoad` uses string nonemptiness, not Boolean parsing. `OFF`, `0`,
   one space, `ON`, lowercase `on`, and Unicode all yield 1. Null and empty
   yield 0 **[OBS, DEC]**.
4. The cloud original-path test is `existsAsFile`, not nonzero size. A
   zero-byte regular file passes; a directory fails **[OBS, DEC]**.
5. A positive cloud service with matching `MasterDBID` selects an existing
   `OrgFolderPath`. Missing originals fall through to cloud-derived path logic
   **[OBS, DEC]**.
6. Neither local nor cloud rows require playable media. A small arbitrary
   sentinel is sufficient to exercise every observed existence branch **[OBS]**.

These are Play Song Info builder rules, not ordinary list-membership rules.
Null and empty `FolderPath` values remain visible in Collection, File Name,
Playlist, Smart Playlist, and Search. Their `0x2102` menus are empty because
this builder has a stricter path precondition. Active streaming protocols are
filtered earlier from ordinary lists by the separate predicate documented in
`LINK_EXPORT_VISIBILITY_ORACLE.md`.

## rbxport comparison

The identical suite and encrypted fixture replayed against source identity
`c144f19+tree.80e87ec8aace`. No case is field-exact. Twelve of fourteen cases
preserve outcome, total, and row count. The two shape differences are the null
and empty `FolderPath` cases: rbxport returns seven rows where Rekordbox returns
zero **[RBX]**.

Rbxport also returns the database `FolderPath` directly for the cloud cases,
does not select an existing `OrgFolderPath`, does not reproduce the cloud-base
fallback, maps negative/null size differently in two cases, and treats null or
empty `HotCueAutoLoad` as 1. The complete actual response and semantic diff
are:

```text
conformance/results/rbxport/c144f19+tree.80e87ec8aace/xdj-rx3/
  song-info-play-paths.actual.json
  song-info-play-paths.diff.txt
  song-info-play-paths.run.log
```

## Reproduction and cleanup

Generate the suite and fixture, then record and independently repeat it:

```sh
python3 conformance/generate_matrices.py
../rekordbox-windows/.venv/bin/python conformance/build_fixture.py \
  play-paths ../rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  conformance/fixtures/generated/play-paths
conformance/record_song_info_play_paths.sh
python3 tools/summarize_play_paths.py
```

The recorder recreates
`C:/Users/Research/link-export-conformance/play-paths` before both cold passes.
That guest directory contains one nonempty file, one zero-byte file, and one
directory. It is disposable after recording and is removed with the broader
guest staging tree described in `CLEANUP.md`. The encrypted fixture, suite,
golden, static disassembly, analyzer, and rbxport replay are retained research
artifacts.

The database-controlled matrix is complete for the recorded nonzero
configuration. The `cloud-sync-zero` fixture and ten-case authority suite cover
the zero setting with controlled `MovedFromCloudDir` and filesystem sentinels;
guarded generation `au18` records it after the provider-path stage.
Provider-authenticated share roots are a separate environment dimension; none
of these runtime values can be selected solely by changing `master.db`
**[OPEN]**.
