"""Reproduce the 342-source adaptation audit and both interchange checks."""

import hashlib
import json
from pathlib import Path

from lxml import etree

from packstudio.default_parameters import library_directory
from packstudio.domain.enums import StructureType
from packstudio.exporters.ecxml import export_ecxml
from packstudio.exporters.pta_constants import MODEL_NAMESPACE
from packstudio.exporters.pta_xml import export_pta_xml
from packstudio.templates.package_library.catalog import default_request, definitions, generate
from packstudio.templates.package_library.core.default_library import template_defaults
from packstudio.templates.package_library.core.native_presets import expand_native_presets
from packstudio.templates.package_library.core.parameters import BgaConfiguration

ROOT = Path(__file__).resolve().parents[1]


def validate_exports(model, schema: etree.XMLSchema) -> dict:
    ecxml = etree.fromstring(export_ecxml(model))
    schema.assertValid(ecxml)
    assert len(ecxml.findall(".//solid3dBlock")) == len(model.blocks)
    pta = etree.fromstring(export_pta_xml(model))
    namespace = {"m": MODEL_NAMESPACE}
    blocks = pta.xpath("./m:Layers/m:Layer/m:Blocks/m:Block", namespaces=namespace)
    assert blocks
    assert set(pta.xpath(".//m:Block/m:MaterialName/text()", namespaces=namespace)) <= {
        material.id for material in model.materials
    }
    assert not model.boundaries
    return {
        "physical_blocks": len(model.blocks),
        "pta_boolean_blocks": len(blocks),
        "ecxml_xsd": "passed",
        "pta_xml": "passed",
        "geometry_references": "passed",
    }


def main() -> None:
    schema = etree.XMLSchema(etree.parse(str(ROOT / "output_format/ecxml/ECXML.xsd")))
    records = []
    cases = 0
    for template_id, definition in definitions().items():
        if template_id == "bare_die":
            continue
        defaults = template_defaults(template_id)
        footprint = next(field for field in defaults["fields"] if field["control"] == "footprint")
        adapted = expand_native_presets(template_id, footprint, defaults["fields"])
        for preset in adapted["presets"]:
            record = {
                "template_id": template_id,
                "preset": preset["value"],
                **preset["metadata"],
                "parameter_audit": preset["audit"],
                "cases": {},
            }
            representations = ["equivalent", "discrete"] if definition.has_bga else [None]
            counts = []
            for representation in representations:
                request = default_request(template_id).model_copy(
                    update={
                        "overrides": {f"{template_id}.footprint.size": preset["value"]},
                        "bga": BgaConfiguration(representation=representation)
                        if representation
                        else None,
                        "die_power_w": 2.5,
                    }
                )
                model = generate(request)
                result = validate_exports(model, schema)
                if representation:
                    count = model.metadata["solder_ball_count"]
                    counts.append(count)
                    result["solder_ball_count"] = count
                    if representation == "discrete":
                        assert (
                            sum(
                                block.structure_type is StructureType.SOLDER_BALL
                                for block in model.blocks
                            )
                            == count
                        )
                record["cases"][representation or "native"] = result
                cases += 1
            assert len(set(counts)) <= 1
            records.append(record)
        print(f"{template_id}: {len(adapted['presets'])} presets passed", flush=True)
    assert len(records) == 342
    directory = library_directory()
    inputs = {
        str(path.relative_to(directory)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(directory.rglob("*.json"))
    }
    report = {
        "schema_version": "packstudio.catalog-adaptation-audit/v1",
        "source_count": 342,
        "model_export_cases": cases,
        "input_sha256": inputs,
        "scope": "Generation, material/group references, nonoverlap, positive sizes, "
        "BGA count parity, ECXML XSD and PTA XML; no native PACK comparison for new presets.",
        "records": records,
    }
    (ROOT / "docs/validation/catalog_presets.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"{len(records)} sources, {cases} model/export cases passed", flush=True)


if __name__ == "__main__":
    main()
