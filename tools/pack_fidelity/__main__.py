"""Capture native DES/FloXML with replayable inputs and content fingerprints."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from tools.floscript.environment import INSTALLATION
from tools.floscript.runner import replay
from tools.pack_fidelity.advanced import cases as advanced_cases
from tools.pack_fidelity.cases import cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    inputs = cases()
    result = replay(INSTALLATION, inputs, args.output.resolve(), timeout=120)
    if result["status"] != "success":
        raise SystemExit(json.dumps(result["errors"], ensure_ascii=False))
    extra_inputs = args.output / "inputs"
    extra = advanced_cases(args.output, extra_inputs)
    extra_output = args.output / "advanced"
    extra_run = replay(INSTALLATION, extra, extra_output.resolve(), timeout=120)
    if extra_run["status"] != "success":
        raise SystemExit(json.dumps(extra_run["errors"], ensure_ascii=False))
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.archive, "w", ZIP_DEFLATED) as archive:
        archive.writestr("cases.json", json.dumps(inputs + extra, ensure_ascii=False, indent=2))
        for name in ("run.json", "replay.xml", "runtime.json"):
            archive.write(args.output / name, name)
        for case in inputs:
            for extension in (".xml", ".des"):
                name = case["id"] + extension
                archive.write(args.output / name, name)
        for name in ("run.json", "replay.xml"):
            archive.write(extra_output / name, "advanced-" + name)
        for case in extra:
            archive.write(extra_inputs / case["input_des"], "inputs/" + case["input_des"])
            for extension in (".xml", ".des"):
                name = case["id"] + extension
                archive.write(extra_output / name, name)
    print(f"{len(inputs) + len(extra)} native cases: {args.archive}")


if __name__ == "__main__":
    main()
