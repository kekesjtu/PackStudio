"""Capture reproducible native evidence for all four wirebond package families."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from tools.floscript.environment import INSTALLATION
from tools.floscript.runner import replay
from tools.remaining_cases import cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    inputs = cases()
    result = replay(INSTALLATION, inputs, args.output.resolve(), timeout=180)
    if result["status"] != "success":
        raise SystemExit(json.dumps(result["errors"], ensure_ascii=False))
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.archive, "w", ZIP_DEFLATED) as archive:
        archive.writestr("cases.json", json.dumps(inputs, ensure_ascii=False, indent=2))
        for name in ("run.json", "replay.xml", "runtime.json"):
            archive.write(args.output / name, name)
        for case in inputs:
            for extension in (".xml", ".des"):
                name = case["id"] + extension
                archive.write(args.output / name, name)
    print(f"{len(inputs)} native cases: {args.archive}")


if __name__ == "__main__":
    main()
