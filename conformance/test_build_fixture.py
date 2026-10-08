import unittest

import build_fixture


def utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


class PayloadPathFixtureProfileTests(unittest.TestCase):
    def test_profile_distinguishes_missing_empty_and_null_paths(self) -> None:
        tracks = build_fixture.payload_path_tracks()

        self.assertEqual(
            "/PIONEER/Artwork/fff/missing-artwork/artwork.jpg",
            tracks[0]["ImagePath"],
        )
        self.assertEqual(
            "/PIONEER/USBANLZ/fff/missing-analysis/ANLZ0000.DAT",
            tracks[0]["AnalysisDataPath"],
        )
        self.assertEqual("", tracks[1]["ImagePath"])
        self.assertEqual("", tracks[1]["AnalysisDataPath"])
        self.assertNotIn("ImagePath", tracks[2])
        self.assertNotIn("AnalysisDataPath", tracks[2])


class PayloadValidFixtureProfileTests(unittest.TestCase):
    def test_profile_points_at_generated_metadata_assets(self) -> None:
        tracks = build_fixture.payload_valid_tracks()

        self.assertEqual(
            "/PIONEER/Artwork/000/deterministic/artwork.jpg",
            tracks[0]["ImagePath"],
        )
        self.assertEqual(
            "/PIONEER/USBANLZ/000/deterministic/ANLZ0000.DAT",
            tracks[0]["AnalysisDataPath"],
        )
        self.assertNotIn("ImagePath", tracks[1])
        self.assertNotIn("AnalysisDataPath", tracks[1])


class AdjacentPayloadCueFixtureProfileTests(unittest.TestCase):
    def test_profile_isolates_cue_shapes_and_count_boundaries(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO djmdCue"):
                    columns = sql[sql.index("(") + 1 : sql.index(")")].split(", ")
                    self.rows.append(dict(zip(columns, values)))

        tracks = build_fixture.adjacent_payload_cue_tracks()
        connection = RecordingConnection()
        build_fixture.add_adjacent_payload_cue_matrix(connection)

        self.assertEqual(len(tracks), len(build_fixture.CUE_PAYLOAD_TRACK_IDS))
        self.assertEqual(len(connection.rows), 530)
        counts = {
            name: sum(
                row["ContentID"] == str(content_id) and not row["rb_local_deleted"]
                for row in connection.rows
            )
            for name, content_id in build_fixture.CUE_PAYLOAD_TRACK_IDS.items()
        }
        self.assertEqual(counts["cue_payload.zero"], 0)
        self.assertEqual(counts["cue_payload.one"], 1)
        self.assertEqual(counts["cue_payload.three"], 3)
        self.assertEqual(counts["cue_payload.count_255"], 255)
        self.assertEqual(counts["cue_payload.count_256"], 256)
        self.assertEqual(counts["cue_payload.deleted_only"], 0)
        self.assertEqual(counts["cue_payload.mixed_deleted"], 1)
        self.assertTrue(all(count == 1 for name, count in counts.items() if name not in {
            "cue_payload.zero",
            "cue_payload.three",
            "cue_payload.count_255",
            "cue_payload.count_256",
            "cue_payload.deleted_only",
        }))

        by_content = {row["ContentID"]: row for row in connection.rows}
        self.assertEqual(
            by_content[str(build_fixture.CUE_PAYLOAD_TRACK_IDS["cue_payload.comment_nul"])]["Comment"],
            "before\0after",
        )
        self.assertEqual(
            by_content[str(build_fixture.CUE_PAYLOAD_TRACK_IDS["cue_payload.seek_in"])]["InPointSeekInfo"],
            "1,2,3",
        )
        self.assertEqual(
            by_content[str(build_fixture.CUE_PAYLOAD_TRACK_IDS["cue_payload.seek_malformed"])]["InPointSeekInfo"],
            "malformed",
        )


class DeliveryFixtureProfileTests(unittest.TestCase):
    def test_delivery_boundary_profile_covers_nullable_and_127_unit_fields(self) -> None:
        tracks = build_fixture.delivery_boundary_tracks()

        self.assertEqual(8, len(tracks))
        self.assertIsNone(tracks[0]["DeliveryComment"])
        self.assertEqual("", tracks[1]["DeliveryComment"])
        ascii_lengths = [len(row["DeliveryComment"]) for row in tracks[2:5]]
        controls = [row["DeliveryControl"] for row in tracks[2:]]

        self.assertEqual([126, 127, 128], ascii_lengths)
        self.assertEqual(
            [126, 127, 128],
            [utf16_units(row["DeliveryComment"]) for row in tracks[5:8]],
        )
        self.assertEqual(["OFF", "ON", "on", "Off", "ON", "ON"], controls)
        self.assertEqual("999999", tracks[6]["ComposerID"])

    def test_delivery_wide_profile_brackets_255_utf16_units(self) -> None:
        tracks = build_fixture.delivery_wide_string_tracks()

        self.assertEqual(8, len(tracks))
        self.assertEqual(
            [254, 255, 256, 252, 254, 255, 256, 257],
            [utf16_units(row["DeliveryComment"]) for row in tracks],
        )
        self.assertTrue(all(row["DeliveryControl"] == "ON" for row in tracks))
        self.assertTrue(all(row["DeliveryComment"] == row["ISRC"] for row in tracks))
        self.assertTrue(all(row["DeliveryComment"] == row["Lyricist"] for row in tracks))


class PlayPathFixtureProfileTests(unittest.TestCase):
    def test_profile_crosses_local_cloud_path_and_hotcue_inputs(self) -> None:
        tracks = build_fixture.play_path_tracks("3194974614")

        self.assertEqual(14, len(tracks))
        self.assertEqual([None, 0, 0x80, 0x81], [row["ContentLink"] for row in tracks[:4]])
        self.assertEqual(
            [None, 0, -1, 0, 1, 1, 2, 2_147_483_647, 0, 0, 1, 1, 0, 0],
            [row["ServiceID"] for row in tracks],
        )
        self.assertEqual(
            [
                8864,
                0,
                -1,
                2_147_483_647,
                1,
                2,
                4_294_967_295,
                4_294_967_296,
                None,
                3,
                4,
                5,
                6,
                6,
            ],
            [row["FileSize"] for row in tracks],
        )
        self.assertEqual(
            ["on", "", None, "OFF", "0", " ", "ON", "Ω", "", "on", "on", "on", "on", "on"],
            [row["HotCueAutoLoad"] for row in tracks],
        )
        self.assertEqual("3194974614", tracks[4]["MasterDBID"])
        self.assertEqual(tracks[0]["FolderPath"], tracks[0]["rb_LocalFolderPath"])

    def test_cloud_sync_zero_fixture_covers_the_static_branch_partition(self) -> None:
        tracks = build_fixture.cloud_sync_zero_tracks("4242")
        self.assertEqual(10, len(tracks))
        self.assertEqual(
            [None, -1, 0, 1, 1, 2, 2, 1, 5, 6],
            [track["ServiceID"] for track in tracks],
        )
        self.assertEqual(
            {"/moved-existing.bin", "/moved-missing.bin", "/moved-service-five.bin"},
            {
                track["FolderPath"]
                for track in tracks
                if track["ServiceID"] in {2, 5}
            },
        )
        self.assertTrue(tracks[3]["OrgFolderPath"].endswith("org-existing.bin"))
        self.assertTrue(tracks[4]["OrgFolderPath"].endswith("org-existing-dir"))


class HotCueBankFixtureProfileTests(unittest.TestCase):
    def test_pagination_profile_crosses_two_full_render_pages(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        tracks = build_fixture.hot_cue_bank_pagination_tracks()
        connection = RecordingConnection()
        build_fixture.add_hot_cue_bank_pagination_matrix(connection)
        memberships = [
            values
            for sql, values in connection.rows
            if "INSERT INTO djmdSongHotCueBanklist" in sql
        ]

        self.assertEqual(70, len(tracks))
        self.assertEqual([40_001, 40_032, 40_033, 40_064, 40_065, 40_070], [
            int(tracks[index - 1]["ID"]) for index in (1, 32, 33, 64, 65, 70)
        ])
        self.assertEqual(70, len(memberships))
        self.assertEqual(list(range(1, 71)), [row[3] for row in memberships])
        self.assertEqual(
            list(range(40_001, 40_071)),
            [int(row[2]) for row in memberships],
        )

    def test_profile_covers_tree_order_membership_limits_and_invalid_relations(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        connection = RecordingConnection()
        build_fixture.add_hot_cue_bank_matrix(connection)

        nodes = [
            values
            for sql, values in connection.rows
            if "INSERT INTO djmdHotCueBanklist" in sql
        ]
        memberships = [
            values
            for sql, values in connection.rows
            if "INSERT INTO djmdSongHotCueBanklist" in sql
        ]
        cues = [
            values
            for sql, values in connection.rows
            if "INSERT INTO djmdCue" in sql
        ]

        self.assertEqual(9, len(nodes))
        self.assertEqual(17, len(memberships))
        self.assertEqual(17, len(cues))
        self.assertEqual(
            [
                build_fixture.IDS["track.eighth"],
                build_fixture.IDS["track.first"],
                build_fixture.IDS["track.sixth"],
            ],
            [int(row[2]) for row in memberships[:3]],
        )
        self.assertEqual(build_fixture.IDS["track.first"], int(memberships[8][2]))
        self.assertEqual(build_fixture.IDS["track.deleted"], int(memberships[9][2]))
        self.assertEqual(999_999, int(memberships[10][2]))
        self.assertEqual(1, memberships[11][6])
        self.assertEqual([0, -1], [memberships[14][3], memberships[15][3]])
        self.assertEqual(int(memberships[0][4]), int(cues[0][0]))
        self.assertEqual(int(memberships[0][2]), int(cues[0][1]))
        self.assertEqual(1, cues[0][10])

    def test_cue_field_profile_pairs_wire_and_ignored_values(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        connection = RecordingConnection()
        build_fixture.add_hot_cue_bank_cue_field_matrix(connection)

        nodes = [
            values
            for sql, values in connection.rows
            if "INSERT INTO djmdHotCueBanklist" in sql
        ]
        memberships = [
            values
            for sql, values in connection.rows
            if "INSERT INTO djmdSongHotCueBanklist" in sql
        ]
        cues = [
            values
            for sql, values in connection.rows
            if "INSERT INTO djmdCue" in sql
        ]

        self.assertEqual(2, len(nodes))
        self.assertEqual(6, len(memberships))
        self.assertEqual(6, len(cues))
        wire_indexes = (2, 3, 5, 7, 8, 9, 11, 12)
        self.assertEqual(
            [memberships[0][index] for index in wire_indexes],
            [memberships[3][index] for index in wire_indexes],
        )
        self.assertEqual(
            [(-1, 1_001), (4_004, 2_002), (1, 3_003)],
            [(row[9], row[5]) for row in memberships[:3]],
        )
        self.assertNotEqual(
            memberships[0][6:],
            memberships[3][6:],
        )
        self.assertNotEqual(cues[0][1:10], cues[3][1:10])

    def test_extended_cue_field_profile_isolates_seek_triples(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        connection = RecordingConnection()
        build_fixture.add_hot_cue_bank_extended_field_matrix(connection)

        memberships = [
            values
            for sql, values in connection.rows
            if "INSERT INTO djmdSongHotCueBanklist" in sql
        ]
        self.assertEqual(9, len(memberships))
        self.assertTrue(all(row[2] == 1 for row in memberships))
        rendered = [
            dict(
                zip(
                    sql[sql.index("(") + 1 : sql.index(")")].split(", "),
                    values,
                )
            )
            for sql, values in connection.rows
            if "INSERT INTO djmdSongHotCueBanklist" in sql
        ]
        self.assertEqual(-1, rendered[1]["OutMsec"])
        self.assertEqual(7, rendered[2]["Color"])
        self.assertEqual("A", rendered[3]["Comment"])
        self.assertEqual("\u00e9\U0001f642", rendered[4]["Comment"])
        self.assertEqual(0x12345678, rendered[5]["BeatLoopSize"])
        self.assertEqual(0x0A0B0C0D, rendered[6]["CueMicrosec"])
        self.assertEqual("1,2,3", rendered[7]["InPointSeekInfo"])
        self.assertEqual("4,5,6", rendered[8]["OutPointSeekInfo"])

    def test_mutation_profile_has_two_same_slot_writable_memberships(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        connection = RecordingConnection()
        build_fixture.add_hot_cue_bank_mutation_fixture(connection)

        rendered = {
            table: [
                dict(
                    zip(
                        sql[sql.index("(") + 1 : sql.index(")")].split(", "),
                        values,
                    )
                )
                for sql, values in connection.rows
                if f"INSERT INTO {table}" in sql
            ]
            for table in (
                "djmdHotCueBanklist",
                "djmdSongHotCueBanklist",
                "djmdCue",
            )
        }

        self.assertEqual(1, len(rendered["djmdHotCueBanklist"]))
        self.assertEqual(2, len(rendered["djmdSongHotCueBanklist"]))
        self.assertEqual(2, len(rendered["djmdCue"]))
        membership = rendered["djmdSongHotCueBanklist"][0]
        self.assertEqual("9060", membership["HotCueBanklistID"])
        self.assertEqual(1, membership["TrackNo"])
        self.assertEqual("94001", membership["CueID"])
        self.assertEqual(100_001, membership["InMsec"])
        self.assertEqual("", membership["InPointSeekInfo"])
        self.assertEqual(
            ["94001", "94002"],
            [row["CueID"] for row in rendered["djmdSongHotCueBanklist"]],
        )

    def test_legacy_mutation_profile_targets_wire_cue_ordinal_four(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        connection = RecordingConnection()
        build_fixture.add_hot_cue_bank_mutation_fixture(
            connection, track_no=4, relation_ids=(94_101, 94_102)
        )
        rows = [
            dict(
                zip(
                    sql[sql.index("(") + 1 : sql.index(")")].split(", "), values
                )
            )
            for sql, values in connection.rows
            if "INSERT INTO djmdSongHotCueBanklist" in sql
        ]

        self.assertEqual([4, 4], [row["TrackNo"] for row in rows])
        self.assertEqual(["94101", "94102"], [row["CueID"] for row in rows])

    def test_legacy_ordinal_profile_has_duplicate_d_e_f_rows(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        connection = RecordingConnection()
        build_fixture.add_hot_cue_bank_legacy_ordinal_fixture(connection)
        rows = [
            dict(
                zip(
                    sql[sql.index("(") + 1 : sql.index(")")].split(", "), values
                )
            )
            for sql, values in connection.rows
            if "INSERT INTO djmdSongHotCueBanklist" in sql
        ]
        banks = [
            sql for sql, _ in connection.rows if "INSERT INTO djmdHotCueBanklist" in sql
        ]

        self.assertEqual(1, len(banks))
        self.assertEqual([4, 4, 5, 5, 6, 6], [row["TrackNo"] for row in rows])
        self.assertEqual(
            ["10001", "10001", "10002", "10002", "10003", "10003"],
            [row["ContentID"] for row in rows],
        )
        self.assertEqual(
            ["94201", "94202", "94203", "94204", "94205", "94206"],
            [row["CueID"] for row in rows],
        )

    def test_legacy_ordinal_boundary_profile_pairs_every_target(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        connection = RecordingConnection()
        build_fixture.add_hot_cue_bank_legacy_ordinal_boundary_fixture(connection)
        rows = [
            dict(
                zip(
                    sql[sql.index("(") + 1 : sql.index(")")].split(", "), values
                )
            )
            for sql, values in connection.rows
            if "INSERT INTO djmdSongHotCueBanklist" in sql
        ]
        banks = [
            sql for sql, _ in connection.rows if "INSERT INTO djmdHotCueBanklist" in sql
        ]

        expected = [0, 1, 2, 3, 7, 8, 255, 256, 32_767, 32_768, 65_535]
        self.assertEqual(1, len(banks))
        self.assertEqual(22, len(rows))
        self.assertEqual(
            [ordinal for ordinal in expected for _ in range(2)],
            [row["TrackNo"] for row in rows],
        )
        self.assertEqual(
            [str(94_301 + index) for index in range(22)],
            [row["CueID"] for row in rows],
        )

    def test_deleted_bank_member_profile_keeps_relation_and_cue_live(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, sql, values=()) -> None:
                if sql.startswith("INSERT INTO"):
                    self.rows.append((sql, values))

        connection = RecordingConnection()
        build_fixture.add_deleted_hot_cue_bank_member(connection)
        rendered = {
            table: [
                dict(
                    zip(
                        sql[sql.index("(") + 1 : sql.index(")")].split(", "),
                        values,
                    )
                )
                for sql, values in connection.rows
                if f"INSERT INTO {table}" in sql
            ]
            for table in ("djmdSongHotCueBanklist", "djmdCue")
        }

        self.assertEqual(1, len(rendered["djmdSongHotCueBanklist"]))
        membership = rendered["djmdSongHotCueBanklist"][0]
        self.assertEqual("9031", membership["HotCueBanklistID"])
        self.assertEqual("10005", membership["ContentID"])
        self.assertEqual(1, membership["TrackNo"])
        self.assertEqual("191450", membership["CueID"])
        self.assertNotIn("rb_local_deleted", membership)
        self.assertEqual("191450", rendered["djmdCue"][0]["ID"])
        self.assertNotIn("rb_local_deleted", rendered["djmdCue"][0])


class LinkVisibilityFixtureProfileTests(unittest.TestCase):
    def test_profile_covers_protocol_and_boundary_paths(self) -> None:
        tracks = build_fixture.link_visibility_tracks()

        self.assertEqual(14, len(tracks))
        self.assertEqual(
            [
                "Z:/tracks/link-export-fixture/local-z.wav",
                "soundcloud:tracks:fixture-2",
                "beatport:tracks:fixture-3",
                "beatsource:tracks:fixture-4",
                "tidal:tracks:fixture-5",
                "spotify:track:fixture-6",
                "apple-music:tracks:fixture-7",
                "unknown:tracks:fixture-8",
                "SOUNDCLOUD:TRACKS:fixture-9",
                "Z:/tracks/soundcloud:tracks:fixture-10.wav",
                "soundcloudish:tracks:fixture-11",
                "",
                None,
                "C:/tracks/link-export-fixture/local-c.wav",
            ],
            [track["FolderPath"] for track in tracks],
        )

    def test_provider_path_profile_covers_beatport_substring_boundaries(self) -> None:
        tracks = build_fixture.streaming_provider_path_tracks()

        self.assertEqual(10, len(tracks))
        self.assertEqual(
            [
                "Z:/tracks/link-export-fixture/provider-local.wav",
                "/v4/catalog/tracks/11002",
                "https://api.beatport.com/v4/catalog/tracks/11003",
                "prefix/v4/catalog/tracks/11004/suffix",
                "/V4/CATALOG/TRACKS/11005",
                "/v4/catalog/tracks",
                "/v4/catalog/track/11007",
                "beatport:tracks:11008",
                "beatsource:tracks:11009",
                "x/v4/catalog/tracksish/11010",
            ],
            [track["FolderPath"] for track in tracks],
        )
        self.assertEqual(
            [11002, 11003, 11004],
            [
                int(track["ID"])
                for track in tracks
                if "/v4/catalog/tracks/" in str(track["FolderPath"])
            ],
        )


class ScalarBoundaryFixtureProfileTests(unittest.TestCase):
    def test_profile_places_values_outside_advertised_scalar_roots(self) -> None:
        tracks = build_fixture.scalar_boundary_tracks()

        self.assertEqual(8, len(tracks))
        self.assertEqual("0", tracks[0]["ColorID"])
        self.assertEqual("999999", tracks[1]["ColorID"])
        self.assertEqual(99, tracks[2]["Rating"])
        self.assertEqual(2_147_483_647, tracks[3]["BitRate"])


class BpmToleranceFixtureProfileTests(unittest.TestCase):
    def test_profile_brackets_every_percentage_edge(self) -> None:
        tracks = build_fixture.bpm_tolerance_tracks()
        bpms = [track["BPM"] for track in tracks]

        self.assertEqual(43, len(tracks))
        self.assertEqual(sorted(set(bpms)), bpms)
        self.assertEqual(
            list(range(50_001, 50_044)),
            [int(track["ID"]) for track in tracks],
        )
        self.assertTrue(
            {11_949, 11_950, 11_951, 12_000, 12_048, 12_049, 12_050}.issubset(
                bpms
            )
        )

        for percent in range(1, 7):
            lower = 12_000 * (100 - percent) // 100
            upper = 12_000 * (100 + percent) // 100
            with self.subTest(percent=percent):
                self.assertTrue(
                    {
                        lower - 1,
                        lower,
                        lower + 1,
                        upper - 1,
                        upper,
                        upper + 1,
                    }.issubset(bpms)
                )


class SmartPlaylistFixtureProfileTests(unittest.TestCase):
    def test_key_notation_profile_uses_distinct_database_spellings(self) -> None:
        self.assertEqual(
            {
                build_fixture.IDS["key.am"]: "08A",
                build_fixture.IDS["key.c"]: "08B",
            },
            build_fixture.KEY_NOTATION_SCALE_NAMES,
        )

    def test_profile_distinguishes_rules_from_materialized_membership(self) -> None:
        class RecordingConnection:
            def __init__(self) -> None:
                self.rows = []

            def execute(self, _sql, values) -> None:
                self.rows.append(values)

        connection = RecordingConnection()
        build_fixture.add_smart_playlist_relations(connection)

        playlists = [row for row in connection.rows if len(row) == 9]
        memberships = [row for row in connection.rows if len(row) == 7]

        self.assertEqual(5, len(playlists))
        self.assertEqual([4, 4, 4, 0, 4], [row[3] for row in playlists])
        self.assertIn('ValueLeft="Fixture House"', playlists[0][5])
        self.assertEqual("<not-valid-smart-list", playlists[2][5])
        self.assertIsNone(playlists[4][5])
        self.assertEqual(6, len(memberships))
        self.assertEqual(
            [
                str(build_fixture.IDS["track.second"]),
                str(build_fixture.IDS["track.fourth"]),
                str(build_fixture.IDS["track.third"]),
                str(build_fixture.IDS["track.fifth"]),
                str(build_fixture.IDS["track.sixth"]),
                str(build_fixture.IDS["track.eighth"]),
            ],
            [row[2] for row in memberships],
        )

    def test_rule_matrix_covers_operators_logic_and_parser_boundaries(self) -> None:
        rules = dict(build_fixture.smart_rule_matrix())

        self.assertEqual(39, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_RULE_MATRIX_NAMES),
            list(rules),
        )
        for operator in range(1, 12):
            self.assertIn(
                f'PropertyName="genre" Operator="{operator}"',
                rules[f"genre_operator_{operator:02}"],
            )
            self.assertIn(
                f'PropertyName="bpm" Operator="{operator}"',
                rules[f"bpm_operator_{operator:02}"],
            )

        self.assertEqual(2, rules["nested_all"].count("<NODE"))
        self.assertEqual(2, rules["nested_any"].count("<NODE"))
        self.assertNotIn("LogicalOperator", rules["missing_logical_operator"])
        self.assertNotIn("AutomaticUpdate", rules["missing_automatic_update"])
        self.assertNotIn("Id=", rules["missing_id"])

    def test_xml_matrix_covers_document_element_and_attribute_boundaries(self) -> None:
        rules = dict(build_fixture.smart_xml_matrix())

        self.assertEqual(73, len(rules))
        self.assertEqual(list(build_fixture.SMART_XML_MATRIX_NAMES), list(rules))
        self.assertTrue(rules["xml_declaration"].startswith("<?xml"))
        self.assertIn("<ROOT><NODE", rules["wrapper_root"])
        self.assertEqual(2, rules["nested_node_only"].count("<NODE"))
        self.assertEqual(2, rules["two_roots_house_then_techno"].count("<NODE"))
        self.assertIn('LogicalOperator="1" LogicalOperator="2"', rules["duplicate_logical_one_then_two"])
        self.assertIn('Operator="1" Operator="2"', rules["duplicate_operator_one_then_two"])
        self.assertIn("\0junk", rules["valid_root_then_nul_junk"])

    def test_numeric_matrix_covers_scales_ranges_and_invalid_values(self) -> None:
        rules = dict(build_fixture.smart_numeric_matrix())

        self.assertEqual(60, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_NUMERIC_MATRIX_NAMES),
            list(rules),
        )
        for name, (property_name, target, low, high) in (
            build_fixture.SMART_NUMERIC_PROPERTIES.items()
        ):
            self.assertIn(
                f'PropertyName="{property_name}" Operator="1"',
                rules[f"{name}_operator_01"],
            )
            self.assertIn(f'ValueLeft="{target}"', rules[f"{name}_operator_01"])
            self.assertIn(f'ValueLeft="{low}"', rules[f"{name}_operator_05"])
            self.assertIn(f'ValueRight="{high}"', rules[f"{name}_operator_05"])
            self.assertIn(f'ValueLeft="{high}"', rules[f"{name}_reversed_range"])
            self.assertIn('ValueLeft=""', rules[f"{name}_empty_equal"])
            self.assertIn(
                'ValueLeft="not-a-number"',
                rules[f"{name}_invalid_not_equal"],
            )

        self.assertIn('ValueLeft="-1"', rules["bpm_negative_equal"])
        self.assertIn('ValueLeft="2147483648"', rules["bpm_overflow_equal"])

    def test_numeric_boundary_matrix_covers_storage_and_missing_attributes(self) -> None:
        tracks = build_fixture.smart_numeric_boundary_tracks()
        rules = dict(build_fixture.smart_numeric_boundary_matrix())

        self.assertEqual(10, len(tracks))
        self.assertEqual(
            [value for _name, value in build_fixture.SMART_NUMERIC_BOUNDARY_TRACKS],
            [track["BPM"] for track in tracks],
        )
        self.assertEqual(100, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_NUMERIC_BOUNDARY_NAMES),
            list(rules),
        )
        for name, property_name in (
            build_fixture.SMART_NUMERIC_BOUNDARY_PROPERTIES.items()
        ):
            self.assertIn(
                f'PropertyName="{property_name}" Operator="1"',
                rules[f"{name}_equal_half"],
            )
            self.assertIn('ValueLeft="0.5"', rules[f"{name}_equal_half"])
            self.assertNotIn('ValueLeft=', rules[f"{name}_missing_left_equal"])
            self.assertNotIn('ValueRight=', rules[f"{name}_range_missing_right"])
            self.assertNotIn('ValueLeft=', rules[f"{name}_range_both_missing"])
            self.assertNotIn('ValueRight=', rules[f"{name}_range_both_missing"])

    def test_property_matrix_covers_written_vocabulary_and_alias_controls(self) -> None:
        tracks = build_fixture.smart_property_tracks()
        rules = dict(build_fixture.smart_property_matrix())

        self.assertEqual(8, len(tracks))
        self.assertEqual(33, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_PROPERTY_MATRIX_NAMES),
            list(rules),
        )
        self.assertEqual("Mix 04", tracks[3]["Subtitle"])
        self.assertEqual("2025-01-04", tracks[3]["DateCreated"])
        self.assertTrue(str(tracks[3]["created_at"]).startswith("2030-03-04"))
        self.assertIn('PropertyName="albumArtist"', rules["album_artist"])
        self.assertIn('PropertyName="remixedBy"', rules["remixed_by"])
        self.assertIn('PropertyName="myTag" Operator="8"', rules["my_tag_warmup_signed"])
        self.assertIn(str(build_fixture.IDS["mytag.warmup"] - 2**32), rules["my_tag_warmup_signed"])
        self.assertIn('PropertyName="filename"', rules["alias_filename_lowercase"])

    def test_date_matrix_covers_comparisons_ranges_and_invalid_values(self) -> None:
        tracks = build_fixture.smart_date_tracks()
        rules = dict(build_fixture.smart_date_matrix())

        self.assertEqual(8, len(tracks))
        self.assertEqual(30, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_DATE_MATRIX_NAMES),
            list(rules),
        )
        self.assertEqual("2024-02-29", tracks[1]["StockDate"])
        self.assertEqual("2024-02-29", tracks[1]["DateCreated"])
        self.assertEqual("2024-02-29", tracks[1]["ReleaseDate"])
        self.assertEqual("", tracks[6]["StockDate"])
        self.assertEqual("not-a-date", tracks[7]["StockDate"])
        for name, property_name in build_fixture.SMART_DATE_PROPERTIES.items():
            self.assertIn(
                f'PropertyName="{property_name}" Operator="1"',
                rules[f"{name}_operator_01"],
            )
            self.assertIn('ValueLeft="2024-02-29"', rules[f"{name}_operator_05"])
            self.assertIn('ValueRight="2025-02-28"', rules[f"{name}_operator_05"])
            self.assertIn(
                'ValueLeft="2025-02-28"', rules[f"{name}_reversed_range"]
            )
            self.assertIn('ValueLeft=""', rules[f"{name}_blank_equal"])
            self.assertIn(
                'ValueLeft="not-a-date"', rules[f"{name}_invalid_not_equal"]
            )

    def test_relative_date_matrix_covers_units_counts_and_clock_boundaries(self) -> None:
        tracks = build_fixture.smart_relative_date_tracks()
        rules = dict(build_fixture.smart_relative_date_matrix())

        self.assertEqual(10, len(tracks))
        self.assertEqual(56, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_RELATIVE_DATE_MATRIX_NAMES),
            list(rules),
        )
        self.assertEqual(
            [
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
            ],
            [row["StockDate"] for row in tracks],
        )
        for name, property_name in build_fixture.SMART_RELATIVE_DATE_PROPERTIES.items():
            for unit in build_fixture.SMART_RELATIVE_DATE_UNITS:
                for operator in (6, 7):
                    rule = rules[f"{name}_{unit}_operator_{operator:02}"]
                    self.assertIn(f'PropertyName="{property_name}"', rule)
                    self.assertIn(f'Operator="{operator}"', rule)
                    self.assertIn(f'ValueUnit="{unit}"', rule)
        self.assertIn(
            'ValueUnit="fortnight"', rules["stock_date_unit_unknown_operator_06"]
        )
        self.assertIn('ValueUnit="MONTH"', rules["stock_date_unit_uppercase_month_operator_06"])
        self.assertIn('ValueUnit="months"', rules["stock_date_unit_months_operator_07"])
        self.assertIn('ValueLeft="1.5"', rules["stock_date_count_fractional_operator_07"])
        self.assertIn('ValueLeft="31"', rules["stock_date_count_thirty_one_operator_06"])
        self.assertIn('ValueUnit="month"', rules["stock_date_month_count_two_operator_06"])
        self.assertIn('ValueRight="31"', rules["stock_date_right_31_operator_07"])

    def test_date_format_matrix_covers_parser_and_calendar_boundaries(self) -> None:
        tracks = build_fixture.smart_date_format_tracks()
        rules = dict(build_fixture.smart_date_format_matrix())

        self.assertEqual(40, len(tracks))
        self.assertEqual(117, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_DATE_FORMAT_MATRIX_NAMES),
            list(rules),
        )
        self.assertEqual("2025/01/31", tracks[6]["StockDate"])
        self.assertEqual("2025\n01\n31", tracks[11]["DateCreated"])
        self.assertEqual("2025-0\x00-31", tracks[-2]["ReleaseDate"])
        self.assertIsNone(tracks[-1]["StockDate"])
        for name, property_name in build_fixture.SMART_DATE_FORMAT_PROPERTIES.items():
            self.assertIn(
                f'PropertyName="{property_name}" Operator="1"',
                rules[f"{name}_canonical_jan_31_equal"],
            )
            self.assertIn(
                'ValueLeft="2025/01/31"',
                rules[f"{name}_separator_slash_equal"],
            )
            self.assertIn(
                f'PropertyName="{property_name}" Operator="2"',
                rules[f"{name}_canonical_not_equal"],
            )

    def test_text_matrix_covers_collation_and_string_boundaries(self) -> None:
        tracks = build_fixture.smart_text_tracks()
        rules = dict(build_fixture.smart_text_matrix())

        self.assertEqual(43, len(tracks))
        self.assertEqual(55, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_TEXT_MATRIX_NAMES),
            list(rules),
        )
        self.assertEqual("A\u0301lpha", tracks[3]["Commnt"])
        self.assertEqual("Alpha\x00Tail", tracks[11]["Commnt"])
        self.assertIsNone(tracks[10]["Commnt"])
        self.assertIn('Operator="9"', rules["alpha_operator_09"])
        self.assertIn('ValueLeft="&amp;"', rules["ampersand_contains"])
        self.assertIn('&quot;Beta&quot;', rules["double_quote_equal"])
        self.assertIn('&apos;Beta&apos;', rules["apostrophe_equal"])

    def test_string_property_matrix_crosses_every_text_database_path(self) -> None:
        tracks = build_fixture.smart_string_property_tracks()
        rules = dict(build_fixture.smart_string_property_matrix())

        self.assertEqual(10, len(tracks))
        self.assertEqual(104, len(rules))
        self.assertEqual(
            list(build_fixture.SMART_STRING_PROPERTY_MATRIX_NAMES),
            list(rules),
        )
        self.assertEqual("A\u0301lpha", tracks[3]["Title"])
        self.assertEqual("", tracks[8]["Commnt"])
        self.assertIsNone(tracks[9]["FileNameL"])
        self.assertEqual("0", tracks[9]["ArtistID"])
        for name, property_name in build_fixture.SMART_STRING_PROPERTIES.items():
            self.assertIn(
                f'PropertyName="{property_name}" Operator="1"',
                rules[f"{name}_alpha_equal"],
            )
            self.assertIn(
                f'PropertyName="{property_name}" Operator="9"',
                rules[f"{name}_alpha_not_contains"],
            )
            self.assertIn('ValueLeft=""', rules[f"{name}_empty_equal"])

    def test_mytag_matrix_covers_operators_boundaries_and_boolean_logic(self) -> None:
        tracks = build_fixture.smart_mytag_tracks()
        rules = dict(build_fixture.smart_mytag_matrix())

        self.assertEqual(8, len(tracks))
        self.assertEqual(49, len(rules))
        self.assertEqual(list(build_fixture.SMART_MYTAG_MATRIX_NAMES), list(rules))
        for operator in range(1, 12):
            self.assertIn(
                f'PropertyName="myTag" Operator="{operator}"',
                rules[f"operator_{operator:02}"],
            )
        self.assertIn('ValueLeft="4294967295"', rules["uint32_max_operator_08"])
        self.assertIn('ValueLeft="-1"', rules["minus_one_operator_09"])
        self.assertIn('ValueLeft=""', rules["blank_operator_08"])
        self.assertIn(
            'LogicalOperator="2"', rules["any_contains_one_high_bit"]
        )


class SearchCeilingFixtureProfileTests(unittest.TestCase):
    def test_profile_crosses_the_search_wrapper_limit(self) -> None:
        tracks = build_fixture.search_ceiling_tracks()

        self.assertEqual(1_005, len(tracks))
        self.assertEqual(["20001", "21000", "21001", "21005"], [
            tracks[index]["ID"] for index in (0, 999, 1000, 1004)
        ])
        self.assertEqual(
            [
                "Ceiling Match 0001",
                "Ceiling Match 1000",
                "Ceiling Match 1001",
                "Ceiling Match 1005",
            ],
            [tracks[index]["Title"] for index in (0, 999, 1000, 1004)],
        )
        self.assertTrue(all("CEILING" in row["SearchStr"] for row in tracks))
        self.assertTrue(all("ceiling" not in row["FileNameL"] for row in tracks))
        self.assertTrue(all(int(row["ID"]) <= 100_000 for row in tracks))

    def test_search_track_profile_crosses_the_new_command_limit(self) -> None:
        tracks = build_fixture.search_ceiling_tracks(5_005)

        self.assertEqual(5_005, len(tracks))
        self.assertEqual(["25000", "25001", "25005"], [
            tracks[index]["ID"] for index in (4_999, 5_000, 5_004)
        ])
        self.assertEqual(
            [
                "Ceiling Match 5000",
                "Ceiling Match 5001",
                "Ceiling Match 5005",
            ],
            [tracks[index]["Title"] for index in (4_999, 5_000, 5_004)],
        )

    def test_large_search_track_profile_has_cache_independent_sort_tokens(self) -> None:
        tracks = build_fixture.search_track_large_tracks()

        self.assertEqual(10_005, len(tracks))
        self.assertEqual("Ceiling Match 10005", tracks[-1]["Title"])
        for sort_id in range(18):
            token = f"SORT{sort_id:02}"
            self.assertTrue(all(token in row["SearchStr"] for row in tracks))

    def test_large_title_profile_places_tokens_in_a_searched_field(self) -> None:
        tracks = build_fixture.search_track_large_title_tracks()

        self.assertEqual(10_005, len(tracks))
        for sort_id in range(18):
            token = f"SORT{sort_id:02}"
            self.assertTrue(all(token in row["Title"] for row in tracks))
        self.assertEqual(tracks[-1]["Title"].upper(), tracks[-1]["SearchStr"])


class SearchTextFixtureProfileTests(unittest.TestCase):
    def test_profile_distinguishes_unicode_representations(self) -> None:
        tracks = build_fixture.search_text_tracks()

        self.assertEqual(
            [
                "Precomposed Éclair",
                "Precomposed éclair",
                "Combining E\u0301clair",
                "Combining e\u0301clair",
                "Emoji 🙂 Search",
                "Emoji 🙃 Search",
                "Sharp ß Search",
                "Dotted İ Search",
            ],
            [row["Title"] for row in tracks],
        )
        self.assertEqual([18, 18, 17, 17, 15, 15, 14, 15], [
            utf16_units(row["Title"]) for row in tracks
        ])
        self.assertTrue(all("fixture" not in row["FileNameL"] for row in tracks))
        self.assertTrue(all(row["SearchStr"] == row["Title"] for row in tracks))


class FilenameBoundaryFixtureProfileTests(unittest.TestCase):
    def test_profile_isolates_long_name_short_name_and_path_inputs(self) -> None:
        tracks = build_fixture.filename_boundary_tracks()

        self.assertEqual(20, len(tracks))
        self.assertIsNone(tracks[0]["FileNameL"])
        self.assertEqual("", tracks[1]["FileNameL"])
        self.assertEqual("nul\0suffix.wav", tracks[11]["FileNameL"])
        self.assertEqual("C:\\embedded\\name.wav", tracks[12]["FileNameL"])
        self.assertEqual("dir/name.wav", tracks[13]["FileNameL"])
        self.assertEqual(
            [254, 255, 256, 254, 255, 256],
            [utf16_units(row["FileNameL"]) for row in tracks[14:]],
        )
        self.assertTrue(
            all(row["FileNameL"] != row["FileNameS"] for row in tracks[2:])
        )
        self.assertTrue(
            all(
                f"path-source-{index:02}.mp3" in row["FolderPath"]
                for index, row in enumerate(tracks, start=1)
            )
        )


if __name__ == "__main__":
    unittest.main()
