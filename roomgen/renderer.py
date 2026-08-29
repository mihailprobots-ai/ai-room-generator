from __future__ import annotations

import struct
import zlib
from pathlib import Path

from .config import PALETTE, TILE_EMPTY, allowed_rgb_values

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def render_grid(room: dict) -> list[list[tuple[int, int, int]]]:
    width = room["width"]
    height = room["height"]
    grid = [[PALETTE[TILE_EMPTY] for _ in range(width)] for _ in range(height)]
    for obj in room.get("objects", []):
        rgb = PALETTE[obj["type"].upper()]
        for y in range(obj["y"], obj["y"] + obj["h"]):
            for x in range(obj["x"], obj["x"] + obj["w"]):
                if 0 <= x < width and 0 <= y < height:
                    grid[y][x] = rgb
    return grid


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_png(path: Path, room: dict) -> None:
    grid = render_grid(room)
    height = len(grid)
    width = len(grid[0]) if height else 0
    raw = bytearray()
    for row in grid:
        raw.append(0)  # filter type 0; no antialiasing, no interpolation.
        for r, g, b in row:
            raw.extend((r, g, b))

    payload = PNG_SIGNATURE
    payload += _chunk("IHDR".encode(), struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += _chunk("IDAT".encode(), zlib.compress(bytes(raw), level=9))
    payload += _chunk("IEND".encode(), b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def read_png_rgb(path: Path) -> tuple[int, int, list[list[tuple[int, int, int]]]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("Not a PNG file")
    offset = len(PNG_SIGNATURE)
    width = height = None
    idat = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if bit_depth != 8 or color_type != 2 or compression != 0 or filter_method != 0 or interlace != 0:
                raise ValueError("Unsupported PNG format")
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise ValueError("PNG missing IHDR")

    raw = zlib.decompress(bytes(idat))
    stride = width * 3
    rows: list[list[tuple[int, int, int]]] = []
    cursor = 0
    previous = bytearray(stride)
    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        row = bytearray(raw[cursor : cursor + stride])
        cursor += stride
        if filter_type != 0:
            raise ValueError("Only filter type 0 is supported by this validator")
        previous = row
        pixels = [tuple(row[i : i + 3]) for i in range(0, stride, 3)]
        rows.append(pixels)  # type: ignore[arg-type]
    return width, height, rows


def validate_png_colors(path: Path) -> list[str]:
    errors: list[str] = []
    _, _, rows = read_png_rgb(path)
    allowed = allowed_rgb_values()
    found = {pixel for row in rows for pixel in row}
    unknown = sorted(found - allowed)
    if unknown:
        errors.append(f"PNG contains colors outside whitelist: {unknown}")
    return errors

