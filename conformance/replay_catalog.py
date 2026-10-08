"""Shared catalog of safe backend replays and explicitly deferred suites."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
@dataclass(frozen=True)
class Replay:
    model: str
    identity: str
    suite: str
    fixture: str
    suite_path: str | None = None
    second_column: str = "key"
    sorts: str | None = None


def select_replays(
    replays: tuple[Replay, ...], selectors: list[str]
) -> tuple[Replay, ...]:
    if not selectors:
        return replays

    wanted = set(selectors)
    selected = tuple(
        replay
        for replay in replays
        if replay.suite in wanted or f"{replay.model}/{replay.suite}" in wanted
    )
    matched = {
        selector
        for selector in selectors
        if any(
            replay.suite == selector
            or f"{replay.model}/{replay.suite}" == selector
            for replay in selected
        )
    }
    missing = sorted(wanted - matched)
    if missing:
        raise SystemExit(f"unknown replay suite: {', '.join(missing)}")

    return selected


DEFAULT_SORTS = (
    "default",
    "track-name",
    "artist",
    "album",
    "bpm",
    "rating",
    "key",
    "label",
    "genre",
    "date-added",
    "dj-play-count",
)


def move_sort_last(sort: str | None) -> str | None:
    if sort is None:
        return None

    return ",".join(item for item in DEFAULT_SORTS if item != sort) + f",{sort}"


def remove_sort(sort: str) -> str:
    return ",".join(item for item in DEFAULT_SORTS if item != sort)


BASE_REPLAYS = (
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "full", "full"),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "chained-navigation",
        "full",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "root-capabilities",
        "full",
        "generated/root-capabilities",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "sort-ids",
        "full",
        "generated/sort-ids",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "contexts",
        "full",
        "generated/contexts",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "render-5",
        "full",
        "generated/render-5",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "render-6",
        "full",
        "generated/render-6",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "render-8",
        "full",
        "generated/render-8",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "render-secondary-controls",
        "full",
        "generated/render-secondary-controls",
    ),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "pagination", "full"),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "request-errors", "full"),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "malformed-framing", "full"),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "concurrent", "full"),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "legacy", "full"),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "extended-families-full",
        "full",
    ),
    Replay("cdj-3000", "cdj-3000-player-1.json", "full", "full"),
    Replay("cdj-3000", "cdj-3000-player-1.json", "legacy", "full"),
    Replay("cdj-2000nxs2", "cdj-2000nxs2-player-2.json", "full", "full"),
    Replay("cdj-2000nxs2", "cdj-2000nxs2-player-2.json", "legacy", "full"),
    Replay("xdj-xz", "xdj-xz-player-3.json", "full", "full"),
    Replay("xdj-xz", "xdj-xz-player-3.json", "legacy", "full"),
    Replay("xdj-az", "xdj-az-player-4.json", "full", "full"),
    Replay("xdj-az", "xdj-az-player-4.json", "legacy", "full"),
    Replay("xdj-1000mk2", "xdj-1000mk2-player-5.json", "full", "full"),
    Replay("xdj-1000mk2", "xdj-1000mk2-player-5.json", "legacy", "full"),
    Replay("unknown-mixer", "unknown-mixer-player-6.json", "full", "full"),
    Replay("unknown-mixer", "unknown-mixer-player-6.json", "legacy", "full"),
    Replay("unknown-djm", "unknown-djm-player-6.json", "full", "full"),
    Replay("unknown-djm", "unknown-djm-player-6.json", "legacy", "full"),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "empty", "empty"),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "extended-families-empty",
        "empty",
    ),
)

DEVICE_CAPABILITY_REPLAYS = tuple(
    Replay(model, identity, "device-capabilities", "full")
    for model, identity in (
        ("xdj-rx3", "xdj-rx3-player-11.json"),
        ("cdj-3000", "cdj-3000-player-1.json"),
        ("cdj-2000nxs2", "cdj-2000nxs2-player-2.json"),
        ("xdj-xz", "xdj-xz-player-3.json"),
        ("xdj-az", "xdj-az-player-4.json"),
        ("xdj-1000mk2", "xdj-1000mk2-player-5.json"),
        ("unknown-mixer", "unknown-mixer-player-6.json"),
        ("unknown-djm", "unknown-djm-player-6.json"),
    )
)

DEVICE_SMART_REPLAYS = tuple(
    Replay(model, identity, "smart-device-cross", "smart-rule-matrix")
    for model, identity in (
        ("xdj-rx3", "xdj-rx3-player-11.json"),
        ("cdj-3000", "cdj-3000-player-1.json"),
        ("cdj-2000nxs2", "cdj-2000nxs2-player-2.json"),
        ("xdj-xz", "xdj-xz-player-3.json"),
        ("xdj-az", "xdj-az-player-4.json"),
        ("xdj-1000mk2", "xdj-1000mk2-player-5.json"),
        ("unknown-mixer", "unknown-mixer-player-6.json"),
        ("unknown-djm", "unknown-djm-player-6.json"),
    )
)

DEVICE_COMPATIBILITY_REPLAYS = tuple(
    Replay(model, identity, "compatibility", "compatibility")
    for model, identity in (
        ("xdj-rx3", "xdj-rx3-player-11.json"),
        ("cdj-3000", "cdj-3000-player-1.json"),
        ("cdj-2000nxs2", "cdj-2000nxs2-player-2.json"),
        ("xdj-xz", "xdj-xz-player-3.json"),
        ("xdj-az", "xdj-az-player-4.json"),
        ("xdj-1000mk2", "xdj-1000mk2-player-5.json"),
        ("unknown-mixer", "unknown-mixer-player-6.json"),
        ("unknown-djm", "unknown-djm-player-6.json"),
    )
)

DEVICE_RECONNECT_REPLAYS = (
    Replay(
        "reconnect-xdj",
        "xdj-rx3-player-11.json",
        "device-reconnect",
        "full",
    ),
    Replay(
        "reconnect-cdj",
        "cdj-3000-player-1.json",
        "device-reconnect",
        "full",
    ),
)


SETTING_CONFIGURATIONS = (
    ("secondary-album", "album", "album"),
    ("secondary-artist", "artist", "artist"),
    ("secondary-bitrate", "bitrate", None),
    ("secondary-bpm", "bpm", "bpm"),
    ("secondary-color", "color", None),
    ("secondary-comment", "comment", None),
    ("secondary-date-added", "date-added", "date-added"),
    ("secondary-genre", "genre", "genre"),
    ("secondary-key", "key", "key"),
    ("secondary-label", "label", "label"),
    ("secondary-original-artist", "original-artist", None),
    ("secondary-play-count", "dj-play-count", "dj-play-count"),
    ("secondary-rating", "rating", "rating"),
    ("secondary-remixer", "remixer", None),
    ("secondary-time", "duration", None),
)

SETTINGS_REPLAYS = tuple(
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        name,
        name,
        f"generated/{name}",
        second_column,
        move_sort_last(moved_sort),
    )
    for name, second_column, moved_sort in SETTING_CONFIGURATIONS
) + (
    # rbxport currently requires a concrete TrackColumn. Comment is the
    # closest runnable control for rekordbox's title-only no-selection state;
    # the resulting diff is the conformance evidence for that missing state.
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "no-secondary-selection",
        "no-secondary-selection",
        "generated/no-secondary-selection",
        "comment",
    ),
    # rekordbox deterministically resolves the invalid Comment+Key database
    # state to Comment, so replay the observed winner.
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "multiple-secondary-selections",
        "multiple-secondary-selections",
        "generated/multiple-secondary-selections",
        "comment",
    ),
)

LEGACY_SETTINGS_REPLAYS = tuple(
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        f"{name}-legacy",
        name,
        f"generated/{name}-legacy",
        second_column,
        move_sort_last(moved_sort),
    )
    for name, second_column, moved_sort in SETTING_CONFIGURATIONS
)

SMART_SETTINGS_REPLAYS = tuple(
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        f"smart-{name}",
        f"smart-{name}",
        f"generated/smart-{name}",
        second_column,
        move_sort_last(moved_sort),
    )
    for name, second_column, moved_sort in SETTING_CONFIGURATIONS
) + (
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-no-secondary-selection",
        "smart-no-secondary-selection",
        "generated/smart-no-secondary-selection",
        "comment",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-multiple-secondary-selections",
        "smart-multiple-secondary-selections",
        "generated/smart-multiple-secondary-selections",
        "comment",
    ),
)

KEY_NOTATION_REPLAYS = tuple(
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        f"key-notation-{state}",
        "key-notation",
        f"generated/key-notation-{state}",
        "key",
    )
    for state in (
        "classic-normalized",
        "classic-database",
        "alphanumeric-normalized",
        "alphanumeric-database",
    )
)

CATEGORY_IDS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 17, 18, 19, 20, 21, 22, 23, 26)

CATEGORY_REPLAYS = tuple(
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        f"category-{category_id:02d}-disabled",
        f"category-{category_id:02d}-disabled",
        f"generated/category-{category_id:02d}-disabled",
    )
    for category_id in CATEGORY_IDS
) + (
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "category-order-reversed",
        "category-order-reversed",
        "generated/category-order-reversed",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "category-special-bits",
        "category-special-bits",
    ),
)

SEARCH_REPLAYS = (
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "search", "full"),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "search-ceiling",
        "search-ceiling",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "search-text",
        "search-text",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "search-track",
        "search-text",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "search-track-ceiling",
        "search-track-ceiling",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "search-track-large-title-sort",
        "search-track-large-title",
    ),
) + tuple(
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        f"search-category-{category_id:02d}-disabled",
        f"category-{category_id:02d}-disabled",
        f"generated/search-category-{category_id:02d}-disabled",
    )
    for category_id in (2, 3, 4, 21)
)

SORT_TOGGLE_CONFIGURATIONS = (
    (0, "default"),
    (1, "track-name"),
    (2, "artist"),
    (3, "album"),
    (4, "bpm"),
    (5, "rating"),
    (6, "genre"),
    (7, None),
    (8, None),
    (9, None),
    (10, "label"),
    (11, None),
    (12, "key"),
    (13, None),
    (15, None),
    (16, "dj-play-count"),
    (17, "date-added"),
)

SORT_REPLAYS = tuple(
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        f"sort-{sort_id:02d}-toggled",
        f"sort-{sort_id:02d}-toggled",
        f"generated/sort-{sort_id:02d}-toggled",
        sorts=remove_sort(sort) if sort is not None else ",".join(DEFAULT_SORTS),
    )
    for sort_id, sort in SORT_TOGGLE_CONFIGURATIONS
) + (
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "sort-order-reversed",
        "sort-order-reversed",
        "generated/sort-order-reversed",
        sorts=",".join(reversed(DEFAULT_SORTS)),
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "hidden-selected-comment",
        "hidden-selected-comment",
        second_column="comment",
        sorts=",".join(DEFAULT_SORTS),
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "custom-colors",
        "custom-colors",
        second_column="color",
        sorts=",".join(DEFAULT_SORTS),
    ),
)

DATA_REPLAYS = (
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "link-visibility",
        "link-visibility",
        "generated/link-visibility",
    ),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "boundaries", "boundaries"),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "secondary-string-boundaries",
        "boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "secondary-date-added-boundaries",
        "boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "secondary-comment-boundaries",
        "boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "secondary-string-thresholds",
        "boundaries",
        "generated/secondary-string-thresholds",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "secondary-unicode-thresholds",
        "unicode-boundaries",
        "generated/secondary-unicode-thresholds",
    ),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "invalid", "invalid"),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "scalar-selector-drilldowns",
        "full",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "scalar-selector-boundaries",
        "scalar-boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "smart-playlists",
        "smart-playlists",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-rule-matrix",
        "smart-rule-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-numeric-matrix",
        "smart-numeric-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-numeric-boundaries",
        "smart-numeric-boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-property-matrix",
        "smart-property-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-date-matrix",
        "smart-date-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-relative-date-matrix",
        "smart-relative-date-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-date-format-matrix",
        "smart-date-format-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-text-matrix",
        "smart-text-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-string-property-matrix",
        "smart-string-property-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-mytag-matrix",
        "smart-mytag-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-xml-matrix",
        "smart-xml-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-serving-crosses",
        "smart-rule-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "smart-serving-legacy",
        "smart-rule-matrix",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "filename-boundaries",
        "filename-boundaries",
    ),
    Replay("xdj-rx3", "xdj-rx3-player-11.json", "history-lifecycle", "full"),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "song-info-play-paths",
        "play-paths",
        "generated/song-info-play-paths",
    ),
)

DISPLAY_SONG_INFO_REPLAYS = (
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "song-info-siblings",
        "full",
        "generated/song-info-siblings",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "song-info-sibling-render",
        "full",
        "generated/song-info-sibling-render",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "song-info-sibling-pagination",
        "full",
        "generated/song-info-sibling-pagination",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "song-info-sibling-errors",
        "full",
        "generated/song-info-sibling-errors",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "song-info-sibling-legacy",
        "full",
        "generated/song-info-sibling-legacy",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "song-info-delivery-boundaries",
        "delivery-boundaries",
        "generated/song-info-delivery-boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-1.json",
        "song-info-delivery-wide-strings",
        "delivery-wide-strings",
        "generated/song-info-delivery-wide-strings",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-render",
        "full",
        "generated/display-song-info-render",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-pagination",
        "full",
        "generated/display-song-info-pagination",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-errors",
        "full",
        "generated/display-song-info-errors",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-legacy",
        "full",
        "generated/display-song-info-legacy",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-boundaries",
        "boundaries",
        "generated/display-song-info-boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-unicode-boundaries",
        "unicode-boundaries",
        "generated/display-song-info-unicode-boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-invalid",
        "invalid",
        "generated/display-song-info-invalid",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-strings-254",
        "display-strings-254",
        "generated/display-song-info-strings-254",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-strings-255",
        "display-strings-255",
        "generated/display-song-info-strings-255",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-strings-256",
        "display-strings-256",
        "generated/display-song-info-strings-256",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info-strings-unicode-256",
        "display-strings-unicode-256",
        "generated/display-song-info-strings-unicode-256",
    ),
    Replay(
        "xdj-rx3-player-1",
        "xdj-rx3-player-1.json",
        "display-song-info",
        "full",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "display-song-info",
        "full",
    ),
    Replay(
        "xdj-rx3-status",
        "xdj-rx3-player-11-status.json",
        "display-song-info-aio-player-11",
        "full",
    ),
    Replay(
        "cdj-3000-status",
        "cdj-3000-player-1-status.json",
        "display-song-info",
        "full",
    ),
    Replay(
        "xdj-xz-status",
        "xdj-xz-player-11-status.json",
        "display-song-info",
        "full",
        "generated/display-song-info-status-xdj-xz",
    ),
    Replay(
        "xdj-az-status",
        "xdj-az-player-11-status.json",
        "display-song-info",
        "full",
        "generated/display-song-info-status-xdj-az",
    ),
    Replay(
        "xdj-1000mk2-status",
        "xdj-1000mk2-player-11-status.json",
        "display-song-info",
        "full",
        "generated/display-song-info-status-xdj-1000mk2",
    ),
    Replay(
        "unknown-mixer-status",
        "unknown-mixer-player-1-status.json",
        "display-song-info",
        "full",
        "generated/display-song-info-status-unknown-mixer",
    ),
)

STATUS_SIBLING_REPLAYS = tuple(
    Replay(
        model,
        identity,
        suite,
        "full",
        f"generated/{suite}-{status_suffix}",
    )
    for model, identity, status_suffix in (
        ("xdj-rx3-status", "xdj-rx3-player-11-status.json", "status-player-11"),
        ("cdj-3000-status", "cdj-3000-player-1-status.json", "status-player-1"),
    )
    for suite in (
        "song-info-siblings",
        "song-info-sibling-render",
        "song-info-sibling-pagination",
        "song-info-sibling-errors",
        "song-info-sibling-legacy",
    )
)

CDJ_2000NEXUS_STATUS_REPLAYS = tuple(
    Replay(
        "cdj-2000nexus-status",
        "cdj-2000nexus-player-1-genuine-status.json",
        suite,
        fixture,
        suite_path,
    )
    for suite, fixture, suite_path in (
        ("display-song-info", "full", "generated/display-song-info-status-cdj-2000nexus"),
        ("full", "full", "full"),
        ("legacy", "full", "legacy"),
        (
            "context-display-status-extended",
            "full",
            "context-display-status-extended",
        ),
        ("context-display-status-legacy", "full", "context-display-status-legacy"),
        (
            "context-play-status-extended",
            "full",
            "context-play-status-player-1-extended",
        ),
        (
            "context-play-status-legacy",
            "full",
            "context-play-status-player-1-legacy",
        ),
        (
            "context-class2-status-extended",
            "full",
            "context-class2-status-player-1-extended",
        ),
        (
            "context-class2-status-legacy",
            "full",
            "context-class2-status-player-1-legacy",
        ),
        (
            "context-hot-cue-getter-status-extended",
            "hot-cue-banks",
            "context-hot-cue-getter-status-player-1-extended",
        ),
        (
            "context-hot-cue-getter-status-legacy",
            "hot-cue-banks",
            "context-hot-cue-getter-status-player-1-legacy",
        ),
        (
            "context-hot-cue-catalog-status-extended",
            "hot-cue-banks",
            "context-hot-cue-catalog-status-player-1-extended",
        ),
        (
            "context-hot-cue-catalog-status-legacy",
            "hot-cue-banks",
            "context-hot-cue-catalog-status-player-1-legacy",
        ),
    )
)

PACKED_CONTEXT_REPLAYS = tuple(
    Replay("xdj-rx3", "xdj-rx3-player-1.json", suite, fixture)
    for suite, fixture in (
        ("context-track-types", "full"),
        ("context-track-type-families", "full"),
        ("context-analysis-track-types", "full"),
        ("context-hot-cue-track-types", "hot-cue-banks"),
    )
)

DEVICE_SETUP_REPLAYS = tuple(
    Replay(model, identity, f"context-device-setup-{setup}", "full")
    for model, identity in (
        ("xdj-rx3", "xdj-rx3-player-11.json"),
        ("cdj-3000", "cdj-3000-player-1.json"),
        ("cdj-2000nxs2", "cdj-2000nxs2-player-2.json"),
        ("xdj-xz", "xdj-xz-player-3.json"),
        ("xdj-az", "xdj-az-player-4.json"),
        ("xdj-1000mk2", "xdj-1000mk2-player-5.json"),
        ("unknown-mixer", "unknown-mixer-player-6.json"),
        ("unknown-djm", "unknown-djm-player-6.json"),
    )
    for setup in ("extended", "legacy")
)

DISPLAY_STATUS_CONTEXT_REPLAYS = tuple(
    Replay(
        model,
        identity,
        f"context-display-status-{setup}",
        "full",
        f"context-display-status{player_suffix}-{setup}",
    )
    for model, identity, player_suffix in (
        ("xdj-rx3-status", "xdj-rx3-player-11-status.json", "-player-11"),
        ("cdj-3000-status", "cdj-3000-player-1-status.json", ""),
    )
    for setup in ("extended", "legacy")
) + tuple(
    Replay(
        "xdj-rx3-status",
        "xdj-rx3-player-11-status.json",
        f"context-display-status-requester-1-{setup}",
        "full",
        f"context-display-status-{setup}",
    )
    for setup in ("extended", "legacy")
)

STATUS_CONTEXT_REPLAYS = tuple(
    Replay(
        model,
        identity,
        f"context-{family}-status-{setup}",
        fixture,
        f"context-{family}-status-player-{player}-{setup}",
    )
    for model, identity, player in (
        ("xdj-rx3-status", "xdj-rx3-player-11-status.json", 11),
        ("cdj-3000-status", "cdj-3000-player-1-status.json", 1),
    )
    for family, fixture in (
        ("play", "full"),
        ("class2", "full"),
        ("hot-cue-getter", "hot-cue-banks"),
        ("hot-cue-catalog", "hot-cue-banks"),
    )
    for setup in ("extended", "legacy")
)

READ_ONLY_CONTEXT_REPLAYS = (
    PACKED_CONTEXT_REPLAYS
    + DEVICE_SETUP_REPLAYS
    + DISPLAY_STATUS_CONTEXT_REPLAYS
    + STATUS_CONTEXT_REPLAYS
)

ADDITIONAL_READ_ONLY_REPLAYS = (
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "bpm-tolerance-boundaries",
        "bpm-tolerance-boundaries",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "track-compatibility-exhaustive-extended",
        "compatibility-exhaustive",
        "generated/track-compatibility-exhaustive/track-compatibility-exhaustive-extended",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "track-compatibility-exhaustive-legacy",
        "compatibility-exhaustive",
        "generated/track-compatibility-exhaustive/track-compatibility-exhaustive-legacy",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "adjacent-payload-fileless",
        "full",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "adjacent-payload-missing-files",
        "payload-paths",
    ),
    Replay(
        "xdj-rx3",
        "xdj-rx3-player-11.json",
        "adjacent-payload-success",
        "payload-valid",
    ),
)

REPLAYS = (
    BASE_REPLAYS
    + DEVICE_CAPABILITY_REPLAYS
    + DEVICE_SMART_REPLAYS
    + DEVICE_COMPATIBILITY_REPLAYS
    + DEVICE_RECONNECT_REPLAYS
    + SETTINGS_REPLAYS
    + LEGACY_SETTINGS_REPLAYS
    + SMART_SETTINGS_REPLAYS
    + KEY_NOTATION_REPLAYS
    + CATEGORY_REPLAYS
    + SEARCH_REPLAYS
    + SORT_REPLAYS
    + DATA_REPLAYS
    + DISPLAY_SONG_INFO_REPLAYS
    + STATUS_SIBLING_REPLAYS
    + CDJ_2000NEXUS_STATUS_REPLAYS
    + READ_ONLY_CONTEXT_REPLAYS
    + ADDITIONAL_READ_ONLY_REPLAYS
)

# These suites need adapter isolation or backend support before they can run
# safely. Keeping them explicit makes every canonical golden accountable.
DEFERRED_REPLAYS = frozenset(
    {
        ("xdj-rx3", "sort-secondary-render-6"),
        ("xdj-rx3", "key-device-setting-classic"),
        ("xdj-rx3", "key-device-setting-alphanumeric"),
        ("xdj-rx3", "device-key-style-alphanumeric-secondary-bpm"),
        ("xdj-rx3", "device-key-style-alphanumeric-smart-secondary-bpm"),
        ("xdj-rx3-status", "context-hot-cue-setter-status-extended"),
        ("xdj-rx3-status", "context-hot-cue-setter-status-legacy"),
        ("cdj-3000-status", "context-hot-cue-setter-status-extended"),
        ("cdj-3000-status", "context-hot-cue-setter-status-legacy"),
        ("xdj-rx3-status", "context-hot-cue-legacy-setter-status-extended"),
        ("xdj-rx3-status", "context-hot-cue-legacy-setter-status-legacy"),
        ("cdj-3000-status", "context-hot-cue-legacy-setter-status-extended"),
        ("cdj-3000-status", "context-hot-cue-legacy-setter-status-legacy"),
        ("xdj-rx3", "hot-cue-bank-discovery"),
        ("xdj-rx3", "hot-cue-bank-matrix"),
        ("xdj-rx3", "hot-cue-bank-location-renders"),
        ("xdj-rx3", "hot-cue-bank-location-cross"),
        ("xdj-rx3", "hot-cue-bank-location-state"),
        ("xdj-rx3", "hot-cue-bank-count-boundaries"),
        ("xdj-rx3", "hot-cue-bank-count-int32-max"),
        ("xdj-rx3", "hot-cue-bank-count-high-bit"),
        ("xdj-rx3", "hot-cue-bank-count-uint32-max"),
        ("xdj-rx3", "hot-cue-bank-cues"),
        ("xdj-rx3", "hot-cue-bank-cues-status"),
        ("xdj-rx3", "hot-cue-bank-cues-legacy"),
        ("xdj-rx3", "hot-cue-bank-legacy-track-cues"),
        ("xdj-rx3", "hot-cue-bank-legacy-ordinals"),
        ("xdj-rx3", "hot-cue-bank-legacy-ordinal-boundaries"),
        ("xdj-rx3", "hot-cue-bank-deleted-bank-member"),
        ("xdj-rx3", "hot-cue-bank-cues-sequence"),
        ("xdj-rx3", "hot-cue-bank-cues-extended"),
        ("xdj-rx3", "hot-cue-bank-cue-fields"),
        ("xdj-rx3", "hot-cue-bank-extended-fields"),
        ("xdj-rx3", "hot-cue-bank-set-extended"),
        ("xdj-rx3", "hot-cue-bank-pagination"),
        ("xdj-rr", "hot-cue-bank-cues-status"),
    }
) | frozenset(
    (
        "xdj-rx3-status",
        f"hot-cue-setter-parser-{variant['id']}",
    )
    for variant in json.loads(
        (ROOT / "data/hot-cue-setter-parser-matrix.json").read_text()
    )["variants"]
) | frozenset(
    (
        "xdj-rx3-status",
        f"hot-cue-setter-field-{variant['id']}",
    )
    for variant in json.loads(
        (ROOT / "data/hot-cue-setter-field-matrix.json").read_text()
    )["variants"]
)
