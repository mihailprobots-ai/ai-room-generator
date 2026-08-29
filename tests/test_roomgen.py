from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from roomgen.config import DECOR_SIZES, GenerationParams
from roomgen.generator import generate_room, generate_rooms
from roomgen.renderer import write_png
from roomgen.validator import validate_output_dir, validate_png, validate_room


class RoomGeneratorTests(unittest.TestCase):
    def make_room(self) -> dict:
        return generate_room(GenerationParams(), room_id=1, seed=123)

    def test_colors_and_png_dimensions(self) -> None:
        room = self.make_room()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "room.png"
            write_png(path, room)
            self.assertEqual(validate_png(path, room), [])

    def test_door_dimensions(self) -> None:
        room = self.make_room()
        doors = [obj for obj in room["objects"] if obj["type"] == "door"]
        self.assertTrue(doors)
        self.assertTrue(all(obj["w"] == 1 and obj["h"] == 3 for obj in doors))

    def test_ladder_dimensions(self) -> None:
        room = self.make_room()
        ladders = [obj for obj in room["objects"] if obj["type"] == "ladder"]
        self.assertTrue(ladders)
        self.assertTrue(all(obj["w"] == 1 and obj["h"] >= 1 for obj in ladders))

    def test_platform_dimensions(self) -> None:
        room = self.make_room()
        platforms = [obj for obj in room["objects"] if obj["type"] == "platform"]
        self.assertTrue(platforms)
        self.assertTrue(all(obj["h"] == 1 and obj["w"] >= 1 for obj in platforms))

    def test_decor_dimensions(self) -> None:
        room = self.make_room()
        decors = [obj for obj in room["objects"] if obj["type"] == "decor"]
        self.assertTrue(all((obj["w"], obj["h"]) in DECOR_SIZES for obj in decors))

    def test_enemy_dimensions(self) -> None:
        room = self.make_room()
        enemies = [obj for obj in room["objects"] if obj["type"] == "enemy"]
        self.assertTrue(all(obj["w"] == 1 and obj["h"] == 1 for obj in enemies))

    def test_bounds_collision_connectivity(self) -> None:
        self.assertEqual(validate_room(self.make_room()), [])

    def test_generate_20_rooms_all_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = generate_rooms(GenerationParams(number_of_rooms=20), Path(tmp))
            self.assertEqual(report["generated"], 20)
            self.assertEqual(report["valid"], 20)
            self.assertEqual(report["invalid"], 0)
            validation = validate_output_dir(Path(tmp))
            self.assertEqual(validation["checked"], 20)
            self.assertEqual(validation["invalid"], 0)


if __name__ == "__main__":
    unittest.main()

