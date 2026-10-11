import json
from pathlib import Path

import pytest

REFERENCE_ROOT = Path(__file__).parents[3] / "flotherm_pack_data" / "templates"

COVER_PROPERTIES = {
    "lidLengthLc": ("lid", "lid.length"),
    "lidWidthWc": ("lid", "lid.width"),
    "lidThicknessTc": ("lid", "lid.thickness"),
    "lidBaseThicknessTcb": ("lid", "lid.base_thickness"),
    "dieAttachThicknessTda": ("lid", "lid.die_attach"),
    "lidAdhesiveThickness": ("lid", "lid.adhesive"),
    "plateLengthLc": ("plate", "plate.length"),
    "plateWidthWc": ("plate", "plate.width"),
    "plateThicknessTc": ("plate", "plate.thickness"),
    "lengthLe": ("encapsulant", "cover.length"),
    "widthWe": ("encapsulant", "cover.width"),
    "thicknessTe": ("encapsulant", "cover.thickness"),
}


def cover_numeric_cases() -> list[object]:
    cases = []
    for template_id in ("cbga_fc", "pbga_fc"):
        manifest_path = REFERENCE_ROOT / template_id / "xml_variations.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest["variations"]:
            property_name = item["target"]["property"]
            if item["kind"] != "numeric_parameter" or property_name not in COVER_PROPERTIES:
                continue
            cover_type, field = COVER_PROPERTIES[property_name]
            model = REFERENCE_ROOT / template_id / item["artifacts"]["model"]
            overrides = {
                f"{template_id}.cover.type": cover_type,
                f"{template_id}.{field}": item["target"]["value"],
            }
            cases.append(
                pytest.param(
                    template_id,
                    overrides,
                    model,
                    id=f"{template_id}-{field}-{item['variation_id']}",
                )
            )
    return cases
