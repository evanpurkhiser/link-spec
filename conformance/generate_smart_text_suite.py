#!/usr/bin/env python3
"""Generate the SmartList text-collation conformance suite."""

from __future__ import annotations

import json
from pathlib import Path

from build_fixture import SMART_TEXT_RULES, SMART_TEXT_VALUES


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "suites/smart-text-matrix.json"
TRACK_NAMES = tuple(name for name, _value in SMART_TEXT_VALUES)
EMPTY = ("empty", "null")
NONEMPTY = tuple(name for name in TRACK_NAMES if name not in EMPTY)
ALPHA_EQUAL = (
    "alpha_upper",
    "alpha_lower",
    "alpha_acute_precomposed",
    "alpha_acute_decomposed",
    "alpha_diaeresis_upper",
    "embedded_nul_suffix",
    "fullwidth",
    "trailing_combining",
    "angstrom_sign",
    "a_ring",
)
ALPHA_CONTAINS = (
    "alpha_upper",
    "alpha_lower",
    "alpha_acute_precomposed",
    "alpha_acute_decomposed",
    "alpha_diaeresis_upper",
    "alpha_prefix",
    "alpha_suffix",
    "alpha_middle",
    "alpha_spaced",
    "embedded_nul_suffix",
    "emoji_prefix",
    "emoji_suffix",
    "fullwidth",
    "punctuation_hyphen",
    "punctuation_none",
    "tab",
    "newline",
    "trailing_combining",
    "angstrom_sign",
    "a_ring",
    "ampersand",
    "double_quote",
    "apostrophe",
)
ALPHA_STARTS = (
    "alpha_upper",
    "alpha_lower",
    "alpha_acute_precomposed",
    "alpha_acute_decomposed",
    "alpha_diaeresis_upper",
    "alpha_prefix",
    "embedded_nul_suffix",
    "emoji_suffix",
    "fullwidth",
    "punctuation_hyphen",
    "punctuation_none",
    "tab",
    "newline",
    "trailing_combining",
    "angstrom_sign",
    "a_ring",
    "ampersand",
    "double_quote",
    "apostrophe",
)
ALPHA_ENDS = (
    "alpha_upper",
    "alpha_lower",
    "alpha_acute_precomposed",
    "alpha_acute_decomposed",
    "alpha_diaeresis_upper",
    "alpha_suffix",
    "embedded_nul_suffix",
    "emoji_prefix",
    "fullwidth",
    "trailing_combining",
    "angstrom_sign",
    "a_ring",
)
BETA_CONTAINS = (
    "alpha_prefix",
    "alpha_suffix",
    "alpha_middle",
    "punctuation_hyphen",
    "punctuation_none",
    "tab",
    "newline",
    "ampersand",
    "double_quote",
    "apostrophe",
)


def complement(names: tuple[str, ...], universe: tuple[str, ...] = TRACK_NAMES) -> tuple[str, ...]:
    return tuple(name for name in universe if name not in names)


EXPECTED_TRACKS = {
    "alpha_operator_01": ALPHA_EQUAL,
    "alpha_operator_02": complement(ALPHA_EQUAL),
    "alpha_operator_08": ALPHA_CONTAINS,
    "alpha_operator_09": complement(ALPHA_CONTAINS, NONEMPTY),
    "alpha_operator_10": ALPHA_STARTS,
    "alpha_operator_11": ALPHA_ENDS,
    "alpha_lower_equal": ALPHA_EQUAL,
    "alpha_acute_precomposed_equal": ALPHA_EQUAL,
    "alpha_acute_decomposed_equal": (),
    "alpha_diaeresis_equal": ALPHA_EQUAL,
    "alpha_trailing_combining_equal": (),
    "alpha_angstrom_equal": ALPHA_EQUAL,
    "alpha_a_ring_equal": ALPHA_EQUAL,
    "beta_contains": BETA_CONTAINS,
    "beta_not_contains": complement(BETA_CONTAINS, NONEMPTY),
    "beta_starts": ("alpha_suffix", "alpha_middle"),
    "beta_ends": (
        "alpha_prefix",
        "punctuation_hyphen",
        "punctuation_none",
        "tab",
        "newline",
        "ampersand",
    ),
    "empty_operator_01": EMPTY,
    "empty_operator_02": NONEMPTY,
    "empty_operator_08": (),
    "empty_operator_09": (),
    "empty_operator_10": (),
    "empty_operator_11": (),
    "emoji_equal": ("emoji_only",),
    "emoji_contains": ("emoji_prefix", "emoji_suffix", "emoji_only"),
    "emoji_starts": ("emoji_prefix", "emoji_only"),
    "emoji_ends": ("emoji_suffix", "emoji_only"),
    "sharp_s_equal": ("sharp_s", "sharp_s_expanded"),
    "sharp_s_expanded_equal": ("sharp_s_expanded",),
    "sharp_s_contains_ss": ("sharp_s_expanded",),
    "ligature_equal": ("ligature", "ligature_expanded"),
    "ligature_expanded_equal": ("ligature_expanded",),
    "fullwidth_equal": ALPHA_EQUAL,
    "turkish_ascii_equal": ("turkish_ascii", "turkish_dotted"),
    "turkish_dotted_equal": ("turkish_ascii", "turkish_dotted"),
    "turkish_dotless_equal": ("turkish_dotless",),
    "greek_upper_equal": ("greek_upper", "greek_sigma", "greek_final_sigma"),
    "greek_sigma_equal": ("greek_upper", "greek_sigma", "greek_final_sigma"),
    "greek_final_sigma_equal": (
        "greek_upper",
        "greek_sigma",
        "greek_final_sigma",
    ),
    "katakana_equal": ("katakana", "hiragana"),
    "hiragana_equal": ("katakana", "hiragana"),
    "combining_dot_acute_equal": (),
    "combining_acute_dot_equal": (),
    "punctuation_none_equal": ("punctuation_none",),
    "punctuation_none_contains": ("punctuation_none",),
    "punctuation_hyphen_equal": ("punctuation_hyphen",),
    "punctuation_space_equal": ("alpha_prefix",),
    "tab_equal": ("tab",),
    "newline_equal": ("newline",),
    "cyrillic_alpha_equal": ("cyrillic_alpha",),
    "greek_alpha_equal": ("greek_alpha",),
    "ampersand_equal": ("ampersand",),
    "ampersand_contains": ("ampersand",),
    "double_quote_equal": ("double_quote",),
    "apostrophe_equal": ("apostrophe",),
}


def number(value: int | str) -> dict[str, int | str]:
    return {"number": value}


def main() -> None:
    assert set(EXPECTED_TRACKS) == {
        name for name, _operator, _value in SMART_TEXT_RULES
    }
    cases = [
        {
            "id": name.replace("_", "-"),
            "description": f"SmartList comments collation probe: {name.replace('_', ' ')}",
            "request_kind": "0x1105",
            "arguments": [
                number("$context"),
                number("$sort"),
                number(f"$fixture.playlist.smart_text.{name}"),
                number(0),
            ],
            "expect": {
                "outcome": "menu",
                "total": len(EXPECTED_TRACKS[name]),
                "row_count": len(EXPECTED_TRACKS[name]),
                "item_ids": [
                    f"$fixture.track.smart_text.{track_name}"
                    for track_name in EXPECTED_TRACKS[name]
                ],
            },
        }
        for name, _operator, _value in SMART_TEXT_RULES
    ]
    suite = {
        "name": "smart-rule-text-collation-matrix",
        "fixture_profile": "smart-text-matrix",
        "fixture_version": 1,
        "defaults": {
            "device": 1,
            "context": "0x01010301",
            "sort": 0,
            "root_capabilities": "0x05cfffff",
            "setup": "extended",
            "page_size": 10,
            "render_arguments": [0, "$total", 12, 1, 0],
        },
        "cases": cases,
    }
    OUTPUT.write_text(json.dumps(suite, indent=2, ensure_ascii=False) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
