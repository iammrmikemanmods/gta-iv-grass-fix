#!/usr/bin/env python3
"""Normalize and harden a PE32 ASI without external dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


IMAGE_FILE_RELOCS_STRIPPED = 0x0001
IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040
IMAGE_DLLCHARACTERISTICS_NX_COMPAT = 0x0100


def pe_checksum(data: bytearray, checksum_offset: int) -> int:
    total = 0
    for index in range(0, len(data), 2):
        if checksum_offset <= index < checksum_offset + 4:
            word = 0
        elif index + 1 < len(data):
            word = data[index] | (data[index + 1] << 8)
        else:
            word = data[index]
        total += word
        total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    return (total + len(data)) & 0xFFFFFFFF


def harden(source: Path, destination: Path) -> dict[str, object]:
    data = bytearray(source.read_bytes())
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ValueError("not a DOS/PE image")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if pe > len(data) - 24 or data[pe : pe + 4] != b"PE\0\0":
        raise ValueError("not a PE image")
    machine, _, _, _, _, optional_size, characteristics = struct.unpack_from(
        "<HHIIIHH", data, pe + 4
    )
    optional = pe + 24
    if machine != 0x014C or optional_size < 224 or optional + optional_size > len(data):
        raise ValueError("not a complete i386 PE32 image")
    if struct.unpack_from("<H", data, optional)[0] != 0x010B:
        raise ValueError("not PE32")
    if characteristics & IMAGE_FILE_RELOCS_STRIPPED:
        raise ValueError("relocations are stripped; DYNAMIC_BASE would be unsafe")
    directory_count = struct.unpack_from("<I", data, optional + 92)[0]
    if directory_count <= 5:
        raise ValueError("base-relocation directory is unavailable")
    relocation_rva, relocation_size = struct.unpack_from(
        "<II", data, optional + 96 + 5 * 8
    )
    if relocation_rva == 0 or relocation_size < 8:
        raise ValueError("base-relocation directory is empty")

    timestamp_before = struct.unpack_from("<I", data, pe + 8)[0]
    checksum_offset = optional + 64
    flags_offset = optional + 70
    flags_before = struct.unpack_from("<H", data, flags_offset)[0]
    flags_after = flags_before | IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE | IMAGE_DLLCHARACTERISTICS_NX_COMPAT

    # Normalize the only volatile linker field used by this pipeline.
    struct.pack_into("<I", data, pe + 8, 0)
    struct.pack_into("<H", data, flags_offset, flags_after)
    struct.pack_into("<I", data, checksum_offset, 0)
    checksum = pe_checksum(data, checksum_offset)
    struct.pack_into("<I", data, checksum_offset, checksum)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    verify = bytearray(destination.read_bytes())
    stored = struct.unpack_from("<I", verify, checksum_offset)[0]
    struct.pack_into("<I", verify, checksum_offset, 0)
    calculated = pe_checksum(verify, checksum_offset)
    if stored != calculated:
        raise RuntimeError("stored PE checksum does not verify")

    return {
        "schema": 1,
        "source": str(source),
        "destination": str(destination),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
        "coff_timestamp_before": timestamp_before,
        "coff_timestamp_after": 0,
        "dll_characteristics_before": f"0x{flags_before:04X}",
        "dll_characteristics_after": f"0x{flags_after:04X}",
        "dynamic_base": bool(flags_after & IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE),
        "nx_compat": bool(flags_after & IMAGE_DLLCHARACTERISTICS_NX_COMPAT),
        "base_relocation_rva": f"0x{relocation_rva:08X}",
        "base_relocation_size": relocation_size,
        "checksum": f"0x{checksum:08X}",
        "checksum_valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = harden(args.source, args.destination)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
