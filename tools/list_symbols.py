#!/usr/bin/env python3
"""List address-bearing symbols from one architecture of a Mach-O binary."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import lief


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("pattern", help="regular expression matched against symbol names")
    parser.add_argument("--architecture", choices=("x86_64", "arm64"), default="x86_64")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    cpu_type = {
        "x86_64": lief.MachO.Header.CPU_TYPE.X86_64,
        "arm64": lief.MachO.Header.CPU_TYPE.ARM64,
    }[args.architecture]
    fat = lief.MachO.parse(str(args.binary))
    binary = next(item for item in fat if item.header.cpu_type == cpu_type)
    expression = re.compile(args.pattern)

    matches = sorted({
        (symbol.value, symbol.name)
        for symbol in binary.symbols
        if symbol.value and expression.search(symbol.name)
    })
    if not matches:
        raise SystemExit(f"no symbols match {args.pattern!r}")

    rendered = "".join(f"{address:#x}\t{name}\n" for address, name in matches)
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
