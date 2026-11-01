"""Extract research snapshots and materials to an explicit scratch directory."""

import argparse
from pathlib import Path

from tools.pack_reference.catalog import write_materials, write_presets
from tools.pack_reference.des import source_record
from tools.pack_reference.materials import read_builtin_materials
from tools.pack_reference.native import FAMILIES
from tools.pack_reference.native_details import DetailedNativePack


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    runtime = Path(__file__).resolve().parents[2] / "runtime_data"
    if arguments.output.resolve().is_relative_to(runtime.resolve()):
        parser.error("native research snapshots must be outside runtime_data")
    native = DetailedNativePack(arguments.installation)
    root = native.installation / "flocentral/flopack"
    source_records = {}
    snapshots = []
    for family in FAMILIES:
        paths = sorted((root / family).glob("*.des"))
        for path in paths:
            source_records[(family, path.stem)] = source_record(path, native.installation)
            record = {
                "family": family,
                "preset": path.stem,
                "groups": native.snapshot(path),
                "wizard": native.wizard,
            }
            if family in {"chip_array", "pbga_wb"}:
                record["four_layer"] = {
                    "family": family,
                    "preset": path.stem,
                    "groups": native.snapshot(path, True),
                    "wizard": native.wizard,
                }
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
