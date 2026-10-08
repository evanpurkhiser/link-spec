#!/usr/bin/env python3
"""Generate deterministic metadata-only assets for payload service tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "payload-assets/source/artwork.ppm"
OUTPUT = ROOT / "payload-assets/generated"
PMAI_EXTRA = bytes.fromhex("00000001000100000001000000000000")
ANALYSIS_PATH = "/PIONEER/USBANLZ/000/deterministic/ANLZ0000.DAT"
ARTWORK_PATH = "/PIONEER/Artwork/000/deterministic/artwork.jpg"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(name: bytes, header: bytes, body: bytes = b"") -> bytes:
    if len(name) != 4:
        raise ValueError("section names must contain four bytes")

    header_length = 12 + len(header)
    return struct.pack(">4sII", name, header_length, header_length + len(body)) + header + body


def pmai(*sections: bytes) -> bytes:
    body = b"".join(sections)
    header_length = 12 + len(PMAI_EXTRA)
    return b"PMAI" + struct.pack(">II", header_length, header_length + len(body)) + PMAI_EXTRA + body


def path_section() -> bytes:
    encoded = ("/Contents/deterministic-fixture.wav\0").encode("utf-16-be")
    return section(b"PPTH", struct.pack(">I", len(encoded)), encoded)


def dat_file() -> bytes:
    vbr = b"".join(struct.pack(">I", value * 4096) for value in range(401))
    beats = b"".join(
        struct.pack(">HHI", beat, 12000, time)
        for beat, time in ((1, 0), (2, 500), (3, 1000), (4, 1500))
    )
    loud = bytes(((index % 25) | ((index % 8) << 5)) for index in range(400))
    dot = bytes(((index % 15) | ((7 - index % 8) << 5)) for index in range(100))
    return pmai(
        path_section(),
        section(b"PVBR", struct.pack(">I", 0), vbr),
        section(b"PQTZ", struct.pack(">III", 0, 0x00080000, 4), beats),
        section(b"PWAV", struct.pack(">II", len(loud), 0), loud),
        section(b"PWV2", struct.pack(">II", len(dot), 0), dot),
    )


def ext_file() -> bytes:
    detailed = bytes((index * 7) & 0xFF for index in range(15))
    keys = (
        struct.pack(">III", 0, 1, 750)
        + struct.pack(">III", 8, 2, 1500)
    )
    return pmai(
        path_section(),
        section(b"PWV3", struct.pack(">III", 1, 15, 150 << 16), detailed),
        section(b"PKEY", struct.pack(">HHHH", 0, 12, 2, 0), keys),
    )


def two_ex_file() -> bytes:
    three_band = bytes((index * 11) & 0xFF for index in range(45))
    return pmai(
        path_section(),
        section(b"PWV7", struct.pack(">III", 3, 15, 150 << 16), three_band),
    )


def write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def generate(output: Path) -> dict:
    cjpeg = shutil.which("cjpeg")
    if cjpeg is None:
        raise RuntimeError("cjpeg is required to generate the JPEG fixture")

    artwork = output / ARTWORK_PATH.lstrip("/")
    artwork.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [cjpeg, "-quality", "90", "-optimize", "-outfile", artwork, SOURCE],
        check=True,
    )

    analysis = output / ANALYSIS_PATH.lstrip("/")
    write(analysis, dat_file())
    write(analysis.with_suffix(".EXT"), ext_file())
    write(analysis.with_suffix(".2EX"), two_ex_file())

    assets = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            assets.append(
                {
                    "path": path.relative_to(output).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )

    manifest = {
        "format": 1,
        "scope": "deterministic metadata-only Link Export payload assets",
        "generator_sha256": sha256(Path(__file__)),
        "source_sha256": sha256(SOURCE),
        "database_paths": {
            "artwork": ARTWORK_PATH,
            "analysis": ANALYSIS_PATH,
        },
        "assets": assets,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    manifest = generate(args.output)
    print(f"wrote {len(manifest['assets'])} assets beneath {args.output}")


if __name__ == "__main__":
    main()
