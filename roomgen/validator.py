from __future__ import annotations

from pathlib import Path

from .config import ALLOWED_TYPES, DECOR_SIZES
from .pathfinding import first_door_cell, flood_fill, object_cells, reachable_ratio
from .renderer import read_png_rgb, validate_png_colors
from .schemas import normalize_type


def validate_room(room: dict) -> list[str]:
    errors: list[str] = []
    width = room.get("width")
    height = room.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        return ["Room width and height must be integers"]
    if width < 8 or height < 8:
        errors.append("Room dimensions must be at least 8x8")
    if width > 512 or height > 512:
        errors.append("Room dimensions must not exceed 512x512")

    occupancy: dict[tuple[int, int], str] = {}
    doors = 0
    ladders = 0
    platforms = 0
    for index, obj in enumerate(room.get("objects", [])):
        obj_type = obj.get("type")
        if obj_type not in {"wall", "platform", "ladder", "door", "decor", "enemy"}:
            errors.append(f"Object {index} has unknown type: {obj_type}")
            continue
        x, y, w, h = (obj.get("x"), obj.get("y"), obj.get("w"), obj.get("h"))
        if not all(isinstance(value, int) for value in (x, y, w, h)):
            errors.append(f"Object {index} coordinates must be integers")
            continue
        if w < 1 or h < 1:
            errors.append(f"Object {index} has non-positive size")
        if x < 0 or y < 0 or x + w > width or y + h > height:
            errors.append(f"Object {index} is out of bounds")

        if obj_type == "platform":
            platforms += 1
            if h != 1:
                errors.append(f"Platform {index} height must be 1")
        elif obj_type == "ladder":
            ladders += 1
            if w != 1:
                errors.append(f"Ladder {index} width must be 1")
        elif obj_type == "door":
            doors += 1
            if w != 1 or h != 3:
                errors.append(f"Door {index} must be exactly 1x3")
        elif obj_type == "decor":
            if (w, h) not in DECOR_SIZES:
                errors.append(f"Decor {index} has unsupported size {w}x{h}")
        elif obj_type == "enemy":
            if w != 1 or h != 1:
                errors.append(f"Enemy {index} must be exactly 1x1")

        for cell in object_cells(obj):
            if cell in occupancy and not (obj_type == "wall" and occupancy[cell] == "wall"):
                errors.append(f"Object {index} collides at {cell} with {occupancy[cell]}")
            occupancy[cell] = obj_type

    if doors < 1:
        errors.append("Room must have at least one door")
    if platforms < 1:
        errors.append("Room must have at least one platform")
    if ladders < 1:
        errors.append("Room must have at least one ladder")

    start = first_door_cell(room)
    if start is None:
        errors.append("No door cell for pathfinding")
    else:
        reachable = reachable_ratio(room)
        if reachable < 0.96:
            errors.append(f"Only {reachable:.1%} of open cells are reachable")
        visited = flood_fill(room, start)
        for obj in room.get("objects", []):
            if obj["type"] in {"door", "ladder", "enemy"}:
                if not object_cells(obj) & visited:
                    errors.append(f"{obj['type']} at {obj['x']},{obj['y']} is isolated")

    return errors


def validate_png(path: Path, room: dict | None = None) -> list[str]:
    errors = validate_png_colors(path)
    width, height, _ = read_png_rgb(path)
    if room is not None:
        if width != room["width"] or height != room["height"]:
            errors.append(f"PNG dimensions {width}x{height} do not match room {room['width']}x{room['height']}")
    return errors


def validate_output_dir(path: Path) -> dict:
    rooms = sorted(path.glob("room_*.json"))
    report = {"checked": 0, "valid": 0, "invalid": 0, "rooms": []}
    for json_path in rooms:
        if json_path.name == "generation_report.json":
            continue
        import json

        room = json.loads(json_path.read_text(encoding="utf-8"))
        png_path = json_path.with_suffix(".png")
        errors = validate_room(room)
        if png_path.exists():
            errors.extend(validate_png(png_path, room))
        else:
            errors.append(f"Missing PNG: {png_path.name}")
        valid = not errors
        report["checked"] += 1
        report["valid" if valid else "invalid"] += 1
        report["rooms"].append({"room": json_path.name, "valid": valid, "errors": errors})
    return report

