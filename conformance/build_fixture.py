#!/usr/bin/env python3
"""Build deterministic encrypted master.db profiles for Link Export tests."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

from Crypto.Cipher import Blowfish
from track_compatibility_matrix import compatibility_exhaustive_cases
from sqlcipher3 import dbapi2 as sqlite


FIXTURE_VERSION = 1
STAMP = "2026-01-01 00:00:00.000 +00:00"
DYNAMIC_TABLES = (
    "djmdSongHotCueBanklist",
    "hotCueBanklistCue",
    "djmdHotCueBanklist",
    "djmdSongMyTag",
    "djmdMyTag",
    "djmdSongTagList",
    "djmdSongPlaylist",
    "djmdPlaylist",
    "djmdRecommendLike",
    "djmdSongHistory",
    "djmdHistory",
    "djmdContent",
    "djmdAlbum",
    "djmdArtist",
    "djmdGenre",
    "djmdLabel",
    "djmdKey",
)

IDS = {
    "artist.alpha": 1001,
    "artist.beta": 1002,
    "artist.remixer": 1003,
    "artist.original": 1004,
    "artist.composer_ascii_126": 1101,
    "artist.composer_ascii_127": 1102,
    "artist.composer_ascii_128": 1103,
    "artist.composer_unicode_126": 1104,
    "artist.composer_unicode_127": 1105,
    "artist.composer_unicode_128": 1106,
    "album.one": 2001,
    "album.two": 2002,
    "album.three": 2003,
    "genre.house": 3001,
    "genre.techno": 3002,
    "label.one": 4001,
    "label.two": 4002,
    "key.am": 5001,
    "key.c": 5002,
    "playlist.cue_analysis": 200000,
    "playlist.folder": 6001,
    "playlist.primary": 6002,
    "playlist.empty": 6003,
    "playlist.smart_rule_only": 6010,
    "playlist.smart_contradiction": 6011,
    "playlist.smart_malformed": 6012,
    "playlist.ordinary_with_rule": 6013,
    "playlist.smart_without_rule": 6014,
    "playlist.visibility_smart": 6015,
    "history.one": 7001,
    "hotcue.folder": 8001,
    "hotcue.bank": 8002,
    "mytag.group.genre": 8501,
    "mytag.warmup": 8502,
    "mytag.group.components": 8503,
    "mytag.vocal": 8504,
    "mytag.empty": 8505,
    "mytag.default.group.genre": 1,
    "mytag.default.group.components": 2,
    "mytag.default.group.situation": 3,
    "mytag.default.group.untitled": 4,
    "mytag.default.sub_bass": 79324672,
    "mytag.default.percussion": 154495003,
    "mytag.default.dark": 158455786,
    "mytag.default.nu_disco": 463364308,
    "mytag.default.acid_house": 539841621,
    "mytag.default.build_up": 832445659,
    "mytag.default.my_comment": 857457019,
    "mytag.default.second_floor": 917243188,
    "mytag.default.deep_house": 999625328,
    "mytag.default.peak_time": 1156949736,
    "mytag.default.trap": 1308912924,
    "mytag.default.vocal": 1387538896,
    "mytag.default.lounge": 1493684869,
    "mytag.default.techno": 1628431659,
    "mytag.default.electro_house": 1971960657,
    "mytag.default.synth": 2005851049,
    "mytag.default.morning": 2045957214,
    "mytag.default.upper": 2169337181,
    "mytag.default.build_down": 2320977753,
    "mytag.default.beat": 2487691792,
    "mytag.default.bass_music": 2502627224,
    "mytag.default.main_floor": 2538315910,
    "mytag.default.mid_night": 3354707172,
    "mytag.default.piano": 3596715289,
    "track.first": 10001,
    "track.second": 10002,
    "track.third": 10003,
    "track.fourth": 10004,
    "track.fifth": 10005,
    "track.sixth": 10006,
    "track.seventh": 10007,
    "track.eighth": 10008,
    "track.ninth": 10009,
    "track.tenth": 10010,
    "track.eleventh": 10011,
    "track.twelfth": 10012,
    "track.thirteenth": 10013,
    "track.fourteenth": 10014,
    "track.deleted": 10999,
}

HOT_CUE_BANK_IDS = {
    "hotcue.folder.alpha": 9001,
    "hotcue.folder.beta": 9002,
    "hotcue.bank.root": 9003,
    "hotcue.folder.deep": 9011,
    "hotcue.bank.alpha": 9012,
    "hotcue.bank.empty": 9013,
    "hotcue.bank.deep": 9021,
    "hotcue.bank.beta_deleted": 9031,
    "hotcue.bank.beta": 9032,
    "hotcue.bank.large": 9070,
}

CUE_FIELD_BANK_IDS = {
    "hotcue.bank.cue_fields": 9041,
    "hotcue.bank.cue_ignored": 9042,
}

EXTENDED_CUE_BANK_IDS = {
    "hotcue.bank.extended_baseline": 9043,
    "hotcue.bank.extended_timing": 9044,
    "hotcue.bank.extended_color": 9045,
    "hotcue.bank.extended_comment_ascii": 9046,
    "hotcue.bank.extended_comment_unicode": 9047,
    "hotcue.bank.extended_beat_loop": 9048,
    "hotcue.bank.extended_microseconds": 9049,
    "hotcue.bank.extended_in_seek": 9050,
    "hotcue.bank.extended_out_seek": 9051,
}

MUTATION_CUE_BANK_IDS = {
    "hotcue.bank.mutation": 9060,
}

CUE_PAYLOAD_TRACK_IDS = {
    "cue_payload.zero": 11_001,
    "cue_payload.one": 11_002,
    "cue_payload.three": 11_003,
    "cue_payload.count_255": 11_004,
    "cue_payload.count_256": 11_005,
    "cue_payload.timing": 11_006,
    "cue_payload.color": 11_007,
    "cue_payload.comment_empty": 11_008,
    "cue_payload.comment_ascii": 11_009,
    "cue_payload.comment_unicode": 11_010,
    "cue_payload.comment_nul": 11_011,
    "cue_payload.beat_loop": 11_012,
    "cue_payload.microseconds": 11_013,
    "cue_payload.null_options": 11_014,
    "cue_payload.seek_in": 11_015,
    "cue_payload.seek_out_only": 11_016,
    "cue_payload.seek_malformed": 11_017,
    "cue_payload.deleted_only": 11_018,
    "cue_payload.mixed_deleted": 11_019,
}
IDS.update({f"track.{name}": value for name, value in CUE_PAYLOAD_TRACK_IDS.items()})

KEY_NOTATION_SCALE_NAMES = {
    IDS["key.am"]: "08A",
    IDS["key.c"]: "08B",
}

SMART_RULE_MATRIX_NAMES = (
    *(f"genre_operator_{operator:02}" for operator in range(1, 12)),
    *(f"bpm_operator_{operator:02}" for operator in range(1, 12)),
    "logic_all",
    "logic_any",
    "nested_all",
    "nested_any",
    "empty_all",
    "empty_any",
    "unknown_operator",
    "unknown_property",
    "condition_outside_node",
    "two_roots",
    "missing_logical_operator",
    "logical_operator_zero",
    "logical_operator_three",
    "automatic_update_zero",
    "missing_automatic_update",
    "mismatched_id",
    "missing_id",
)
IDS.update(
    {
        f"playlist.smart_matrix.{name}": 6301 + index
        for index, name in enumerate(SMART_RULE_MATRIX_NAMES)
    }
)

SMART_NUMERIC_PROPERTIES = {
    "bpm": ("bpm", "12150", "12050", "12250"),
    "rating": ("rating", "3", "1", "4"),
    "play_count": ("counter", "3", "2", "5"),
    "duration": ("duration", "599", "60", "601"),
    "year": ("year", "2020", "1999", "2024"),
}
SMART_NUMERIC_MATRIX_NAMES = (
    *(
        f"{name}_operator_{operator:02}"
        for name in SMART_NUMERIC_PROPERTIES
        for operator in range(1, 6)
    ),
    *(f"{name}_reversed_range" for name in SMART_NUMERIC_PROPERTIES),
    *(
        f"{name}_{variant}"
        for name in SMART_NUMERIC_PROPERTIES
        for variant in ("empty_equal", "empty_not_equal")
    ),
    *(
        f"{name}_{variant}"
        for name in SMART_NUMERIC_PROPERTIES
        for variant in ("invalid_equal", "invalid_not_equal")
    ),
    *(
        f"bpm_{variant}"
        for variant in (
            "negative_equal",
            "negative_not_equal",
            "negative_greater",
            "negative_less",
            "negative_range",
            "overflow_equal",
            "overflow_not_equal",
            "overflow_greater",
            "overflow_less",
            "overflow_range",
        )
    ),
)
IDS.update(
    {
        f"playlist.smart_numeric.{name}": 6401 + index
        for index, name in enumerate(SMART_NUMERIC_MATRIX_NAMES)
    }
)

SMART_NUMERIC_BOUNDARY_TRACKS = (
    ("null", None),
    ("zero", 0),
    ("half", 0.5),
    ("one_half", 1.5),
    ("minus_half", -0.5),
    ("minus_one", -1),
    ("int32_max", 2_147_483_647),
    ("int32_plus_one", 2_147_483_648),
    ("uint32_max", 4_294_967_295),
    ("uint32_plus_one", 4_294_967_296),
)
SMART_NUMERIC_BOUNDARY_PROPERTIES = {
    "bpm": "bpm",
    "rating": "rating",
    "play_count": "counter",
    "duration": "duration",
    "year": "year",
}
SMART_NUMERIC_BOUNDARY_VARIANTS = (
    "equal_zero",
    "not_equal_zero",
    "greater_zero",
    "less_zero",
    "range_minus_one_to_one",
    "equal_half",
    "not_equal_half",
    "greater_half",
    "less_half",
    "range_half_to_one_half",
    "equal_int32_max",
    "greater_int32_max",
    "equal_int32_plus_one",
    "equal_uint32_max",
    "equal_uint32_plus_one",
    "missing_left_equal",
    "missing_left_not_equal",
    "range_missing_left",
    "range_missing_right",
    "range_both_missing",
)
SMART_NUMERIC_BOUNDARY_NAMES = tuple(
    f"{name}_{variant}"
    for name in SMART_NUMERIC_BOUNDARY_PROPERTIES
    for variant in SMART_NUMERIC_BOUNDARY_VARIANTS
)
IDS.update(
    {
        f"track.smart_numeric_boundary.{name}": 35_001 + index
        for index, (name, _value) in enumerate(SMART_NUMERIC_BOUNDARY_TRACKS)
    }
)
IDS.update(
    {
        f"playlist.smart_numeric_boundary.{name}": 7601 + index
        for index, name in enumerate(SMART_NUMERIC_BOUNDARY_NAMES)
    }
)

SMART_PROPERTY_MATRIX_NAMES = (
    "artist",
    "album",
    "album_artist",
    "original_artist",
    "bpm",
    "grouping",
    "comments",
    "producer",
    "stock_date",
    "date_created_field",
    "date_created_audit",
    "counter",
    "file_name",
    "genre",
    "key",
    "label",
    "mix_name",
    "my_tag_warmup_raw",
    "my_tag_warmup_signed",
    "my_tag_vocal_raw",
    "my_tag_vocal_signed",
    "rating",
    "date_released",
    "remixed_by",
    "duration",
    "name",
    "year",
    "alias_title",
    "alias_color",
    "alias_play_count",
    "alias_remixer",
    "alias_composer",
    "alias_filename_lowercase",
)
IDS.update(
    {
        f"playlist.smart_property.{name}": 6501 + index
        for index, name in enumerate(SMART_PROPERTY_MATRIX_NAMES)
    }
)

SMART_DATE_PROPERTIES = {
    "stock_date": "stockDate",
    "date_created": "dateCreated",
    "date_released": "dateReleased",
}
SMART_DATE_MATRIX_NAMES = (
    *(
        f"{name}_{suffix}"
        for name in SMART_DATE_PROPERTIES
        for suffix in (
            *(f"operator_{operator:02}" for operator in range(1, 6)),
            "reversed_range",
            "blank_equal",
            "blank_not_equal",
            "invalid_equal",
            "invalid_not_equal",
        )
    ),
)
IDS.update(
    {
        f"playlist.smart_date.{name}": 6701 + index
        for index, name in enumerate(SMART_DATE_MATRIX_NAMES)
    }
)

SMART_RELATIVE_DATE_PROPERTIES = {
    "stock_date": "stockDate",
    "date_created": "dateCreated",
    "date_released": "dateReleased",
}
SMART_RELATIVE_DATE_UNITS = ("day", "week", "month", "year")
SMART_RELATIVE_DATE_MATRIX_NAMES = (
    *(
        f"{name}_{unit}_operator_{operator:02}"
        for name in SMART_RELATIVE_DATE_PROPERTIES
        for unit in SMART_RELATIVE_DATE_UNITS
        for operator in (6, 7)
    ),
    *(
        f"stock_date_unit_{variant}_operator_{operator:02}"
        for variant in (
            "days",
            "weeks",
            "months",
            "years",
            "uppercase_month",
            "empty",
            "unknown",
        )
        for operator in (6, 7)
    ),
    *(
        f"stock_date_count_{variant}_operator_{operator:02}"
        for variant in (
            "zero",
            "negative",
            "blank",
            "invalid",
            "fractional",
            "two",
            "thirty_one",
        )
        for operator in (6, 7)
    ),
    *(f"stock_date_month_count_two_operator_{operator:02}" for operator in (6, 7)),
    *(f"stock_date_right_31_operator_{operator:02}" for operator in (6, 7)),
)
IDS.update(
    {
        f"playlist.smart_relative_date.{name}": 6801 + index
        for index, name in enumerate(SMART_RELATIVE_DATE_MATRIX_NAMES)
    }
)

SMART_DATE_FORMAT_PROPERTIES = {
    "stock_date": "stockDate",
    "date_created": "dateCreated",
    "date_released": "dateReleased",
}
SMART_DATE_FORMAT_VALUES = (
    ("canonical_jan_31", "2025-01-31"),
    ("canonical_leap_day", "2024-02-29"),
    ("canonical_epoch", "1970-01-01"),
    ("pre_epoch", "1969-12-31"),
    ("year_zero", "0000-01-01"),
    ("year_9999", "9999-12-31"),
    ("separator_slash", "2025/01/31"),
    ("separator_dot", "2025.01.31"),
    ("separator_space", "2025 01 31"),
    ("separator_letters", "2025x01y31"),
    ("separator_unicode", "2025Ω01Ω31"),
    ("separator_newline", "2025\n01\n31"),
    ("nonleap_feb_29", "2025-02-29"),
    ("leap_feb_30", "2024-02-30"),
    ("nonleap_feb_30", "2025-02-30"),
    ("nonleap_feb_31", "2025-02-31"),
    ("april_31", "2025-04-31"),
    ("month_zero", "2025-00-15"),
    ("month_13", "2025-13-01"),
    ("day_zero", "2025-01-00"),
    ("day_32", "2025-01-32"),
    ("month_99", "2025-99-01"),
    ("day_99", "2025-01-99"),
    ("single_digit_month", "2025-1-31"),
    ("single_digit_day", "2025-01-1"),
    ("five_digit_year", "02025-01-31"),
    ("timestamp_t", "2025-01-31T00:00"),
    ("timestamp_space", "2025-01-31 00:00:00"),
    ("leading_space", " 2025-01-31"),
    ("trailing_space", "2025-01-31 "),
    ("not_a_date", "not-a-date"),
    ("ascii_letters", "abcdefghij"),
    ("zero_digits", "0000000000"),
    ("letter_in_year", "202A-01-31"),
    ("plus_year", "+025-01-31"),
    ("minus_year", "-001-01-01"),
    ("fullwidth_digits", "２０２５-０１-３１"),
    ("empty", ""),
    ("embedded_nul", "2025-0\x00-31"),
    ("null", None),
)
SMART_DATE_FORMAT_RULE_VALUES = SMART_DATE_FORMAT_VALUES[:-2]
SMART_DATE_FORMAT_MATRIX_NAMES = (
    *(
        name
        for property_name in SMART_DATE_FORMAT_PROPERTIES
        for name in (
            *(
                f"{property_name}_{value_name}_equal"
                for value_name, _ in SMART_DATE_FORMAT_RULE_VALUES
            ),
            f"{property_name}_canonical_not_equal",
        )
    ),
)
IDS.update(
    {
        f"track.date_format.{name}": 11_001 + index
        for index, (name, _) in enumerate(SMART_DATE_FORMAT_VALUES)
    }
)
IDS.update(
    {
        f"playlist.smart_date_format.{name}": 6901 + index
        for index, name in enumerate(SMART_DATE_FORMAT_MATRIX_NAMES)
    }
)

SMART_TEXT_VALUES = (
    ("alpha_upper", "Alpha"),
    ("alpha_lower", "alpha"),
    ("alpha_acute_precomposed", "Álpha"),
    ("alpha_acute_decomposed", "A\u0301lpha"),
    ("alpha_diaeresis_upper", "ÄLPHÄ"),
    ("alpha_prefix", "Alpha Beta"),
    ("alpha_suffix", "Beta Alpha"),
    ("alpha_middle", "Beta Alpha Gamma"),
    ("alpha_spaced", " Alpha "),
    ("empty", ""),
    ("null", None),
    ("embedded_nul_suffix", "Alpha\x00Tail"),
    ("embedded_nul_prefix", "Before\x00Alpha"),
    ("emoji_prefix", "U0001f600Alpha"),
    ("emoji_suffix", "AlphaU0001f600"),
    ("emoji_only", "U0001f600"),
    ("sharp_s", "straße"),
    ("sharp_s_expanded", "STRASSE"),
    ("ligature", "Æther"),
    ("ligature_expanded", "AETHER"),
    ("fullwidth", "Ａｌｐｈａ"),
    ("turkish_ascii", "Istanbul"),
    ("turkish_dotted", "İstanbul"),
    ("turkish_dotless", "ıstanbul"),
    ("greek_upper", "ΟΣ"),
    ("greek_sigma", "οσ"),
    ("greek_final_sigma", "ος"),
    ("katakana", "カタカナ"),
    ("hiragana", "かたかな"),
    ("combining_dot_acute", "a\u0323\u0301"),
    ("combining_acute_dot", "a\u0301\u0323"),
    ("punctuation_hyphen", "Alpha-Beta"),
    ("punctuation_none", "AlphaBeta"),
    ("tab", "Alpha\tBeta"),
    ("newline", "Alpha\nBeta"),
    ("cyrillic_alpha", "Аlpha"),
    ("greek_alpha", "Αlpha"),
    ("trailing_combining", "Alpha\u0301"),
    ("angstrom_sign", "Ålpha"),
    ("a_ring", "Ålpha"),
    ("ampersand", "Alpha & Beta"),
    ("double_quote", 'Alpha "Beta"'),
    ("apostrophe", "Alpha 'Beta'"),
)
SMART_TEXT_RULES = (
    *((f"alpha_operator_{operator:02}", operator, "Alpha") for operator in (1, 2, 8, 9, 10, 11)),
    ("alpha_lower_equal", 1, "alpha"),
    ("alpha_acute_precomposed_equal", 1, "Álpha"),
    ("alpha_acute_decomposed_equal", 1, "A\u0301lpha"),
    ("alpha_diaeresis_equal", 1, "Älpha"),
    ("alpha_trailing_combining_equal", 1, "Alpha\u0301"),
    ("alpha_angstrom_equal", 1, "Ålpha"),
    ("alpha_a_ring_equal", 1, "Ålpha"),
    ("beta_contains", 8, "Beta"),
    ("beta_not_contains", 9, "Beta"),
    ("beta_starts", 10, "Beta"),
    ("beta_ends", 11, "Beta"),
    *((f"empty_operator_{operator:02}", operator, "") for operator in (1, 2, 8, 9, 10, 11)),
    ("emoji_equal", 1, "U0001f600"),
    ("emoji_contains", 8, "U0001f600"),
    ("emoji_starts", 10, "U0001f600"),
    ("emoji_ends", 11, "U0001f600"),
    ("sharp_s_equal", 1, "straße"),
    ("sharp_s_expanded_equal", 1, "STRASSE"),
    ("sharp_s_contains_ss", 8, "ss"),
    ("ligature_equal", 1, "Æther"),
    ("ligature_expanded_equal", 1, "AETHER"),
    ("fullwidth_equal", 1, "Alpha"),
    ("turkish_ascii_equal", 1, "istanbul"),
    ("turkish_dotted_equal", 1, "İSTANBUL"),
    ("turkish_dotless_equal", 1, "ıstanbul"),
    ("greek_upper_equal", 1, "ΟΣ"),
    ("greek_sigma_equal", 1, "οσ"),
    ("greek_final_sigma_equal", 1, "ος"),
    ("katakana_equal", 1, "カタカナ"),
    ("hiragana_equal", 1, "かたかな"),
    ("combining_dot_acute_equal", 1, "a\u0323\u0301"),
    ("combining_acute_dot_equal", 1, "a\u0301\u0323"),
    ("punctuation_none_equal", 1, "AlphaBeta"),
    ("punctuation_none_contains", 8, "AlphaBeta"),
    ("punctuation_hyphen_equal", 1, "Alpha-Beta"),
    ("punctuation_space_equal", 1, "Alpha Beta"),
    ("tab_equal", 1, "Alpha\tBeta"),
    ("newline_equal", 1, "Alpha\nBeta"),
    ("cyrillic_alpha_equal", 1, "Аlpha"),
    ("greek_alpha_equal", 1, "Αlpha"),
    ("ampersand_equal", 1, "Alpha & Beta"),
    ("ampersand_contains", 8, "&"),
    ("double_quote_equal", 1, 'Alpha "Beta"'),
    ("apostrophe_equal", 1, "Alpha 'Beta'"),
)
SMART_TEXT_MATRIX_NAMES = tuple(name for name, _operator, _value in SMART_TEXT_RULES)
IDS.update(
    {
        f"track.smart_text.{name}": 12_001 + index
        for index, (name, _value) in enumerate(SMART_TEXT_VALUES)
    }
)

SMART_STRING_PROPERTY_VALUES = (
    ("alpha_upper", "Alpha"),
    ("alpha_lower", "alpha"),
    ("alpha_acute_precomposed", "\u00c1lpha"),
    ("alpha_acute_decomposed", "A\u0301lpha"),
    ("fullwidth", "\uff21\uff4c\uff50\uff48\uff41"),
    ("alpha_prefix", "Alpha Beta"),
    ("alpha_suffix", "Beta Alpha"),
    ("beta", "Beta"),
    ("empty", ""),
    ("null", None),
)
SMART_STRING_PROPERTIES = {
    "artist": "artist",
    "album": "album",
    "album_artist": "albumArtist",
    "original_artist": "originalArtist",
    "producer": "producer",
    "genre": "genre",
    "key": "key",
    "label": "label",
    "remixed_by": "remixedBy",
    "comments": "comments",
    "file_name": "fileName",
    "mix_name": "mixName",
    "name": "name",
}
SMART_STRING_PROPERTY_RULES = (
    ("alpha_equal", 1, "Alpha"),
    ("alpha_not_equal", 2, "Alpha"),
    ("alpha_contains", 8, "Alpha"),
    ("alpha_not_contains", 9, "Alpha"),
    ("alpha_starts", 10, "Alpha"),
    ("alpha_ends", 11, "Alpha"),
    ("empty_equal", 1, ""),
    ("empty_not_equal", 2, ""),
)
SMART_STRING_PROPERTY_MATRIX_NAMES = tuple(
    f"{property_name}_{rule_name}"
    for property_name in SMART_STRING_PROPERTIES
    for rule_name, _operator, _value in SMART_STRING_PROPERTY_RULES
)
IDS.update(
    {
        f"track.smart_string_property.{name}": 13_001 + index
        for index, (name, _value) in enumerate(SMART_STRING_PROPERTY_VALUES)
    }
)
IDS.update(
    {
        f"playlist.smart_string_property.{name}": 7201 + index
        for index, name in enumerate(SMART_STRING_PROPERTY_MATRIX_NAMES)
    }
)

SMART_MYTAG_TRACK_NAMES = (
    "tag_one",
    "tag_int32_max",
    "tag_high_bit",
    "tag_uint32_max",
    "tag_zero",
    "tag_one_high_bit",
    "tag_high_bit_uint32_max",
    "untagged",
)
SMART_MYTAG_VALUE_CASES = (
    ("zero", "0"),
    ("int32_max", "2147483647"),
    ("high_bit_raw", "2147483648"),
    ("uint32_max", "4294967295"),
    ("minus_one", "-1"),
    ("int32_min", "-2147483648"),
    ("uint32_overflow", "4294967296"),
    ("negative_overflow", "-2147483649"),
    ("blank", ""),
    ("invalid", "not-a-number"),
    ("leading_zero_one", "0001"),
    ("plus_one", "+1"),
    ("spaced_one", " 1 "),
    ("hex_one", "0x1"),
    ("comma_pair", "1,2147483648"),
)
SMART_MYTAG_SINGLE_NAMES = (
    *(f"operator_{operator:02}" for operator in range(1, 12)),
    *(
        f"{name}_operator_{operator:02}"
        for name, _value in SMART_MYTAG_VALUE_CASES
        for operator in (8, 9)
    ),
    "value_right_ignored",
    "value_unit_ignored",
)
SMART_MYTAG_MULTI_NAMES = (
    "all_contains_one_high_bit",
    "any_contains_one_high_bit",
    "all_not_contains_one_high_bit",
    "any_not_contains_one_high_bit",
    "all_contains_one_not_high_bit",
    "any_contains_one_not_high_bit",
)
SMART_MYTAG_MATRIX_NAMES = (*SMART_MYTAG_SINGLE_NAMES, *SMART_MYTAG_MULTI_NAMES)
IDS.update(
    {
        f"track.smart_mytag.{name}": 19_001 + index
        for index, name in enumerate(SMART_MYTAG_TRACK_NAMES)
    }
)
IDS.update(
    {
        f"playlist.smart_mytag.{name}": 7401 + index
        for index, name in enumerate(SMART_MYTAG_MATRIX_NAMES)
    }
)
SMART_XML_MATRIX_NAMES = (
    "canonical_house",
    "lowercase_elements",
    "mixedcase_elements",
    "xml_declaration",
    "xml_declaration_encoding",
    "leading_bom",
    "leading_comment",
    "leading_processing_instruction",
    "trailing_comment",
    "surrounding_whitespace",
    "reordered_attributes",
    "single_quoted_attributes",
    "decimal_character_reference",
    "hex_character_reference",
    "empty_string",
    "whitespace_only",
    "text_only",
    "malformed_open",
    "unclosed_root",
    "mismatched_close",
    "unclosed_condition",
    "missing_attribute_quote",
    "unescaped_ampersand",
    "unknown_entity",
    "invalid_numeric_entity",
    "wrapper_root",
    "namespaced_root",
    "condition_as_root",
    "self_closing_node",
    "text_child_only",
    "comment_child_only",
    "cdata_child_only",
    "unknown_child",
    "unknown_wrapper_condition",
    "nested_node_only",
    "nested_then_direct_house",
    "direct_house_then_nested_techno",
    "two_direct_all",
    "two_direct_any",
    "condition_before_node",
    "two_roots_house_then_techno",
    "valid_root_trailing_text",
    "leading_text_valid_root",
    "missing_logical_operator",
    "blank_logical_operator",
    "invalid_logical_operator",
    "plus_two_logical_operator",
    "spaced_two_logical_operator",
    "duplicate_logical_one_then_two",
    "duplicate_logical_two_then_one",
    "lowercase_root_attributes",
    "uppercase_root_attributes",
    "missing_property",
    "blank_property",
    "whitespace_property",
    "uppercase_property_value",
    "property_leading_space",
    "missing_operator",
    "blank_operator",
    "invalid_operator_text",
    "plus_one_operator",
    "spaced_one_operator",
    "leading_zero_operator",
    "duplicate_operator_one_then_two",
    "duplicate_operator_two_then_one",
    "missing_value_left",
    "duplicate_value_house_then_techno",
    "duplicate_value_techno_then_house",
    "extra_condition_attributes",
    "condition_with_text_content",
    "namespaced_condition",
    "valid_root_then_nul_junk",
    "nul_before_root",
)
IDS.update(
    {
        f"playlist.smart_xml.{name}": 7501 + index
        for index, name in enumerate(SMART_XML_MATRIX_NAMES)
    }
)
IDS.update(
    {
        f"playlist.smart_text.{name}": 7101 + index
        for index, name in enumerate(SMART_TEXT_MATRIX_NAMES)
    }
)

DEFAULT_MYTAGS = (
    ("mytag.default.group.genre", 1, "Genre", 1, "root"),
    ("mytag.default.group.components", 2, "Components", 1, "root"),
    ("mytag.default.group.situation", 3, "Situation", 1, "root"),
    ("mytag.default.group.untitled", 4, "Untitled Column", 1, "root"),
    ("mytag.default.acid_house", 1, "Acid House", 0, "mytag.default.group.genre"),
    ("mytag.default.deep_house", 2, "Deep House", 0, "mytag.default.group.genre"),
    ("mytag.default.techno", 3, "Techno", 0, "mytag.default.group.genre"),
    ("mytag.default.nu_disco", 4, "Nu Disco", 0, "mytag.default.group.genre"),
    ("mytag.default.electro_house", 5, "Electro House", 0, "mytag.default.group.genre"),
    ("mytag.default.bass_music", 6, "Bass Music", 0, "mytag.default.group.genre"),
    ("mytag.default.trap", 7, "Trap", 0, "mytag.default.group.genre"),
    ("mytag.default.synth", 1, "Synth", 0, "mytag.default.group.components"),
    ("mytag.default.vocal", 2, "Vocal", 0, "mytag.default.group.components"),
    ("mytag.default.beat", 3, "Beat", 0, "mytag.default.group.components"),
    ("mytag.default.sub_bass", 4, "Sub Bass", 0, "mytag.default.group.components"),
    ("mytag.default.percussion", 5, "Percussion", 0, "mytag.default.group.components"),
    ("mytag.default.piano", 6, "Piano", 0, "mytag.default.group.components"),
    ("mytag.default.dark", 7, "Dark", 0, "mytag.default.group.components"),
    ("mytag.default.upper", 8, "Upper", 0, "mytag.default.group.components"),
    ("mytag.default.main_floor", 1, "Main Floor", 0, "mytag.default.group.situation"),
    ("mytag.default.second_floor", 2, "Second Floor", 0, "mytag.default.group.situation"),
    ("mytag.default.lounge", 3, "Lounge", 0, "mytag.default.group.situation"),
    ("mytag.default.mid_night", 4, "Mid Night", 0, "mytag.default.group.situation"),
    ("mytag.default.morning", 5, "Morning", 0, "mytag.default.group.situation"),
    ("mytag.default.build_up", 6, "Build up", 0, "mytag.default.group.situation"),
    ("mytag.default.peak_time", 7, "Peak Time", 0, "mytag.default.group.situation"),
    ("mytag.default.build_down", 8, "Build down", 0, "mytag.default.group.situation"),
    ("mytag.default.my_comment", 1, "My Comment", 0, "mytag.default.group.untitled"),
)


def key_from_options(path: Path) -> str:
    options = dict(json.loads(path.read_text())["options"])
    encrypted = base64.b64decode(options["dp"])
    value = Blowfish.new(b"ZOwUlUZYqe9Rdm6j", Blowfish.MODE_ECB).decrypt(encrypted)
    return value.rstrip(b"\x00 \t\r\n").decode()


def connect(path: Path, key: str, readonly: bool = False):
    target = f"{path.resolve().as_uri()}?mode=ro" if readonly else str(path)
    connection = sqlite.connect(target, uri=readonly)
    connection.execute("PRAGMA key = '" + key.replace("'", "''") + "'")
    connection.execute("PRAGMA cipher_compatibility = 4")
    connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
    return connection


def insert(connection, table: str, **values) -> None:
    values.setdefault("UUID", str(values["ID"]))
    values.setdefault("created_at", STAMP)
    values.setdefault("updated_at", STAMP)
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    connection.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(values.values())
    )


def clear_library(connection) -> None:
    for table in DYNAMIC_TABLES:
        connection.execute(f"DELETE FROM {table}")


def add_lookups(connection) -> None:
    for item_id, name in (
        (IDS["artist.alpha"], "Alpha Artist"),
        (IDS["artist.beta"], "Beta Artist"),
        (IDS["artist.remixer"], "Fixture Remixer"),
        (IDS["artist.original"], "Fixture Original"),
    ):
        insert(connection, "djmdArtist", ID=str(item_id), Name=name, SearchStr=name.upper())

    for item_id, name, artist_id in (
        (IDS["album.one"], "Album One", IDS["artist.alpha"]),
        (IDS["album.two"], "Album Two", IDS["artist.alpha"]),
        (IDS["album.three"], "Album Three", IDS["artist.beta"]),
    ):
        insert(
            connection,
            "djmdAlbum",
            ID=str(item_id),
            Name=name,
            AlbumArtistID=str(artist_id),
            SearchStr=name.upper(),
        )

    for item_id, name in (
        (IDS["genre.house"], "Fixture House"),
        (IDS["genre.techno"], "Fixture Techno"),
    ):
        insert(connection, "djmdGenre", ID=str(item_id), Name=name)

    for item_id, name in (
        (IDS["label.one"], "Fixture Label One"),
        (IDS["label.two"], "Fixture Label Two"),
    ):
        insert(connection, "djmdLabel", ID=str(item_id), Name=name)

    insert(connection, "djmdKey", ID=str(IDS["key.am"]), ScaleName="Am", Seq=1)
    insert(connection, "djmdKey", ID=str(IDS["key.c"]), ScaleName="C", Seq=2)


def apply_key_notation_scale_names(connection) -> None:
    for key_id, scale_name in KEY_NOTATION_SCALE_NAMES.items():
        connection.execute(
            "UPDATE djmdKey SET ScaleName = ? WHERE CAST(ID AS INTEGER) = ?",
            (scale_name, key_id),
        )


def full_tracks() -> list[dict[str, object]]:
    titles = (
        "Alpha One",
        "Alpha Two",
        "Beta One",
        "Boundary Fifty Nine",
        "Boundary Sixty",
        "Unicode \u03a9 Search",
        "Unknown Album",
        "Maximum Ordinary",
    )
    rows = []
    for index, title in enumerate(titles, start=1):
        odd = index % 2 == 1
        rows.append(
            {
                "ID": str(10000 + index),
                "Title": title,
                "FileNameL": f"fixture-{index:02}.wav",
                "FileNameS": f"FIXTU~{index}.WAV",
                "ArtistID": str(IDS["artist.alpha"] if index <= 5 else IDS["artist.beta"]),
                "AlbumID": str(
                    0
                    if index == 7
                    else IDS["album.one"]
                    if index in (1, 3, 4)
                    else IDS["album.two"]
                    if index in (2, 5)
                    else IDS["album.three"]
                ),
                "GenreID": str(IDS["genre.house"] if odd else IDS["genre.techno"]),
                "BPM": (11950 + index * 50),
                "Length": (59, 60, 61, 599, 600, 601, 10799, 10800)[index - 1],
                "TrackNo": index,
                "BitRate": (0, 32, 128, 160, 192, 256, 320, 1411)[index - 1],
                "BitDepth": 16,
                "Commnt": f"comment-{index}",
                "FileType": 1,
                "Rating": (index - 1) % 6,
                "ReleaseYear": (0, 1999, 2000, 2020, 2021, 2024, 2999, 3000)[index - 1],
                "RemixerID": str(IDS["artist.remixer"]),
                "LabelID": str(IDS["label.one"] if odd else IDS["label.two"]),
                "OrgArtistID": str(IDS["artist.original"]),
                "KeyID": str(IDS["key.am"] if odd else IDS["key.c"]),
                "StockDate": f"202{index % 5}-0{(index % 9) + 1}-0{(index % 9) + 1}",
                "ColorID": str(index),
                "DJPlayCount": index - 1,
                "SearchStr": f"{title} Alpha Beta Fixture".upper(),
                "FolderPath": f"Z:/tracks/link-export-fixture/fixture-{index:02}.wav",
                "OrgFolderPath": f"Z:/tracks/link-export-fixture/fixture-{index:02}.wav",
                "rb_LocalFolderPath": f"Z:/tracks/link-export-fixture/fixture-{index:02}.wav",
                "FileSize": 8864,
                "SampleRate": 44100 if index != 8 else 48000,
                "HotCueAutoLoad": "on",
            }
        )
    return rows


def payload_path_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    rows[0].update(
        ImagePath="/PIONEER/Artwork/fff/missing-artwork/artwork.jpg",
        AnalysisDataPath="/PIONEER/USBANLZ/fff/missing-analysis/ANLZ0000.DAT",
    )
    rows[1].update(ImagePath="", AnalysisDataPath="")

    return rows


def payload_valid_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    rows[0].update(
        ImagePath="/PIONEER/Artwork/000/deterministic/artwork.jpg",
        AnalysisDataPath="/PIONEER/USBANLZ/000/deterministic/ANLZ0000.DAT",
    )

    return rows


def adjacent_payload_cue_tracks() -> list[dict[str, object]]:
    templates = full_tracks()
    rows = []
    for index, (name, content_id) in enumerate(CUE_PAYLOAD_TRACK_IDS.items(), 1):
        row = dict(templates[(index - 1) % len(templates)])
        filename = f"adjacent-cue-{index:02}.wav"
        row.update(
            ID=str(content_id),
            Title=f"Adjacent Cue {name.removeprefix('cue_payload.').replace('_', ' ').title()}",
            FileNameL=filename,
            FileNameS=f"ACQ{index:05}.WAV",
            SearchStr=f"ADJACENT CUE {name.upper()}",
            FolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            OrgFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            rb_LocalFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
        )
        rows.append(row)

    return rows


def hot_cue_bank_pagination_tracks() -> list[dict[str, object]]:
    templates = full_tracks()
    rows = []
    for index in range(1, 71):
        row = dict(templates[(index - 1) % len(templates)])
        filename = f"hot-cue-page-{index:03}.wav"
        row.update(
            ID=str(40_000 + index),
            Title=f"Hot Cue Page {index:03}",
            FileNameL=filename,
            FileNameS=f"HCP{index:05}.WAV",
            TrackNo=index,
            DJPlayCount=index,
            SearchStr=f"HOT CUE PAGE {index:03}",
            FolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            OrgFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            rb_LocalFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
        )
        rows.append(row)

    return rows


def link_visibility_tracks() -> list[dict[str, object]]:
    paths = (
        ("local-z", "Z:/tracks/link-export-fixture/local-z.wav"),
        ("soundcloud", "soundcloud:tracks:fixture-2"),
        ("beatport", "beatport:tracks:fixture-3"),
        ("beatsource", "beatsource:tracks:fixture-4"),
        ("tidal", "tidal:tracks:fixture-5"),
        ("spotify", "spotify:track:fixture-6"),
        ("apple-music", "apple-music:tracks:fixture-7"),
        ("unknown-scheme", "unknown:tracks:fixture-8"),
        ("uppercase-soundcloud", "SOUNDCLOUD:TRACKS:fixture-9"),
        ("embedded-soundcloud", "Z:/tracks/soundcloud:tracks:fixture-10.wav"),
        ("soundcloudish", "soundcloudish:tracks:fixture-11"),
        ("empty", ""),
        ("null", None),
        ("local-c", "C:/tracks/link-export-fixture/local-c.wav"),
    )
    templates = full_tracks()
    rows = []
    for index, (name, folder_path) in enumerate(paths, start=1):
        filename = f"visibility-{index:02}.wav"
        row = dict(templates[(index - 1) % len(templates)])
        row.update(
            ID=str(10_000 + index),
            Title=f"Visibility Match {index:02} {name}",
            FileNameL=filename,
            FileNameS=f"VIS{index:05}.WAV",
            TrackNo=index,
            SearchStr=f"VISIBILITY MATCH {index:02} {name.upper()}",
            FolderPath=folder_path,
            OrgFolderPath=f"Z:/original/{filename}",
            rb_LocalFolderPath=f"Z:/local/{filename}",
        )
        rows.append(row)

    return rows


def streaming_provider_path_tracks() -> list[dict[str, object]]:
    paths = (
        ("local-control", "Z:/tracks/link-export-fixture/provider-local.wav"),
        ("beatport-start", "/v4/catalog/tracks/11002"),
        ("beatport-url", "https://api.beatport.com/v4/catalog/tracks/11003"),
        ("beatport-middle", "prefix/v4/catalog/tracks/11004/suffix"),
        ("beatport-uppercase", "/V4/CATALOG/TRACKS/11005"),
        ("beatport-no-trailing-slash", "/v4/catalog/tracks"),
        ("beatport-singular-track", "/v4/catalog/track/11007"),
        ("beatport-scheme", "beatport:tracks:11008"),
        ("beatsource-scheme", "beatsource:tracks:11009"),
        ("beatport-near-substring", "x/v4/catalog/tracksish/11010"),
    )
    templates = full_tracks()
    rows = []
    for index, (name, folder_path) in enumerate(paths, start=1):
        filename = f"provider-path-{index:02}.wav"
        row = dict(templates[(index - 1) % len(templates)])
        row.update(
            ID=str(11_000 + index),
            Title=f"Provider Path {index:02} {name}",
            FileNameL=filename,
            FileNameS=f"PVP{index:05}.WAV",
            TrackNo=index,
            SearchStr=f"PROVIDER PATH {index:02} {name.upper()}",
            FolderPath=folder_path,
            OrgFolderPath=f"Z:/original/{filename}",
            rb_LocalFolderPath=f"Z:/local/{filename}",
        )
        rows.append(row)

    return rows


def smart_numeric_boundary_tracks() -> list[dict[str, object]]:
    base = full_tracks()
    rows = []
    for index, (name, value) in enumerate(SMART_NUMERIC_BOUNDARY_TRACKS, start=1):
        row = dict(base[(index - 1) % len(base)])
        filename = f"smart-numeric-boundary-{index:02}.wav"
        row.update(
            ID=str(IDS[f"track.smart_numeric_boundary.{name}"]),
            Title=f"Smart Numeric Boundary {name.replace('_', ' ').title()}",
            FileNameL=filename,
            FileNameS=f"SNB{index:05}.WAV",
            BPM=value,
            Rating=value,
            DJPlayCount=value,
            Length=value,
            ReleaseYear=value,
            SearchStr=f"SMART NUMERIC BOUNDARY {name.replace('_', ' ').upper()}",
            FolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            OrgFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            rb_LocalFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
        )
        rows.append(row)

    return rows


def search_ceiling_tracks(count: int = 1_005) -> list[dict[str, object]]:
    template = full_tracks()[0]
    rows = []
    for index in range(1, count + 1):
        title = f"Ceiling Match {index:04}"
        filename = f"large-{index:04}.wav"
        row = dict(template)
        row.update(
            ID=str(20_000 + index),
            Title=title,
            FileNameL=filename,
            FileNameS=f"LARGE{index:04}.WAV",
            TrackNo=index,
            DJPlayCount=index,
            SearchStr=title.upper(),
            FolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            OrgFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            rb_LocalFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
        )
        rows.append(row)

    return rows


def search_track_large_tracks() -> list[dict[str, object]]:
    tokens = " ".join(f"SORT{sort_id:02}" for sort_id in range(18))
    rows = search_ceiling_tracks(10_005)
    for row in rows:
        row["SearchStr"] = f"{row['SearchStr']} {tokens}"

    return rows


def search_track_large_title_tracks() -> list[dict[str, object]]:
    tokens = " ".join(f"SORT{sort_id:02}" for sort_id in range(18))
    rows = search_ceiling_tracks(10_005)
    for row in rows:
        row["Title"] = f"{row['Title']} {tokens}"
        row["SearchStr"] = str(row["Title"]).upper()

    return rows


def search_text_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    titles = (
        "Precomposed Éclair",
        "Precomposed éclair",
        "Combining E\u0301clair",
        "Combining e\u0301clair",
        "Emoji 🙂 Search",
        "Emoji 🙃 Search",
        "Sharp ß Search",
        "Dotted İ Search",
    )
    for index, (row, title) in enumerate(zip(rows, titles, strict=True), start=1):
        filename = f"text-{index:02}.wav"
        row.update(
            Title=title,
            FileNameL=filename,
            FileNameS=f"TEXT{index:02}.WAV",
            SearchStr=title,
            FolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            OrgFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            rb_LocalFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
        )

    return rows


def boundary_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    bpms = (0, 49, 50, 99, 100, 149, 150, 49_949)
    years = (0, 9, 10, 1999, 2000, 2999, 3000, 4000)
    play_counts = (0, 1, 254, 255, 256, 257, 32_767, 65_535)
    comments = (
        "",
        "c" * 126,
        "c" * 127,
        "c" * 128,
        "c" * 254,
        "c" * 255,
        "c" * 256,
        "\U0001f642" * 256,
    )
    stock_dates = (
        "",
        "d" * 126,
        "d" * 127,
        "d" * 128,
        "d" * 254,
        "d" * 255,
        "d" * 256,
        "\U0001f642" * 256,
    )
    values = zip(rows, bpms, years, play_counts, comments, stock_dates, strict=True)
    for row, bpm, year, play_count, comment, stock_date in values:
        row["BPM"] = bpm
        row["ReleaseYear"] = year
        row["DJPlayCount"] = play_count
        row["Commnt"] = comment
        row["StockDate"] = stock_date
        row["Title"] = f"Boundary BPM {bpm} Year {year}"
        row["SearchStr"] = str(row["Title"]).upper()
    return rows


def bpm_tolerance_tracks() -> list[dict[str, object]]:
    selected_bpm = 12_000
    rounded_bpm = (selected_bpm + 50) // 100 * 100
    points = {
        rounded_bpm - 51,
        rounded_bpm - 50,
        rounded_bpm - 49,
        selected_bpm,
        rounded_bpm + 48,
        rounded_bpm + 49,
        rounded_bpm + 50,
    }
    for percent in range(1, 7):
        lower = selected_bpm * (100 - percent) // 100
        upper = selected_bpm * (100 + percent) // 100
        points.update((lower - 1, lower, lower + 1, upper - 1, upper, upper + 1))

    template = full_tracks()[0]
    rows = []
    for index, bpm in enumerate(sorted(points), start=1):
        row = dict(template)
        filename = f"bpm-tolerance-{bpm:05}.wav"
        row.update(
            ID=str(50_000 + index),
            Title=f"BPM Tolerance {bpm / 100:.2f}",
            FileNameL=filename,
            FileNameS=f"BPM{index:05}.WAV",
            BPM=bpm,
            TrackNo=index,
            SearchStr=f"BPM TOLERANCE {bpm}",
            FolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            OrgFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            rb_LocalFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
        )
        rows.append(row)

    return rows


def unicode_boundary_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    values = (
        ("\U0001f642" * 126, 252),
        ("\U0001f642" * 127, 254),
        (("\U0001f642" * 127) + "a", 255),
        ("\U0001f642" * 128, 256),
        (("\U0001f642" * 128) + "a", 257),
        ("\U0001f642" * 254, 508),
        ("\U0001f642" * 255, 510),
        ("\U0001f642" * 256, 512),
    )
    years = (0, 9, 10, 1999, 2000, 2999, 3000, 4000)
    for row, (value, code_units), year in zip(rows, values, years, strict=True):
        row["Commnt"] = value
        row["StockDate"] = value
        row["ReleaseYear"] = year
        row["Title"] = f"Unicode Boundary {code_units} UTF-16 Units"
        row["SearchStr"] = str(row["Title"]).upper()

    return rows


def filename_boundary_tracks() -> list[dict[str, object]]:
    values = (
        None,
        "",
        "A.wav",
        "a.WAV",
        ".hidden",
        "multi.part.name.flac",
        "trailing.",
        "no-extension",
        "\u00e9.wav",
        "e\u0301.wav",
        "\U0001f642.wav",
        "nul\0suffix.wav",
        "C:\\embedded\\name.wav",
        "dir/name.wav",
        "x" * 254,
        "x" * 255,
        "x" * 256,
        "\U0001f642" * 127,
        ("\U0001f642" * 127) + "a",
        "\U0001f642" * 128,
    )
    base = full_tracks()
    rows = []
    for offset, value in enumerate(values, start=1):
        row = dict(base[(offset - 1) % len(base)])
        row.update(
            ID=str(30_000 + offset),
            Title=f"Filename Title {offset:02}",
            FileNameL=value,
            FileNameS=f"SHORT{len(values) - offset:02}.WAV",
            SearchStr=f"Filename Title {offset:02}",
            FolderPath=f"Z:/tracks/path-source-{offset:02}.mp3",
            OrgFolderPath=f"Z:/tracks/original-source-{offset:02}.aiff",
            rb_LocalFolderPath=f"Z:/tracks/local-source-{offset:02}.flac",
        )
        rows.append(row)
    return rows


def smart_property_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    for index, row in enumerate(rows, start=1):
        row.update(
            ComposerID=str(IDS["artist.alpha"] if index % 2 else IDS["artist.beta"]),
            Subtitle=f"Mix {index:02}",
            DateCreated=f"2025-01-{index:02}",
            ReleaseDate=f"2026-02-{index:02}",
            created_at=f"2030-03-{index:02} 00:00:00.000 +00:00",
        )
    return rows


def smart_date_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    dates = (
        "2024-02-28",
        "2024-02-29",
        "2024-03-01",
        "2025-01-31",
        "2025-02-28",
        "2025-03-01",
        "",
        "not-a-date",
    )
    for row, value in zip(rows, dates, strict=True):
        row.update(
            StockDate=value,
            DateCreated=value,
            ReleaseDate=value,
        )

    return rows


def smart_relative_date_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    for index in (9, 10):
        row = dict(rows[(index - 1) % len(rows)])
        row.update(
            ID=str(10000 + index),
            Title=f"Relative Date {index:02}",
            FileNameL=f"relative-date-{index:02}.wav",
            FileNameS=f"RELDAT{index}.WAV",
            TrackNo=index,
        )
        rows.append(row)

    dates = (
        "2032-03-31",
        "2032-03-30",
        "2032-03-24",
        "2032-02-29",
        "2032-02-28",
        "2031-03-31",
        "2031-03-30",
        "2032-04-01",
        "",
        "not-a-date",
    )
    for row, value in zip(rows, dates, strict=True):
        row.update(
            StockDate=value,
            DateCreated=value,
            ReleaseDate=value,
        )

    return rows


def smart_date_format_tracks() -> list[dict[str, object]]:
    templates = full_tracks()
    rows = []
    for index, (name, value) in enumerate(SMART_DATE_FORMAT_VALUES, start=1):
        row = dict(templates[(index - 1) % len(templates)])
        row.update(
            ID=str(IDS[f"track.date_format.{name}"]),
            Title=f"Date Format {index:02}",
            FileNameL=f"date-format-{index:02}.wav",
            FileNameS=f"DATE{index:02}.WAV",
            TrackNo=index,
            StockDate=value,
            DateCreated=value,
            ReleaseDate=value,
        )
        rows.append(row)

    return rows


def smart_text_tracks() -> list[dict[str, object]]:
    templates = full_tracks()
    rows = []
    for index, (name, value) in enumerate(SMART_TEXT_VALUES, start=1):
        row = dict(templates[(index - 1) % len(templates)])
        row.update(
            ID=str(IDS[f"track.smart_text.{name}"]),
            Title=f"Smart Text {index:02}",
            Commnt=value,
            FileNameL=f"smart-text-{index:02}.wav",
            FileNameS=f"TEXT{index:02}.WAV",
            TrackNo=index,
        )
        rows.append(row)

    return rows


def smart_string_property_tracks() -> list[dict[str, object]]:
    templates = full_tracks()
    rows = []
    for index, (name, value) in enumerate(SMART_STRING_PROPERTY_VALUES, start=1):
        row = dict(templates[(index - 1) % len(templates)])
        lookup_ids = {
            relation: base + index if value is not None else 0
            for relation, base in (
                ("artist", 14_000),
                ("album", 15_000),
                ("genre", 16_000),
                ("label", 17_000),
                ("key", 18_000),
            )
        }
        row.update(
            ID=str(IDS[f"track.smart_string_property.{name}"]),
            Title=value,
            ArtistID=str(lookup_ids["artist"]),
            AlbumID=str(lookup_ids["album"]),
            GenreID=str(lookup_ids["genre"]),
            LabelID=str(lookup_ids["label"]),
            KeyID=str(lookup_ids["key"]),
            ComposerID=str(lookup_ids["artist"]),
            OrgArtistID=str(lookup_ids["artist"]),
            RemixerID=str(lookup_ids["artist"]),
            Commnt=value,
            FileNameL=value,
            FileNameS=f"STRPROP{index:02}.WAV",
            Subtitle=value,
            TrackNo=index,
            SearchStr=value,
        )
        rows.append(row)

    return rows


def smart_mytag_tracks() -> list[dict[str, object]]:
    templates = full_tracks()
    rows = []
    for index, name in enumerate(SMART_MYTAG_TRACK_NAMES, start=1):
        row = dict(templates[(index - 1) % len(templates)])
        row.update(
            ID=str(IDS[f"track.smart_mytag.{name}"]),
            Title=f"Smart My Tag {index:02}",
            FileNameL=f"smart-mytag-{index:02}.wav",
            FileNameS=f"MYTAG{index:02}.WAV",
            TrackNo=index,
        )
        rows.append(row)

    return rows


def add_smart_string_property_lookups(connection) -> None:
    for index, (_name, value) in enumerate(SMART_STRING_PROPERTY_VALUES, start=1):
        if value is None:
            continue

        artist_id = 14_000 + index
        album_id = 15_000 + index
        genre_id = 16_000 + index
        label_id = 17_000 + index
        key_id = 18_000 + index
        insert(connection, "djmdArtist", ID=str(artist_id), Name=value, SearchStr=value)
        insert(
            connection,
            "djmdAlbum",
            ID=str(album_id),
            Name=value,
            AlbumArtistID=str(artist_id),
            SearchStr=value,
        )
        insert(connection, "djmdGenre", ID=str(genre_id), Name=value)
        insert(connection, "djmdLabel", ID=str(label_id), Name=value)
        insert(connection, "djmdKey", ID=str(key_id), ScaleName=value, Seq=100 + index)


def add_smart_mytag_relations(connection) -> None:
    tag_ids = (0, 1, 2_147_483_647, 2_147_483_648, 4_294_967_295)
    for sequence, tag_id in enumerate(tag_ids, start=1):
        insert(
            connection,
            "djmdMyTag",
            ID=str(tag_id),
            Seq=100 + sequence,
            Name=f"Smart Boundary Tag {tag_id}",
            Attribute=0,
            ParentID=str(IDS["mytag.group.genre"]),
        )

    memberships = (
        (1, "tag_one"),
        (2_147_483_647, "tag_int32_max"),
        (2_147_483_648, "tag_high_bit"),
        (4_294_967_295, "tag_uint32_max"),
        (0, "tag_zero"),
        (1, "tag_one_high_bit"),
        (2_147_483_648, "tag_one_high_bit"),
        (2_147_483_648, "tag_high_bit_uint32_max"),
        (4_294_967_295, "tag_high_bit_uint32_max"),
    )
    for relation_id, (tag_id, track_name) in enumerate(memberships, start=19_501):
        insert(
            connection,
            "djmdSongMyTag",
            ID=str(relation_id),
            MyTagID=str(tag_id),
            ContentID=str(IDS[f"track.smart_mytag.{track_name}"]),
            TrackNo=relation_id - 19_500,
        )


def apply_boundary_lookup_strings(connection) -> None:
    updates = {
        "djmdArtist": {
            IDS["artist.alpha"]: "a" * 126,
            IDS["artist.beta"]: "a" * 128,
            IDS["artist.remixer"]: "a" * 127,
            IDS["artist.original"]: "a" * 128,
        },
        "djmdAlbum": {
            IDS["album.one"]: "b" * 126,
            IDS["album.two"]: "b" * 127,
            IDS["album.three"]: "b" * 128,
        },
        "djmdGenre": {
            IDS["genre.house"]: "g" * 126,
            IDS["genre.techno"]: "g" * 128,
        },
        "djmdLabel": {
            IDS["label.one"]: "l" * 127,
            IDS["label.two"]: "l" * 128,
        },
    }
    for table, rows in updates.items():
        for item_id, name in rows.items():
            connection.execute(
                f"UPDATE {table} SET Name = ? WHERE CAST(ID AS INTEGER) = ?",
                (name, item_id),
            )

    connection.execute(
        "UPDATE djmdKey SET ScaleName = CASE CAST(ID AS INTEGER) "
        "WHEN ? THEN ? ELSE ? END",
        (IDS["key.am"], "k" * 126, "k" * 128),
    )
    for color_id in range(1, 9):
        connection.execute(
            "UPDATE djmdColor SET Commnt = ? WHERE CAST(ID AS INTEGER) = ?",
            ("o" * (126 if color_id % 2 else 128), color_id),
        )


def display_string_tracks(value: str) -> list[dict[str, object]]:
    rows = full_tracks()
    for row in rows:
        row["Title"] = value
        row["Commnt"] = value
        row["StockDate"] = value
        row["SearchStr"] = value

    return rows


def apply_display_string_lookups(connection, value: str) -> None:
    for table, column in (
        ("djmdArtist", "Name"),
        ("djmdAlbum", "Name"),
        ("djmdGenre", "Name"),
        ("djmdLabel", "Name"),
        ("djmdKey", "ScaleName"),
        ("djmdColor", "Commnt"),
    ):
        connection.execute(f"UPDATE {table} SET {column} = ?", (value,))


def compatibility_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    formats = (
        (1, "mp3", 44_100, 16),
        (1, "mp3", 48_000, 16),
        (4, "m4a", 44_100, 16),
        (5, "flac", 48_000, 24),
        (5, "flac", 96_000, 24),
        (11, "wav", 44_100, 16),
        (11, "wav", 88_200, 24),
        (12, "aiff", 96_000, 24),
    )
    for index, (row, (file_type, extension, sample_rate, bit_depth)) in enumerate(
        zip(rows, formats, strict=True), start=1
    ):
        filename = f"compatibility-{index:02}.{extension}"
        row.update(
            Title=f"Compatibility type {file_type} rate {sample_rate} depth {bit_depth}",
            FileNameL=filename,
            FileNameS=filename.upper(),
            FileType=file_type,
            SampleRate=sample_rate,
            BitDepth=bit_depth,
            FolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            OrgFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            rb_LocalFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
        )
        row["SearchStr"] = str(row["Title"]).upper()
    return rows


def compatibility_exhaustive_tracks() -> list[dict[str, object]]:
    templates = full_tracks()
    rows = []
    for index, case in enumerate(compatibility_exhaustive_cases(), start=1):
        row = dict(templates[(index - 1) % len(templates)])
        filename = f"compatibility-exhaustive-{index:03}.bin"
        row.update(
            ID=str(case["id"]),
            Title=(
                f"Compatibility {case['axis']} file-type {case['file_type']} "
                f"rate {case['sample_rate']} depth {case['bit_depth']}"
            ),
            FileNameL=filename,
            FileNameS=f"CE{index:06}.BIN",
            FileType=case["file_type"],
            SampleRate=case["sample_rate"],
            BitDepth=case["bit_depth"],
            TrackNo=index,
            FolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            OrgFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
            rb_LocalFolderPath=f"Z:/tracks/link-export-fixture/{filename}",
        )
        row["SearchStr"] = str(row["Title"]).upper()
        rows.append(row)

    return rows


def play_path_tracks(local_dbid: str) -> list[dict[str, object]]:
    rows = full_tracks()
    for offset in range(9, 15):
        row = dict(rows[0])
        row["ID"] = str(10_000 + offset)
        row["FileNameL"] = f"play-path-{offset:02}.wav"
        row["FileNameS"] = f"PLAYPA~{offset}.WAV"
        rows.append(row)

    base = "C:/Users/Research/link-export-conformance/play-paths"
    variants = (
        {
            "ContentLink": None,
            "ServiceID": None,
            "MasterDBID": None,
            "FolderPath": f"{base}/local-control.wav",
            "OrgFolderPath": f"{base}/org-missing-control.wav",
            "FileSize": 8864,
            "HotCueAutoLoad": "on",
        },
        {
            "ContentLink": 0,
            "ServiceID": 0,
            "MasterDBID": "",
            "FolderPath": "",
            "OrgFolderPath": f"{base}/org-existing.bin",
            "FileSize": 0,
            "HotCueAutoLoad": "",
        },
        {
            "ContentLink": 0x80,
            "ServiceID": -1,
            "MasterDBID": local_dbid,
            "FolderPath": f"{base}/local-high-bit.wav",
            "OrgFolderPath": f"{base}/org-existing.bin",
            "FileSize": -1,
            "HotCueAutoLoad": None,
        },
        {
            "ContentLink": 0x81,
            "ServiceID": 0,
            "MasterDBID": "0",
            "FolderPath": f"{base}/local-high-bits.wav",
            "OrgFolderPath": f"{base}/org-existing-dir",
            "FileSize": 2_147_483_647,
            "HotCueAutoLoad": "OFF",
        },
        {
            "ContentLink": 0,
            "ServiceID": 1,
            "MasterDBID": local_dbid,
            "FolderPath": f"{base}/cloud-match-file.wav",
            "OrgFolderPath": f"{base}/org-existing.bin",
            "FileSize": 1,
            "HotCueAutoLoad": "0",
        },
        {
            "ContentLink": 0,
            "ServiceID": 1,
            "MasterDBID": "18446744073709551615",
            "FolderPath": f"{base}/cloud-mismatch-directory.wav",
            "OrgFolderPath": f"{base}/org-existing-dir",
            "FileSize": 2,
            "HotCueAutoLoad": " ",
        },
        {
            "ContentLink": 0,
            "ServiceID": 2,
            "MasterDBID": local_dbid,
            "FolderPath": f"{base}/cloud-match-missing.wav",
            "OrgFolderPath": f"{base}/org-missing.wav",
            "FileSize": 4_294_967_295,
            "HotCueAutoLoad": "ON",
        },
        {
            "ContentLink": 0,
            "ServiceID": 2_147_483_647,
            "MasterDBID": None,
            "FolderPath": f"{base}/cloud-null-master-unicode-Ω.wav",
            "OrgFolderPath": "",
            "FileSize": 4_294_967_296,
            "HotCueAutoLoad": "Ω",
        },
        {
            "ContentLink": 0,
            "ServiceID": 0,
            "MasterDBID": local_dbid,
            "FolderPath": f"{base}/local-empty-hotcue.wav",
            "OrgFolderPath": f"{base}/org-missing-empty-hotcue.wav",
            "FileSize": None,
            "HotCueAutoLoad": "",
        },
        {
            "ContentLink": 0,
            "ServiceID": 0,
            "MasterDBID": local_dbid,
            "FolderPath": None,
            "OrgFolderPath": f"{base}/org-existing.bin",
            "FileSize": 3,
            "HotCueAutoLoad": "on",
        },
        {
            "ContentLink": 0,
            "ServiceID": 1,
            "MasterDBID": local_dbid,
            "FolderPath": f"{base}/cloud-match-existing-directory.wav",
            "OrgFolderPath": f"{base}/org-existing-dir",
            "FileSize": 4,
            "HotCueAutoLoad": "on",
        },
        {
            "ContentLink": 0,
            "ServiceID": 1,
            "MasterDBID": local_dbid,
            "FolderPath": f"{base}/cloud-match-zero-byte-file.wav",
            "OrgFolderPath": f"{base}/org-zero-byte.bin",
            "FileSize": 5,
            "HotCueAutoLoad": "on",
        },
        {
            "ContentLink": 0,
            "ServiceID": 0,
            "MasterDBID": local_dbid,
            "FolderPath": f"{base}/content-link-pair.wav",
            "OrgFolderPath": f"{base}/org-missing-link-pair.wav",
            "FileSize": 6,
            "HotCueAutoLoad": "on",
        },
        {
            "ContentLink": 0x80,
            "ServiceID": 0,
            "MasterDBID": local_dbid,
            "FolderPath": f"{base}/content-link-pair.wav",
            "OrgFolderPath": f"{base}/org-missing-link-pair.wav",
            "FileSize": 6,
            "HotCueAutoLoad": "on",
        },
    )
    for index, (row, variant) in enumerate(zip(rows, variants, strict=True), start=1):
        row.update(variant)
        row["rb_LocalFolderPath"] = row["FolderPath"]
        row["Title"] = f"Play Path Variant {index}"
        row["SearchStr"] = str(row["Title"]).upper()

    return rows


def cloud_sync_zero_tracks(local_dbid: str) -> list[dict[str, object]]:
    rows = full_tracks()
    for offset in range(9, 11):
        row = dict(rows[0])
        row["ID"] = str(10_000 + offset)
        row["FileNameL"] = f"cloud-sync-zero-{offset:02}.wav"
        row["FileNameS"] = f"CLDSYN~{offset}.WAV"
        rows.append(row)

    root = "C:/Users/Research/link-export-conformance/cloud-sync-zero"
    variants = (
        (None, None, f"{root}/local-null.wav", f"{root}/org-missing.wav"),
        (-1, local_dbid, f"{root}/local-negative.wav", f"{root}/org-missing.wav"),
        (0, "0", f"{root}/local-zero.wav", f"{root}/org-existing-dir"),
        (1, "18446744073709551615", "/service-one-file.wav", f"{root}/org-existing.bin"),
        (1, "18446744073709551615", "/service-one-dir.wav", f"{root}/org-existing-dir"),
        (2, "18446744073709551615", "/moved-existing.bin", f"{root}/org-missing.wav"),
        (2, local_dbid, "/moved-missing.bin", f"{root}/org-missing.wav"),
        (1, local_dbid, "/unsupported-one.bin", f"{root}/org-missing.wav"),
        (5, local_dbid, "/moved-service-five.bin", f"{root}/org-missing.wav"),
        (6, local_dbid, "/unsupported-six.bin", f"{root}/org-missing.wav"),
    )
    for index, (row, variant) in enumerate(zip(rows, variants, strict=True), start=1):
        service_id, master_dbid, folder_path, original_path = variant
        row.update(
            ContentLink=0,
            ServiceID=service_id,
            MasterDBID=master_dbid,
            FolderPath=folder_path,
            OrgFolderPath=original_path,
            rb_LocalFolderPath=folder_path,
            FileSize=index,
            HotCueAutoLoad="on",
            Title=f"Cloud Sync Zero Variant {index}",
            SearchStr=f"CLOUD SYNC ZERO VARIANT {index}",
        )

    return rows


def invalid_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    rows[0].update(
        Title=None,
        FileNameL=None,
        SearchStr=None,
        Commnt=None,
    )
    rows[1].update(
        ArtistID="999999",
        AlbumID="999999",
        GenreID="999999",
        LabelID="999999",
        OrgArtistID="999999",
        RemixerID="999999",
        KeyID="999999",
    )
    rows[2].update(FileType=0, SampleRate=0, BitDepth=0, BitRate=0)
    rows[3].update(FileType=255, SampleRate=1, BitDepth=255, BitRate=2_147_483_647)
    rows[4].update(BPM=-1, Length=-1, ReleaseYear=-1, TrackNo=-1, DJPlayCount=-1)
    rows[5].update(ColorID="999999", Rating=99)
    rows[6].update(StockDate="not-a-date")
    rows[7].update(
        Title="",
        FileNameL="",
        FileNameS="",
        FolderPath="",
        OrgFolderPath="",
        rb_LocalFolderPath="",
        SearchStr="",
    )
    return rows


def scalar_boundary_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    rows[0]["ColorID"] = "0"
    rows[1]["ColorID"] = "999999"
    rows[2]["Rating"] = 99
    rows[3]["BitRate"] = 2_147_483_647

    return rows


def delivery_boundary_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    unicode_126 = "\U0001f642" * 63
    unicode_127 = unicode_126 + "a"
    unicode_128 = "\U0001f642" * 64
    values = (
        (None, None, None),
        ("", "", ""),
        ("d" * 126, "OFF", IDS["artist.composer_ascii_126"]),
        ("d" * 127, "ON", IDS["artist.composer_ascii_127"]),
        ("d" * 128, "on", IDS["artist.composer_ascii_128"]),
        (unicode_126, "Off", IDS["artist.composer_unicode_126"]),
        (unicode_127, "ON", "999999"),
        (unicode_128, "ON", IDS["artist.composer_unicode_128"]),
    )
    for row, (value, delivery_control, composer_id) in zip(rows, values, strict=True):
        row.update(
            ComposerID=None if composer_id is None else str(composer_id),
            DeliveryControl=delivery_control,
            DeliveryComment=value,
            Lyricist=value,
            ISRC=value,
        )

    return rows


def delivery_wide_string_tracks() -> list[dict[str, object]]:
    rows = full_tracks()
    values = (
        "w" * 254,
        "w" * 255,
        "w" * 256,
        "\U0001f642" * 126,
        "\U0001f642" * 127,
        ("\U0001f642" * 127) + "a",
        "\U0001f642" * 128,
        ("\U0001f642" * 128) + "a",
    )
    for row, value in zip(rows, values, strict=True):
        row.update(
            DeliveryControl="ON",
            DeliveryComment=value,
            Lyricist=value,
            ISRC=value,
        )

    return rows


def add_delivery_composer_lookups(connection) -> None:
    values = (
        (IDS["artist.composer_ascii_126"], "c" * 126),
        (IDS["artist.composer_ascii_127"], "c" * 127),
        (IDS["artist.composer_ascii_128"], "c" * 128),
        (IDS["artist.composer_unicode_126"], "\U0001f642" * 63),
        (IDS["artist.composer_unicode_127"], ("\U0001f642" * 63) + "a"),
        (IDS["artist.composer_unicode_128"], "\U0001f642" * 64),
    )
    for artist_id, name in values:
        insert(connection, "djmdArtist", ID=str(artist_id), Name=name)


def add_track(connection, row: dict[str, object], deleted: int = 0) -> None:
    values = dict(row)
    values["rb_local_deleted"] = deleted
    insert(connection, "djmdContent", **values)


def add_rekordbox_baseline(connection) -> None:
    insert(
        connection,
        "djmdPlaylist",
        ID=str(IDS["playlist.cue_analysis"]),
        Seq=1,
        Name="CUE Analysis Playlist",
        Attribute=0,
        ParentID="root",
        UUID="0b7b7b65-34a3-49fd-92a2-9f6e6893e696",
    )


def add_default_mytags(connection) -> None:
    for key, sequence, name, attribute, parent in DEFAULT_MYTAGS:
        parent_id = IDS[parent] if parent != "root" else parent
        insert(
            connection,
            "djmdMyTag",
            ID=str(IDS[key]),
            Seq=sequence,
            Name=name,
            Attribute=attribute,
            ParentID=str(parent_id),
        )


def add_relations(connection) -> None:
    insert(
        connection,
        "djmdPlaylist",
        ID=str(IDS["playlist.folder"]),
        Seq=2,
        Name="Fixture Folder",
        Attribute=1,
        ParentID="root",
    )
    insert(
        connection,
        "djmdPlaylist",
        ID=str(IDS["playlist.primary"]),
        Seq=1,
        Name="Fixture Playlist",
        Attribute=0,
        ParentID=str(IDS["playlist.folder"]),
    )
    insert(
        connection,
        "djmdPlaylist",
        ID=str(IDS["playlist.empty"]),
        Seq=3,
        Name="Empty Fixture Playlist",
        Attribute=0,
        ParentID="root",
    )
    for position, track in enumerate((10003, 10001, 10002), start=1):
        insert(
            connection,
            "djmdSongPlaylist",
            ID=str(6100 + position),
            PlaylistID=str(IDS["playlist.primary"]),
            ContentID=str(track),
            TrackNo=position,
        )

    for relation_id, left, right, rate in (
        (9001, 10001, 10002, 1),
        (9002, 10001, 10003, 99),
    ):
        insert(
            connection,
            "djmdRecommendLike",
            ID=str(relation_id),
            ContentID1=str(left),
            ContentID2=str(right),
            LikeRate=rate,
        )
    insert(
        connection,
        "djmdRecommendLike",
        ID="9999",
        ContentID1="10001",
        ContentID2="10008",
        LikeRate=100,
        rb_local_deleted=1,
    )

    insert(
        connection,
        "djmdHistory",
        ID=str(IDS["history.one"]),
        Seq=1,
        Name="FIXTURE HISTORY",
        Attribute=0,
        ParentID="root",
        DateCreated="2026-01-01",
    )
    insert(
        connection,
        "djmdSongHistory",
        ID="7101",
        HistoryID=str(IDS["history.one"]),
        ContentID=str(IDS["track.first"]),
        TrackNo=1,
    )

    for item_id, sequence, name, attribute, parent_id in (
        (IDS["mytag.group.genre"], 1, "Fixture Genre Tags", 1, "root"),
        (IDS["mytag.warmup"], 1, "Fixture Warmup", 0, IDS["mytag.group.genre"]),
        (IDS["mytag.empty"], 2, "Fixture Empty Tag", 0, IDS["mytag.group.genre"]),
        (IDS["mytag.group.components"], 2, "Fixture Components", 1, "root"),
        (IDS["mytag.vocal"], 1, "Fixture Vocal", 0, IDS["mytag.group.components"]),
    ):
        insert(
            connection,
            "djmdMyTag",
            ID=str(item_id),
            Seq=sequence,
            Name=name,
            Attribute=attribute,
            ParentID=str(parent_id),
        )

    for relation_id, tag_id, content_id in (
        (8601, IDS["mytag.warmup"], IDS["track.first"]),
        (8602, IDS["mytag.vocal"], IDS["track.first"]),
        (8603, IDS["mytag.warmup"], IDS["track.second"]),
        (8604, IDS["mytag.vocal"], IDS["track.third"]),
    ):
        insert(
            connection,
            "djmdSongMyTag",
            ID=str(relation_id),
            MyTagID=str(tag_id),
            ContentID=str(content_id),
        )

    for relation_id, content_id, track_number in (
        (8701, IDS["track.second"], 1),
        (8702, IDS["track.first"], 2),
    ):
        insert(
            connection,
            "djmdSongTagList",
            ID=str(relation_id),
            ContentID=str(content_id),
            TrackNo=track_number,
        )

    insert(
        connection,
        "djmdHotCueBanklist",
        ID=str(IDS["hotcue.folder"]),
        Seq=1,
        Name="Fixture Hot Cue Folder",
        Attribute=1,
        ParentID="root",
    )
    insert(
        connection,
        "djmdHotCueBanklist",
        ID=str(IDS["hotcue.bank"]),
        Seq=1,
        Name="Fixture Hot Cue Bank",
        Attribute=0,
        ParentID=str(IDS["hotcue.folder"]),
    )
    insert(
        connection,
        "djmdSongHotCueBanklist",
        ID="8101",
        HotCueBanklistID=str(IDS["hotcue.bank"]),
        ContentID=str(IDS["track.first"]),
        TrackNo=1,
        CueID="1",
        InMsec=1000,
    )


def add_hot_cue_bank_matrix(connection) -> None:
    for table in (
        "hotCueBanklistCue",
        "djmdSongHotCueBanklist",
        "djmdHotCueBanklist",
        "djmdCue",
    ):
        connection.execute(f"DELETE FROM {table}")

    nodes = (
        ("hotcue.folder.beta", 1, "Beta Folder", 1, "root", 0),
        ("hotcue.folder.alpha", 2, "Alpha Folder", 1, "root", 0),
        ("hotcue.bank.root", 3, "Root Bank", 0, "root", 0),
        ("hotcue.bank.alpha", 1, "Alpha Bank", 0, "hotcue.folder.alpha", 0),
        ("hotcue.folder.deep", 2, "Deep Folder", 1, "hotcue.folder.alpha", 0),
        ("hotcue.bank.empty", 3, "Empty Bank", 0, "hotcue.folder.alpha", 0),
        ("hotcue.bank.deep", 1, "Deep Bank", 0, "hotcue.folder.deep", 0),
        ("hotcue.bank.beta_deleted", 1, "Deleted Bank", 0, "hotcue.folder.beta", 1),
        ("hotcue.bank.beta", 2, "Beta Bank", 0, "hotcue.folder.beta", 0),
    )
    for name, sequence, label, attribute, parent_name, deleted in nodes:
        parent_id = (
            parent_name
            if parent_name == "root"
            else str(HOT_CUE_BANK_IDS[parent_name])
        )
        insert(
            connection,
            "djmdHotCueBanklist",
            ID=str(HOT_CUE_BANK_IDS[name]),
            Seq=sequence,
            Name=label,
            Attribute=attribute,
            ParentID=parent_id,
            rb_local_deleted=deleted,
        )

    alpha_order = (
        IDS["track.eighth"],
        IDS["track.first"],
        IDS["track.sixth"],
        IDS["track.third"],
        IDS["track.second"],
        IDS["track.seventh"],
        IDS["track.fourth"],
        IDS["track.fifth"],
        IDS["track.first"],
        IDS["track.deleted"],
        999_999,
    )
    memberships = [
        (91_001 + index, "hotcue.bank.alpha", content_id, index, 0)
        for index, content_id in enumerate(alpha_order, 1)
    ]
    memberships.extend(
        (
            (91_100, "hotcue.bank.alpha", IDS["track.second"], 12, 1),
            (91_201, "hotcue.bank.root", IDS["track.second"], 1, 0),
            (91_202, "hotcue.bank.root", IDS["track.first"], 2, 0),
            (91_301, "hotcue.bank.deep", IDS["track.third"], 0, 0),
            (91_302, "hotcue.bank.deep", IDS["track.fourth"], -1, 0),
            (91_401, "hotcue.bank.beta", IDS["track.seventh"], 1, 0),
        )
    )
    for relation_id, bank_name, content_id, track_number, deleted in memberships:
        cue_id = relation_id + 100_000
        insert(
            connection,
            "djmdSongHotCueBanklist",
            ID=str(relation_id),
            HotCueBanklistID=str(HOT_CUE_BANK_IDS[bank_name]),
            ContentID=str(content_id),
            TrackNo=track_number,
            CueID=str(cue_id),
            InMsec=relation_id,
            rb_local_deleted=deleted,
        )
        insert(
            connection,
            "djmdCue",
            ID=str(cue_id),
            ContentID=str(content_id),
            InMsec=relation_id,
            InFrame=relation_id % 150,
            InMpegFrame=relation_id + 10,
            InMpegAbs=relation_id + 20,
            OutMsec=-1,
            OutFrame=-1,
            OutMpegFrame=-1,
            OutMpegAbs=-1,
            Kind=track_number if track_number in (1, 2, 3) else 1,
            Color=relation_id % 8,
            ColorTableIndex=(relation_id % 8) + 1,
            ActiveLoop=0,
            Comment=f"Fixture bank cue {relation_id}",
            rb_local_deleted=deleted,
        )


def add_hot_cue_bank_pagination_matrix(connection) -> None:
    bank_id = HOT_CUE_BANK_IDS["hotcue.bank.large"]
    insert(
        connection,
        "djmdHotCueBanklist",
        ID=str(bank_id),
        Seq=4,
        Name="Large Pagination Bank",
        Attribute=0,
        ParentID=str(HOT_CUE_BANK_IDS["hotcue.folder.alpha"]),
    )

    for index in range(1, 71):
        relation_id = 95_000 + index
        content_id = 40_000 + index
        cue_id = 195_000 + index
        insert(
            connection,
            "djmdSongHotCueBanklist",
            ID=str(relation_id),
            HotCueBanklistID=str(bank_id),
            ContentID=str(content_id),
            TrackNo=index,
            CueID=str(cue_id),
            InMsec=relation_id,
        )
        insert(
            connection,
            "djmdCue",
            ID=str(cue_id),
            ContentID=str(content_id),
            InMsec=relation_id,
            InFrame=relation_id % 150,
            InMpegFrame=relation_id + 10,
            InMpegAbs=relation_id + 20,
            OutMsec=-1,
            OutFrame=-1,
            OutMpegFrame=-1,
            OutMpegAbs=-1,
            Kind=((index - 1) % 3) + 1,
            Color=index % 8,
            ColorTableIndex=(index % 8) + 1,
            ActiveLoop=0,
            Comment=f"Large bank cue {index:03}",
        )


def add_deleted_hot_cue_bank_member(connection) -> None:
    relation_id = 91_450
    cue_id = relation_id + 100_000
    values = {
        "ContentID": str(IDS["track.fifth"]),
        "InMsec": 91_450,
        "InFrame": 50,
        "InMpegFrame": 91_460,
        "InMpegAbs": 91_470,
        "OutMsec": -1,
        "OutFrame": -1,
        "OutMpegFrame": -1,
        "OutMpegAbs": -1,
    }
    insert(
        connection,
        "djmdSongHotCueBanklist",
        ID=str(relation_id),
        HotCueBanklistID=str(HOT_CUE_BANK_IDS["hotcue.bank.beta_deleted"]),
        TrackNo=1,
        CueID=str(cue_id),
        **values,
    )
    insert(
        connection,
        "djmdCue",
        ID=str(cue_id),
        Kind=1,
        Color=5,
        ColorTableIndex=6,
        ActiveLoop=0,
        Comment="Deleted bank live member",
        **values,
    )


def add_hot_cue_bank_cue_field_matrix(connection) -> None:
    for name, sequence, label in (
        ("hotcue.bank.cue_fields", 4, "Cue Field Bank"),
        ("hotcue.bank.cue_ignored", 5, "Ignored Field Bank"),
    ):
        insert(
            connection,
            "djmdHotCueBanklist",
            ID=str(CUE_FIELD_BANK_IDS[name]),
            Seq=sequence,
            Name=label,
            Attribute=0,
            ParentID="root",
        )

    wire_rows = (
        (1, IDS["track.first"], 1_001, -1, 111_113, 111_114, 111_115, 111_116),
        (
            2,
            IDS["track.second"],
            2_002,
            4_004,
            222_213,
            222_214,
            222_215,
            222_216,
        ),
        (3, IDS["track.third"], 3_003, 1, 333_313, 333_314, 333_315, 333_316),
    )
    for bank_offset, bank_name in enumerate(CUE_FIELD_BANK_IDS):
        for (
            slot,
            content_id,
            in_msec,
            out_msec,
            in_mpeg_frame,
            out_mpeg_frame,
            in_mpeg_abs,
            out_mpeg_abs,
        ) in wire_rows:
            relation_id = 92_000 + bank_offset * 100 + slot
            cue_id = relation_id + 100_000
            ignored_base = (bank_offset + 1) * 1_000_000 + slot * 10_000
            insert(
                connection,
                "djmdSongHotCueBanklist",
                ID=str(relation_id),
                HotCueBanklistID=str(CUE_FIELD_BANK_IDS[bank_name]),
                ContentID=str(content_id),
                TrackNo=slot,
                CueID=str(cue_id),
                InMsec=in_msec,
                InFrame=ignored_base + 1,
                InMpegFrame=in_mpeg_frame,
                InMpegAbs=in_mpeg_abs,
                OutMsec=out_msec,
                OutFrame=ignored_base + 2,
                OutMpegFrame=out_mpeg_frame,
                OutMpegAbs=out_mpeg_abs,
                Color=(slot + bank_offset * 3) % 8,
                ColorTableIndex=slot + bank_offset * 30,
                ActiveLoop=bank_offset,
                Comment=f"Ignored membership fields {bank_offset}:{slot}",
                BeatLoopSize=ignored_base + 3,
                CueMicrosec=ignored_base + 4,
                InPointSeekInfo=f"ignored-member-in-{bank_offset}-{slot}",
                OutPointSeekInfo=f"ignored-member-out-{bank_offset}-{slot}",
            )
            cue_base = (bank_offset + 5) * 10_000_000 + slot * 100_000
            insert(
                connection,
                "djmdCue",
                ID=str(cue_id),
                ContentID=str(IDS["track.eighth"]),
                InMsec=cue_base + 1,
                InFrame=cue_base + 2,
                InMpegFrame=cue_base + 3,
                InMpegAbs=cue_base + 4,
                OutMsec=cue_base + 5,
                OutFrame=cue_base + 6,
                OutMpegFrame=cue_base + 7,
                OutMpegAbs=cue_base + 8,
                Kind=slot + bank_offset * 20,
                Color=(slot + bank_offset * 3) % 8,
                ColorTableIndex=slot + bank_offset * 30,
                ActiveLoop=bank_offset,
                Comment=f"Ignored cue fields {bank_offset}:{slot}",
                BeatLoopSize=ignored_base + 4,
                CueMicrosec=ignored_base + 5,
                InPointSeekInfo=f"ignored-in-{bank_offset}-{slot}",
                OutPointSeekInfo=f"ignored-out-{bank_offset}-{slot}",
            )


def add_hot_cue_bank_extended_field_matrix(connection) -> None:
    rows = (
        ("hotcue.bank.extended_baseline", "Extended Baseline", {}),
        (
            "hotcue.bank.extended_timing",
            "Extended Timing",
            {
                "OutMsec": -1,
                "InMpegFrame": 0x01020304,
                "OutMpegFrame": 0x21222324,
                "InMpegAbs": 0x11121314,
                "OutMpegAbs": 0x31323334,
            },
        ),
        (
            "hotcue.bank.extended_color",
            "Extended Color",
            {"Color": 7, "ColorTableIndex": 255},
        ),
        (
            "hotcue.bank.extended_comment_ascii",
            "Extended ASCII Comment",
            {"Comment": "A"},
        ),
        (
            "hotcue.bank.extended_comment_unicode",
            "Extended Unicode Comment",
            {"Comment": "\u00e9\U0001f642"},
        ),
        (
            "hotcue.bank.extended_beat_loop",
            "Extended Beat Loop",
            {"BeatLoopSize": 0x12345678},
        ),
        (
            "hotcue.bank.extended_microseconds",
            "Extended Microseconds",
            {"CueMicrosec": 0x0A0B0C0D},
        ),
        (
            "hotcue.bank.extended_in_seek",
            "Extended In Seek",
            {"InPointSeekInfo": "1,2,3"},
        ),
        (
            "hotcue.bank.extended_out_seek",
            "Extended Out Seek",
            {"OutPointSeekInfo": "4,5,6"},
        ),
    )
    for index, (bank_name, label, overrides) in enumerate(rows, 1):
        bank_id = EXTENDED_CUE_BANK_IDS[bank_name]
        insert(
            connection,
            "djmdHotCueBanklist",
            ID=str(bank_id),
            Seq=4 + index,
            Name=label,
            Attribute=0,
            ParentID="root",
        )

        relation_id = 93_000 + index
        cue_id = relation_id + 100_000
        values = {
            "ContentID": str(IDS["track.first"]),
            "InMsec": 100_000 + index,
            **overrides,
        }
        insert(
            connection,
            "djmdSongHotCueBanklist",
            ID=str(relation_id),
            HotCueBanklistID=str(bank_id),
            TrackNo=1,
            CueID=str(cue_id),
            **values,
        )
        insert(
            connection,
            "djmdCue",
            ID=str(cue_id),
            Kind=1,
            **values,
        )


def add_adjacent_payload_cue_matrix(connection) -> None:
    connection.execute("DELETE FROM djmdCue")
    next_id = 300_000

    def add_cue(
        name: str,
        *,
        deleted: int = 0,
        **overrides,
    ) -> None:
        nonlocal next_id

        next_id += 1
        values = {
            "ContentID": str(CUE_PAYLOAD_TRACK_IDS[name]),
            "InMsec": next_id,
            "InFrame": next_id % 150,
            "InMpegFrame": next_id + 10,
            "InMpegAbs": next_id + 20,
            "OutMsec": -1,
            "OutFrame": -1,
            "OutMpegFrame": -1,
            "OutMpegAbs": -1,
            "Kind": 1,
            "Color": 0,
            "ColorTableIndex": 0,
            "ActiveLoop": 0,
            "Comment": "",
            "BeatLoopSize": 0,
            "CueMicrosec": 0,
            "InPointSeekInfo": None,
            "OutPointSeekInfo": None,
            "rb_local_deleted": deleted,
            **overrides,
        }
        insert(connection, "djmdCue", ID=str(next_id), **values)

    add_cue("cue_payload.one")
    for kind in (1, 2, 3):
        add_cue("cue_payload.three", Kind=kind)
    for _index in range(255):
        add_cue("cue_payload.count_255")
    for _index in range(256):
        add_cue("cue_payload.count_256")

    add_cue(
        "cue_payload.timing",
        InMsec=0x7FFFFFFF,
        InFrame=0x01020304,
        InMpegFrame=0x11121314,
        InMpegAbs=0x21222324,
        OutMsec=-1,
        OutFrame=-2,
        OutMpegFrame=-3,
        OutMpegAbs=-4,
        ActiveLoop=1,
    )
    add_cue("cue_payload.color", Color=7, ColorTableIndex=255)
    add_cue("cue_payload.comment_empty", Comment="")
    add_cue("cue_payload.comment_ascii", Comment="Adjacent cue ASCII")
    add_cue("cue_payload.comment_unicode", Comment="é🙂")
    add_cue("cue_payload.comment_nul", Comment="before\0after")
    add_cue("cue_payload.beat_loop", BeatLoopSize=0x12345678)
    add_cue("cue_payload.microseconds", CueMicrosec=0x0A0B0C0D)
    add_cue(
        "cue_payload.null_options",
        Color=None,
        ColorTableIndex=None,
        ActiveLoop=None,
        Comment=None,
        BeatLoopSize=None,
        CueMicrosec=None,
    )
    add_cue("cue_payload.seek_in", InPointSeekInfo="1,2,3")
    add_cue("cue_payload.seek_out_only", OutPointSeekInfo="4,5,6")
    add_cue("cue_payload.seek_malformed", InPointSeekInfo="malformed")
    add_cue("cue_payload.deleted_only", deleted=1)
    add_cue("cue_payload.mixed_deleted")
    add_cue("cue_payload.mixed_deleted", deleted=1)


def add_hot_cue_bank_mutation_fixture(
    connection,
    *,
    track_no: int = 1,
    relation_ids: tuple[int, int] = (94_001, 94_002),
    content_id: int = IDS["track.first"],
    add_bank: bool = True,
) -> None:
    bank_id = MUTATION_CUE_BANK_IDS["hotcue.bank.mutation"]
    values = {
        "ContentID": str(content_id),
        "InMsec": 100_001,
        "OutMsec": 0,
        "InMpegFrame": 0,
        "OutMpegFrame": 0,
        "InMpegAbs": 0,
        "OutMpegAbs": 0,
        "Color": 0,
        "ColorTableIndex": 0,
        "BeatLoopSize": 0,
        "CueMicrosec": 0,
        "Comment": "",
        "InPointSeekInfo": "",
        "OutPointSeekInfo": "",
    }
    if add_bank:
        insert(
            connection,
            "djmdHotCueBanklist",
            ID=str(bank_id),
            Seq=14,
            Name="Mutation Bank",
            Attribute=0,
            ParentID="root",
        )
    # HCBnkSong_GetCueID rejects a one-element SQL result before reading row 0.
    # Two valid same-slot rows exercise that literal resolver behavior. AppSync
    # then supplies the selected row's CueID to SongHotCueBanklist.updateById,
    # so each writable membership uses its own row ID as CueID.
    for relation_id in relation_ids:
        insert(
            connection,
            "djmdSongHotCueBanklist",
            ID=str(relation_id),
            HotCueBanklistID=str(bank_id),
            TrackNo=track_no,
            CueID=str(relation_id),
            **values,
        )
        insert(
            connection,
            "djmdCue",
            ID=str(relation_id),
            Kind=1,
            **values,
        )


def add_hot_cue_bank_legacy_ordinal_fixture(connection) -> None:
    slots = (
        (4, (94_201, 94_202), IDS["track.first"]),
        (5, (94_203, 94_204), IDS["track.second"]),
        (6, (94_205, 94_206), IDS["track.third"]),
    )
    for index, (track_no, relation_ids, content_id) in enumerate(slots):
        add_hot_cue_bank_mutation_fixture(
            connection,
            track_no=track_no,
            relation_ids=relation_ids,
            content_id=content_id,
            add_bank=index == 0,
        )


def add_hot_cue_bank_legacy_ordinal_boundary_fixture(connection) -> None:
    ordinals = (0, 1, 2, 3, 7, 8, 255, 256, 32_767, 32_768, 65_535)
    content_ids = tuple(IDS[f"track.{name}"] for name in (
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
    ))
    for index, ordinal in enumerate(ordinals):
        first_relation_id = 94_301 + index * 2
        add_hot_cue_bank_mutation_fixture(
            connection,
            track_no=ordinal,
            relation_ids=(first_relation_id, first_relation_id + 1),
            content_id=content_ids[index % len(content_ids)],
            add_bank=index == 0,
        )


def add_smart_playlist_relations(connection) -> None:
    house_rule = (
        '<NODE Id="1" LogicalOperator="1" AutomaticUpdate="1">'
        '<CONDITION PropertyName="genre" Operator="1" ValueUnit="" '
        'ValueLeft="Fixture House" ValueRight=""/></NODE>'
    )
    playlists = (
        (
            "playlist.smart_rule_only",
            4,
            "Smart Rule Only",
            4,
            house_rule,
        ),
        (
            "playlist.smart_contradiction",
            5,
            "Smart Contradictory Membership",
            4,
            house_rule,
        ),
        (
            "playlist.smart_malformed",
            6,
            "Smart Malformed Rule",
            4,
            "<not-valid-smart-list",
        ),
        (
            "playlist.ordinary_with_rule",
            7,
            "Ordinary With Smart Rule",
            0,
            house_rule,
        ),
        (
            "playlist.smart_without_rule",
            8,
            "Smart Without Rule",
            4,
            None,
        ),
    )
    for key, sequence, name, attribute, smart_list in playlists:
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[key]),
            Seq=sequence,
            Name=name,
            Attribute=attribute,
            ParentID="root",
            SmartList=smart_list,
        )

    memberships = (
        (6201, "playlist.smart_contradiction", "track.second", 1),
        (6202, "playlist.smart_contradiction", "track.fourth", 2),
        (6203, "playlist.smart_malformed", "track.third", 1),
        (6204, "playlist.smart_malformed", "track.fifth", 2),
        (6205, "playlist.smart_without_rule", "track.sixth", 1),
        (6206, "playlist.smart_without_rule", "track.eighth", 2),
    )
    for relation_id, playlist, track, position in memberships:
        insert(
            connection,
            "djmdSongPlaylist",
            ID=str(relation_id),
            PlaylistID=str(IDS[playlist]),
            ContentID=str(IDS[track]),
            TrackNo=position,
        )


def add_link_visibility_relations(connection) -> None:
    connection.execute(
        "DELETE FROM djmdSongPlaylist WHERE PlaylistID = ?",
        (str(IDS["playlist.primary"]),),
    )
    connection.execute(
        "DELETE FROM djmdSongHistory WHERE HistoryID = ?",
        (str(IDS["history.one"]),),
    )
    for position in range(1, 15):
        content_id = 10_000 + position
        insert(
            connection,
            "djmdSongPlaylist",
            ID=str(8800 + position),
            PlaylistID=str(IDS["playlist.primary"]),
            ContentID=str(content_id),
            TrackNo=position,
        )
        insert(
            connection,
            "djmdSongHistory",
            ID=str(8900 + position),
            HistoryID=str(IDS["history.one"]),
            ContentID=str(content_id),
            TrackNo=position,
        )

    smart_list = (
        '<NODE Id="6015" LogicalOperator="1" AutomaticUpdate="1">'
        '<CONDITION PropertyName="name" Operator="8" ValueUnit="" '
        'ValueLeft="Visibility Match" ValueRight=""/></NODE>'
    )
    insert(
        connection,
        "djmdPlaylist",
        ID=str(IDS["playlist.visibility_smart"]),
        Seq=4,
        Name="Visibility Smart Playlist",
        Attribute=4,
        ParentID="root",
        SmartList=smart_list,
    )


def add_streaming_provider_path_relations(connection) -> None:
    connection.execute(
        "DELETE FROM djmdSongPlaylist WHERE PlaylistID = ?",
        (str(IDS["playlist.primary"]),),
    )
    connection.execute(
        "DELETE FROM djmdSongHistory WHERE HistoryID = ?",
        (str(IDS["history.one"]),),
    )
    for position in range(1, 11):
        content_id = 11_000 + position
        insert(
            connection,
            "djmdSongPlaylist",
            ID=str(98_800 + position),
            PlaylistID=str(IDS["playlist.primary"]),
            ContentID=str(content_id),
            TrackNo=position,
        )
        insert(
            connection,
            "djmdSongHistory",
            ID=str(98_900 + position),
            HistoryID=str(IDS["history.one"]),
            ContentID=str(content_id),
            TrackNo=position,
        )

    smart_list = (
        '<NODE Id="6015" LogicalOperator="1" AutomaticUpdate="1">'
        '<CONDITION PropertyName="name" Operator="8" ValueUnit="" '
        'ValueLeft="Provider Path" ValueRight=""/></NODE>'
    )
    insert(
        connection,
        "djmdPlaylist",
        ID=str(IDS["playlist.visibility_smart"]),
        Seq=4,
        Name="Provider Path Smart Playlist",
        Attribute=4,
        ParentID="root",
        SmartList=smart_list,
    )

def smart_condition(
    property_name: str,
    operator: int,
    left: str,
    right: str = "",
    unit: str = "",
) -> str:
    attributes = {
        "property": escape(property_name, {'"': "&quot;", "'": "&apos;"}),
        "unit": escape(unit, {'"': "&quot;", "'": "&apos;"}),
        "left": escape(left, {'"': "&quot;", "'": "&apos;"}),
        "right": escape(right, {'"': "&quot;", "'": "&apos;"}),
    }
    return (
        f'<CONDITION PropertyName="{attributes["property"]}" Operator="{operator}" '
        f'ValueUnit="{attributes["unit"]}" ValueLeft="{attributes["left"]}" '
        f'ValueRight="{attributes["right"]}"/>'
    )


def smart_node(
    body: str,
    *,
    logical_operator: int | None = 1,
    automatic_update: int | None = 1,
    playlist_id: int | None = 1,
) -> str:
    attributes = []
    if playlist_id is not None:
        attributes.append(f'Id="{playlist_id}"')
    if logical_operator is not None:
        attributes.append(f'LogicalOperator="{logical_operator}"')
    if automatic_update is not None:
        attributes.append(f'AutomaticUpdate="{automatic_update}"')
    return f"<NODE {' '.join(attributes)}>{body}</NODE>"


def smart_rule_matrix() -> list[tuple[str, str]]:
    genre_values = {
        1: ("Fixture House", "", ""),
        2: ("Fixture House", "", ""),
        3: ("Fixture House", "", ""),
        4: ("Fixture Techno", "", ""),
        5: ("Fixture House", "Fixture Techno", ""),
        6: ("1", "", "day"),
        7: ("1", "", "day"),
        8: ("House", "", ""),
        9: ("House", "", ""),
        10: ("Fixture", "", ""),
        11: ("Techno", "", ""),
    }
    bpm_values = {
        1: ("121.5", "", ""),
        2: ("121.5", "", ""),
        3: ("121.5", "", ""),
        4: ("121.5", "", ""),
        5: ("120.5", "122.5", ""),
        6: ("1", "", "day"),
        7: ("1", "", "day"),
        8: ("121", "", ""),
        9: ("121", "", ""),
        10: ("121", "", ""),
        11: ("121", "", ""),
    }

    rules = []
    for operator, (left, right, unit) in genre_values.items():
        condition = smart_condition("genre", operator, left, right, unit)
        rules.append((f"genre_operator_{operator:02}", smart_node(condition)))
    for operator, (left, right, unit) in bpm_values.items():
        condition = smart_condition("bpm", operator, left, right, unit)
        rules.append((f"bpm_operator_{operator:02}", smart_node(condition)))

    house = smart_condition("genre", 1, "Fixture House")
    techno = smart_condition("genre", 1, "Fixture Techno")
    bpm_high = smart_condition("bpm", 3, "121.5")
    rating_high = smart_condition("rating", 3, "2")
    nested_any = smart_node(house + techno, logical_operator=2, playlist_id=None)
    nested_all = smart_node(house + rating_high, playlist_id=None)
    rules.extend(
        (
            ("logic_all", smart_node(house + bpm_high)),
            ("logic_any", smart_node(house + bpm_high, logical_operator=2)),
            ("nested_all", smart_node(nested_any + rating_high)),
            ("nested_any", smart_node(nested_all + bpm_high, logical_operator=2)),
            ("empty_all", smart_node("")),
            ("empty_any", smart_node("", logical_operator=2)),
            (
                "unknown_operator",
                smart_node(smart_condition("genre", 99, "Fixture House")),
            ),
            (
                "unknown_property",
                smart_node(smart_condition("notAProperty", 1, "Fixture House")),
            ),
            ("condition_outside_node", house + smart_node("")),
            ("two_roots", smart_node(house) + smart_node(techno)),
            (
                "missing_logical_operator",
                smart_node(house, logical_operator=None),
            ),
            ("logical_operator_zero", smart_node(house, logical_operator=0)),
            ("logical_operator_three", smart_node(house, logical_operator=3)),
            ("automatic_update_zero", smart_node(house, automatic_update=0)),
            ("missing_automatic_update", smart_node(house, automatic_update=None)),
            ("mismatched_id", smart_node(house, playlist_id=4_294_967_295)),
            ("missing_id", smart_node(house, playlist_id=None)),
        )
    )
    assert [name for name, _ in rules] == list(SMART_RULE_MATRIX_NAMES)
    return rules


def add_smart_rule_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_rule_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_matrix.{name}"]),
            Seq=sequence,
            Name=f"Smart Matrix {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_numeric_matrix() -> list[tuple[str, str]]:
    rules = []
    for name, (property_name, target, low, high) in SMART_NUMERIC_PROPERTIES.items():
        for operator in range(1, 6):
            left = low if operator == 5 else target
            right = high if operator == 5 else ""
            condition = smart_condition(property_name, operator, left, right)
            rules.append((f"{name}_operator_{operator:02}", smart_node(condition)))

    for name, (property_name, _target, low, high) in SMART_NUMERIC_PROPERTIES.items():
        condition = smart_condition(property_name, 5, high, low)
        rules.append((f"{name}_reversed_range", smart_node(condition)))

    for name, (property_name, _target, _low, _high) in SMART_NUMERIC_PROPERTIES.items():
        rules.extend(
            (
                (
                    f"{name}_empty_equal",
                    smart_node(smart_condition(property_name, 1, "")),
                ),
                (
                    f"{name}_empty_not_equal",
                    smart_node(smart_condition(property_name, 2, "")),
                ),
            )
        )

    for name, (property_name, _target, _low, _high) in SMART_NUMERIC_PROPERTIES.items():
        rules.extend(
            (
                (
                    f"{name}_invalid_equal",
                    smart_node(smart_condition(property_name, 1, "not-a-number")),
                ),
                (
                    f"{name}_invalid_not_equal",
                    smart_node(smart_condition(property_name, 2, "not-a-number")),
                ),
            )
        )

    for prefix, value, range_right in (
        ("negative", "-1", "0"),
        ("overflow", "2147483648", "4294967296"),
    ):
        for operator, suffix in enumerate(
            ("equal", "not_equal", "greater", "less", "range"), start=1
        ):
            right = range_right if operator == 5 else ""
            condition = smart_condition("bpm", operator, value, right)
            rules.append((f"bpm_{prefix}_{suffix}", smart_node(condition)))

    assert [name for name, _ in rules] == list(SMART_NUMERIC_MATRIX_NAMES)
    return rules


def add_smart_numeric_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_numeric_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_numeric.{name}"]),
            Seq=sequence,
            Name=f"Smart Numeric {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_numeric_boundary_matrix() -> list[tuple[str, str]]:
    rule_values = {
        "equal_zero": (1, "0", ""),
        "not_equal_zero": (2, "0", ""),
        "greater_zero": (3, "0", ""),
        "less_zero": (4, "0", ""),
        "range_minus_one_to_one": (5, "-1", "1"),
        "equal_half": (1, "0.5", ""),
        "not_equal_half": (2, "0.5", ""),
        "greater_half": (3, "0.5", ""),
        "less_half": (4, "0.5", ""),
        "range_half_to_one_half": (5, "0.5", "1.5"),
        "equal_int32_max": (1, "2147483647", ""),
        "greater_int32_max": (3, "2147483647", ""),
        "equal_int32_plus_one": (1, "2147483648", ""),
        "equal_uint32_max": (1, "4294967295", ""),
        "equal_uint32_plus_one": (1, "4294967296", ""),
    }
    rules = []
    for name, property_name in SMART_NUMERIC_BOUNDARY_PROPERTIES.items():
        for variant in SMART_NUMERIC_BOUNDARY_VARIANTS:
            if variant in rule_values:
                operator, left, right = rule_values[variant]
                condition = smart_condition(property_name, operator, left, right)
            else:
                missing_values = {
                    "missing_left_equal": (1, "", "", True, False),
                    "missing_left_not_equal": (2, "", "", True, False),
                    "range_missing_left": (5, "", "1", True, False),
                    "range_missing_right": (5, "-1", "", False, True),
                    "range_both_missing": (5, "", "", True, True),
                }
                operator, left, right, missing_left, missing_right = missing_values[variant]
                condition = smart_condition(property_name, operator, left, right)
                if missing_left:
                    condition = condition.replace(' ValueLeft=""', "")
                if missing_right:
                    condition = condition.replace(' ValueRight=""', "")
            rules.append((f"{name}_{variant}", smart_node(condition)))

    assert [name for name, _rule in rules] == list(SMART_NUMERIC_BOUNDARY_NAMES)
    return rules


def add_smart_numeric_boundary_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_numeric_boundary_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_numeric_boundary.{name}"]),
            Seq=sequence,
            Name=f"Smart Numeric Boundary {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_property_matrix() -> list[tuple[str, str]]:
    warmup = IDS["mytag.warmup"]
    vocal = IDS["mytag.vocal"]
    signed_warmup = warmup - 2**32
    signed_vocal = vocal - 2**32
    conditions = (
        ("artist", "artist", 1, "Alpha Artist"),
        ("album", "album", 1, "Album One"),
        ("album_artist", "albumArtist", 1, "Alpha Artist"),
        ("original_artist", "originalArtist", 1, "Fixture Original"),
        ("bpm", "bpm", 1, "12150"),
        ("grouping", "grouping", 1, "4"),
        ("comments", "comments", 1, "comment-4"),
        ("producer", "producer", 1, "Alpha Artist"),
        ("stock_date", "stockDate", 1, "2024-05-05"),
        ("date_created_field", "dateCreated", 1, "2025-01-04"),
        ("date_created_audit", "dateCreated", 1, "2030-03-04"),
        ("counter", "counter", 1, "3"),
        ("file_name", "fileName", 1, "fixture-04.wav"),
        ("genre", "genre", 1, "Fixture House"),
        ("key", "key", 1, "Am"),
        ("label", "label", 1, "Fixture Label One"),
        ("mix_name", "mixName", 1, "Mix 04"),
        ("my_tag_warmup_raw", "myTag", 8, str(warmup)),
        ("my_tag_warmup_signed", "myTag", 8, str(signed_warmup)),
        ("my_tag_vocal_raw", "myTag", 8, str(vocal)),
        ("my_tag_vocal_signed", "myTag", 8, str(signed_vocal)),
        ("rating", "rating", 1, "3"),
        ("date_released", "dateReleased", 1, "2026-02-04"),
        ("remixed_by", "remixedBy", 1, "Fixture Remixer"),
        ("duration", "duration", 1, "599"),
        ("name", "name", 1, "Boundary Fifty Nine"),
        ("year", "year", 1, "2020"),
        ("alias_title", "title", 1, "Boundary Fifty Nine"),
        ("alias_color", "color", 1, "4"),
        ("alias_play_count", "playCount", 1, "3"),
        ("alias_remixer", "remixer", 1, "Fixture Remixer"),
        ("alias_composer", "composer", 1, "Alpha Artist"),
        ("alias_filename_lowercase", "filename", 1, "fixture-04.wav"),
    )
    rules = [
        (name, smart_node(smart_condition(property_name, operator, value)))
        for name, property_name, operator, value in conditions
    ]
    assert [name for name, _ in rules] == list(SMART_PROPERTY_MATRIX_NAMES)
    return rules


def add_smart_property_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_property_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_property.{name}"]),
            Seq=sequence,
            Name=f"Smart Property {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_date_matrix() -> list[tuple[str, str]]:
    rules = []
    for name, property_name in SMART_DATE_PROPERTIES.items():
        for operator in range(1, 6):
            left = "2024-02-29" if operator == 5 else "2025-01-31"
            right = "2025-02-28" if operator == 5 else ""
            rules.append(
                (
                    f"{name}_operator_{operator:02}",
                    smart_node(smart_condition(property_name, operator, left, right)),
                )
            )
        rules.extend(
            (
                (
                    f"{name}_reversed_range",
                    smart_node(
                        smart_condition(
                            property_name, 5, "2025-02-28", "2024-02-29"
                        )
                    ),
                ),
                (
                    f"{name}_blank_equal",
                    smart_node(smart_condition(property_name, 1, "")),
                ),
                (
                    f"{name}_blank_not_equal",
                    smart_node(smart_condition(property_name, 2, "")),
                ),
                (
                    f"{name}_invalid_equal",
                    smart_node(smart_condition(property_name, 1, "not-a-date")),
                ),
                (
                    f"{name}_invalid_not_equal",
                    smart_node(smart_condition(property_name, 2, "not-a-date")),
                ),
            )
        )

    assert [name for name, _ in rules] == list(SMART_DATE_MATRIX_NAMES)
    return rules


def add_smart_date_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_date_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_date.{name}"]),
            Seq=sequence,
            Name=f"Smart Date {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_relative_date_matrix() -> list[tuple[str, str]]:
    rules = []
    for name, property_name in SMART_RELATIVE_DATE_PROPERTIES.items():
        for unit in SMART_RELATIVE_DATE_UNITS:
            for operator in (6, 7):
                condition = smart_condition(property_name, operator, "1", unit=unit)
                rules.append(
                    (f"{name}_{unit}_operator_{operator:02}", smart_node(condition))
                )

    unit_variants = {
        "days": "days",
        "weeks": "weeks",
        "months": "months",
        "years": "years",
        "uppercase_month": "MONTH",
        "empty": "",
        "unknown": "fortnight",
    }
    for variant, unit in unit_variants.items():
        for operator in (6, 7):
            condition = smart_condition("stockDate", operator, "1", unit=unit)
            rules.append(
                (f"stock_date_unit_{variant}_operator_{operator:02}", smart_node(condition))
            )

    count_variants = {
        "zero": "0",
        "negative": "-1",
        "blank": "",
        "invalid": "not-a-number",
        "fractional": "1.5",
        "two": "2",
        "thirty_one": "31",
    }
    for variant, value in count_variants.items():
        for operator in (6, 7):
            condition = smart_condition("stockDate", operator, value, unit="day")
            rules.append(
                (f"stock_date_count_{variant}_operator_{operator:02}", smart_node(condition))
            )

    for operator in (6, 7):
        condition = smart_condition("stockDate", operator, "2", unit="month")
        rules.append(
            (f"stock_date_month_count_two_operator_{operator:02}", smart_node(condition))
        )
    for operator in (6, 7):
        condition = smart_condition("stockDate", operator, "1", "31", "day")
        rules.append((f"stock_date_right_31_operator_{operator:02}", smart_node(condition)))

    assert [name for name, _ in rules] == list(SMART_RELATIVE_DATE_MATRIX_NAMES)
    return rules


def add_smart_relative_date_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_relative_date_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_relative_date.{name}"]),
            Seq=sequence,
            Name=f"Smart Relative Date {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_date_format_matrix() -> list[tuple[str, str]]:
    rules = []
    for name, property_name in SMART_DATE_FORMAT_PROPERTIES.items():
        for value_name, value in SMART_DATE_FORMAT_RULE_VALUES:
            condition = smart_condition(property_name, 1, value)
            rules.append((f"{name}_{value_name}_equal", smart_node(condition)))
        rules.append(
            (
                f"{name}_canonical_not_equal",
                smart_node(smart_condition(property_name, 2, "2025-01-31")),
            )
        )

    assert [name for name, _ in rules] == list(SMART_DATE_FORMAT_MATRIX_NAMES)
    return rules


def add_smart_date_format_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_date_format_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_date_format.{name}"]),
            Seq=sequence,
            Name=f"Smart Date Format {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_text_matrix() -> list[tuple[str, str]]:
    rules = [
        (
            name,
            smart_node(smart_condition("comments", operator, value)),
        )
        for name, operator, value in SMART_TEXT_RULES
    ]
    assert [name for name, _rule in rules] == list(SMART_TEXT_MATRIX_NAMES)
    return rules


def add_smart_text_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_text_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_text.{name}"]),
            Seq=sequence,
            Name=f"Smart Text {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_string_property_matrix() -> list[tuple[str, str]]:
    rules = [
        (
            f"{property_name}_{rule_name}",
            smart_node(smart_condition(written_name, operator, value)),
        )
        for property_name, written_name in SMART_STRING_PROPERTIES.items()
        for rule_name, operator, value in SMART_STRING_PROPERTY_RULES
    ]
    assert [name for name, _rule in rules] == list(SMART_STRING_PROPERTY_MATRIX_NAMES)
    return rules


def add_smart_string_property_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_string_property_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_string_property.{name}"]),
            Seq=sequence,
            Name=f"Smart String Property {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_mytag_matrix() -> list[tuple[str, str]]:
    rules = [
        (
            f"operator_{operator:02}",
            smart_node(smart_condition("myTag", operator, "1")),
        )
        for operator in range(1, 12)
    ]
    rules.extend(
        (
            f"{name}_operator_{operator:02}",
            smart_node(smart_condition("myTag", operator, value)),
        )
        for name, value in SMART_MYTAG_VALUE_CASES
        for operator in (8, 9)
    )
    rules.extend(
        (
            (
                "value_right_ignored",
                smart_node(smart_condition("myTag", 8, "1", "2147483648")),
            ),
            (
                "value_unit_ignored",
                smart_node(smart_condition("myTag", 8, "1", unit="fortnight")),
            ),
        )
    )

    contains_one = smart_condition("myTag", 8, "1")
    contains_high = smart_condition("myTag", 8, "2147483648")
    not_one = smart_condition("myTag", 9, "1")
    not_high = smart_condition("myTag", 9, "2147483648")
    rules.extend(
        (
            (
                "all_contains_one_high_bit",
                smart_node(contains_one + contains_high),
            ),
            (
                "any_contains_one_high_bit",
                smart_node(contains_one + contains_high, logical_operator=2),
            ),
            (
                "all_not_contains_one_high_bit",
                smart_node(not_one + not_high),
            ),
            (
                "any_not_contains_one_high_bit",
                smart_node(not_one + not_high, logical_operator=2),
            ),
            (
                "all_contains_one_not_high_bit",
                smart_node(contains_one + not_high),
            ),
            (
                "any_contains_one_not_high_bit",
                smart_node(contains_one + not_high, logical_operator=2),
            ),
        )
    )
    assert [name for name, _rule in rules] == list(SMART_MYTAG_MATRIX_NAMES)
    return rules


def add_smart_mytag_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_mytag_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_mytag.{name}"]),
            Seq=sequence,
            Name=f"Smart My Tag {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def smart_xml_matrix() -> list[tuple[str, str]]:
    house = smart_condition("genre", 1, "Fixture House")
    techno = smart_condition("genre", 1, "Fixture Techno")
    canonical = smart_node(house)
    mutually_exclusive_all = smart_node(house + techno)
    mutually_exclusive_any = smart_node(house + techno, logical_operator=2)
    rules = [
        ("canonical_house", canonical),
        (
            "lowercase_elements",
            canonical.replace("NODE", "node").replace("CONDITION", "condition"),
        ),
        (
            "mixedcase_elements",
            canonical.replace("NODE", "NoDe").replace("CONDITION", "CoNdItIoN"),
        ),
        ("xml_declaration", f'<?xml version="1.0"?>{canonical}'),
        (
            "xml_declaration_encoding",
            f'<?xml version="1.0" encoding="UTF-8"?>{canonical}',
        ),
        ("leading_bom", f"\ufeff{canonical}"),
        ("leading_comment", f"<!--before-->{canonical}"),
        ("leading_processing_instruction", f"<?fixture probe?>{canonical}"),
        ("trailing_comment", f"{canonical}<!--after-->"),
        ("surrounding_whitespace", f" \r\n\t{canonical}\r\n "),
        (
            "reordered_attributes",
            '<NODE AutomaticUpdate="1" LogicalOperator="1" Id="1">'
            '<CONDITION ValueRight="" ValueLeft="Fixture House" ValueUnit="" '
            'Operator="1" PropertyName="genre"/></NODE>',
        ),
        (
            "single_quoted_attributes",
            "<NODE Id='1' LogicalOperator='1' AutomaticUpdate='1'>"
            "<CONDITION PropertyName='genre' Operator='1' ValueUnit='' "
            "ValueLeft='Fixture House' ValueRight=''/></NODE>",
        ),
        (
            "decimal_character_reference",
            canonical.replace("Fixture House", "Fixture&#32;House"),
        ),
        (
            "hex_character_reference",
            canonical.replace("Fixture House", "Fixture&#x20;House"),
        ),
        ("empty_string", ""),
        ("whitespace_only", " \r\n\t "),
        ("text_only", "Fixture House"),
        ("malformed_open", "<not-valid-smart-list"),
        ("unclosed_root", canonical.removesuffix("</NODE>")),
        ("mismatched_close", canonical.replace("</NODE>", "</NODES>")),
        ("unclosed_condition", canonical.replace("/></NODE>", "></NODE>")),
        (
            "missing_attribute_quote",
            canonical.replace('ValueLeft="Fixture House"', 'ValueLeft="Fixture House'),
        ),
        (
            "unescaped_ampersand",
            canonical.replace("Fixture House", "Fixture & House"),
        ),
        ("unknown_entity", canonical.replace("Fixture House", "Fixture &bogus; House")),
        ("invalid_numeric_entity", canonical.replace("Fixture House", "Fixture &#xZZ; House")),
        ("wrapper_root", f"<ROOT>{canonical}</ROOT>"),
        ("namespaced_root", canonical.replace("NODE", "x:NODE")),
        ("condition_as_root", house),
        ("self_closing_node", '<NODE Id="1" LogicalOperator="1" AutomaticUpdate="1"/>'),
        ("text_child_only", '<NODE LogicalOperator="1">Fixture House</NODE>'),
        ("comment_child_only", '<NODE LogicalOperator="1"><!--condition--></NODE>'),
        ("cdata_child_only", '<NODE LogicalOperator="1"><![CDATA[condition]]></NODE>'),
        ("unknown_child", '<NODE LogicalOperator="1"><UNKNOWN/></NODE>'),
        ("unknown_wrapper_condition", f'<NODE LogicalOperator="1"><WRAP>{house}</WRAP></NODE>'),
        ("nested_node_only", smart_node(smart_node(house, playlist_id=None))),
        ("nested_then_direct_house", smart_node(smart_node(techno, playlist_id=None) + house)),
        ("direct_house_then_nested_techno", smart_node(house + smart_node(techno, playlist_id=None))),
        ("two_direct_all", smart_node(house + techno)),
        ("two_direct_any", smart_node(house + techno, logical_operator=2)),
        ("condition_before_node", house + smart_node(techno)),
        ("two_roots_house_then_techno", smart_node(house) + smart_node(techno)),
        ("valid_root_trailing_text", canonical + "trailing"),
        ("leading_text_valid_root", "leading" + canonical),
        (
            "missing_logical_operator",
            smart_node(house + techno, logical_operator=None),
        ),
        (
            "blank_logical_operator",
            mutually_exclusive_all.replace(
                'LogicalOperator="1"', 'LogicalOperator=""'
            ),
        ),
        (
            "invalid_logical_operator",
            mutually_exclusive_all.replace(
                'LogicalOperator="1"', 'LogicalOperator="wat"'
            ),
        ),
        (
            "plus_two_logical_operator",
            mutually_exclusive_any.replace(
                'LogicalOperator="2"', 'LogicalOperator="+2"'
            ),
        ),
        (
            "spaced_two_logical_operator",
            mutually_exclusive_any.replace(
                'LogicalOperator="2"', 'LogicalOperator=" 2 "'
            ),
        ),
        (
            "duplicate_logical_one_then_two",
            mutually_exclusive_all.replace(
                'LogicalOperator="1"', 'LogicalOperator="1" LogicalOperator="2"'
            ),
        ),
        (
            "duplicate_logical_two_then_one",
            mutually_exclusive_any.replace(
                'LogicalOperator="2"', 'LogicalOperator="2" LogicalOperator="1"'
            ),
        ),
        (
            "lowercase_root_attributes",
            mutually_exclusive_any.replace("Id=", "id=")
            .replace("LogicalOperator=", "logicaloperator=")
            .replace("AutomaticUpdate=", "automaticupdate="),
        ),
        (
            "uppercase_root_attributes",
            mutually_exclusive_any.replace("Id=", "ID=")
            .replace("LogicalOperator=", "LOGICALOPERATOR=")
            .replace("AutomaticUpdate=", "AUTOMATICUPDATE="),
        ),
        ("missing_property", canonical.replace(' PropertyName="genre"', "")),
        ("blank_property", canonical.replace('PropertyName="genre"', 'PropertyName=""')),
        ("whitespace_property", canonical.replace('PropertyName="genre"', 'PropertyName=" genre "')),
        ("uppercase_property_value", canonical.replace('PropertyName="genre"', 'PropertyName="GENRE"')),
        ("property_leading_space", canonical.replace('PropertyName="genre"', 'PropertyName=" genre"')),
        ("missing_operator", canonical.replace(' Operator="1"', "")),
        ("blank_operator", canonical.replace('Operator="1"', 'Operator=""')),
        ("invalid_operator_text", canonical.replace('Operator="1"', 'Operator="wat"')),
        ("plus_one_operator", canonical.replace('Operator="1"', 'Operator="+1"')),
        ("spaced_one_operator", canonical.replace('Operator="1"', 'Operator=" 1 "')),
        ("leading_zero_operator", canonical.replace('Operator="1"', 'Operator="0001"')),
        ("duplicate_operator_one_then_two", canonical.replace('Operator="1"', 'Operator="1" Operator="2"')),
        ("duplicate_operator_two_then_one", canonical.replace('Operator="1"', 'Operator="2" Operator="1"')),
        ("missing_value_left", canonical.replace(' ValueLeft="Fixture House"', "")),
        ("duplicate_value_house_then_techno", canonical.replace('ValueLeft="Fixture House"', 'ValueLeft="Fixture House" ValueLeft="Fixture Techno"')),
        ("duplicate_value_techno_then_house", canonical.replace('ValueLeft="Fixture House"', 'ValueLeft="Fixture Techno" ValueLeft="Fixture House"')),
        ("extra_condition_attributes", canonical.replace("/>", ' Future="yes"/>')),
        ("condition_with_text_content", canonical.replace("/></NODE>", ">ignored</CONDITION></NODE>")),
        ("namespaced_condition", canonical.replace("CONDITION", "x:CONDITION")),
        ("valid_root_then_nul_junk", canonical + "\0junk"),
        ("nul_before_root", "\0" + canonical),
    ]
    assert [name for name, _rule in rules] == list(SMART_XML_MATRIX_NAMES)
    return rules


def add_smart_xml_matrix(connection) -> None:
    for sequence, (name, rule) in enumerate(smart_xml_matrix(), start=4):
        insert(
            connection,
            "djmdPlaylist",
            ID=str(IDS[f"playlist.smart_xml.{name}"]),
            Seq=sequence,
            Name=f"Smart XML {name.replace('_', ' ').title()}",
            Attribute=4,
            ParentID="root",
            SmartList=rule,
        )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_value(digest, value) -> None:
    if value is None:
        kind, data = b"null", b""
    elif isinstance(value, bytes):
        kind, data = b"blob", value
    elif isinstance(value, str):
        kind, data = b"text", value.encode("utf-8")
    elif isinstance(value, int):
        kind, data = b"integer", str(value).encode("ascii")
    elif isinstance(value, float):
        kind, data = b"real", value.hex().encode("ascii")
    else:
        raise TypeError(f"unsupported SQLite value type: {type(value).__name__}")

    digest.update(kind)
    digest.update(b"\0")
    digest.update(len(data).to_bytes(8, "big"))
    digest.update(data)


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def logical_fingerprint(connection) -> str:
    """Hash canonical decrypted schema and rows, independent of SQLCipher salt."""
    digest = hashlib.sha256()
    schema = connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_autoindex_%' ORDER BY type, name, tbl_name"
    ).fetchall()
    for row in schema:
        digest.update(b"schema\0")
        for value in row:
            hash_value(digest, value)

    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    for (table,) in tables:
        quoted = quote_identifier(table)
        columns = [
            row[1]
            for row in connection.execute(f"PRAGMA table_xinfo({quoted})").fetchall()
            if row[6] == 0
        ]
        digest.update(b"table\0")
        hash_value(digest, table)
        for column in columns:
            hash_value(digest, column)

        if not columns:
            continue

        ordering = ", ".join(quote_identifier(column) for column in columns)
        rows = connection.execute(f"SELECT * FROM {quoted} ORDER BY {ordering}")
        for row in rows:
            digest.update(b"row\0")
            for value in row:
                hash_value(digest, value)

    return digest.hexdigest()


def apply_settings(connection, settings: dict[str, object]) -> None:
    if "secondary_sorts" in settings:
        selected_sorts = [int(value) for value in settings["secondary_sorts"]]
    else:
        selected_sorts = [int(settings.get("secondary_sort", 12))]

    if len(selected_sorts) != len(set(selected_sorts)):
        raise ValueError("secondary_sorts contains duplicate IDs")

    connection.execute("UPDATE djmdSort SET Disable = Disable & ~2")
    for selected in selected_sorts:
        changed = connection.execute(
            "UPDATE djmdSort SET Disable = Disable | 2 WHERE CAST(ID AS INTEGER) = ?",
            (selected,),
        ).rowcount
        if changed != 1:
            raise ValueError(f"secondary sort {selected} does not identify one djmdSort row")

    for sort_id, values in dict(settings.get("sort", {})).items():
        row = dict(values)
        if "enabled" in row:
            operation = "Disable & ~1" if row["enabled"] else "Disable | 1"
            connection.execute(
                f"UPDATE djmdSort SET Disable = {operation} WHERE CAST(ID AS INTEGER) = ?",
                (int(sort_id),),
            )
        if "seq" in row:
            connection.execute(
                "UPDATE djmdSort SET Seq = ? WHERE CAST(ID AS INTEGER) = ?",
                (int(row["seq"]), int(sort_id)),
            )

    for category_id, values in dict(settings.get("category", {})).items():
        row = dict(values)
        if "disable" in row:
            connection.execute(
                "UPDATE djmdCategory SET Disable = ? WHERE CAST(ID AS INTEGER) = ?",
                (int(row["disable"]), int(category_id)),
            )
        if "seq" in row:
            connection.execute(
                "UPDATE djmdCategory SET Seq = ? WHERE CAST(ID AS INTEGER) = ?",
                (int(row["seq"]), int(category_id)),
            )

    for color_id, comment in dict(settings.get("colors", {})).items():
        connection.execute(
            "UPDATE djmdColor SET Commnt = ? WHERE CAST(ID AS INTEGER) = ?",
            (str(comment), int(color_id)),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "profile",
        choices=(
            "empty",
            "full",
            "boundaries",
            "bpm-tolerance-boundaries",
            "unicode-boundaries",
            "filename-boundaries",
            "invalid",
            "scalar-boundaries",
            "smart-playlists",
            "smart-rule-matrix",
            "smart-numeric-matrix",
            "smart-numeric-boundaries",
            "smart-property-matrix",
            "smart-date-matrix",
            "smart-relative-date-matrix",
            "smart-date-format-matrix",
            "smart-text-matrix",
            "smart-string-property-matrix",
            "smart-mytag-matrix",
            "smart-xml-matrix",
            "smart-settings",
            "key-notation",
            "hot-cue-banks",
            "hot-cue-bank-pagination",
            "hot-cue-bank-cue-fields",
            "hot-cue-bank-extended-fields",
            "hot-cue-bank-mutation",
            "hot-cue-bank-legacy-mutation",
            "hot-cue-bank-legacy-ordinals",
            "hot-cue-bank-legacy-ordinal-boundaries",
            "hot-cue-bank-deleted-bank-member",
            "link-visibility",
            "streaming-provider-paths",
            "compatibility",
            "compatibility-exhaustive",
            "play-paths",
            "cloud-sync-zero",
            "payload-paths",
            "payload-valid",
            "adjacent-payload-cues",
            "delivery-boundaries",
            "delivery-wide-strings",
            "search-ceiling",
            "search-track-ceiling",
            "search-track-large",
            "search-track-large-title",
            "search-text",
            "display-strings-254",
            "display-strings-255",
            "display-strings-256",
            "display-strings-unicode-256",
            "settings",
        ),
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("options", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--settings-file", type=Path)
    args = parser.parse_args()

    database = args.output / "master.db"
    if args.output.exists() or database.exists():
        raise SystemExit(f"refusing to overwrite fixture output: {args.output}")
    args.output.mkdir(parents=True)

    settings = None
    if args.profile in ("settings", "smart-settings"):
        if args.settings_file is None:
            raise SystemExit(f"{args.profile} profile requires --settings-file")
        settings = json.loads(args.settings_file.read_text())
    elif args.settings_file is not None:
        raise SystemExit("--settings-file is valid only for the settings profile")

    key = key_from_options(args.options)
    source = connect(args.source, key, readonly=True)
    target = connect(database, key)
    source.backup(target)
    source.close()

    clear_library(target)
    add_rekordbox_baseline(target)
    if args.profile == "empty":
        add_default_mytags(target)
    else:
        add_lookups(target)
        display_string_values = {
            "display-strings-254": "s" * 254,
            "display-strings-255": "s" * 255,
            "display-strings-256": "s" * 256,
            "display-strings-unicode-256": "\U0001f642" * 128,
        }
        display_string_value = display_string_values.get(args.profile)
        local_dbid = str(target.execute("SELECT DBID FROM djmdProperty").fetchone()[0])
        tracks = {
            "boundaries": boundary_tracks,
            "bpm-tolerance-boundaries": bpm_tolerance_tracks,
            "unicode-boundaries": unicode_boundary_tracks,
            "filename-boundaries": filename_boundary_tracks,
            "smart-property-matrix": smart_property_tracks,
            "smart-numeric-boundaries": smart_numeric_boundary_tracks,
            "smart-date-matrix": smart_date_tracks,
            "smart-relative-date-matrix": smart_relative_date_tracks,
            "smart-date-format-matrix": smart_date_format_tracks,
            "smart-text-matrix": smart_text_tracks,
            "smart-string-property-matrix": smart_string_property_tracks,
            "smart-mytag-matrix": smart_mytag_tracks,
            "invalid": invalid_tracks,
            "scalar-boundaries": scalar_boundary_tracks,
            "compatibility": compatibility_tracks,
            "compatibility-exhaustive": compatibility_exhaustive_tracks,
            "play-paths": lambda: play_path_tracks(local_dbid),
            "cloud-sync-zero": lambda: cloud_sync_zero_tracks(local_dbid),
            "payload-paths": payload_path_tracks,
            "payload-valid": payload_valid_tracks,
            "adjacent-payload-cues": adjacent_payload_cue_tracks,
            "link-visibility": link_visibility_tracks,
            "streaming-provider-paths": streaming_provider_path_tracks,
            "delivery-boundaries": delivery_boundary_tracks,
            "delivery-wide-strings": delivery_wide_string_tracks,
            "search-ceiling": search_ceiling_tracks,
            "search-track-ceiling": lambda: search_ceiling_tracks(5_005),
            "search-track-large": search_track_large_tracks,
            "search-track-large-title": search_track_large_title_tracks,
            "search-text": search_text_tracks,
            "hot-cue-bank-pagination": hot_cue_bank_pagination_tracks,
        }.get(
            args.profile,
            (lambda: display_string_tracks(display_string_value))
            if display_string_value is not None
            else full_tracks,
        )()
        for track in tracks:
            add_track(target, track)
        deleted = dict(tracks[0])
        deleted.update(ID=str(IDS["track.deleted"]), Title="Deleted Fixture Track")
        add_track(target, deleted, deleted=1)
        if args.profile in (
            "bpm-tolerance-boundaries",
            "search-ceiling",
            "search-track-ceiling",
            "search-track-large",
            "search-track-large-title",
            "compatibility-exhaustive",
        ):
            add_default_mytags(target)
        else:
            add_relations(target)
        if args.profile == "smart-playlists":
            add_smart_playlist_relations(target)
        if args.profile == "smart-rule-matrix":
            add_smart_rule_matrix(target)
        if args.profile == "smart-settings":
            add_smart_rule_matrix(target)
        if args.profile == "key-notation":
            add_smart_rule_matrix(target)
            apply_key_notation_scale_names(target)
        if args.profile in (
            "hot-cue-banks",
            "hot-cue-bank-pagination",
            "hot-cue-bank-cue-fields",
            "hot-cue-bank-extended-fields",
            "hot-cue-bank-mutation",
            "hot-cue-bank-legacy-mutation",
            "hot-cue-bank-legacy-ordinals",
            "hot-cue-bank-legacy-ordinal-boundaries",
            "hot-cue-bank-deleted-bank-member",
        ):
            add_hot_cue_bank_matrix(target)
        if args.profile == "hot-cue-bank-pagination":
            add_hot_cue_bank_pagination_matrix(target)
        if args.profile == "hot-cue-bank-cue-fields":
            add_hot_cue_bank_cue_field_matrix(target)
        if args.profile == "hot-cue-bank-extended-fields":
            add_hot_cue_bank_extended_field_matrix(target)
        if args.profile == "hot-cue-bank-mutation":
            add_hot_cue_bank_mutation_fixture(target)
        if args.profile == "hot-cue-bank-legacy-mutation":
            add_hot_cue_bank_mutation_fixture(
                target, track_no=4, relation_ids=(94_101, 94_102)
            )
        if args.profile == "hot-cue-bank-legacy-ordinals":
            add_hot_cue_bank_legacy_ordinal_fixture(target)
        if args.profile == "hot-cue-bank-legacy-ordinal-boundaries":
            add_hot_cue_bank_legacy_ordinal_boundary_fixture(target)
        if args.profile == "hot-cue-bank-deleted-bank-member":
            add_deleted_hot_cue_bank_member(target)
        if args.profile == "link-visibility":
            add_link_visibility_relations(target)
        if args.profile == "streaming-provider-paths":
            add_streaming_provider_path_relations(target)
        if args.profile == "payload-paths":
            target.execute(
                "UPDATE djmdPlaylist SET ImagePath = ? WHERE CAST(ID AS INTEGER) = ?",
                (
                    "/PIONEER/Artwork/fff/missing-playlist-artwork/artwork.jpg",
                    IDS["playlist.primary"],
                ),
            )
        if args.profile == "payload-valid":
            target.execute(
                "UPDATE djmdPlaylist SET ImagePath = ? WHERE CAST(ID AS INTEGER) = ?",
                (
                    "/PIONEER/Artwork/000/deterministic/artwork.jpg",
                    IDS["playlist.primary"],
                ),
            )
        if args.profile == "adjacent-payload-cues":
            add_adjacent_payload_cue_matrix(target)
        if args.profile == "smart-numeric-matrix":
            add_smart_numeric_matrix(target)
        if args.profile == "smart-numeric-boundaries":
            add_smart_numeric_boundary_matrix(target)
        if args.profile == "smart-property-matrix":
            add_smart_property_matrix(target)
        if args.profile == "smart-date-matrix":
            add_smart_date_matrix(target)
        if args.profile == "smart-relative-date-matrix":
            add_smart_relative_date_matrix(target)
        if args.profile == "smart-date-format-matrix":
            add_smart_date_format_matrix(target)
        if args.profile == "smart-text-matrix":
            add_smart_text_matrix(target)
        if args.profile == "smart-string-property-matrix":
            add_smart_string_property_lookups(target)
            add_smart_string_property_matrix(target)
        if args.profile == "smart-mytag-matrix":
            add_smart_mytag_relations(target)
            add_smart_mytag_matrix(target)
        if args.profile == "smart-xml-matrix":
            add_smart_xml_matrix(target)
        if args.profile == "boundaries":
            apply_boundary_lookup_strings(target)
        if args.profile == "delivery-boundaries":
            add_delivery_composer_lookups(target)
        if display_string_value is not None:
            apply_display_string_lookups(target, display_string_value)
    if settings is not None:
        apply_settings(target, settings)

    target.execute(
        "CREATE TABLE IF NOT EXISTS link_export_fixture "
        "(profile TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL)"
    )
    target.execute("DELETE FROM link_export_fixture")
    target.execute(
        "INSERT INTO link_export_fixture VALUES (?, ?, ?)",
        (args.profile, FIXTURE_VERSION, STAMP),
    )
    target.commit()
    integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
    track_count = target.execute(
        "SELECT count(*) FROM djmdContent WHERE rb_local_deleted = 0"
    ).fetchone()[0]
    fixture_fingerprint = logical_fingerprint(target)
    target.close()

    if args.profile.startswith("delivery-"):
        manifest_ids = dict(IDS)
    else:
        manifest_ids = {
            name: value
            for name, value in IDS.items()
            if not name.startswith("artist.composer_")
        }
    if args.profile == "search-ceiling":
        manifest_ids = {
            name: value
            for name, value in manifest_ids.items()
            if not name.startswith("track.")
        }
        manifest_ids.update(
            {
                "track.search_ceiling.first": 20_001,
                "track.search_ceiling.thousandth": 21_000,
                "track.search_ceiling.thousand_first": 21_001,
                "track.search_ceiling.last": 21_005,
                "track.deleted": IDS["track.deleted"],
            }
        )
    if args.profile == "filename-boundaries":
        manifest_ids.update(
            {
                f"track.filename_{index:02}": 30_000 + index
                for index in range(1, 21)
            }
        )
    if args.profile == "bpm-tolerance-boundaries":
        manifest_ids = {
            name: value
            for name, value in manifest_ids.items()
            if not name.startswith("track.")
        }
        manifest_ids.update(
            {
                f"track.bpm_{track['BPM']}": int(track["ID"])
                for track in bpm_tolerance_tracks()
            }
        )
        manifest_ids["track.deleted"] = IDS["track.deleted"]
    if args.profile == "compatibility-exhaustive":
        manifest_ids = {
            name: value
            for name, value in manifest_ids.items()
            if not name.startswith("track.")
        }
        manifest_ids.update(
            {
                f"track.compatibility_exhaustive.{index:03}": case["id"]
                for index, case in enumerate(
                    compatibility_exhaustive_cases(), start=1
                )
            }
        )
        manifest_ids["track.deleted"] = IDS["track.deleted"]
    if args.profile in (
        "hot-cue-banks",
        "hot-cue-bank-pagination",
        "hot-cue-bank-cue-fields",
        "hot-cue-bank-extended-fields",
        "hot-cue-bank-mutation",
        "hot-cue-bank-legacy-mutation",
        "hot-cue-bank-legacy-ordinals",
        "hot-cue-bank-legacy-ordinal-boundaries",
        "hot-cue-bank-deleted-bank-member",
    ):
        manifest_ids.update(HOT_CUE_BANK_IDS)
    if args.profile == "hot-cue-bank-pagination":
        manifest_ids.update(
            {
                "track.hot_cue_page.first": 40_001,
                "track.hot_cue_page.thirty_second": 40_032,
                "track.hot_cue_page.thirty_third": 40_033,
                "track.hot_cue_page.sixty_fourth": 40_064,
                "track.hot_cue_page.sixty_fifth": 40_065,
                "track.hot_cue_page.last": 40_070,
            }
        )
    if args.profile == "hot-cue-bank-cue-fields":
        manifest_ids.update(CUE_FIELD_BANK_IDS)
    if args.profile == "hot-cue-bank-extended-fields":
        manifest_ids.update(EXTENDED_CUE_BANK_IDS)
    if args.profile in (
        "hot-cue-bank-mutation",
        "hot-cue-bank-legacy-mutation",
        "hot-cue-bank-legacy-ordinals",
        "hot-cue-bank-legacy-ordinal-boundaries",
    ):
        manifest_ids.update(MUTATION_CUE_BANK_IDS)
    manifest = {
        "fixture_version": FIXTURE_VERSION,
        "profile": args.profile,
        "database_sha256": sha256(database),
        "fixture_fingerprint": fixture_fingerprint,
        "integrity": integrity,
        "track_count": track_count,
        "ids": manifest_ids,
    }
    if settings is not None:
        manifest["settings"] = settings
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
