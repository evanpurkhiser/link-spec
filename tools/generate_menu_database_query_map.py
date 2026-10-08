#!/usr/bin/env python3
"""Generate the exhaustive request-kind to database-query classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data/static-analysis/menu-database-query-map.json"


def family(
    identity: str,
    requests: str,
    operation: str,
    tables: str,
    predicate: str,
    ordering: str,
    result: str,
    evidence: str = "OBS DB DEC",
) -> dict[str, object]:
    return {
        "id": identity,
        "requests": requests.split(),
        "operation": operation,
        "tables": tables.split(),
        "predicate": predicate,
        "ordering": ordering,
        "result": result,
        "evidence": evidence.split(),
    }


FAMILIES = [
    family(
        "root", "1000", "configuration_query", "djmdCategory djmdMenuItems",
        "Live category rows passing the capability-aware Disable predicate.",
        "djmdCategory.Seq ascending.",
        "Typed root rows; enabled empty categories remain visible.",
    ),
    family(
        "genre_hierarchy", "1001 1101 1201 1301", "hierarchy_query",
        "djmdContent djmdGenre djmdArtist djmdAlbum",
        "Live visible content constrained by GenreID and optional ArtistID and AlbumID; ffffffff removes an intermediate constraint.",
        "Entity labels for hierarchy rows; requested content sort for tracks.",
        "Genre, artist or ALL, album or ALL, then track rows.",
    ),
    family(
        "artist_hierarchy", "1002 1102 1202", "hierarchy_query",
        "djmdContent djmdArtist djmdAlbum",
        "Live visible content constrained by ArtistID and optional AlbumID.",
        "Entity labels; concrete-album tracks default to TrackNo.",
        "Artist, album or ALL, then track rows.",
    ),
    family(
        "album_hierarchy", "1003 1103", "hierarchy_query",
        "djmdContent djmdAlbum",
        "Referenced live AlbumID followed by live visible content equality.",
        "Album label; concrete-album tracks default to TrackNo.",
        "Album then track rows.",
    ),
    family(
        "collection_tracks", "1004", "track_query",
        "djmdContent djmdTrackSort",
        "rb_local_deleted = 0 and Link Export visible FolderPath.",
        "Requested djdsqlFlexSort; default title order.",
        "Track rows with render-time secondary and compatibility enrichment.",
    ),
    family(
        "bpm", "1006 1106 1206", "scalar_hierarchy_query", "djmdContent",
        "Distinct nonzero rounded BPM; tolerance zero uses [-50,+49] and tolerance 1..6 uses signed percentage bounds.",
        "Numeric BPM; requested content sort for tracks.",
        "BPM, tolerance, then track rows.",
    ),
    family(
        "rating", "1007 1107", "scalar_query", "djmdContent",
        "Root advertises Rating 0..5; direct selection can reach stored out-of-domain values.",
        "Numeric selector; requested content sort.",
        "Rating then track rows.",
    ),
    family(
        "release_year", "1008 1108 1208", "scalar_hierarchy_query",
        "djmdContent",
        "Nonzero ReleaseYear through 2999 grouped by floor(year / 10) * 10.",
        "Decades and years descending; requested content sort.",
        "Decade, year or ALL, then track rows.",
    ),
    family(
        "label_hierarchy", "100A 110A 120A 130A", "hierarchy_query",
        "djmdContent djmdLabel djmdArtist djmdAlbum",
        "Live visible content constrained by LabelID and optional ArtistID and AlbumID.",
        "Entity labels; requested content sort for tracks.",
        "Label, artist or ALL, album or ALL, then track rows.",
    ),
    family(
        "old_key", "100B 110B", "legacy_key_query",
        "djmdKey djmdContent djmdTrackSort",
        "Root reads every non-deleted djmdKey row; track selection constrains live visible content by the requested KeyID.",
        "Database row order for roots; requested djdsqlFlexSort for tracks.",
        "Old-Key labels followed by ordinary enriched track rows.",
        "DEC",
    ),
    family(
        "color", "100D 110D", "scalar_lookup_query",
        "djmdContent djmdColor",
        "Root advertises palette IDs 1..8; direct equality reaches ColorID zero but not dangling lookup IDs.",
        "Palette order; requested content sort.",
        "Color then track rows.",
    ),
    family(
        "dj_play_count", "100E 110E", "scalar_query", "djmdContent",
        "Root de-duplicates 16-bit DJPlayCount; track predicate compares one-byte request and stored values.",
        "Counts ascending; requested content sort.",
        "Play-count then track rows with a low-byte collision boundary.",
    ),
    family(
        "prepare", "100F", "membership_query",
        "djmdSongTagList djmdContent djmdTrackSort",
        "Live persisted tag-list memberships resolved to live content.",
        "Membership TrackNo for sort zero; requested content sort otherwise.",
        "Track rows retaining membership position.",
    ),
    family(
        "duration", "1010 1110", "scalar_query", "djmdContent",
        "Length / 60 minute buckets for lengths through 10799 seconds.",
        "Minute buckets descending; requested content sort.",
        "Duration bucket then track rows.",
    ),
    family(
        "bitrate", "1011 1111", "scalar_query", "djmdContent",
        "Distinct BitRate including zero but excluding stored INT32_MAX; direct equality-like selection.",
        "Numeric bitrate; requested content sort.",
        "Bitrate then track rows.",
    ),
    family(
        "history", "1012 1112", "stateful_membership_query",
        "djmdHistory djmdSongHistory djmdContent",
        "Current Link session history and memberships; Windows AppSync history does not apply the FolderPath streaming gate.",
        "History creation order; song insertion and TrackNo order.",
        "History then track rows.",
    ),
    family(
        "file_name", "1013", "track_query", "djmdContent djmdTrackSort",
        "The same live visible content set as Collection.",
        "Requested content sort; FileNameL remains primary text.",
        "Track rows with FileNameL primary text.",
    ),
    family(
        "key", "1014 1114 1214", "normalized_hierarchy_query",
        "djmdContent djmdKey",
        "Normalize historical KeyID and ScaleName variants into 24 harmonic positions, then apply distance 0..2.",
        "Harmonic key order; requested content sort.",
        "Key, distance, then tracks; labels use DEVSETTING.DAT notation.",
    ),
    family(
        "my_tag", "1015 1315", "hierarchy_and_inverse_membership_query",
        "djmdMyTag djmdSongMyTag",
        "Root or group hierarchy for 1015; content ID to assigned group and leaf pairs for 1315.",
        "Stored tag sequence and group-leaf pairing.",
        "Tag hierarchy or tags assigned to one track.",
    ),
    family(
        "matching", "1017", "relationship_query",
        "djmdRecommendLike djmdContent djmdTrackSort",
        "Seed matches either relationship endpoint; return the opposite endpoint; LikeRate is ignored.",
        "Requested content sort.",
        "Related track rows.",
    ),
    family(
        "rejected_guessed_route", "1018", "no_database_builder", "",
        "No implemented list builder is selected for this guessed request.",
        "None.", "4003 error.", "OBS",
    ),
    family(
        "playlist", "1105", "hierarchy_or_membership_query",
        "djmdPlaylist djmdSongPlaylist djmdContent djmdArtist djmdAlbum djmdGenre djmdKey djmdLabel djmdSongMyTag djmdTrackSort",
        "folder_flag one reads ParentID children; zero uses TrackNo membership or evaluates SmartList when Attribute = 4.",
        "Playlist Seq; membership TrackNo for sort zero; requested content sort otherwise.",
        "Folder and playlist rows or filtered track rows.",
    ),
    family(
        "search", "1300", "multi_domain_query",
        "djmdCategory djmdArtist djmdAlbum djmdContent djmdTrackSort",
        "Enabled Artist, Album, Track, and File Name domains; every token matches and content passes Link Export visibility.",
        "Domain grouping then requested content sort; insertion capped at 1000.",
        "Mixed entity headings and track rows.",
    ),
    family(
        "cue_track_root", "130C", "no_database_builder", "",
        "The kind is recognized and logged, then returns internal -2 without selecting a database-interface builder.",
        "None.", "No reply is built.", "DEC",
    ),
    family(
        "original_artist_hierarchy", "1302 1402 1502", "hierarchy_query",
        "djmdContent djmdArtist djmdAlbum",
        "Live visible content constrained by OrgArtistID and optional AlbumID.",
        "Entity labels; requested content sort for tracks.",
        "Original artist, album or ALL, then track rows.",
    ),
    family(
        "sort_menu", "1400", "configuration_query", "djmdSort djmdMenuItems",
        "Live sort rows where (Disable & 1) = 0.",
        "djmdSort.Seq ascending.", "Configured sort rows.",
    ),
    family(
        "search_tracks", "1500", "track_query",
        "djmdCategory djmdContent djmdTrackSort",
        "New-command Title and FileName search with Link Export visibility; SearchStr is not queried.",
        "Default insertion capped at 5000; explicit sorts returned the tested 10005 eligible rows.",
        "Track-only search rows.",
    ),
    family(
        "remixer_hierarchy", "1602 1702 1802", "hierarchy_query",
        "djmdContent djmdArtist djmdAlbum",
        "Live visible content constrained by RemixerID and optional AlbumID.",
        "Entity labels; requested content sort for tracks.",
        "Remixer, album or ALL, then track rows.",
    ),
    family(
        "date_added", "1708 1808 1908 1A08", "date_hierarchy_query",
        "djmdContent",
        "Parse StockDate into year, month, and day; ffffffff takes wildcard branches.",
        "Date selectors descending; requested content sort for tracks.",
        "Year, month or ALL, day or ALL, then track rows.",
    ),
    family(
        "hot_cue_bank_catalog", "2001", "hierarchy_or_membership_query",
        "djmdHotCueBanklist djmdSongHotCueBanklist djmdContent",
        "Mode one reads live ParentID children; mode zero reads bank memberships and resolves live content.",
        "Tree Seq; membership signed TrackNo.",
        "Folder or bank rows, or track rows with AppSync signed-count behavior.",
    ),
    family(
        "display_song_info", "2002", "single_content_metadata_query",
        "djmdContent djmdCategory djmdArtist djmdAlbum djmdGenre djmdKey djmdColor djmdLabel",
        "One live content ID plus all live category enable rows; entity IDs resolve to display text.",
        "Fixed 16-row schema; XDJ-prefix AIO classification moves Comment before Key.",
        "Metadata rows with category-enabled flags.",
    ),
    family(
        "artwork_payload", "2003 2103", "single_content_image_query",
        "djmdContent djmdPlaylist djmdImage",
        "AppSync resolves ImagePath directly by content or playlist ID; the Master fallback resolves a content ImageID through djmdImage.",
        "Single identifier lookup; filesystem candidates are tried in loader order.",
        "JPEG bytes or an empty 4002 response; success additionally requires a recognized image no larger than one MiB.",
        "DEC",
    ),
    family(
        "analysis_payload", "2004 2204 2504 2804 2904 2A04 2C04 2D04",
        "single_content_analysis_query", "djmdContent",
        "Resolve one content analysis path, then load the kind-specific waveform, beat-grid, VBR, key, or specified-atom payload; specified atoms admit EXT/2EX and short-circuit PCP2, PCPT, and PMAI.",
        "Single identifier lookup followed by format-specific file parsing.",
        "Kind-specific direct blob response or an empty kind-specific response when the file, atom, or parser result is unavailable.",
        "DEC",
    ),
    family(
        "analysis_log_only", "2304 2404 2604 2704", "no_database_builder", "",
        "Read only the packed context track-type byte, emit request and delivery logs, and return internal -2.",
        "None.",
        "No payload reply is built.",
        "DEC",
    ),
    family(
        "cue_payload", "2104 2B04", "single_content_cue_query",
        "djmdContent djmdCue",
        "Resolve cue and extended-cue data for one content ID through the database/callback path.",
        "Stored cue order and callback serialization.",
        "Kind-specific direct cue blob response without an analysis-file read.",
        "DEC",
    ),
    family(
        "hot_cue_bank_legacy_getter", "2101", "direct_membership_query",
        "djmdSongHotCueBanklist",
        "AppSync reads TrackNo 1..3 for one bank ID without validating the owning bank row.",
        "Slot order 1..3.", "4702 fixed cue records and timing extensions.",
    ),
    family(
        "play_song_info", "2102", "single_content_metadata_query",
        "djmdContent djmdKey djmdProperty djmdLeftBuf",
        "One live content ID; path selection examines FolderPath, OrgFolderPath, FileSize, ServiceID, MasterDBID, DBID, and file existence.",
        "Fixed seven-row schema.", "Play metadata and local or cloud delivery path.",
    ),
    family(
        "hot_cue_bank_legacy_setter", "2201",
        "mutation_then_content_cue_query", "djmdSongHotCueBanklist djmdCue",
        "Only D/E/F ordinals 4..6 pass the gate; AppSync rejects exactly one membership and selects row zero otherwise.",
        "Mutation target by TrackNo; response cue rows by request ContentID.",
        "Membership update then 4702 content cues; out-of-gate ordinals acknowledge a no-op.",
    ),
    family(
        "recognized_song_info_without_builder", "2202 2302 2402 2502",
        "no_database_builder", "",
        "The kind is recognized but has no serving builder on the tested host path.",
        "None.", "Kind-specific 4003 error.", "OBS DEC",
    ),
    family(
        "hot_cue_bank_extended_getter", "2301", "direct_membership_query",
        "djmdSongHotCueBanklist",
        "Live rows by HotCueBanklistID and each requested TrackNo without validating the owning bank row.",
        "Requested slot order.", "4e02 extended option and conditional seek records.",
    ),
    family(
        "hot_cue_bank_extended_setter", "2401", "mutation_then_direct_query",
        "djmdSongHotCueBanklist",
        "Slots 1..8 admitted; AppSync rejects exactly one row and selects row zero for other cardinalities.",
        "Up to three updateById calls for fixed, option, and seek fields.",
        "Membership update then 4e02 echo; malformed seek input can terminate or stall.",
    ),
    family(
        "delivery_song_info", "2602", "single_content_metadata_query",
        "djmdContent djmdArtist djmdAlbum djmdGenre djmdKey djmdLabel djmdProperty djmdLeftBuf",
        "One live content ID; resolve ComposerID and entities; compare DeliveryControl with ON.",
        "Fixed 13-row AppSync schema with process-lifetime row interaction state.",
        "Delivery metadata rows.",
    ),
    family(
        "render_buffer", "3000", "materialized_buffer_query",
        "djmdLeftBuf djmdContent djmdSort djmdKey djmdSongTagList",
        "Buffer column zero equals the complete packed context; requested ranges use renderer-specific normalization.",
        "Preserved materialized row order.",
        "4001, 4101, and 4201 rows enriched for compatibility, secondary column, notation, and tags.",
    ),
    family(
        "user_info_djid", "3006", "no_database_builder", "",
        "Return the process-startup DJ-ID buffer loaded from a validated djprofile.nxs file, or the typed empty reply when no buffer was loaded.",
        "None.",
        "4d02 with three numeric fields and a zero- or 160-byte blob.",
        "DEC CDJ-DEC",
    ),
    family(
        "link_history_mutation", "3001 3101 3401", "mutation",
        "djmdHistory djmdSongHistory",
        "3001 creates or appends current history; 3101 deletes its ID; 3401 removes one content membership.",
        "Append insertion order; removal closes the ordinal gap.",
        "Status response and changed subsequent 1012 and 1112 menus.",
    ),
    family(
        "play_state_snapshot", "3B03", "no_database_builder", "",
        "Search the critical-section-protected Link-played ContentID snapshot for the requested ID.",
        "None.",
        "4000 scalar value 2 when present and zero when absent.",
        "DEC RR-DEC",
    ),
    family(
        "malformed_unknown_kind", "0000 FFFF", "no_database_builder", "",
        "Unknown kind is rejected before a database request family is selected.",
        "None.", "Transport timeout or connection close according to framing.",
        "OBS",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    document = {
        "format": 1,
        "scope": (
            "Every request kind declared by the backend-neutral conformance "
            "corpus, classified by Rekordbox 7.2.19 database behavior."
        ),
        "families": FAMILIES,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {args.output}: {len(FAMILIES)} families")


if __name__ == "__main__":
    main()
