from __future__ import annotations

from typing import Any


def room_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["room_id", "width", "height", "seed", "layout_type", "objects"],
        "properties": {
            "room_id": {"type": "integer", "minimum": 1},
            "width": {"type": "integer", "minimum": 8, "maximum": 512},
            "height": {"type": "integer", "minimum": 8, "maximum": 512},
            "seed": {"type": "integer"},
            "layout_type": {"type": "string"},
            "objects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["type", "x", "y", "w", "h"],
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["wall", "platform", "ladder", "door", "decor", "enemy"],
                        },
                        "x": {"type": "integer", "minimum": 0},
                        "y": {"type": "integer", "minimum": 0},
                        "w": {"type": "integer", "minimum": 1},
                        "h": {"type": "integer", "minimum": 1},
                    },
                },
            },
        },
    }


def normalize_type(value: str) -> str:
    return value.strip().upper().replace("-", "_")


def semantic_type(value: str) -> str:
    return value.strip().lower()

