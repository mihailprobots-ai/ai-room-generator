from __future__ import annotations

import argparse
import json
from pathlib import Path

from roomgen.validator import validate_output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated room JSON and PNG files.")
    parser.add_argument("path", nargs="?", default="output")
    args = parser.parse_args()
    report = validate_output_dir(Path(args.path))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["invalid"] == 0 and report["checked"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

