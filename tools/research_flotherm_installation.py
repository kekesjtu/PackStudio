"""Read-only inventory of installed PACK text presets; never used at runtime."""

import argparse
import hashlib
import json
from collections import Counter
from math import isclose
from pathlib import Path

from packstudio.templates.package_library.catalog import definitions

FAMILIES = {
    "cbga_fc": "flip_chip_cbga",
    "pbga_fc": "flip_chip_pbga",
    "pbga_wb": "wirebond_pbga",
    "chip_array": "fbga_fsbga",
    "QFN": "qfn",
    "pqfp": "qfp_family",
    "tsop_conv": "soic_family",
}


def inventory(installation: Path) -> dict:
    directory = installation / "flocentral" / "flopack"
    if not directory.is_dir():
        raise ValueError(f"PACK preset directory not found: {directory}")
    records = []
    for path in sorted(directory.rglob("*.des")):
        raw = path.read_bytes()
        fields = {}
        for line in raw.decode("utf-8-sig").splitlines():
            if not line:
                continue
            key, delimiter, value = line.partition("|")
            if not delimiter or key in fields:
                raise ValueError(f"malformed or duplicate key in {path}: {line}")
            fields[key] = value
        records.append(
            {
                "path": path.relative_to(installation).as_posix(),
                "family": path.parent.name,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "fields": fields,
            }
        )
    comparisons = []
    for template_id, definition in definitions().items():
        family = next((key for key, value in FAMILIES.items() if value == template_id), None)
        for field in definition.fields:
            for preset in field.presets:
                matches = [
                    record
                    for record in records
                    if record["family"] == family
                    and Path(record["path"]).stem.casefold() == preset.value.casefold()
                ]
                comparisons.append(
                    {
                        "template_id": template_id,
                        "preset": preset.value,
                        "production_values": preset.values,
                        "installed_record": matches[0]["path"] if matches else None,
                        "die_dimension_comparison": (
                            {
                                key: {
                                    "symbol": symbol,
                                    "production": preset.values[key],
                                    "installed": matches[0]["fields"].get(symbol),
                                    "matches": isclose(
                                        float(preset.values[key]),
                                        float(matches[0]["fields"][symbol]),
                                        rel_tol=1e-12,
                                    ),
                                }
                                for key, symbol in (("die.length", "Ld"), ("die.width", "Wd"))
                                if key in preset.values and matches[0]["fields"].get(symbol)
                            }
                            if matches
                            else {}
                        ),
                    }
                )
    schema_path = installation / "WinXP/PlugIns/ECXML_PLUGIN_SCHEMA/ECXML.xsd"
    return {
        "installation": str(installation.resolve()),
        "format": "key|value; empty values are unresolved, not zero",
        "family_counts": dict(sorted(Counter(item["family"] for item in records).items())),
        "record_count": len(records),
        "ecxml_schema_sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
        "production_presets": comparisons,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = inventory(arguments.installation)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"records": report["record_count"], "families": report["family_counts"]}))


if __name__ == "__main__":
    main()
