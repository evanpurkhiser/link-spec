def compatibility_exhaustive_cases() -> list[dict[str, object]]:
    cases = [
        {
            "axis": "file-type-byte",
            "file_type": file_type,
            "sample_rate": 44_100,
            "bit_depth": 16,
        }
        for file_type in range(256)
    ]

    for file_type in (
        -2_147_483_648,
        -129,
        -128,
        -1,
        256,
        257,
        261,
        262,
        267,
        268,
        65_535,
        65_536,
        2_147_483_647,
        4_294_967_295,
    ):
        cases.append(
            {
                "axis": "file-type-wide",
                "file_type": file_type,
                "sample_rate": 44_100,
                "bit_depth": 16,
            }
        )

    sample_rates = (
        -2_147_483_648,
        -1,
        0,
        1,
        44_099,
        44_100,
        44_101,
        47_999,
        48_000,
        48_001,
        65_535,
        65_536,
        2_147_483_647,
        4_294_967_295,
    )
    for file_type in (5, 6, 11, 12):
        for sample_rate in sample_rates:
            cases.append(
                {
                    "axis": "sample-rate",
                    "file_type": file_type,
                    "sample_rate": sample_rate,
                    "bit_depth": 16,
                }
            )

    bit_depths = (
        -2_147_483_648,
        -1,
        0,
        1,
        8,
        16,
        24,
        32,
        255,
        256,
        32_767,
        32_768,
        65_535,
        4_294_967_295,
    )
    for file_type, sample_rate in (
        (1, 44_100),
        (5, 44_100),
        (11, 44_100),
        (11, 48_001),
    ):
        for bit_depth in bit_depths:
            cases.append(
                {
                    "axis": "bit-depth",
                    "file_type": file_type,
                    "sample_rate": sample_rate,
                    "bit_depth": bit_depth,
                }
            )

    for index, case in enumerate(cases, start=1):
        raw_file_type = int(case["file_type"]) & 0xFF
        raw_sample_rate = int(case["sample_rate"]) & 0xFFFFFFFF
        case["id"] = 60_000 + index
        case["supported"] = raw_file_type not in (5, 6) and (
            raw_file_type not in (11, 12)
            or raw_sample_rate in (44_100, 48_000)
        )

    return cases
