from __future__ import annotations

import argparse
from pathlib import Path

from roomgen.config import DENSITIES, DIFFICULTIES, LAYOUT_TYPES, GenerationParams
from roomgen.generator import generate_rooms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate pixel-perfect game room PNG maps.")
    parser.add_argument("--rooms", type=int, default=20)
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--height", type=int, default=40)
    parser.add_argument("--doors", type=int, default=2)
    parser.add_argument("--enemies", type=int, default=5)
    parser.add_argument("--difficulty", choices=DIFFICULTIES, default="medium")
    parser.add_argument("--platform-density", choices=DENSITIES, default="medium")
    parser.add_argument("--decor-density", choices=DENSITIES, default="medium")
    parser.add_argument("--layout-type", choices=LAYOUT_TYPES, default="industrial")
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--output", default="output")
    parser.add_argument("--use-ai", action="store_true", help="Reserved for optional OpenAI structured design flow.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    params = GenerationParams(
        width=args.width,
        height=args.height,
        doors=args.doors,
        enemies=args.enemies,
        difficulty=args.difficulty,
        platform_density=args.platform_density,
        decor_density=args.decor_density,
        layout_type=args.layout_type,
        number_of_rooms=args.rooms,
        seed=args.seed,
        use_ai=args.use_ai,
    )
    report = generate_rooms(params, Path(args.output))
    print(
        "generated={generated} valid={valid} invalid={invalid} retries={retries} avg_time={average_generation_time}s".format(
            **report
        )
    )
    if report["invalid"]:
        print(f"Generation finished with {report['invalid']} invalid room(s). See {args.output}/generation_report.json")
        return 1
    print(f"Output saved to {args.output}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

