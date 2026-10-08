# Exact SQL literal index

This generated reference indexes SQL text that appears literally in the
retained Rekordbox disassembly evidence. It is narrower than the logical
query pipelines in `DATABASE_QUERIES.md`: runtime table selection, bound
values, and dynamically concatenated clauses are not reconstructed here.

The scan covers 84 disassembly artifacts and
finds 36 unique SQL literals across
79 occurrences. Of those,
33 contain the structural keywords of a
complete statement and 3 are explicit fragments.

Every entry retains the source file, line, address, nearest function heading,
and platform. `data/static-analysis/sql-literal-index.json` is the
machine-readable authority.

## Complete statements

### Statement 1

```sql
select * from djmdAlbum where rb_local_deleted = 0
```

- `data/static-analysis/search-result-implementation.disasm.txt:1752` at `0x01016d9809` in `function 0x1016d9390` (macos-x86_64)
- `data/static-analysis/search-result-implementation.disasm.txt:4820` at `0x01016dc83a` in `function 0x1016dc7e0` (macos-x86_64)

### Statement 2

```sql
select * from djmdArtist where rb_local_deleted = 0
```

- `data/static-analysis/search-result-implementation.disasm.txt:1623` at `0x01016d95a8` in `function 0x1016d9390` (macos-x86_64)
- `data/static-analysis/search-result-implementation.disasm.txt:4490` at `0x01016dc314` in `function 0x1016dc2b0` (macos-x86_64)

### Statement 3

```sql
select * from djmdCategory where rb_local_deleted = 0
```

- `data/static-analysis/search-result-implementation.disasm.txt:1218` at `0x01016d8ee6` in `function 0x1016d8c40` (macos-x86_64)

### Statement 4

```sql
select * from djmdContent where rb_local_deleted = 0
```

- `data/static-analysis/search-result-implementation.disasm.txt:3520` at `0x01016db440` in `function 0x1016db3d0` (macos-x86_64)

### Statement 5

```sql
select * from djmdContent where rb_local_deleted = 0 and ID = %lu
```

- `data/static-analysis/client-and-render.disasm.txt:942` at `0x0100fa08e0` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/context-track-type.disasm.txt:674` at `0x0100fa08e0` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/device-identity-paths.disasm.txt:1368` at `0x0100fa08e0` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/device-identity-paths.disasm.txt:2189` at `0x01016c01fe` in `function 0x1016c01b0` (macos-x86_64)
- `data/static-analysis/display-song-info-dispatch.disasm.txt:1082` at `0x01016c01fe` in `function 0x1016c01b0` (macos-x86_64)
- `data/static-analysis/song-info-siblings.disasm.txt:22` at `0x01016c1528` in `function 0x1016c14e0` (macos-x86_64)
- `data/static-analysis/song-info-siblings.disasm.txt:1011` at `0x01016cdc32` in `function 0x1016cdc00` (macos-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:28` at `0x0142361f86` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-history.disasm.txt:112` at `0x014236c84a` in `function 0x14236c690` (windows-x86_64)

### Statement 6

```sql
select * from djmdContent where rb_local_deleted = 0 and ID in(__CONTENT_IDs__)
```

- `data/static-analysis/smart-xml-parser.disasm.txt:122` at `0x01016c4a17` in `function 0x1016c47f0` (macos-x86_64)

### Statement 7

```sql
select * from djmdHotCueBankList where rb_local_deleted = 0
```

- `data/static-analysis/hot-cue-bank.disasm.txt:800` at `0x01016d1ca9` in `function 0x1016d1c60` (macos-x86_64)

### Statement 8

```sql
select * from djmdKey where rb_local_deleted = 0
```

- `data/static-analysis/source-only-client-db-effects.disasm.txt:247` at `0x01016c98ff` in `function 0x1016c98c0` (macos-x86_64)

### Statement 9

```sql
select * from djmdLabel where rb_local_deleted = 0
```

- `data/static-analysis/search-result-implementation.disasm.txt:1879` at `0x01016d9a4c` in `function 0x1016d9390` (macos-x86_64)

### Statement 10

```sql
select * from djmdSongHotCueBanklist where rb_local_deleted = 0
```

- `data/static-analysis/hot-cue-bank-membership-resolver.disasm.txt:14` at `0x01016d2d8a` in `function 0x1016d2d70` (macos-x86_64)
- `data/static-analysis/hot-cue-bank-mutations.disasm.txt:359` at `0x01016d301b` in `function 0x1016d2f20` (macos-x86_64)
- `data/static-analysis/hot-cue-bank.disasm.txt:1442` at `0x01016d261c` in `function 0x1016d2600` (macos-x86_64)
- `data/static-analysis/hot-cue-bank.disasm.txt:1685` at `0x01016d301b` in `function 0x1016d2f20` (macos-x86_64)
- `data/static-analysis/hot-cue-seek-fault.disasm.txt:139` at `0x01016d301b` in `function 0x1016d2f20` (macos-x86_64)

### Statement 11

```sql
select * from djmdSongTagList where rb_local_deleted = 0
```

- `data/static-analysis/client-and-render.disasm.txt:439` at `0x0100fa0093` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/context-track-type.disasm.txt:171` at `0x0100fa0093` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/device-identity-paths.disasm.txt:865` at `0x0100fa0093` in `function 0x100f9fe40` (macos-x86_64)

### Statement 12

```sql
select * from djmdSort where rb_local_deleted = 0
```

- `data/static-analysis/right-column-precompute.disasm.txt:963` at `0x01016bc5b6` in `function 0x1016bc5a0` (macos-x86_64)

### Statement 13

```sql
select * from djmdSort where rb_local_deleted = 0 order by Seq
```

- `data/static-analysis/subcolumn-controller-paths.disasm.txt:1529` at `0x0100b1c865` in `function 0x100b1c740` (macos-x86_64)

### Statement 14

```sql
select AnalysisDataPath from djmdContent where rb_local_deleted = 0 and ID = %lu
```

- `data/static-analysis/source-only-client-db-effects.disasm.txt:14` at `0x01016c242d` in `function 0x1016c2410` (macos-x86_64)

### Statement 15

```sql
select Bpm from djmdContent where rb_local_deleted = 0 and ID = %lu
```

- `data/static-analysis/source-only-client-db-effects.disasm.txt:850` at `0x01016d5737` in `function 0x1016d5720` (macos-x86_64)

### Statement 16

```sql
select ContentLink from djmdContent where rb_local_deleted = 0
```

- `data/static-analysis/source-only-client-db-effects.disasm.txt:976` at `0x01016d8a65` in `function 0x1016d8a50` (macos-x86_64)

### Statement 17

```sql
select DBID from djmdProperty
```

- `data/static-analysis/song-info-siblings.disasm.txt:390` at `0x01016c1aa9` in `function 0x1016c14e0` (macos-x86_64)

### Statement 18

```sql
select DBID from djmdProperty where rb_local_deleted = 0
```

- `data/static-analysis/song-info-siblings.disasm.txt:1049` at `0x01016cdcf4` in `function 0x1016cdc00` (macos-x86_64)

### Statement 19

```sql
select FileType, SampleRate from djmdContent where rb_local_deleted = 0
```

- `data/static-analysis/client-and-render.disasm.txt:600` at `0x0100fa0326` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/context-track-type.disasm.txt:332` at `0x0100fa0326` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/device-identity-paths.disasm.txt:1026` at `0x0100fa0326` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/windows/get-list-row-content-compatibility.disasm.txt:5` at `0x014238ca7f` in `function 0x14238ca79` (windows-x86_64)

### Statement 20

```sql
select HotCueAutoLoad from djmdContent where rb_local_deleted = 0
```

- `data/static-analysis/client-and-render.disasm.txt:728` at `0x0100fa0544` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/context-track-type.disasm.txt:460` at `0x0100fa0544` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/device-identity-paths.disasm.txt:1154` at `0x0100fa0544` in `function 0x100f9fe40` (macos-x86_64)

### Statement 21

```sql
select ID from djmdSort
```

- `data/static-analysis/subcolumn-controller-paths.disasm.txt:2143` at `0x0100b4adf2` in `function 0x100b4ac50` (macos-x86_64)

### Statement 22

```sql
select ID from djmdSort where rb_local_deleted = 0
```

- `data/static-analysis/subcolumn-controller-paths.disasm.txt:1872` at `0x0100b4a9ea` in `function 0x100b4a890` (macos-x86_64)

### Statement 23

```sql
select ID from djmdSort where rb_local_deleted = 0 and (Disable & 2) = 2
```

- `data/static-analysis/client-and-render.disasm.txt:972` at `0x0100fa0958` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/context-track-type.disasm.txt:704` at `0x0100fa0958` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/device-identity-paths.disasm.txt:1398` at `0x0100fa0958` in `function 0x100f9fe40` (macos-x86_64)

### Statement 24

```sql
select ImagePath from __TABLE_NAME__ where rb_local_deleted = 0 and ID = %lu
```

- `data/static-analysis/adjacent-payload-loaders.disasm.txt:90` at `0x01016c553b` in `function 0x1016c5520` (macos-x86_64)

### Statement 25

```sql
select KeyID from djmdContent where rb_local_deleted = 0
```

- `data/static-analysis/client-and-render.disasm.txt:798` at `0x0100fa0660` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/context-track-type.disasm.txt:530` at `0x0100fa0660` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/device-identity-paths.disasm.txt:1224` at `0x0100fa0660` in `function 0x100f9fe40` (macos-x86_64)

### Statement 26

```sql
select MenuItemID from djmdCategory where rb_local_deleted = 0 and ID = %lu
```

- `data/static-analysis/right-column-precompute.disasm.txt:341` at `0x01016b8cf1` in `function 0x1016b8790` (macos-x86_64)

### Statement 27

```sql
select MenuItemID from djmdSort where rb_local_deleted = 0 and ID = %lu
```

- `data/static-analysis/right-column-precompute.disasm.txt:399` at `0x01016b8e0e` in `function 0x1016b8790` (macos-x86_64)

### Statement 28

```sql
select MenuItemID, Disable from djmdCategory where rb_local_deleted = 0
```

- `data/static-analysis/device-identity-paths.disasm.txt:2224` at `0x01016c029e` in `function 0x1016c01b0` (macos-x86_64)
- `data/static-analysis/display-song-info-dispatch.disasm.txt:1117` at `0x01016c029e` in `function 0x1016c01b0` (macos-x86_64)

### Statement 29

```sql
select Rating from djmdContent where rb_local_deleted = 0 and ID = %lu
```

- `data/static-analysis/source-only-client-db-effects.disasm.txt:718` at `0x01016d555a` in `function 0x1016d5540` (macos-x86_64)

### Statement 30

```sql
select ScaleName from djmdKey where rb_local_deleted = 0
```

- `data/static-analysis/client-and-render.disasm.txt:851` at `0x0100fa074b` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/context-track-type.disasm.txt:583` at `0x0100fa074b` in `function 0x100f9fe40` (macos-x86_64)
- `data/static-analysis/device-identity-paths.disasm.txt:1277` at `0x0100fa074b` in `function 0x100f9fe40` (macos-x86_64)

### Statement 31

```sql
update djmdSort set Disable = (Disable & ~0x02), rb_data_status = case when usn != 0 then 257 else 0 end, rb_local_usn = __RB_LOCAL_USN__, updated_at = CURRENT_TIMESTAMP
```

- `data/static-analysis/subcolumn-controller-paths.disasm.txt:1801` at `0x0100b4a8b3` in `function 0x100b4a890` (macos-x86_64)

### Statement 32

```sql
update djmdSort set Disable = (Disable | 0x02), rb_data_status = case when usn != 0 then 257 else 0 end, rb_local_usn = __RB_LOCAL_USN__, updated_at = CURRENT_TIMESTAMP where rb_local_deleted = 0
```

- `data/static-analysis/subcolumn-controller-paths.disasm.txt:2065` at `0x0100b4ac89` in `function 0x100b4ac50` (macos-x86_64)

### Statement 33

```sql
update djmdSort set rb_local_usn = __RB_LOCAL_USN__
```

- `data/static-analysis/subcolumn-controller-paths.disasm.txt:1931` at `0x0100b4aabb` in `function 0x100b4a890` (macos-x86_64)

## Fragments

### Fragment 1

```sql
select
```

- `data/static-analysis/device-identity-paths.disasm.txt:3271` at `0x01016c12ea` in `function 0x1016c1250` (macos-x86_64)
- `data/static-analysis/display-song-info-dispatch.disasm.txt:2164` at `0x01016c12ea` in `function 0x1016c1250` (macos-x86_64)
- `data/static-analysis/predicates-and-mapping.disasm.txt:616` at `0x01016b841a` in `function 0x1016b8380` (macos-x86_64)
- `data/static-analysis/right-column-precompute.disasm.txt:462` at `0x01016b8f40` in `function 0x1016b8790` (macos-x86_64)
- `data/static-analysis/song-info-siblings.disasm.txt:2666` at `0x01016cf518` in `function 0x1016cf4c0` (macos-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:172` at `0x01423621db` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:342` at `0x0142362494` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:671` at `0x01423629ba` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:901` at `0x0142362d58` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:1071` at `0x0142363011` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:1290` at `0x0142363386` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:1520` at `0x0142363723` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:1691` at `0x01423639df` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:2064` at `0x0142363fb3` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:2235` at `0x014236426f` in `function 0x142361f30` (windows-x86_64)
- `data/static-analysis/windows/appsync-display-song-info.disasm.txt:2406` at `0x014236452f` in `function 0x142361f30` (windows-x86_64)

### Fragment 2

```sql
select djmdContent.*, djmdArtist.Name as ArtistName, djmdSongHotCueBanklist.TrackNo as HcblTrackNo
```

- `data/static-analysis/hot-cue-bank.disasm.txt:827` at `0x01016d1d20` in `function 0x1016d1c60` (macos-x86_64)

### Fragment 3

```sql
update djmdSort
```

- `data/static-analysis/subcolumn-controller-paths.disasm.txt:2217` at `0x0100b4af1c` in `function 0x100b4ac50` (macos-x86_64)

## Interpretation boundary

A complete-statement label means the literal itself contains the expected
SQL structural keywords. It does not prove that the string is the whole
runtime query after placeholder substitution or concatenation. Fragments
must be interpreted only with their owning disassembly and the corresponding
pipeline in `DATABASE_QUERIES.md`.

Regenerate both artifacts with:

```sh
./.venv/bin/python tools/generate_sql_literal_index.py
```
