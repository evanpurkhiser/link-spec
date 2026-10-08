# Link Export track-visibility oracle

This chapter defines when Rekordbox 7.2.19 admits a content row to an ordinary
Link Export track list. It combines pinned x86-64 static analysis with a
restart-isolated, fourteen-track Windows oracle. The result applies to list
membership. It is independent of the compatibility flag in track-row argument
10 and the path/file rules used by Play Song Info `0x2102`.

## Result

The two overloads of `dsqlIsLinkExportVisibleTrack` implement this predicate:

```text
visible(content) = !streaming::isStreamingProtocol(content.FolderPath)
```

`DsqlCommonFunctionInternal::_isStreamingTrack` asks its supplied field getter
for content column index 1, converts the value to a JUCE string, and passes it
to `streaming::isStreamingProtocol`. In the content schema that column is
`djmdContent.FolderPath`. Both public overloads invert the returned Boolean.

The predicate does not inspect `ServiceID`, `ContentLink`, `OrgFolderPath`,
codec/sample-rate compatibility, or the existence of a media file. Those
fields belong to other builders and predicates.

## Static call graph

The pinned functions and addresses are:

| Address | Symbol | Role |
| ---: | --- | --- |
| `0x101f3ed50` | `dsqlIsLinkExportVisibleTrack(uint32_t)` | Fetch by content ID and invert streaming classification |
| `0x101f3edf0` | `dsqlIsLinkExportVisibleTrack(void *)` | Fetch from an existing content row and invert classification |
| `0x101f3efd0` | `DsqlCommonFunctionInternal::_isStreamingTrack(...)` | Read `FolderPath` and classify it |
| `0x1030d8820` | `streaming::isStreamingProtocol(...)` | Query active provider protocol handlers |

Nine direct call sites occur in seven serving paths:

| Containing function | Calls | Observed surface |
| --- | ---: | --- |
| `djepl_getPlaylistTracks` | 2 | Ordinary playlists |
| `djdsqlFlexSort` | 2 | Collection and other flex-sorted lists |
| `djeplGetNewSearchResult` | 1 | Search |
| `djeplGetTrack_History` | 2 | Persisted History path; see the exception below |
| `dsqlInsertLeftBuf_Track` | 1 | Shared track insertion |
| `djepl_getSmartlistTracks` | 1 | Smart playlists |

The manager constructs SoundCloud, Beatport, Tidal, Spotify, and Apple Music
services unconditionally. Its generic classifier dispatches through exactly
those five service slots. The reserved Beatsource slot remains null, and the
standalone Beatsource helper returns false. Login state is queried through a
different virtual method and is not part of this path-classification call
graph **[DEC]**.

Beatport's service predicate calls `juce::String::contains` with
`/v4/catalog/tracks/`. It does not recognize the separate compiled
`beatport:tracks:` literal at this boundary. The existing live Beatport row is
therefore a negative syntax control, not evidence that an unauthenticated
provider was inactive. The generated ownership audit is:

```text
data/static-analysis/streaming-provider-registry.json
data/static-analysis/streaming-provider-registry.disasm.txt
tools/audit_streaming_provider_registry.py
```

The complete disassembly and direct-xref report are retained in:

```text
data/static-analysis/link-export-visibility.disasm.txt
data/static-analysis/link-export-visibility-xrefs.txt
```

## Controlled fixture

The `link-visibility` fixture contains fourteen live rows. Every title begins
with `Visibility Match`, all rows belong to ordinary playlist 6002 and
persisted History 7001, and Smart playlist 6015 selects them with the native
`name contains "Visibility Match"` condition.

| ID | `FolderPath` | Collection result | Purpose |
| ---: | --- | --- | --- |
| 10001 | `Z:/tracks/link-export-fixture/local-z.wav` | visible | Local control |
| 10002 | `soundcloud:tracks:fixture-2` | filtered | Active provider protocol |
| 10003 | `beatport:tracks:fixture-3` | visible | Compiled literal that does not match the serving predicate |
| 10004 | `beatsource:tracks:fixture-4` | visible | Reserved provider has no constructed service in this build |
| 10005 | `tidal:tracks:fixture-5` | filtered | Active provider protocol |
| 10006 | `spotify:track:fixture-6` | filtered | Active provider protocol |
| 10007 | `apple-music:tracks:fixture-7` | filtered | Active provider protocol |
| 10008 | `unknown:tracks:fixture-8` | visible | Unknown scheme control |
| 10009 | `SOUNDCLOUD:TRACKS:fixture-9` | visible | Case-sensitivity control |
| 10010 | `Z:/tracks/soundcloud:tracks:fixture-10.wav` | visible | Embedded-substring control |
| 10011 | `soundcloudish:tracks:fixture-11` | visible | Prefix-boundary control |
| 10012 | empty string | visible | Empty-value control |
| 10013 | SQL `NULL` | visible | Null-value control |
| 10014 | `C:/tracks/link-export-fixture/local-c.wav` | visible | Alternate local control |

The controlled installation recognizes exact lowercase SoundCloud, Tidal,
Spotify, and Apple Music protocol forms. Their matching is case-sensitive and
anchored to each service's complete form. The tested `beatport:tracks:` value
remains visible because Beatport instead searches for `/v4/catalog/tracks/`.
The tested `beatsource:tracks:` value remains visible because no Beatsource
service is constructed. Authentication does not select either path predicate
in Rekordbox 7.2.19 **[OBS, DEC]**.

No media files were created. All local controls and every visible protocol
control prove that ordinary list admission does not perform file-existence or
playability checks.

## Surface matrix

The canonical suite makes seven requests after replacing the encrypted database
and cold-starting Rekordbox. A second database replacement and cold process
produced the same normalized golden.

| Case | Request path | Returned IDs |
| --- | --- | --- |
| `collection-default` | Track `1004`, default sort | 10001, 10003, 10004, 10008-10014 |
| `collection-key-sort` | Track `1004`, Key sort | same ten IDs, sort-dependent order |
| `file-name` | File Name `1013` | same ten IDs |
| `ordinary-playlist` | Playlist 6002 | same ten IDs |
| `smart-playlist` | Smart playlist 6015 | same ten IDs |
| `search` | `Visibility Match` search | same ten IDs |
| `history` | persisted History 7001 | all fourteen IDs |

The six filtered surfaces produce identical membership. Their canonical order
is `10001, 10003, 10004, 10008, 10009, 10010, 10011, 10012, 10013, 10014`
except for the Key-sorted collection, whose order is `10001, 10003, 10009,
10011, 10013, 10004, 10008, 10010, 10012, 10014`.

### History platform split

Persisted History returns all fourteen rows, including the four protocols
filtered everywhere else. The pinned macOS x86-64
`djeplGetTrack_History` implementation is stronger contrary evidence than an
xref count alone: it looks up each history member's content row and calls the
visibility helper in both the no-`TrackFilter` loop (`0x1010c5e12`) and the
`TrackFilter` loop (`0x1010c5f20`). A false result advances to the next history
row in each branch.

The exact Windows 7.2.19 executable used by the oracle resolves request `1112`
through `PSvAppSyncDBIF` vtable slot `+0x230` to function `0x14236c690`. That
function iterates `djmdSongHistory`, reads `TrackNo` and `ContentID`, and issues:

```sql
select * from djmdContent where rb_local_deleted = 0 and ID = %lu
```

It then constructs the title and selected secondary value directly. The
no-`TrackFilter` path proceeds from the content query to row construction with
no visibility call, and the function never reads `FolderPath`. The Windows
oracle consequently returns every controlled streaming row, twice from cold
process state.

This is a proven platform implementation split: the pinned macOS
`djeplGetTrack_History` filters both loops, while the active Windows
`PSvAppSyncDBIF` History builder has no streaming gate. An implementation
targeting the Windows oracle should preserve that behavior instead of applying
a global post-filter to every track-shaped response.

The Windows derivation is reproducible from the hash-pinned PE through RTTI,
the `0x1112` dispatch, and its `PSvAppSyncDBIF` vtable:

```text
data/static-analysis/windows/rekordbox-metadata.json
data/static-analysis/windows/request-1112-immediates.json
data/static-analysis/windows/request-1112-dispatch.disasm.txt
data/static-analysis/windows/appsync-history-vtable.json
data/static-analysis/windows/appsync-history.disasm.txt
data/experiments/link-visibility/windows-history-summary.json
```

## Relationship to other gates

Track compatibility is calculated later and serialized in row argument 10.
Unsupported codec, sample-rate, or bit-depth combinations remain list members
with bit 0 set. See `BOUNDARY_INVALID_LIFECYCLE_ORACLE.md`.

Play Song Info `0x2102` has its own builder precondition: null or empty
`FolderPath` yields a zero-row Song Info menu, and cloud fields control which
path is returned. That behavior does not contradict this oracle: null and empty
paths remain visible in ordinary lists. See `PLAY_SONG_INFO_PATH_ORACLE.md`.

Soft deletion and deleted relationship rows are separate database liveness
rules. This fixture keeps every content and relationship row live so it isolates
the streaming predicate.

## rbxport replay

The identical seven-case suite replayed against
`c144f19+tree.80e87ec8aace`. None of the cases is field-exact. Persisted History
is the sole case with the same outcome, total, and row count; the six ordinary
list surfaces differ in membership. The retained actuals, semantic diff, and
run log are under:

```text
conformance/results/rbxport/c144f19+tree.80e87ec8aace/xdj-rx3/
  link-visibility.actual.json
  link-visibility.diff.txt
  link-visibility.run.log
```

## Reproduction

From the lab root:

```sh
../rekordbox-windows/.venv/bin/python conformance/build_fixture.py \
  link-visibility ../rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  conformance/fixtures/generated/link-visibility
python3 conformance/generate_link_visibility_suite.py
conformance/record_link_visibility.sh
../rekordbox-windows/.venv/bin/python tools/summarize_link_visibility.py
../rekordbox-windows/.venv/bin/python conformance/replay_rbxport.py --no-build
```

The recorder refuses to proceed unless the isolated VM passes its network
guard, replaces the guest database for both cold passes, and restores the
`play-paths` baseline on exit.

## Provenance and retained diagnostics

The canonical database SHA-256 is
`a8fb80c9797cd7fd8ccacf6c69e69ada80048db0f9a8d8c7dc511c25472f7496`;
its fixture fingerprint is
`9975fba58e7a0a36de29dc15709de254b68b4e8276d10b987ed2fe9d645dc342`.
The suite and golden hashes are recorded in
`data/experiments/link-visibility/summary.json`.

An initial diagnostic used the non-native Smart property spelling `title` and
correctly returned an empty Smart result. Its complete fixture and golden are
retained under
`data/experiments/link-visibility/diagnostic-v1-invalid-smart/`; the canonical
fixture uses `name`. This records why the preliminary capture differs without
mixing it into the conformance corpus.

`tools/summarize_windows_history.py` asserts the PE identity, dispatch owner,
RTTI/vtable binding, content SQL, absence of a `FolderPath` read, and both
macOS visibility call sites before writing the cross-platform static summary.

The `streaming-provider-paths` fixture and seven-case authority suite declare
the production-shaped Beatport Windows live-oracle follow-up: they place
`/v4/catalog/tracks/` at the start, inside a URL, and in the middle of a path,
then cross case variation, missing/singular delimiters, provider URI syntax,
and a near-match through six ordinary serving surfaces plus History. The live
recording is serialized behind the user-info/DJ-ID authority stage. Beatsource
cannot be activated through authentication in this build's fixed manager layout.
Account-conditioned application roots and another Rekordbox version may still
have different provider availability. The database predicate, service
ownership, login independence, six ordinary serving surfaces, History
exception, and no-media requirement are otherwise closed.
