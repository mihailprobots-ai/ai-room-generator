from __future__ import annotations

from collections import deque

from .config import TILE_WALL


def build_blocked_grid(room: dict) -> list[list[bool]]:
    width = room["width"]
    height = room["height"]
    blocked = [[False for _ in range(width)] for _ in range(height)]
    for obj in room.get("objects", []):
        if obj["type"] != "wall":
            continue
        for y in range(obj["y"], obj["y"] + obj["h"]):
            for x in range(obj["x"], obj["x"] + obj["w"]):
                if 0 <= x < width and 0 <= y < height:
                    blocked[y][x] = True
    return blocked


def flood_fill(room: dict, start: tuple[int, int]) -> set[tuple[int, int]]:
    width = room["width"]
    height = room["height"]
    blocked = build_blocked_grid(room)
    sx, sy = start
    if not (0 <= sx < width and 0 <= sy < height) or blocked[sy][sx]:
        return set()

    seen = {(sx, sy)}
    queue: deque[tuple[int, int]] = deque([(sx, sy)])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            if blocked[ny][nx] or (nx, ny) in seen:
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))
    return seen


def object_cells(obj: dict) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y in range(obj["y"], obj["y"] + obj["h"])
        for x in range(obj["x"], obj["x"] + obj["w"])
    }


def first_door_cell(room: dict) -> tuple[int, int] | None:
    for obj in room.get("objects", []):
        if obj["type"] == "door":
            return obj["x"], obj["y"] + obj["h"] - 1
    return None


def reachable_ratio(room: dict) -> float:
    start = first_door_cell(room)
    if start is None:
        return 0.0
    visited = flood_fill(room, start)
    blocked = build_blocked_grid(room)
    total_open = sum(1 for row in blocked for cell in row if not cell)
    return len(visited) / total_open if total_open else 0.0

