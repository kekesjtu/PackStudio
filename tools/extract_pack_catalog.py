"""Extract the standalone PACK preset/material catalog without exporting FloXML."""

import argparse
import hashlib
import json
from pathlib import Path

from tools.pack_catalog_builder import write_materials, write_presets
from tools.pack_native import FAMILIES
from tools.pack_native_details import DetailedNativePack
from tools.pack_native_materials import read_builtin_materials


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    parser.add_argument("--output", type=Path, default=Path("default_parameters"))
    arguments = parser.parse_args()
    native = DetailedNativePack(arguments.installation)
    root = native.installation / "flocentral/flopack"
    source_records = {}
    snapshots = []
    for family in FAMILIES:
        source = json.loads((Path("default_parameters/flotherm") / f"{family}.json")
                            .read_text(encoding="utf-8"))
        source_records.update({(family, p["id"]): p for p in source["records"]})
        paths = sorted((root / family).glob("*.des"))
        for path in paths:
            reference = source_records[(family, path.stem)]
            if hashlib.sha256(path.read_bytes()).hexdigest() != reference["source_sha256"]:
                raise ValueError(f"DES source changed: {path}")
            record = {"family": family, "preset": path.stem,
                      "groups": native.snapshot(path), "wizard": native.wizard}
            if family in {"chip_array", "pbga_wb"}:
                record["four_layer"] = {"family": family, "preset": path.stem,
                                        "groups": native.snapshot(path, True),
                                        "wizard": native.wizard}
            snapshots.append(record)
        print(f"{family}: {len(paths)} presets", flush=True)
    if len(snapshots) != 342:
        raise ValueError("the reviewed source catalog must contain exactly 342 presets")
    materials = read_builtin_materials(native)
    names = write_materials(arguments.output, materials)
    write_presets(arguments.output, snapshots, source_records, names)
    print(f"saved {len(snapshots)} presets and {len(materials)} materials", flush=True)


if __name__ == "__main__":
    main()
