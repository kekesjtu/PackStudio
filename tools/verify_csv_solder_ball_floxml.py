"""Verify arbitrary-coordinate CSV maps against actual native solder-ball geometry."""

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.csv_solder_ball_probes import DEFAULT_OUTPUT, MAP_ROWS, saved_map
from tools.floxml_validation.native_suite import read_des
from tools.infer_chip_array_bond_wires_floxml import provenance
from tools.solder_ball_array_probes import FAMILIES, ROOT
from tools.verify_solder_ball_arrays_floxml import (
    compare_group,
    expected_positions,
    predicted_cells,
)


def verify_case(directory, definition):
    identifier = definition["id"]
    xml = directory / "native" / f"{identifier}.xml"
    saved = xml.with_suffix(".des")
    values = read_des(saved)
    assert all(values.get(k) == v for k, v in definition["des_changes"].items())
    rows = saved_map(saved)
    expected_rows = [(n, round(x, 6), round(y, 6)) for n, x, y in definition["map_rows"]]
    assert rows == expected_rows
    root = ET.parse(xml).getroot()
    if values["csvBGA"] == "CHECKED":
        main_expected = {name: (x, y) for name, x, y in rows}
        center_expected = {}
    else:
        cells, central = predicted_cells(values)
        main_expected = expected_positions(
            cells, int(values["MD"]), int(values["ME"]), float(values["e"]), "solder_ball"
        )
        center_expected = expected_positions(
            central, int(values["MDc"]), int(values["MEc"]), float(values["e"]), "center_sball"
        )
    main = compare_group(root, "Solder_ball", main_expected, values)
    center = compare_group(root, "Center_SBall", center_expected, values)
    centers = set(map(tuple, main["centers_xy_mm"])) | set(map(tuple, center["centers_xy_mm"]))
    return {
        "id": identifier,
        "sources": [
            provenance(xml),
            provenance(saved),
            provenance(directory / "inputs" / f"{identifier}.des"),
        ],
        "inputs": {k: values[k] for k in definition["des_changes"]},
        "saved_map_rows": rows,
        "main": main,
        "center": center,
        "entity_count": main["count"] + center["count"],
        "unique_center_count": len(centers),
        "passed": True,
    }


def verify(archive, output):
    ui = ROOT / "flotherm_pack_data/validation/csv_ball_map_2026-10-25/ui"
    seed = ui / "ui-seed.des"
    assert saved_map(seed) == MAP_ROWS
    baseline_run_file = archive / "baselines/run.json"
    baseline_run = json.loads(baseline_run_file.read_text(encoding="utf-8"))
    assert baseline_run["exit_code"] == 0 and not baseline_run["errors"]
    assert set(baseline_run["exports"]) == set(FAMILIES)
    for family, digest in baseline_run["exports"].items():
        assert provenance(archive / "baselines" / f"{family}.xml")["sha256"] == digest
    families = {}
    for family in FAMILIES:
        directory = archive / family
        definition_file = directory / "definitions.json"
        definitions = json.loads(definition_file.read_text(encoding="utf-8"))
        run_file = directory / "native/run.json"
        run = json.loads(run_file.read_text(encoding="utf-8"))
        assert run["exit_code"] == 0 and not run["errors"]
        assert len(run["exports"]) == len(definitions)
        for identifier, digest in run["exports"].items():
            assert provenance(directory / "native" / f"{identifier}.xml")["sha256"] == digest
        cases = [verify_case(directory, case) for case in definitions]
        families[family] = {
            "sources": [
                provenance(definition_file),
                provenance(run_file),
                provenance(directory / "native/replay.xml"),
            ],
            "native_execution": run,
            "cases": cases,
        }
    reference = families["chip_array"]["cases"]
    for family in FAMILIES[1:]:
        for a, b in zip(reference, families[family]["cases"], strict=True):
            assert a["id"] == b["id"]
            for group in ("main", "center"):
                assert a[group]["centers_xy_mm"] == b[group]["centers_xy_mm"]
    summary = {
        "family_count": len(families),
        "cases_per_family": len(reference),
        "new_probe_exports": sum(len(f["cases"]) for f in families.values()),
        "new_baseline_exports": len(baseline_run["exports"]),
        "all_passed": True,
        "cross_family_positions_identical": True,
        "max_error_mm": max(
            c[g]["max_error_mm"]
            for f in families.values()
            for c in f["cases"]
            for g in ("main", "center")
        ),
    }
    report = {
        "date": "2026-10-25",
        "scope": "Four BGA families, nonempty arbitrary-coordinate maps",
        "evidence": "CSV imported through the actual PACK editor, saved DES var2 payload, "
        "fresh native FloXML and saved DES readback. No native calculation probes.",
        "ui_import_sources": [provenance(ui / "sample.csv"), provenance(seed)],
        "baseline_native_execution": baseline_run,
        "baseline_sources": [
            provenance(baseline_run_file),
            provenance(archive / "baselines/replay.xml"),
        ],
        "csv_source": provenance(archive / "nonempty-map.csv"),
        "summary": summary,
        "families": families,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/validation/csv_solder_ball_map_floxml_2026-10-25.json",
    )
    args = parser.parse_args()
    verify(args.archive.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
