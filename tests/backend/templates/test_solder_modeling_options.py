import pytest
from lxml import etree

from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import generate
from packstudio.templates.package_library.core.parameters import BgaConfiguration
from tests.backend.templates.reference_requests import reference_request


@pytest.mark.parametrize("with_center", [False, True])
def test_wb_isotropic_solder_keeps_equivalent_geometry_mass_and_axial_conductivity(with_center):
    request = reference_request("pbga_wb")
    options = {"representation": "equivalent"}
    if with_center:
        options.update(
            depopulated_center=True,
            populated_rows=4,
            populated_columns=4,
            center_solder_enabled=True,
            center_solder_rows=1,
            center_solder_columns=1,
            staggered=True,
        )
    orthotropic = generate(request.model_copy(update={"bga": BgaConfiguration(**options)}))
    isotropic = generate(
        request.model_copy(
            update={"bga": BgaConfiguration(**{**options, "representation": "isotropic"})}
        )
    )
    assert isotropic.metadata["solder_ball_representation"] == "isotropic"
    groups = {"group-solder-ball", "group-center-solder-ball"}

    def geometry(model):
        return [
            (block.id, block.origin, block.size, block.material_id)
            for block in model.blocks
            if block.parent_group_id in groups
        ]

    assert geometry(isotropic) == geometry(orthotropic)
    baseline = {material.id: material for material in orthotropic.materials}
    derived = [
        material for material in isotropic.materials if material.id.startswith("solder-ball-")
    ]
    assert len(derived) == (2 if with_center else 1)
    root = etree.fromstring(export_floxml(isotropic))
    for material in derived:
        expected = baseline[material.id]
        assert material.conductivity.x == material.conductivity.y == material.conductivity.z
        assert material.conductivity.z == pytest.approx(expected.conductivity.z)
        assert material.density == expected.density
        assert material.specific_heat == expected.specific_heat
        assert root.xpath(f"./attributes/materials/isotropic_material_att[name='{material.id}']")


@pytest.mark.parametrize("template", ["chip_array", "cbga_fc", "pbga_fc"])
def test_isotropic_solder_is_only_available_for_wirebond_pbga(template):
    with pytest.raises(ValueError, match="only available for Wirebond PBGA"):
        generate(
            reference_request(template).model_copy(
                update={"bga": BgaConfiguration(representation="isotropic")}
            )
        )


@pytest.mark.parametrize(
    "options",
    [
        {"ball_map_enabled": True},
        {"solder_removal_enabled": True, "omitted_cells": [{"row": 0, "column": 0}]},
    ],
)
def test_explicit_solder_layout_rejects_isotropic_equivalence(options):
    with pytest.raises(ValueError, match="离散建模"):
        generate(
            reference_request("pbga_wb").model_copy(
                update={"bga": BgaConfiguration(representation="isotropic", **options)}
            )
        )
