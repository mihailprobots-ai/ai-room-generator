from __future__ import annotations

from dataclasses import dataclass

TILE_EMPTY = "EMPTY"
TILE_WALL = "WALL"
TILE_PLATFORM = "PLATFORM"
TILE_LADDER = "LADDER"
TILE_DOOR = "DOOR"
TILE_DECOR = "DECOR"
TILE_ENEMY = "ENEMY"

ALLOWED_TYPES = {
    TILE_WALL,
    TILE_PLATFORM,
    TILE_LADDER,
    TILE_DOOR,
    TILE_DECOR,
    TILE_ENEMY,
}

# TODO: confirm exact RGB values with the production level constructor.
# This demo palette is centralized intentionally: no colors are hardcoded elsewhere.
PALETTE: dict[str, tuple[int, int, int]] = {
    TILE_EMPTY: (255, 255, 255),
    TILE_WALL: (0, 0, 0),
    TILE_PLATFORM: (79, 184, 255),
    TILE_LADDER: (255, 220, 48),
    TILE_DOOR: (255, 72, 72),
    TILE_DECOR: (255, 150, 170),
    TILE_ENEMY: (220, 30, 30),
}

DECOR_SIZES = {(1, 1), (1, 2), (2, 1), (2, 2), (3, 3), (4, 3)}


@dataclass(frozen=True)
class GenerationParams:
    width: int = 80
    height: int = 40
    doors: int = 2
    enemies: int = 5
    difficulty: str = "medium"
    platform_density: str = "medium"
    decor_density: str = "medium"
    layout_type: str = "industrial"
    number_of_rooms: int = 20
    seed: int = 12345
    use_ai: bool = False


LAYOUT_TYPES = (
    "industrial",
    "vertical",
    "multi-level",
    "open",
    "compact",
    "platform-heavy",
    "ladder-heavy",
)

DIFFICULTIES = ("easy", "medium", "hard")
DENSITIES = ("low", "medium", "high")


def density_value(value: str, low: int, medium: int, high: int) -> int:
    normalized = (value or "medium").lower()
    if normalized == "low":
        return low
    if normalized == "high":
        return high
    return medium


def allowed_rgb_values() -> set[tuple[int, int, int]]:
    return set(PALETTE.values())

