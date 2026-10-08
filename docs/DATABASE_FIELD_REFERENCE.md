# Database field reference

This generated reference enumerates the database fields behind the Link
Export request map for Rekordbox 7.2.19. It keeps four claims distinct:
the field exists in the deterministic AppSync fixture, literal SQL retrieves
or names it, the reconstructed request-family description names it, or the
field is schema-only and has no Link Export use claim here.

A recovered `SELECT *` proves that Rekordbox retrieves the complete database
row. It does not prove that every returned field affects a response. The exact
SQL evidence remains in `SQL_LITERAL_INDEX.md`; logical pipelines remain in
`DATABASE_QUERIES.md`.

The index covers 25 table-like names:
22 physical AppSync fixture tables and
3 runtime or alternate-interface names,
with 389 physical columns.
It directly joins those names to 95 wire request kinds.

The machine-readable authority is
`data/database/link-export-schema.json`. The SQLCipher key is decoded only in
memory and is never written to either generated artifact.

## Evidence legend

- **STAR**: at least one retained exact SQL literal selects the complete row.
- **SQL**: an exact SQL literal names this field.
- **SEM**: a request-family predicate, ordering, or result description names it.
- **SCHEMA**: presence only; no field-use claim is made.

## Request-kind index

This inverse index maps every classified wire request to its database-path
family, operation, table set, and fields explicitly named by that family's
reconstructed predicate, ordering, or result description. The field list is
family-level evidence: a multi-stage family can name a field used by only one
stage, so membership does not assert that every request in that family reads
every listed field.

| Request | Family | Operation | Tables | Family-named fields | Evidence |
|---:|---|---|---|---|---|
| `0x0000` | `malformed_unknown_kind` | `no_database_builder` | none | none named | OBS |
| `0x1000` | `root` | `configuration_query` | `djmdCategory`, `djmdMenuItems` | `djmdCategory.Disable`, `djmdCategory.Seq` | OBS, DB, DEC |
| `0x1001` | `genre_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdGenre`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.GenreID` | OBS, DB, DEC |
| `0x1002` | `artist_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.TrackNo` | OBS, DB, DEC |
| `0x1003` | `album_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.TrackNo` | OBS, DB, DEC |
| `0x1004` | `collection_tracks` | `track_query` | `djmdContent`, `djmdTrackSort` | `djmdContent.FolderPath`, `djmdContent.Title`, `djmdContent.rb_local_deleted` | OBS, DB, DEC |
| `0x1006` | `bpm` | `scalar_hierarchy_query` | `djmdContent` | `djmdContent.BPM` | OBS, DB, DEC |
| `0x1007` | `rating` | `scalar_query` | `djmdContent` | `djmdContent.Rating` | OBS, DB, DEC |
| `0x1008` | `release_year` | `scalar_hierarchy_query` | `djmdContent` | `djmdContent.ReleaseYear` | OBS, DB, DEC |
| `0x100a` | `label_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdLabel`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.LabelID` | OBS, DB, DEC |
| `0x100b` | `old_key` | `legacy_key_query` | `djmdKey`, `djmdContent`, `djmdTrackSort` | `djmdContent.KeyID` | DEC |
| `0x100d` | `color` | `scalar_lookup_query` | `djmdContent`, `djmdColor` | `djmdContent.ColorID` | OBS, DB, DEC |
| `0x100e` | `dj_play_count` | `scalar_query` | `djmdContent` | `djmdContent.DJPlayCount` | OBS, DB, DEC |
| `0x100f` | `prepare` | `membership_query` | `djmdSongTagList`, `djmdContent`, `djmdTrackSort` | `djmdContent.Tag`, `djmdContent.TrackNo`, `djmdSongTagList.TrackNo` | OBS, DB, DEC |
| `0x1010` | `duration` | `scalar_query` | `djmdContent` | `djmdContent.Length` | OBS, DB, DEC |
| `0x1011` | `bitrate` | `scalar_query` | `djmdContent` | `djmdContent.BitRate` | OBS, DB, DEC |
| `0x1012` | `history` | `stateful_membership_query` | `djmdHistory`, `djmdSongHistory`, `djmdContent` | `djmdContent.FolderPath`, `djmdContent.TrackNo`, `djmdSongHistory.TrackNo` | OBS, DB, DEC |
| `0x1013` | `file_name` | `track_query` | `djmdContent`, `djmdTrackSort` | `djmdContent.FileNameL` | OBS, DB, DEC |
| `0x1014` | `key` | `normalized_hierarchy_query` | `djmdContent`, `djmdKey` | `djmdContent.KeyID`, `djmdKey.ScaleName` | OBS, DB, DEC |
| `0x1015` | `my_tag` | `hierarchy_and_inverse_membership_query` | `djmdMyTag`, `djmdSongMyTag` | `djmdMyTag.ID`, `djmdSongMyTag.ID` | OBS, DB, DEC |
| `0x1017` | `matching` | `relationship_query` | `djmdRecommendLike`, `djmdContent`, `djmdTrackSort` | `djmdRecommendLike.LikeRate` | OBS, DB, DEC |
| `0x1018` | `rejected_guessed_route` | `no_database_builder` | none | none named | OBS |
| `0x1101` | `genre_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdGenre`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.GenreID` | OBS, DB, DEC |
| `0x1102` | `artist_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.TrackNo` | OBS, DB, DEC |
| `0x1103` | `album_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.TrackNo` | OBS, DB, DEC |
| `0x1105` | `playlist` | `hierarchy_or_membership_query` | `djmdPlaylist`, `djmdSongPlaylist`, `djmdContent`, `djmdArtist`, `djmdAlbum`, `djmdGenre`, `djmdKey`, `djmdLabel`, `djmdSongMyTag`, `djmdTrackSort` | `djmdContent.TrackNo`, `djmdKey.Seq`, `djmdPlaylist.Attribute`, `djmdPlaylist.ParentID`, `djmdPlaylist.Seq`, `djmdPlaylist.SmartList`, `djmdSongMyTag.TrackNo`, `djmdSongPlaylist.TrackNo` | OBS, DB, DEC |
| `0x1106` | `bpm` | `scalar_hierarchy_query` | `djmdContent` | `djmdContent.BPM` | OBS, DB, DEC |
| `0x1107` | `rating` | `scalar_query` | `djmdContent` | `djmdContent.Rating` | OBS, DB, DEC |
| `0x1108` | `release_year` | `scalar_hierarchy_query` | `djmdContent` | `djmdContent.ReleaseYear` | OBS, DB, DEC |
| `0x110a` | `label_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdLabel`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.LabelID` | OBS, DB, DEC |
| `0x110b` | `old_key` | `legacy_key_query` | `djmdKey`, `djmdContent`, `djmdTrackSort` | `djmdContent.KeyID` | DEC |
| `0x110d` | `color` | `scalar_lookup_query` | `djmdContent`, `djmdColor` | `djmdContent.ColorID` | OBS, DB, DEC |
| `0x110e` | `dj_play_count` | `scalar_query` | `djmdContent` | `djmdContent.DJPlayCount` | OBS, DB, DEC |
| `0x1110` | `duration` | `scalar_query` | `djmdContent` | `djmdContent.Length` | OBS, DB, DEC |
| `0x1111` | `bitrate` | `scalar_query` | `djmdContent` | `djmdContent.BitRate` | OBS, DB, DEC |
| `0x1112` | `history` | `stateful_membership_query` | `djmdHistory`, `djmdSongHistory`, `djmdContent` | `djmdContent.FolderPath`, `djmdContent.TrackNo`, `djmdSongHistory.TrackNo` | OBS, DB, DEC |
| `0x1114` | `key` | `normalized_hierarchy_query` | `djmdContent`, `djmdKey` | `djmdContent.KeyID`, `djmdKey.ScaleName` | OBS, DB, DEC |
| `0x1201` | `genre_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdGenre`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.GenreID` | OBS, DB, DEC |
| `0x1202` | `artist_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.TrackNo` | OBS, DB, DEC |
| `0x1206` | `bpm` | `scalar_hierarchy_query` | `djmdContent` | `djmdContent.BPM` | OBS, DB, DEC |
| `0x1208` | `release_year` | `scalar_hierarchy_query` | `djmdContent` | `djmdContent.ReleaseYear` | OBS, DB, DEC |
| `0x120a` | `label_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdLabel`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.LabelID` | OBS, DB, DEC |
| `0x1214` | `key` | `normalized_hierarchy_query` | `djmdContent`, `djmdKey` | `djmdContent.KeyID`, `djmdKey.ScaleName` | OBS, DB, DEC |
| `0x1300` | `search` | `multi_domain_query` | `djmdCategory`, `djmdArtist`, `djmdAlbum`, `djmdContent`, `djmdTrackSort` | `djmdAlbum.Name`, `djmdArtist.Name` | OBS, DB, DEC |
| `0x1301` | `genre_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdGenre`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.GenreID` | OBS, DB, DEC |
| `0x1302` | `original_artist_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.OrgArtistID` | OBS, DB, DEC |
| `0x130a` | `label_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdLabel`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.ArtistID`, `djmdContent.LabelID` | OBS, DB, DEC |
| `0x130c` | `cue_track_root` | `no_database_builder` | none | none named | DEC |
| `0x1315` | `my_tag` | `hierarchy_and_inverse_membership_query` | `djmdMyTag`, `djmdSongMyTag` | `djmdMyTag.ID`, `djmdSongMyTag.ID` | OBS, DB, DEC |
| `0x1400` | `sort_menu` | `configuration_query` | `djmdSort`, `djmdMenuItems` | `djmdSort.Disable`, `djmdSort.Seq` | OBS, DB, DEC |
| `0x1402` | `original_artist_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.OrgArtistID` | OBS, DB, DEC |
| `0x1500` | `search_tracks` | `track_query` | `djmdCategory`, `djmdContent`, `djmdTrackSort` | `djmdContent.SearchStr`, `djmdContent.Title` | OBS, DB, DEC |
| `0x1502` | `original_artist_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.OrgArtistID` | OBS, DB, DEC |
| `0x1602` | `remixer_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.RemixerID` | OBS, DB, DEC |
| `0x1702` | `remixer_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.RemixerID` | OBS, DB, DEC |
| `0x1708` | `date_added` | `date_hierarchy_query` | `djmdContent` | `djmdContent.StockDate` | OBS, DB, DEC |
| `0x1802` | `remixer_hierarchy` | `hierarchy_query` | `djmdContent`, `djmdArtist`, `djmdAlbum` | `djmdContent.AlbumID`, `djmdContent.RemixerID` | OBS, DB, DEC |
| `0x1808` | `date_added` | `date_hierarchy_query` | `djmdContent` | `djmdContent.StockDate` | OBS, DB, DEC |
| `0x1908` | `date_added` | `date_hierarchy_query` | `djmdContent` | `djmdContent.StockDate` | OBS, DB, DEC |
| `0x1a08` | `date_added` | `date_hierarchy_query` | `djmdContent` | `djmdContent.StockDate` | OBS, DB, DEC |
| `0x2001` | `hot_cue_bank_catalog` | `hierarchy_or_membership_query` | `djmdHotCueBanklist`, `djmdSongHotCueBanklist`, `djmdContent` | `djmdContent.TrackNo`, `djmdHotCueBanklist.ParentID`, `djmdHotCueBanklist.Seq`, `djmdSongHotCueBanklist.TrackNo` | OBS, DB, DEC |
| `0x2002` | `display_song_info` | `single_content_metadata_query` | `djmdContent`, `djmdCategory`, `djmdArtist`, `djmdAlbum`, `djmdGenre`, `djmdKey`, `djmdColor`, `djmdLabel` | `djmdAlbum.ID`, `djmdArtist.ID`, `djmdCategory.ID`, `djmdColor.ID`, `djmdContent.ID`, `djmdGenre.ID`, `djmdKey.ID`, `djmdLabel.ID` | OBS, DB, DEC |
| `0x2003` | `artwork_payload` | `single_content_image_query` | `djmdContent`, `djmdPlaylist`, `djmdImage` | `djmdContent.ID`, `djmdContent.ImagePath`, `djmdPlaylist.ID`, `djmdPlaylist.ImagePath` | DEC |
| `0x2004` | `analysis_payload` | `single_content_analysis_query` | `djmdContent` | none named | DEC |
| `0x2101` | `hot_cue_bank_legacy_getter` | `direct_membership_query` | `djmdSongHotCueBanklist` | `djmdSongHotCueBanklist.ID`, `djmdSongHotCueBanklist.TrackNo` | OBS, DB, DEC |
| `0x2102` | `play_song_info` | `single_content_metadata_query` | `djmdContent`, `djmdKey`, `djmdProperty`, `djmdLeftBuf` | `djmdContent.FileSize`, `djmdContent.FolderPath`, `djmdContent.ID`, `djmdContent.MasterDBID`, `djmdContent.OrgFolderPath`, `djmdContent.ServiceID`, `djmdKey.ID`, `djmdProperty.DBID` | OBS, DB, DEC |
| `0x2103` | `artwork_payload` | `single_content_image_query` | `djmdContent`, `djmdPlaylist`, `djmdImage` | `djmdContent.ID`, `djmdContent.ImagePath`, `djmdPlaylist.ID`, `djmdPlaylist.ImagePath` | DEC |
| `0x2104` | `cue_payload` | `single_content_cue_query` | `djmdContent`, `djmdCue` | `djmdContent.ID`, `djmdCue.ID`, `djmdCue.Kind` | DEC |
| `0x2201` | `hot_cue_bank_legacy_setter` | `mutation_then_content_cue_query` | `djmdSongHotCueBanklist`, `djmdCue` | `djmdCue.ContentID`, `djmdSongHotCueBanklist.ContentID`, `djmdSongHotCueBanklist.TrackNo` | OBS, DB, DEC |
| `0x2202` | `recognized_song_info_without_builder` | `no_database_builder` | none | none named | OBS, DEC |
| `0x2204` | `analysis_payload` | `single_content_analysis_query` | `djmdContent` | none named | DEC |
| `0x2301` | `hot_cue_bank_extended_getter` | `direct_membership_query` | `djmdSongHotCueBanklist` | `djmdSongHotCueBanklist.HotCueBanklistID`, `djmdSongHotCueBanklist.TrackNo` | OBS, DB, DEC |
| `0x2302` | `recognized_song_info_without_builder` | `no_database_builder` | none | none named | OBS, DEC |
| `0x2304` | `analysis_log_only` | `no_database_builder` | none | none named | DEC |
| `0x2401` | `hot_cue_bank_extended_setter` | `mutation_then_direct_query` | `djmdSongHotCueBanklist` | none named | OBS, DB, DEC |
| `0x2402` | `recognized_song_info_without_builder` | `no_database_builder` | none | none named | OBS, DEC |
| `0x2404` | `analysis_log_only` | `no_database_builder` | none | none named | DEC |
| `0x2502` | `recognized_song_info_without_builder` | `no_database_builder` | none | none named | OBS, DEC |
| `0x2504` | `analysis_payload` | `single_content_analysis_query` | `djmdContent` | none named | DEC |
| `0x2602` | `delivery_song_info` | `single_content_metadata_query` | `djmdContent`, `djmdArtist`, `djmdAlbum`, `djmdGenre`, `djmdKey`, `djmdLabel`, `djmdProperty`, `djmdLeftBuf` | `djmdAlbum.ID`, `djmdArtist.ID`, `djmdContent.ComposerID`, `djmdContent.DeliveryControl`, `djmdContent.ID`, `djmdGenre.ID`, `djmdKey.ID`, `djmdLabel.ID` | OBS, DB, DEC |
| `0x2604` | `analysis_log_only` | `no_database_builder` | none | none named | DEC |
| `0x2704` | `analysis_log_only` | `no_database_builder` | none | none named | DEC |
| `0x2804` | `analysis_payload` | `single_content_analysis_query` | `djmdContent` | none named | DEC |
| `0x2904` | `analysis_payload` | `single_content_analysis_query` | `djmdContent` | none named | DEC |
| `0x2a04` | `analysis_payload` | `single_content_analysis_query` | `djmdContent` | none named | DEC |
| `0x2b04` | `cue_payload` | `single_content_cue_query` | `djmdContent`, `djmdCue` | `djmdContent.ID`, `djmdCue.ID`, `djmdCue.Kind` | DEC |
| `0x2c04` | `analysis_payload` | `single_content_analysis_query` | `djmdContent` | none named | DEC |
| `0x2d04` | `analysis_payload` | `single_content_analysis_query` | `djmdContent` | none named | DEC |
| `0x3000` | `render_buffer` | `materialized_buffer_query` | `djmdLeftBuf`, `djmdContent`, `djmdSort`, `djmdKey`, `djmdSongTagList` | none named | OBS, DB, DEC |
| `0x3001` | `link_history_mutation` | `mutation` | `djmdHistory`, `djmdSongHistory` | `djmdHistory.ID`, `djmdSongHistory.ID` | OBS, DB, DEC |
| `0x3006` | `user_info_djid` | `no_database_builder` | none | none named | DEC, CDJ-DEC |
| `0x3101` | `link_history_mutation` | `mutation` | `djmdHistory`, `djmdSongHistory` | `djmdHistory.ID`, `djmdSongHistory.ID` | OBS, DB, DEC |
| `0x3401` | `link_history_mutation` | `mutation` | `djmdHistory`, `djmdSongHistory` | `djmdHistory.ID`, `djmdSongHistory.ID` | OBS, DB, DEC |
| `0x3b03` | `play_state_snapshot` | `no_database_builder` | none | none named | DEC, RR-DEC |
| `0xffff` | `malformed_unknown_kind` | `no_database_builder` | none | none named | OBS |

## Runtime and alternate-interface names

### `djmdImage`

Classification: `alternate-master-interface-table`.

Master-interface artwork lookup named by recovered code; the active AppSync fixture instead stores ImagePath on djmdContent and djmdPlaylist.

Request families: `artwork_payload`.

Request kinds: `0x2003`, `0x2103`.

### `djmdLeftBuf`

Classification: `runtime-materialized-table`.

Process-local context-keyed list buffer populated after a menu query and consumed by 0x3000 rendering.

Request families: `play_song_info`, `delivery_song_info`, `render_buffer`.

Request kinds: `0x2102`, `0x2602`, `0x3000`.

### `djmdTrackSort`

Classification: `runtime-materialized-table`.

Intermediate track rowset used by djdsqlFlexSort before rows enter djmdLeftBuf.

Request families: `collection_tracks`, `old_key`, `prepare`, `file_name`, `matching`, `playlist`, `search`, `search_tracks`.

Request kinds: `0x1004`, `0x100b`, `0x100f`, `0x1013`, `0x1017`, `0x1105`, `0x110b`, `0x1300`, `0x1500`.

## Physical AppSync tables

### `djmdAlbum`

Request families: `genre_hierarchy`, `artist_hierarchy`, `album_hierarchy`, `label_hierarchy`, `playlist`, `search`, `original_artist_hierarchy`, `remixer_hierarchy`, `display_song_info`, `delivery_song_info`.

Request kinds: `0x1001`, `0x1002`, `0x1003`, `0x100a`, `0x1101`, `0x1102`, `0x1103`, `0x1105`, `0x110a`, `0x1201`, `0x1202`, `0x120a`, `0x1300`, `0x1301`, `0x1302`, `0x130a`, `0x1402`, `0x1502`, `0x1602`, `0x1702`, `0x1802`, `0x2002`, `0x2602`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR, SEM | families `display_song_info`, `delivery_song_info`; requests `0x2002`, `0x2602` |
| `Name` | `VARCHAR(255)` | STAR, SEM | families `search`; requests `0x1300` |
| `AlbumArtistID` | `VARCHAR(255)` | STAR | presence only |
| `ImagePath` | `VARCHAR(255)` | STAR | presence only |
| `Compilation` | `INTEGER` | STAR | presence only |
| `SearchStr` | `VARCHAR(255)` | STAR | presence only |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 1 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdArtist`

Request families: `genre_hierarchy`, `artist_hierarchy`, `label_hierarchy`, `playlist`, `search`, `original_artist_hierarchy`, `remixer_hierarchy`, `display_song_info`, `delivery_song_info`.

Request kinds: `0x1001`, `0x1002`, `0x100a`, `0x1101`, `0x1102`, `0x1105`, `0x110a`, `0x1201`, `0x1202`, `0x120a`, `0x1300`, `0x1301`, `0x1302`, `0x130a`, `0x1402`, `0x1502`, `0x1602`, `0x1702`, `0x1802`, `0x2002`, `0x2602`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR, SEM | families `display_song_info`, `delivery_song_info`; requests `0x2002`, `0x2602` |
| `Name` | `VARCHAR(255)` | STAR, SQL, SEM | families `search`; requests `0x1300`; named by 1 literal(s) |
| `SearchStr` | `VARCHAR(255)` | STAR | presence only |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 1 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdCategory`

Request families: `root`, `search`, `search_tracks`, `display_song_info`.

Request kinds: `0x1000`, `0x1300`, `0x1500`, `0x2002`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR, SQL, SEM | families `display_song_info`; requests `0x2002`; named by 1 literal(s) |
| `MenuItemID` | `VARCHAR(255)` | STAR, SQL | named by 2 literal(s) |
| `Seq` | `INTEGER` | STAR, SEM | families `root`; requests `0x1000` |
| `Disable` | `INTEGER` | STAR, SQL, SEM | families `root`; requests `0x1000`; named by 1 literal(s) |
| `InfoOrder` | `INTEGER` | STAR | presence only |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 3 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdColor`

Request families: `color`, `display_song_info`.

Request kinds: `0x100d`, `0x110d`, `0x2002`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SEM | families `display_song_info`; requests `0x2002` |
| `ColorCode` | `INTEGER` | SCHEMA | presence only |
| `SortKey` | `INTEGER` | SCHEMA | presence only |
| `Commnt` | `VARCHAR(255)` | SCHEMA | presence only |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdContent`

Request families: `genre_hierarchy`, `artist_hierarchy`, `album_hierarchy`, `collection_tracks`, `bpm`, `rating`, `release_year`, `label_hierarchy`, `old_key`, `color`, `dj_play_count`, `prepare`, `duration`, `bitrate`, `history`, `file_name`, `key`, `matching`, `playlist`, `search`, `original_artist_hierarchy`, `search_tracks`, `remixer_hierarchy`, `date_added`, `hot_cue_bank_catalog`, `display_song_info`, `artwork_payload`, `analysis_payload`, `cue_payload`, `play_song_info`, `delivery_song_info`, `render_buffer`.

Request kinds: `0x1001`, `0x1002`, `0x1003`, `0x1004`, `0x1006`, `0x1007`, `0x1008`, `0x100a`, `0x100b`, `0x100d`, `0x100e`, `0x100f`, `0x1010`, `0x1011`, `0x1012`, `0x1013`, `0x1014`, `0x1017`, `0x1101`, `0x1102`, `0x1103`, `0x1105`, `0x1106`, `0x1107`, `0x1108`, `0x110a`, `0x110b`, `0x110d`, `0x110e`, `0x1110`, `0x1111`, `0x1112`, `0x1114`, `0x1201`, `0x1202`, `0x1206`, `0x1208`, `0x120a`, `0x1214`, `0x1300`, `0x1301`, `0x1302`, `0x130a`, `0x1402`, `0x1500`, `0x1502`, `0x1602`, `0x1702`, `0x1708`, `0x1802`, `0x1808`, `0x1908`, `0x1a08`, `0x2001`, `0x2002`, `0x2003`, `0x2004`, `0x2102`, `0x2103`, `0x2104`, `0x2204`, `0x2504`, `0x2602`, `0x2804`, `0x2904`, `0x2a04`, `0x2b04`, `0x2c04`, `0x2d04`, `0x3000`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR, SQL, SEM | families `display_song_info`, `artwork_payload`, `cue_payload`, `play_song_info`, `delivery_song_info`; requests `0x2002`, `0x2003`, `0x2102`, `0x2103`, `0x2104`, `0x2602`, `0x2b04`; named by 5 literal(s) |
| `FolderPath` | `VARCHAR(255)` | STAR, SEM | families `collection_tracks`, `history`, `play_song_info`; requests `0x1004`, `0x1012`, `0x1112`, `0x2102` |
| `FileNameL` | `VARCHAR(255)` | STAR, SEM | families `file_name`; requests `0x1013` |
| `FileNameS` | `VARCHAR(255)` | STAR | presence only |
| `Title` | `VARCHAR(255)` | STAR, SEM | families `collection_tracks`, `search_tracks`; requests `0x1004`, `0x1500` |
| `ArtistID` | `VARCHAR(255)` | STAR, SEM | families `genre_hierarchy`, `artist_hierarchy`, `label_hierarchy`; requests `0x1001`, `0x1002`, `0x100a`, `0x1101`, `0x1102`, `0x110a`, `0x1201`, `0x1202`, `0x120a`, `0x1301`, `0x130a` |
| `AlbumID` | `VARCHAR(255)` | STAR, SEM | families `genre_hierarchy`, `artist_hierarchy`, `album_hierarchy`, `label_hierarchy`, `original_artist_hierarchy`, `remixer_hierarchy`; requests `0x1001`, `0x1002`, `0x1003`, `0x100a`, `0x1101`, `0x1102`, `0x1103`, `0x110a`, `0x1201`, `0x1202`, `0x120a`, `0x1301`, `0x1302`, `0x130a`, `0x1402`, `0x1502`, `0x1602`, `0x1702`, `0x1802` |
| `GenreID` | `VARCHAR(255)` | STAR, SEM | families `genre_hierarchy`; requests `0x1001`, `0x1101`, `0x1201`, `0x1301` |
| `BPM` | `INTEGER` | STAR, SQL, SEM | families `bpm`; requests `0x1006`, `0x1106`, `0x1206`; named by 1 literal(s) |
| `Length` | `INTEGER` | STAR, SEM | families `duration`; requests `0x1010`, `0x1110` |
| `TrackNo` | `INTEGER` | STAR, SQL, SEM | families `artist_hierarchy`, `album_hierarchy`, `prepare`, `history`, `playlist`, `hot_cue_bank_catalog`; requests `0x1002`, `0x1003`, `0x100f`, `0x1012`, `0x1102`, `0x1103`, `0x1105`, `0x1112`, `0x1202`, `0x2001`; named by 1 literal(s) |
| `BitRate` | `INTEGER` | STAR, SEM | families `bitrate`; requests `0x1011`, `0x1111` |
| `BitDepth` | `INTEGER` | STAR | presence only |
| `Commnt` | `TEXT` | STAR | presence only |
| `FileType` | `INTEGER` | STAR, SQL | named by 1 literal(s) |
| `Rating` | `INTEGER` | STAR, SQL, SEM | families `rating`; requests `0x1007`, `0x1107`; named by 1 literal(s) |
| `ReleaseYear` | `INTEGER` | STAR, SEM | families `release_year`; requests `0x1008`, `0x1108`, `0x1208` |
| `RemixerID` | `VARCHAR(255)` | STAR, SEM | families `remixer_hierarchy`; requests `0x1602`, `0x1702`, `0x1802` |
| `LabelID` | `VARCHAR(255)` | STAR, SEM | families `label_hierarchy`; requests `0x100a`, `0x110a`, `0x120a`, `0x130a` |
| `OrgArtistID` | `VARCHAR(255)` | STAR, SEM | families `original_artist_hierarchy`; requests `0x1302`, `0x1402`, `0x1502` |
| `KeyID` | `VARCHAR(255)` | STAR, SQL, SEM | families `old_key`, `key`; requests `0x100b`, `0x1014`, `0x110b`, `0x1114`, `0x1214`; named by 1 literal(s) |
| `StockDate` | `VARCHAR(255)` | STAR, SEM | families `date_added`; requests `0x1708`, `0x1808`, `0x1908`, `0x1a08` |
| `ColorID` | `VARCHAR(255)` | STAR, SEM | families `color`; requests `0x100d`, `0x110d` |
| `DJPlayCount` | `INTEGER` | STAR, SEM | families `dj_play_count`; requests `0x100e`, `0x110e` |
| `ImagePath` | `VARCHAR(255)` | STAR, SEM | families `artwork_payload`; requests `0x2003`, `0x2103` |
| `MasterDBID` | `VARCHAR(255)` | STAR, SEM | families `play_song_info`; requests `0x2102` |
| `MasterSongID` | `VARCHAR(255)` | STAR | presence only |
| `AnalysisDataPath` | `VARCHAR(255)` | STAR, SQL | named by 1 literal(s) |
| `SearchStr` | `VARCHAR(255)` | STAR, SEM | families `search_tracks`; requests `0x1500` |
| `FileSize` | `INTEGER` | STAR, SEM | families `play_song_info`; requests `0x2102` |
| `DiscNo` | `INTEGER` | STAR | presence only |
| `ComposerID` | `VARCHAR(255)` | STAR, SEM | families `delivery_song_info`; requests `0x2602` |
| `Subtitle` | `VARCHAR(255)` | STAR | presence only |
| `SampleRate` | `INTEGER` | STAR, SQL | named by 1 literal(s) |
| `DisableQuantize` | `INTEGER` | STAR | presence only |
| `Analysed` | `INTEGER` | STAR | presence only |
| `ReleaseDate` | `VARCHAR(255)` | STAR | presence only |
| `DateCreated` | `VARCHAR(255)` | STAR | presence only |
| `ContentLink` | `INTEGER` | STAR, SQL | named by 1 literal(s) |
| `Tag` | `VARCHAR(255)` | STAR, SEM | families `prepare`; requests `0x100f` |
| `ModifiedByRBM` | `VARCHAR(255)` | STAR | presence only |
| `HotCueAutoLoad` | `VARCHAR(255)` | STAR, SQL | named by 1 literal(s) |
| `DeliveryControl` | `VARCHAR(255)` | STAR, SEM | families `delivery_song_info`; requests `0x2602` |
| `DeliveryComment` | `VARCHAR(255)` | STAR | presence only |
| `CueUpdated` | `VARCHAR(255)` | STAR | presence only |
| `AnalysisUpdated` | `VARCHAR(255)` | STAR | presence only |
| `TrackInfoUpdated` | `VARCHAR(255)` | STAR | presence only |
| `Lyricist` | `VARCHAR(255)` | STAR | presence only |
| `ISRC` | `VARCHAR(255)` | STAR | presence only |
| `SamplerTrackInfo` | `INTEGER` | STAR | presence only |
| `SamplerPlayOffset` | `INTEGER` | STAR | presence only |
| `SamplerGain` | `FLOAT` | STAR | presence only |
| `VideoAssociate` | `VARCHAR(255)` | STAR | presence only |
| `LyricStatus` | `INTEGER` | STAR | presence only |
| `ServiceID` | `INTEGER` | STAR, SEM | families `play_song_info`; requests `0x2102` |
| `OrgFolderPath` | `VARCHAR(255)` | STAR, SEM | families `play_song_info`; requests `0x2102` |
| `Reserved1` | `TEXT` | STAR | presence only |
| `Reserved2` | `TEXT` | STAR | presence only |
| `Reserved3` | `TEXT` | STAR | presence only |
| `Reserved4` | `TEXT` | STAR | presence only |
| `ExtInfo` | `TEXT` | STAR | presence only |
| `rb_file_id` | `VARCHAR(255)` | STAR | presence only |
| `DeviceID` | `VARCHAR(255)` | STAR | presence only |
| `rb_LocalFolderPath` | `VARCHAR(255)` | STAR | presence only |
| `SrcID` | `VARCHAR(255)` | STAR | presence only |
| `SrcTitle` | `VARCHAR(255)` | STAR | presence only |
| `SrcArtistName` | `VARCHAR(255)` | STAR | presence only |
| `SrcAlbumName` | `VARCHAR(255)` | STAR | presence only |
| `SrcLength` | `INTEGER` | STAR | presence only |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL, SEM | families `collection_tracks`; requests `0x1004`; named by 10 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdCue`

Request families: `cue_payload`, `hot_cue_bank_legacy_setter`.

Request kinds: `0x2104`, `0x2201`, `0x2b04`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SEM | families `cue_payload`; requests `0x2104`, `0x2b04` |
| `ContentID` | `VARCHAR(255)` | SEM | families `hot_cue_bank_legacy_setter`; requests `0x2201` |
| `InMsec` | `INTEGER` | SCHEMA | presence only |
| `InFrame` | `INTEGER` | SCHEMA | presence only |
| `InMpegFrame` | `INTEGER` | SCHEMA | presence only |
| `InMpegAbs` | `INTEGER` | SCHEMA | presence only |
| `OutMsec` | `INTEGER` | SCHEMA | presence only |
| `OutFrame` | `INTEGER` | SCHEMA | presence only |
| `OutMpegFrame` | `INTEGER` | SCHEMA | presence only |
| `OutMpegAbs` | `INTEGER` | SCHEMA | presence only |
| `Kind` | `INTEGER` | SEM | families `cue_payload`; requests `0x2104`, `0x2b04` |
| `Color` | `INTEGER` | SCHEMA | presence only |
| `ColorTableIndex` | `INTEGER` | SCHEMA | presence only |
| `ActiveLoop` | `INTEGER` | SCHEMA | presence only |
| `Comment` | `VARCHAR(255)` | SCHEMA | presence only |
| `BeatLoopSize` | `INTEGER` | SCHEMA | presence only |
| `CueMicrosec` | `INTEGER` | SCHEMA | presence only |
| `InPointSeekInfo` | `VARCHAR(255)` | SCHEMA | presence only |
| `OutPointSeekInfo` | `VARCHAR(255)` | SCHEMA | presence only |
| `ContentUUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdGenre`

Request families: `genre_hierarchy`, `playlist`, `display_song_info`, `delivery_song_info`.

Request kinds: `0x1001`, `0x1101`, `0x1105`, `0x1201`, `0x1301`, `0x2002`, `0x2602`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SEM | families `display_song_info`, `delivery_song_info`; requests `0x2002`, `0x2602` |
| `Name` | `VARCHAR(255)` | SCHEMA | presence only |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdHistory`

Request families: `history`, `link_history_mutation`.

Request kinds: `0x1012`, `0x1112`, `0x3001`, `0x3101`, `0x3401`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SEM | families `link_history_mutation`; requests `0x3001`, `0x3101`, `0x3401` |
| `Seq` | `INTEGER` | SCHEMA | presence only |
| `Name` | `VARCHAR(255)` | SCHEMA | presence only |
| `Attribute` | `INTEGER` | SCHEMA | presence only |
| `ParentID` | `VARCHAR(255)` | SCHEMA | presence only |
| `DateCreated` | `VARCHAR(255)` | SCHEMA | presence only |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdHotCueBanklist`

Request families: `hot_cue_bank_catalog`.

Request kinds: `0x2001`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR | presence only |
| `Seq` | `INTEGER` | STAR, SEM | families `hot_cue_bank_catalog`; requests `0x2001` |
| `Name` | `VARCHAR(255)` | STAR | presence only |
| `ImagePath` | `VARCHAR(255)` | STAR | presence only |
| `Attribute` | `INTEGER` | STAR | presence only |
| `ParentID` | `VARCHAR(255)` | STAR, SEM | families `hot_cue_bank_catalog`; requests `0x2001` |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 1 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdKey`

Request families: `old_key`, `key`, `playlist`, `display_song_info`, `play_song_info`, `delivery_song_info`, `render_buffer`.

Request kinds: `0x100b`, `0x1014`, `0x1105`, `0x110b`, `0x1114`, `0x1214`, `0x2002`, `0x2102`, `0x2602`, `0x3000`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR, SEM | families `display_song_info`, `play_song_info`, `delivery_song_info`; requests `0x2002`, `0x2102`, `0x2602` |
| `ScaleName` | `VARCHAR(255)` | STAR, SQL, SEM | families `key`; requests `0x1014`, `0x1114`, `0x1214`; named by 1 literal(s) |
| `Seq` | `INTEGER` | STAR, SEM | families `playlist`; requests `0x1105` |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 2 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdLabel`

Request families: `label_hierarchy`, `playlist`, `display_song_info`, `delivery_song_info`.

Request kinds: `0x100a`, `0x1105`, `0x110a`, `0x120a`, `0x130a`, `0x2002`, `0x2602`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR, SEM | families `display_song_info`, `delivery_song_info`; requests `0x2002`, `0x2602` |
| `Name` | `VARCHAR(255)` | STAR | presence only |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 1 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdMenuItems`

Request families: `root`, `sort_menu`.

Request kinds: `0x1000`, `0x1400`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SCHEMA | presence only |
| `Class` | `INTEGER` | SCHEMA | presence only |
| `Name` | `VARCHAR(255)` | SCHEMA | presence only |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdMyTag`

Request families: `my_tag`.

Request kinds: `0x1015`, `0x1315`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SEM | families `my_tag`; requests `0x1015`, `0x1315` |
| `Seq` | `INTEGER` | SCHEMA | presence only |
| `Name` | `VARCHAR(255)` | SCHEMA | presence only |
| `Attribute` | `INTEGER` | SCHEMA | presence only |
| `ParentID` | `VARCHAR(255)` | SCHEMA | presence only |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdPlaylist`

Request families: `playlist`, `artwork_payload`.

Request kinds: `0x1105`, `0x2003`, `0x2103`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SEM | families `artwork_payload`; requests `0x2003`, `0x2103` |
| `Seq` | `INTEGER` | SEM | families `playlist`; requests `0x1105` |
| `Name` | `VARCHAR(255)` | SCHEMA | presence only |
| `ImagePath` | `VARCHAR(255)` | SEM | families `artwork_payload`; requests `0x2003`, `0x2103` |
| `Attribute` | `INTEGER` | SEM | families `playlist`; requests `0x1105` |
| `ParentID` | `VARCHAR(255)` | SEM | families `playlist`; requests `0x1105` |
| `SmartList` | `TEXT` | SEM | families `playlist`; requests `0x1105` |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdProperty`

Request families: `play_song_info`, `delivery_song_info`.

Request kinds: `0x2102`, `0x2602`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `DBID` | `VARCHAR(255)` | SQL, SEM | families `play_song_info`; requests `0x2102`; named by 2 literal(s) |
| `DBVersion` | `VARCHAR(255)` | SCHEMA | presence only |
| `BaseDBDrive` | `VARCHAR(255)` | SCHEMA | presence only |
| `CurrentDBDrive` | `VARCHAR(255)` | SCHEMA | presence only |
| `DeviceID` | `VARCHAR(255)` | SCHEMA | presence only |
| `Reserved1` | `TEXT` | SCHEMA | presence only |
| `Reserved2` | `TEXT` | SCHEMA | presence only |
| `Reserved3` | `TEXT` | SCHEMA | presence only |
| `Reserved4` | `TEXT` | SCHEMA | presence only |
| `Reserved5` | `TEXT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdRecommendLike`

Request families: `matching`.

Request kinds: `0x1017`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SCHEMA | presence only |
| `ContentID1` | `VARCHAR(255)` | SCHEMA | presence only |
| `ContentID2` | `VARCHAR(255)` | SCHEMA | presence only |
| `LikeRate` | `INTEGER` | SEM | families `matching`; requests `0x1017` |
| `DataCreatedH` | `INTEGER` | SCHEMA | presence only |
| `DataCreatedL` | `INTEGER` | SCHEMA | presence only |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdSongHistory`

Request families: `history`, `link_history_mutation`.

Request kinds: `0x1012`, `0x1112`, `0x3001`, `0x3101`, `0x3401`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SEM | families `link_history_mutation`; requests `0x3001`, `0x3101`, `0x3401` |
| `HistoryID` | `VARCHAR(255)` | SCHEMA | presence only |
| `ContentID` | `VARCHAR(255)` | SCHEMA | presence only |
| `TrackNo` | `INTEGER` | SEM | families `history`; requests `0x1012`, `0x1112` |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdSongHotCueBanklist`

Request families: `hot_cue_bank_catalog`, `hot_cue_bank_legacy_getter`, `hot_cue_bank_legacy_setter`, `hot_cue_bank_extended_getter`, `hot_cue_bank_extended_setter`.

Request kinds: `0x2001`, `0x2101`, `0x2201`, `0x2301`, `0x2401`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR, SEM | families `hot_cue_bank_legacy_getter`; requests `0x2101` |
| `HotCueBanklistID` | `VARCHAR(255)` | STAR, SEM | families `hot_cue_bank_extended_getter`; requests `0x2301` |
| `ContentID` | `VARCHAR(255)` | STAR, SEM | families `hot_cue_bank_legacy_setter`; requests `0x2201` |
| `TrackNo` | `INTEGER` | STAR, SQL, SEM | families `hot_cue_bank_catalog`, `hot_cue_bank_legacy_getter`, `hot_cue_bank_legacy_setter`, `hot_cue_bank_extended_getter`; requests `0x2001`, `0x2101`, `0x2201`, `0x2301`; named by 1 literal(s) |
| `CueID` | `VARCHAR(255)` | STAR | presence only |
| `InMsec` | `INTEGER` | STAR | presence only |
| `InFrame` | `INTEGER` | STAR | presence only |
| `InMpegFrame` | `INTEGER` | STAR | presence only |
| `InMpegAbs` | `INTEGER` | STAR | presence only |
| `OutMsec` | `INTEGER` | STAR | presence only |
| `OutFrame` | `INTEGER` | STAR | presence only |
| `OutMpegFrame` | `INTEGER` | STAR | presence only |
| `OutMpegAbs` | `INTEGER` | STAR | presence only |
| `Color` | `INTEGER` | STAR | presence only |
| `ColorTableIndex` | `INTEGER` | STAR | presence only |
| `ActiveLoop` | `INTEGER` | STAR | presence only |
| `Comment` | `VARCHAR(255)` | STAR | presence only |
| `BeatLoopSize` | `INTEGER` | STAR | presence only |
| `CueMicrosec` | `INTEGER` | STAR | presence only |
| `InPointSeekInfo` | `VARCHAR(255)` | STAR | presence only |
| `OutPointSeekInfo` | `VARCHAR(255)` | STAR | presence only |
| `HotCueBanklistUUID` | `VARCHAR(255)` | STAR | presence only |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 1 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdSongMyTag`

Request families: `my_tag`, `playlist`.

Request kinds: `0x1015`, `0x1105`, `0x1315`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SEM | families `my_tag`; requests `0x1015`, `0x1315` |
| `MyTagID` | `VARCHAR(255)` | SCHEMA | presence only |
| `ContentID` | `VARCHAR(255)` | SCHEMA | presence only |
| `TrackNo` | `INTEGER` | SEM | families `playlist`; requests `0x1105` |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdSongPlaylist`

Request families: `playlist`.

Request kinds: `0x1105`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | SCHEMA | presence only |
| `PlaylistID` | `VARCHAR(255)` | SCHEMA | presence only |
| `ContentID` | `VARCHAR(255)` | SCHEMA | presence only |
| `TrackNo` | `INTEGER` | SEM | families `playlist`; requests `0x1105` |
| `UUID` | `VARCHAR(255)` | SCHEMA | presence only |
| `rb_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_data_status` | `INTEGER` | SCHEMA | presence only |
| `rb_local_deleted` | `TINYINT(1)` | SCHEMA | presence only |
| `rb_local_synced` | `TINYINT(1)` | SCHEMA | presence only |
| `usn` | `BIGINT` | SCHEMA | presence only |
| `rb_local_usn` | `BIGINT` | SCHEMA | presence only |
| `created_at` | `DATETIME` | SCHEMA | presence only |
| `updated_at` | `DATETIME` | SCHEMA | presence only |

### `djmdSongTagList`

Request families: `prepare`, `render_buffer`.

Request kinds: `0x100f`, `0x3000`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR | presence only |
| `ContentID` | `VARCHAR(255)` | STAR | presence only |
| `TrackNo` | `INTEGER` | STAR, SEM | families `prepare`; requests `0x100f` |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 1 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR | presence only |
| `rb_local_usn` | `BIGINT` | STAR | presence only |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR | presence only |

### `djmdSort`

Request families: `sort_menu`, `render_buffer`.

Request kinds: `0x1400`, `0x3000`.

| Column | Declared type | Evidence | Family or exact-SQL detail |
|---|---|---|---|
| `ID` | `VARCHAR(255)` | STAR, SQL | named by 4 literal(s) |
| `MenuItemID` | `VARCHAR(255)` | STAR, SQL | named by 1 literal(s) |
| `Seq` | `INTEGER` | STAR, SQL, SEM | families `sort_menu`; requests `0x1400`; named by 1 literal(s) |
| `Disable` | `INTEGER` | STAR, SQL, SEM | families `sort_menu`; requests `0x1400`; named by 3 literal(s) |
| `UUID` | `VARCHAR(255)` | STAR | presence only |
| `rb_data_status` | `INTEGER` | STAR, SQL | named by 2 literal(s) |
| `rb_local_data_status` | `INTEGER` | STAR | presence only |
| `rb_local_deleted` | `TINYINT(1)` | STAR, SQL | named by 6 literal(s) |
| `rb_local_synced` | `TINYINT(1)` | STAR | presence only |
| `usn` | `BIGINT` | STAR, SQL | named by 2 literal(s) |
| `rb_local_usn` | `BIGINT` | STAR, SQL | named by 3 literal(s) |
| `created_at` | `DATETIME` | STAR | presence only |
| `updated_at` | `DATETIME` | STAR, SQL | named by 2 literal(s) |

## Reproduce

```bash
.venv/bin/python tools/generate_database_field_reference.py \
  --database conformance/fixtures/generated/full/master.db \
  --options /mnt/documents/multimedia/djing/rekordbox/options.json
```

Regeneration reads schema metadata only. It does not export library rows or
persist the database key.
