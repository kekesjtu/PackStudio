"""Reproducible live audit; findings are evidence, not a production behavior change."""

import argparse
import hashlib
from pathlib import Path

from packstudio.preset_catalog import PresetCatalog
from packstudio.templates.package_library.catalog import definitions
from tools.pack_catalog_builder import compiled_branch, write_json
from tools.pack_coupled_probes import coupled_probes
from tools.pack_interaction_archive import corroborate_inert
from tools.pack_interaction_audit import audit_covers, audit_fields
from tools.pack_native import VERIFIED_BINARIES
from tools.pack_native_details import EXTRA_BINARIES
from tools.pack_native_interactions import InteractionNativePack
from tools.pack_project_controls import audit_project_controls


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("docs/validation/pack_interactions.json")
    )
    arguments = parser.parse_args()
    native = InteractionNativePack(arguments.installation)
    native.wizard_choices, native.dataset_edits = {}, {}
    catalog = PresetCatalog()
    baseline = []
    for preset in catalog.list_ids():
        record = catalog.read(preset)
        path = native.installation / record["source"]["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["source"]["sha256"]:
            raise ValueError(f"changed native DES: {preset}")
        for branch in record["branches"]:
            groups = native.snapshot(path, branch == "four_layer")
            actual = compiled_branch(
                {"groups": groups, "wizard": native.wizard, "family": record["family"]}
            )
            baseline.append(
                {
                    "preset": preset,
                    "branch": branch,
                    "matches_catalog": actual == record["branches"][branch],
                }
            )
    print(
        f"catalog branches: {len(baseline)}, differences: "
        f"{sum(not r['matches_catalog'] for r in baseline)}",
        flush=True,
    )
    fields, covers = {}, {}
    for identifier, definition in definitions().items():
        footprint = next(f for f in definition.fields if f.control == "footprint")
        fields[identifier] = audit_fields(native, definition, footprint.default)
        if identifier in {"cbga_fc", "pbga_fc"}:
            covers[identifier] = audit_covers(native, definition, footprint.default)
        inert = [
            r["field"]
            for r in fields[identifier]
            if r.get("model_changed") is False and not r.get("packstudio_error")
        ]
        print(f"{identifier}: {len(fields[identifier])} fields, inert: {inert}", flush=True)
    write_json(
        arguments.output,
        {
            "schema_version": "packstudio.pack-interaction-audit/v1",
            "review_date": "2026-10-12",
            "installation": str(native.installation),
            "binary_sha256": VERIFIED_BINARIES | EXTRA_BINARIES,
            "catalog_branches": baseline,
            "field_probes": fields,
            "cover_probes": covers,
            "coupled_probes": coupled_probes(native),
            "inert_field_archive_corroboration": corroborate_inert(fields),
            "project_controls": audit_project_controls(),
            "limitations": [
                "Native groupValid is a parameter-group check, not full realization validation.",
                "One scalar perturbation per field in an active context; no exhaustive claim.",
                "Native dataset edits use setData; wizard choices use setWizardData before edits.",
                "No native geometry realization, FloXML export, or live GUI notification replay.",
            ],
        },
    )


if __name__ == "__main__":
    main()
