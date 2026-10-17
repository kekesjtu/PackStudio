"""Explicit archived input mappings plus native replay probes of exposed branches."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

from packstudio.templates.package_library.catalog import catalog
from packstudio.templates.package_library.core.materials import production_materials
from tests.backend.templates.reference_cover_cases import cover_numeric_cases
from tests.backend.templates.reference_requests import reference_request
from tests.backend.templates.reference_variation_fidelity import FIELD_PROPERTIES

ROOT = Path(__file__).resolve().parents[2]
REFERENCES = ROOT / "flotherm_pack_data/templates"


def base_commands(template):
    root = ET.parse(REFERENCES / template / "baseline/script.xml").getroot()
    return [ET.tostring(e, encoding="unicode") for e in root if e.tag == "new_package"]


def archived_cases():
    for template in (item["id"] for item in catalog()):
        yield {
            "id": f"{template}-baseline",
            "template": template,
            "kind": "baseline",
            "request": reference_request(template),
            "native": REFERENCES / template / "baseline/model.xml",
            "source": REFERENCES / template / "baseline/params.json",
        }
        manifest_path = REFERENCES / template / "xml_variations.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        fields = {prop: field for field, prop in FIELD_PROPERTIES[template].items()}
        for item in manifest["variations"]:
            target = item["target"]
            changes = None
            if (
                item["kind"] == "numeric_parameter"
                and item["comparison_baseline"] == "baseline/model.xml"
                and target["property"] in fields
            ):
                changes = {fields[target["property"]]: target["value"]}
            if target["property"] == "topCover" and target["value"] in {
                "lid",
                "plate",
                "encapsulant",
            }:
                changes = {"cover.type": target["value"]}
            if changes is not None:
                yield {
                    "id": f"{template}-{item['variation_id']}",
                    "template": template,
                    "kind": item["kind"],
                    "request": reference_request(template, changes),
                    "native": REFERENCES / template / item["artifacts"]["model"],
                    "source": REFERENCES / template / item["artifacts"]["config"],
                }
    for parameter in cover_numeric_cases():
        template, overrides, path = parameter.values
        yield {
            "id": f"{template}-cover-{path.parent.name}",
            "template": template,
            "kind": "cover_numeric",
            "request": reference_request(template, overrides),
            "native": path,
            "source": path.with_name("config.json"),
        }


def fresh_cases(directory):
    cases = []
    for item in catalog():
        template = item["id"]
        cases.append(
            {
                "id": f"fresh-{template}",
                "template": template,
                "kind": "fresh_baseline",
                "request": reference_request(template),
                "commands": base_commands(template),
            }
        )
    # Values are explicit; native component/property paths come from archived probes.
    probes = [
        (
            "qfp-negative",
            "pqfp",
            {"flag.downset": 0.44},
            [("dieFlagAndTieBars", "dieFlagDownsetDdf", 0.44)],
        ),
        (
            "qfp-small-height",
            "pqfp",
            {"flag.downset": 0.384},
            [("dieFlagAndTieBars", "dieFlagDownsetDdf", 0.384)],
        ),
        (
            "qfp-rectangle",
            "pqfp",
            {"body.length": 8, "flag.coverage": 50},
            [
                ("encapsulant", "lengthD1", 8),
                ("dieFlagAndTieBars", "metalCoverageForDieFlagCf", 50),
            ],
        ),
        (
            "wb-copper-asymmetry",
            "pbga_wb",
            {"trace.top_thickness": 0.01, "trace.bottom_thickness": 0.04},
            [
                ("packageSubstrate", "topSignalLayerThickness", 0.01),
                ("packageSubstrate", "bottomSignalLayerThickness", 0.04),
            ],
        ),
        (
            "chip-attach-thick",
            "chip_array",
            {"die.attach": 0.2},
            [("die", "dieAttachThicknessTda", 0.2)],
        ),
        ("sop-attach-thick", "sop", {"die.attach": 0.2}, [("die", "dieAttachThicknessTda", 0.2)]),
        (
            "qfp-count-33",
            "pqfp",
            {"bond_wire.count": 33},
            [("bondWires", "numberOfBondWiresN", 33)],
        ),
    ]
    for identifier, template, changes, modifications in probes:
        commands = base_commands(template)
        # Copper thickness is a wizard input, not an editable component property.
        if identifier == "wb-copper-asymmetry":
            wizard = ET.fromstring(commands[0])
            for element in wizard:
                if element.get("property_name") == "topSignalLayerThickness":
                    element.set("new_value", "0.01")
                if element.get("property_name") == "bottomSignalLayerThickness":
                    element.set("new_value", "0.04")
            commands = [ET.tostring(wizard, encoding="unicode")]
            modifications = []
        commands.extend(
            ET.tostring(
                ET.Element(
                    "modify_component", name=group, property_name=prop, new_value=str(value)
                ),
                encoding="unicode",
            )
            for group, prop, value in modifications
        )
        cases.append(
            {
                "id": identifier,
                "template": template,
                "kind": "combination_or_boundary",
                "request": reference_request(template, changes),
                "commands": commands,
            }
        )
    for template in ["pqfp", "sop", "pbga_wb", "qfn"]:
        material = production_materials()["gold"]
        custom = material.model_copy(
            update={
                "conductivity": material.conductivity.model_copy(update=dict.fromkeys("xyz", 200.0))
            }
        )
        request = reference_request(template).model_copy(update={"custom_materials": [custom]})
        cases.append(
            {
                "id": f"{template}-gold-edit",
                "template": template,
                "kind": "coupled_material_edit",
                "request": request,
                "native_custom_material": custom,
                "des_changes": {"k_wire" if template == "pbga_wb" else "k_bw": "AuditMaterial"},
                "commands": [],
            }
        )
    for item in catalog():
        template = item["id"]
        cases.append(
            {
                "id": f"powered-{template}",
                "template": template,
                "kind": "power",
                "request": reference_request(template).model_copy(update={"die_power_w": 2.5}),
                "des_changes": {"P": "2.5"},
                "commands": [],
            }
        )
    # Edit physical constituents in both applications. No production model fix is implied.
    for identifier, template, material_id, conductivity in [
        ("fc-solder-edit", "pbga_fc", "solder-pb90", 72),
        ("cbga-underfill-edit", "cbga_fc", "underfill", 1.2),
        ("wb-copper-edit", "pbga_wb", "copper", 100),
        ("wb-ball-edit", "pbga_wb", "solder-sn63", 100),
    ]:
        material = production_materials()[material_id]
        custom = material.model_copy(
            update={
                "conductivity": material.conductivity.model_copy(
                    update=dict.fromkeys("xyz", conductivity)
                )
            }
        )
        request = reference_request(template).model_copy(update={"custom_materials": [custom]})
        key = {
            "solder-pb90": "k_C4",
            "underfill": "k_underfill",
            "copper": "k_metal",
            "solder-sn63": "k_solder",
        }[material_id]
        cases.append(
            {
                "id": identifier,
                "template": template,
                "kind": "constituent_material",
                "request": request,
                "commands": [],
                "native_custom_material": custom,
                "des_changes": {key: "AuditMaterial"},
            }
        )
    for case in cases:
        case["native"] = directory / f"{case['id']}.xml"
        case["source"] = directory / "replay.xml"
    return cases
