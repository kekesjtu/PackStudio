"""Regressions for the reviewed PACK omissions and explicit scope decisions."""

from math import pi, sqrt
from pathlib import Path

import pytest
from lxml import etree

from packstudio.domain.enums import StructureType
from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import (
    default_request,
    definitions,
    generate,
    schema,
)
from packstudio.templates.package_library.core.materials import material_id_for_name
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.via_configuration import ViaConfiguration

ROOT = Path(__file__).resolve().parents[3]


def validate_exports(model):
    root = etree.fromstring(export_floxml(model))
    path = ROOT / "output_format/floxml/xmlSchema.xsd"
    etree.XMLSchema(etree.parse(str(path))).assertValid(root)


def request(template, **values):
    return default_request(template).model_copy(
        update={"overrides": {f"{template}.{key}": value for key, value in values.items()}}
    )


def volume(blocks):
    return sum(b.size.x * b.size.y * b.size.z for b in blocks)


def test_wirebond_native_spreader_and_bottom_trace_opening():
    model = generate(request("pbga_wb", **{"footprint.size": "PBGA_192_17X17mm"}))
    spreader = [b for b in model.blocks if b.parent_group_id == "group-backside-spreader"]
    assert len(spreader) == 1
    assert spreader[0].size.model_dump() == pytest.approx({"x": 9.4, "y": 9.4, "z": 0.018})
    assert spreader[0].material_id == material_id_for_name("Copper (Pure)")
    bottom = [b for b in model.blocks if b.id.startswith("bottom-trace")]
    assert volume(bottom) == pytest.approx((17 * 17 - 9.4**2) * 0.018)
    assert not any("spreader" in b.id for b in generate(default_request("pbga_wb")).blocks)


def test_wirebond_spreader_controls_and_material_reach_geometry_and_exports():
    r = request(
        "pbga_wb",
        **{
            "spreader.enabled": True,
            "spreader.length": 4,
            "spreader.width": 5,
            "spreader.thickness": 0.03,
            "spreader.hole_length": 6,
            "spreader.hole_width": 7,
        },
    ).model_copy(
        update={
            "material_assignments": {
                "group-backside-spreader": material_id_for_name("Alloy-42"),
            }
        }
    )
    model = generate(r)
    spreader = next(b for b in model.blocks if "spreader" in b.id)
    assert spreader.origin.z == pytest.approx(0.6)
    assert volume([spreader]) == pytest.approx(4 * 5 * 0.03)
    assert spreader.material_id == material_id_for_name("Alloy-42")
    assert volume([b for b in model.blocks if b.id.startswith("bottom-trace")]) == pytest.approx(
        (15 * 15 - 6 * 7) * 0.018
    )
    validate_exports(model)
    with pytest.raises(ValueError, match="inactive"):
        generate(r.model_copy(update={"overrides": {"pbga_wb.spreader.enabled": False}}))


@pytest.mark.parametrize("template", ["pbga_wb", "chip_array", "qfn"])
def test_via_region_and_explicit_removal_union_preserves_material_and_cells(template):
    prefix = "bga" if template == "chip_array" else "vias"
    r = request(template, **{"vias.enabled": True, f"{prefix}.rows": 3, f"{prefix}.columns": 4})
    baseline = generate(r)
    config = ViaConfiguration(
        removal_enabled=True,
        removal_rows=1,
        removal_columns=2,
        omitted_cells=[{"row": 0, "column": 0}, {"row": 1, "column": 1}],
    )
    model = generate(r.model_copy(update={"vias": config}))
    vias = [b for b in model.blocks if b.structure_type is StructureType.VIA]
    assert len(vias) == 12 - 3
    assert all(
        not b.id.startswith(("thermal-via-r1-c1-", "thermal-via-r2-c2-", "thermal-via-r2-c3-"))
        for b in vias
    )
    before = [b for b in baseline.blocks if b.structure_type is StructureType.VIA]
    assert volume(vias) / volume(before) == pytest.approx(9 / 12)
    assert {m.id: m for m in baseline.materials}[vias[0].material_id] == next(
        m for m in model.materials if m.id == vias[0].material_id
    )
    disabled = config.model_copy(update={"removal_enabled": False})
    if template == "qfn":
        validate_exports(model)
    assert (
        len(
            [
                b
                for b in generate(r.model_copy(update={"vias": disabled})).blocks
                if b.structure_type is StructureType.VIA
            ]
        )
        == 12
    )
    assert (
        TemplateRequest.model_validate_json(
            r.model_copy(update={"vias": config}).model_dump_json()
        ).vias
        == config
    )


def test_qfn_via_dimensions_shell_properties_and_disabled_branch():
    assert not any(
        b.structure_type is StructureType.VIA for b in generate(default_request("qfn")).blocks
    )
    model = generate(request("qfn", **{"vias.enabled": True}))
    vias = [b for b in model.blocks if b.structure_type is StructureType.VIA]
    assert len(vias) == 25
    assert vias[0].size.x == pytest.approx(sqrt(pi) * 0.2 / 2)
    assert vias[0].size.z == pytest.approx(0.85)
    assert vias[0].origin.z == pytest.approx(-0.85)
    via = next(m for m in model.materials if m.id == vias[0].material_id)
    assert via.conductivity.x == pytest.approx(138.6)
    assert via.density == pytest.approx(3214.8)
    assert via.specific_heat == 385
    validate_exports(model)
    assert etree.fromstring(export_floxml(model)) is not None
    with pytest.raises(ValueError, match="inactive"):
        generate(request("qfn", **{"vias.length": 1}))


@pytest.mark.parametrize(
    "values,error",
    [
        ({"vias.plating": 0.2}, "radius"),
        ({"vias.pitch": 0.1}, "pitch"),
        ({"vias.columns": 50}, "exposed pad"),
    ],
)
def test_qfn_rejects_invalid_via_geometry(values, error):
    with pytest.raises(ValueError, match=error):
        generate(request("qfn", **{"vias.enabled": True, **values}))


@pytest.mark.parametrize(
    "config,error",
    [
        ({"removal_rows": 6, "removal_columns": 1}, "fit"),
        ({"removal_rows": 1}, "both"),
        ({"omitted_cells": [{"row": 5, "column": 0}]}, "outside"),
    ],
)
def test_invalid_via_removal_is_rejected(config, error):
    with pytest.raises(ValueError, match=error):
        generate(
            request("qfn", **{"vias.enabled": True}).model_copy(
                update={
                    "vias": ViaConfiguration(removal_enabled=True, **config),
                }
            )
        )


def test_via_configuration_is_rejected_for_templates_without_vias():
    with pytest.raises(ValueError, match="only valid"):
        generate(default_request("bare_die").model_copy(update={"vias": ViaConfiguration()}))


def test_bare_die_gaas_and_resin_underfill_are_selectable_and_consumed():
    gaas, resin = material_id_for_name("Gallium Arsenide"), material_id_for_name("Cookson-7115")
    r = request("bare_die", **{"bumps.enabled": True}).model_copy(
        update={
            "material_assignments": {"group-die": gaas, "group-underfill": resin},
        }
    )
    model = generate(r)
    assert (
        next(b for b in model.blocks if b.structure_type is StructureType.DIE).material_id == gaas
    )
    assert (
        next(b for b in model.blocks if b.structure_type is StructureType.DIE).name
        == "Gallium Arsenide die"
    )
    mixture = next(m for m in model.materials if m.id == "flip-chip-bumps-equivalent")
    assert resin in mixture.source
    for name in ("Cookson-7115", "Nitto-HC100X2", "Sumitomo-EME7740"):
        selection = next(
            s
            for s in definitions()["bare_die"].material_selections
            if s.group_id == "group-underfill"
        )
        assert material_id_for_name(name) in selection.options
    assert gaas.encode() in export_floxml(model)


def test_explicit_exclusions_have_no_controls_and_heat_remains_uniform():
    for template in definitions():
        fields = [f for step in schema(template)["steps"] for f in step["fields"]]
        assert not any("nonUniform" in f["target_id"] for f in fields)
        model = generate(default_request(template))
        densities = {
            round(h.power_w / volume([next(b for b in model.blocks if b.id == h.block_id)]), 10)
            for h in model.heat_sources
        }
        assert len(densities) == 1


@pytest.mark.parametrize("template", ["pqfp", "sop"])
def test_leadframe_coverage_uses_current_width_over_pitch(template):
    r = request(template, **{"leads.width": 0.4, "leads.pitch": 1.0})
    model = generate(r)
    equivalent = next(m for m in model.materials if m.id.startswith(f"{template}-leadframe-inner"))
    assert "volume_fraction=0.4" in equivalent.source
    with pytest.raises(ValueError, match="unknown"):
        generate(request(template, **{"leadframe.coverage": 75}))
