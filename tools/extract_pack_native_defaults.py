"""Snapshot PACK parameter objects through its native ABI; no FloSCRIPT or FloXML."""

import argparse
import hashlib
import json
from pathlib import Path

from tools.pack_native import FAMILIES, VERIFIED_BINARIES, NativePack


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preset", help="Inspect one .des stem instead of all 342 records")
    parser.add_argument("--four-layer", action="store_true")
    arguments = parser.parse_args()
    native = NativePack(arguments.installation)
    source_root = native.installation / "flocentral/flopack"
    records = []
    for family in FAMILIES:
        paths = sorted((source_root / family).glob("*.des"))
        for path in paths:
            if arguments.preset and path.stem != arguments.preset:
                continue
            if arguments.four_layer and family not in {"pbga_wb", "chip_array"}:
                continue
            groups = native.snapshot(path, arguments.four_layer)
            records.append(
                {
                    "family": family,
                    "preset": path.stem,
                    "source_path": path.relative_to(native.installation).as_posix(),
                    "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "wizard": "4-Layer" if arguments.four_layer else "native-initialised-defaults",
                    "groups": groups,
                }
            )
        count = sum(item["family"] == family for item in records)
        if count:
            print(f"{family}: {count} snapshots", flush=True)
    if not records:
        raise ValueError("no matching PACK preset")
    payload = {
        "schema_version": "packstudio.pack-native-defaults/v1",
        "method": (
            "loadDESPackage -> initialise wizard -> setWizardData -> getData -> "
            "native property serialization"
        ),
        "binary_sha256": VERIFIED_BINARIES,
        "scope": (
            "Enumerated parameter objects for the recorded wizard branch; "
            "empty/unset values are preserved. Not geometry or material-library validation."
        ),
        "record_count": len(records),
        "records": records,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"saved {len(records)} presets to {arguments.output}")


if __name__ == "__main__":
    main()
