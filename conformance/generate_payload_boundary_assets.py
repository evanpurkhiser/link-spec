#!/usr/bin/env python3
"""Generate deterministic artwork and ANLZ parser-boundary asset profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path

import generate_payload_assets as baseline


ROOT = Path(__file__).resolve().parent
BASE_ASSETS = ROOT / "payload-assets/generated"
OUTPUT = ROOT / "payload-assets/boundaries"

VARIANTS = (
    {"name": "jpeg-bytes-1048576", "family": "artwork", "axis": "jpeg_bytes", "value": 1_048_576},
    {"name": "jpeg-bytes-1048577", "family": "artwork", "axis": "jpeg_bytes", "value": 1_048_577},
    {"name": "jpeg-width-800", "family": "artwork", "axis": "jpeg_width", "value": 800},
    {"name": "jpeg-width-801", "family": "artwork", "axis": "jpeg_width", "value": 801},
    {"name": "jpeg-height-800", "family": "artwork", "axis": "jpeg_height", "value": 800},
    {"name": "jpeg-height-801", "family": "artwork", "axis": "jpeg_height", "value": 801},
    {"name": "pqtz-count-6248", "family": "pqtz", "axis": "pqtz_count", "value": 6_248},
    {"name": "pqtz-count-6249", "family": "pqtz", "axis": "pqtz_count", "value": 6_249},
    {"name": "pwav-count-399", "family": "preview", "axis": "pwav_count", "value": 399},
    {"name": "pwav-count-400", "family": "preview", "axis": "pwav_count", "value": 400},
    {"name": "pwav-count-401", "family": "preview", "axis": "pwav_count", "value": 401},
    {"name": "pwv2-count-99", "family": "preview", "axis": "pwv2_count", "value": 99},
    {"name": "pwv2-count-100", "family": "preview", "axis": "pwv2_count", "value": 100},
    {"name": "pwv2-count-101", "family": "preview", "axis": "pwv2_count", "value": 101},
    {"name": "pvbr-words-399", "family": "pvbr", "axis": "pvbr_words", "value": 399},
    {"name": "pvbr-words-400", "family": "pvbr", "axis": "pvbr_words", "value": 400},
    {"name": "pvbr-words-401", "family": "pvbr", "axis": "pvbr_words", "value": 401},
    {"name": "pwv3-count-0", "family": "pwv3", "axis": "pwv3_count", "value": 0},
    {"name": "pwv3-count-1", "family": "pwv3", "axis": "pwv3_count", "value": 1},
    {"name": "pwv3-count-65535", "family": "pwv3", "axis": "pwv3_count", "value": 65_535},
    {"name": "pwv3-stride-0", "family": "pwv3", "axis": "pwv3_stride", "value": 0},
    {"name": "pwv3-stride-2", "family": "pwv3", "axis": "pwv3_stride", "value": 2},
    {"name": "pkey-count-0", "family": "pkey", "axis": "pkey_count", "value": 0},
    {"name": "pkey-count-1", "family": "pkey", "axis": "pkey_count", "value": 1},
    {"name": "pkey-count-65535", "family": "pkey", "axis": "pkey_count", "value": 65_535},
    {"name": "pkey-stride-0", "family": "pkey", "axis": "pkey_stride", "value": 0},
    {"name": "pkey-stride-11", "family": "pkey", "axis": "pkey_stride", "value": 11},
    {"name": "pkey-stride-13", "family": "pkey", "axis": "pkey_stride", "value": 13},
    {"name": "atom-duplicate-aligned", "family": "atom", "axis": "atom_layout", "value": "aligned"},
    {"name": "atom-duplicate-unaligned", "family": "atom", "axis": "atom_layout", "value": "unaligned"},
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jpeg(width: int, height: int) -> bytes:
    pixels = bytes(width * height * 3)
    ppm = f"P6\n{width} {height}\n255\n".encode() + pixels
    result = subprocess.run(
        ["cjpeg", "-quality", "90", "-optimize"],
        input=ppm,
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def padded_jpeg(size: int) -> bytes:
    data = jpeg(8, 8)
    if len(data) > size:
        raise ValueError(f"JPEG is larger than requested boundary size {size}")
    return data + bytes(size - len(data))


def dat_file(
    *,
    pvbr_words: int = 401,
    pqtz_count: int = 4,
    pwav_count: int = 400,
    pwv2_count: int = 100,
) -> bytes:
    vbr = b"".join(struct.pack(">I", value * 4096) for value in range(pvbr_words))
    beats = b"".join(
        struct.pack(">HHI", (index % 4) + 1, 12_000, index * 500)
        for index in range(pqtz_count)
    )
    loud = bytes((index % 25) | ((index % 8) << 5) for index in range(pwav_count))
    dot = bytes((index % 15) | ((7 - index % 8) << 5) for index in range(pwv2_count))
    return baseline.pmai(
        baseline.path_section(),
        baseline.section(b"PVBR", struct.pack(">I", 0), vbr),
        baseline.section(b"PQTZ", struct.pack(">III", 0, 0x00080000, pqtz_count), beats),
        baseline.section(b"PWAV", struct.pack(">II", pwav_count, 0), loud),
        baseline.section(b"PWV2", struct.pack(">II", pwv2_count, 0), dot),
    )


def ext_file(
    *,
    pwv3_count: int = 15,
    pwv3_stride: int = 1,
    pkey_count: int = 2,
    pkey_stride: int = 12,
) -> bytes:
    detailed_length = max(1, pwv3_count * pwv3_stride)
    detailed = bytes((index * 7) & 0xFF for index in range(detailed_length))
    key_length = max(12, pkey_count * pkey_stride)
    keys = bytes((index * 13) & 0xFF for index in range(key_length))
    return baseline.pmai(
        baseline.path_section(),
        baseline.section(
            b"PWV3",
            struct.pack(">III", pwv3_stride, pwv3_count, 150 << 16),
            detailed,
        ),
        baseline.section(
            b"PKEY",
            struct.pack(">HHHH", 0, pkey_stride, pkey_count, 0),
            keys,
        ),
    )


def duplicate_atom_file(layout: str) -> bytes:
    body_lengths = (44, 44) if layout == "aligned" else (45, 47)
    atoms = tuple(
        baseline.section(
            b"PWV7",
            struct.pack(">III", 3, body_length // 3, 150 << 16),
            bytes((atom * 31 + index * 11) & 0xFF for index in range(body_length)),
        )
        for atom, body_length in enumerate(body_lengths)
    )
    return baseline.pmai(baseline.path_section(), *atoms)


def write_manifest(directory: Path, specification: dict) -> dict:
    assets = [
        {
            "path": path.relative_to(directory).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    ]
    manifest = {
        "format": 1,
        "scope": "deterministic Link Export payload parser boundary assets",
        "variant": specification["name"],
        "family": specification["family"],
        "axis": specification["axis"],
        "value": specification["value"],
        "generator_sha256": sha256(Path(__file__)),
        "baseline_manifest_sha256": sha256(BASE_ASSETS / "manifest.json"),
        "database_paths": {
            "artwork": baseline.ARTWORK_PATH,
            "analysis": baseline.ANALYSIS_PATH,
        },
        "assets": assets,
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def generate(output: Path) -> dict:
    if shutil.which("cjpeg") is None:
        raise RuntimeError("cjpeg is required to generate JPEG boundary assets")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    entries = []
    for specification in VARIANTS:
        directory = output / specification["name"]
        shutil.copytree(BASE_ASSETS / "PIONEER", directory / "PIONEER")
        artwork = directory / baseline.ARTWORK_PATH.lstrip("/")
        analysis = directory / baseline.ANALYSIS_PATH.lstrip("/")
        axis = specification["axis"]
        value = specification["value"]

        if axis == "jpeg_bytes":
            artwork.write_bytes(padded_jpeg(value))
        elif axis == "jpeg_width":
            artwork.write_bytes(jpeg(value, 8))
        elif axis == "jpeg_height":
            artwork.write_bytes(jpeg(8, value))
        elif axis in {"pqtz_count", "pwav_count", "pwv2_count", "pvbr_words"}:
            analysis.write_bytes(dat_file(**{axis: value}))
        elif axis in {"pwv3_count", "pwv3_stride", "pkey_count", "pkey_stride"}:
            analysis.with_suffix(".EXT").write_bytes(ext_file(**{axis: value}))
        elif axis == "atom_layout":
            analysis.with_suffix(".2EX").write_bytes(duplicate_atom_file(value))
        else:
            raise ValueError(f"unhandled boundary axis: {axis}")

        manifest = write_manifest(directory, specification)
        entries.append(
            {
                **specification,
                "case_count": {"artwork": 3, "pqtz": 2, "pwv3": 2, "pkey": 2, "atom": 2}.get(specification["family"], 1),
                "service_count": {"artwork": 2, "pqtz": 2, "pwv3": 2, "pkey": 2, "atom": 2}.get(specification["family"], 1),
                "manifest_sha256": hashlib.sha256(
                    json.dumps(manifest, indent=2).encode() + b"\n"
                ).hexdigest(),
            }
        )

    index = {
        "format": 1,
        "scope": "deterministic Link Export payload parser boundary matrix",
        "generator_sha256": sha256(Path(__file__)),
        "baseline_manifest_sha256": sha256(BASE_ASSETS / "manifest.json"),
        "variant_count": len(entries),
        "variants": entries,
    }
    (output / "manifest.json").write_text(json.dumps(index, indent=2) + "\n")
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    index = generate(args.output)
    print(f"wrote {index['variant_count']} boundary asset profiles beneath {args.output}")


if __name__ == "__main__":
    main()
