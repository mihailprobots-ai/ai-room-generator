from __future__ import annotations

import json
import random
import time
from pathlib import Path

from .config import (
    DENSITIES,
    DIFFICULTIES,
    LAYOUT_TYPES,
    GenerationParams,
    density_value,
)
from .renderer import write_png
from .validator import validate_png, validate_room


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _rand_segment(rng: random.Random, width: int, min_w: int = 6, max_w: int = 18) -> tuple[int, int]:
    w = rng.randint(min_w, max(min_w, min(max_w, width - 6)))
    x = rng.randint(2, max(2, width - w - 2))
    return x, w


def _occupied(room: dict) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for obj in room["objects"]:
        for y in range(obj["y"], obj["y"] + obj["h"]):
            for x in range(obj["x"], obj["x"] + obj["w"]):
                cells.add((x, y))
    return cells


def _add_if_free(room: dict, obj: dict) -> bool:
    occupied = _occupied(room)
    cells = {
        (x, y)
        for y in range(obj["y"], obj["y"] + obj["h"])
        for x in range(obj["x"], obj["x"] + obj["w"])
    }
    if cells & occupied:
        return False
    room["objects"].append(obj)
    return True


def _support_lines(room: dict) -> list[tuple[int, int, int]]:
    supports = []
    floor_y = room["height"] - 2
    supports.append((1, room["width"] - 2, floor_y))
    for obj in room["objects"]:
        if obj["type"] == "platform":
            supports.append((obj["x"], obj["x"] + obj["w"] - 1, obj["y"]))
    return supports


def generate_room(params: GenerationParams, room_id: int, seed: int) -> dict:
    rng = random.Random(seed)
    width = _clamp(params.width, 16, 512)
    height = _clamp(params.height, 12, 512)
    layout = params.layout_type if params.layout_type in LAYOUT_TYPES else rng.choice(LAYOUT_TYPES)
    floor_y = height - 2

    room = {
        "room_id": room_id,
        "width": width,
        "height": height,
        "seed": seed,
        "layout_type": layout,
        "objects": [],
    }

    # Outer shell leaves playable interior and deterministic door space.
    room["objects"].extend(
        [
            {"type": "wall", "x": 0, "y": floor_y, "w": width, "h": 2},
            {"type": "wall", "x": 0, "y": 0, "w": 1, "h": height},
            {"type": "wall", "x": width - 1, "y": 0, "w": 1, "h": height},
        ]
    )
    if layout != "open":
        for _ in range(rng.randint(2, 5)):
            x, w = _rand_segment(rng, width, 5, 16)
            h = rng.randint(1, 3)
            room["objects"].append({"type": "wall", "x": x, "y": 0, "w": w, "h": h})

    door_count = _clamp(params.doors, 1, 6)
    door_positions = [(1, floor_y - 3), (width - 2, floor_y - 3)]
    for index in range(door_count):
        if index < 2:
            x, y = door_positions[index]
        else:
            x = rng.randint(4, width - 5)
            y = floor_y - 3
        _add_if_free(room, {"type": "door", "x": x, "y": y, "w": 1, "h": 3})

    base_platforms = density_value(params.platform_density, 3, 6, 10)
    if layout == "platform-heavy":
        base_platforms += 4
    if layout == "open":
        base_platforms = max(2, base_platforms - 3)
    if layout == "vertical":
        base_platforms += 2
    min_y = 5
    max_y = max(min_y, floor_y - 4)
    levels = sorted({rng.randint(min_y, max_y) for _ in range(base_platforms)})
    for y in levels:
        x, w = _rand_segment(rng, width, 7, 20 if layout != "compact" else 12)
        _add_if_free(room, {"type": "platform", "x": x, "y": y, "w": w, "h": 1})

    platforms = [obj for obj in room["objects"] if obj["type"] == "platform"]
    platforms.sort(key=lambda item: item["y"], reverse=True)
    ladder_budget = max(1, min(len(platforms), density_value(params.platform_density, 2, 4, 7)))
    if layout == "ladder-heavy":
        ladder_budget += 3
    previous_y = floor_y
    for platform in platforms[:ladder_budget]:
        x = rng.randint(platform["x"], platform["x"] + platform["w"] - 1)
        y1 = platform["y"] + 1
        y2 = previous_y - 1
        if y2 >= y1:
            _add_if_free(room, {"type": "ladder", "x": x, "y": y1, "w": 1, "h": y2 - y1 + 1})
        previous_y = platform["y"]
    if not any(obj["type"] == "ladder" for obj in room["objects"]):
        target = platforms[0] if platforms else {"x": width // 2, "y": floor_y - 6, "w": 8}
        _add_if_free(
            room,
            {"type": "ladder", "x": target["x"], "y": target["y"] + 1, "w": 1, "h": floor_y - target["y"] - 1},
        )

    decor_count = density_value(params.decor_density, 3, 8, 14)
    decor_sizes = [(1, 1), (1, 2), (2, 1), (2, 2), (3, 3), (4, 3)]
    supports = _support_lines(room)
    for _ in range(decor_count):
        w, h = rng.choice(decor_sizes)
        sx1, sx2, sy = rng.choice(supports)
        if sx2 - sx1 + 1 < w:
            continue
        x = rng.randint(sx1, sx2 - w + 1)
        y = sy - h
        if y <= 0:
            continue
        _add_if_free(room, {"type": "decor", "x": x, "y": y, "w": w, "h": h})

    enemy_count = _clamp(params.enemies, 0, 50)
    if params.difficulty == "hard":
        enemy_count += 2
    elif params.difficulty == "easy":
        enemy_count = max(0, enemy_count - 2)
    supports = _support_lines(room)
    for _ in range(enemy_count):
        sx1, sx2, sy = rng.choice(supports)
        x = rng.randint(sx1, sx2)
        y = sy - 1
        _add_if_free(room, {"type": "enemy", "x": x, "y": y, "w": 1, "h": 1})

    return room


def auto_fix_room(room: dict) -> dict:
    """Small deterministic repair pass used before failing a generated room."""
    fixed = dict(room)
    fixed["objects"] = []
    occupied: set[tuple[int, int]] = set()
    for obj in room.get("objects", []):
        if obj["x"] < 0 or obj["y"] < 0 or obj["x"] + obj["w"] > room["width"] or obj["y"] + obj["h"] > room["height"]:
            continue
        cells = {
            (x, y)
            for y in range(obj["y"], obj["y"] + obj["h"])
            for x in range(obj["x"], obj["x"] + obj["w"])
        }
        if cells & occupied:
            continue
        fixed["objects"].append(obj)
        occupied |= cells
    return fixed


def generate_rooms(params: GenerationParams, output_dir: Path, max_retries: int = 3) -> dict:
    start_all = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    rooms = []
    generated = valid = invalid = retries = 0
    estimated_api_cost = 0.0 if not params.use_ai else None

    for room_id in range(1, params.number_of_rooms + 1):
        room_start = time.perf_counter()
        room = None
        errors: list[str] = []
        retry_count = 0
        for attempt in range(max_retries + 1):
            seed = params.seed + room_id * 1009 + attempt * 9176
            candidate = generate_room(params, room_id, seed)
            candidate = auto_fix_room(candidate)
            errors = validate_room(candidate)
            retry_count = attempt
            if not errors:
                room = candidate
                break
        generated += 1
        retries += retry_count

        room_record = {
            "room_id": room_id,
            "valid": False,
            "validation_errors": errors,
            "retry_count": retry_count,
            "generation_time": round(time.perf_counter() - room_start, 4),
            "estimated_api_cost": estimated_api_cost,
            "parameters": params.__dict__,
        }

        if room is None:
            invalid += 1
            rooms.append(room_record)
            continue

        png_path = output_dir / f"room_{room_id:03d}.png"
        json_path = output_dir / f"room_{room_id:03d}.json"
        json_path.write_text(json.dumps(room, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_png(png_path, room)
        png_errors = validate_png(png_path, room)
        room_record["validation_errors"] = png_errors
        room_record["valid"] = not png_errors
        if png_errors:
            invalid += 1
        else:
            valid += 1
        rooms.append(room_record)

    report = {
        "generated": generated,
        "valid": valid,
        "invalid": invalid,
        "retries": retries,
        "average_generation_time": round((time.perf_counter() - start_all) / max(1, generated), 4),
        "estimated_openai_cost": estimated_api_cost,
        "parameters": params.__dict__,
        "rooms": rooms,
    }
    (output_dir / "generation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report

