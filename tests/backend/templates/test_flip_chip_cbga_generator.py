from itertools import pairwise
from math import pi, sqrt

import pytest
from pydantic import ValidationError

from packstudio.domain.enums import StructureType
from packstudio.templates.flip_chip_cbga.generator import generate_flip_chip_cbga
from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayRepresentation,
    EnvironmentParameters,
    FlipChipCbgaParameters,
)


def test_default_model_uses_one_full_bga_equivalent_layer() -> None:
    model = generate_flip_chip_cbga(FlipChipCbgaParameters())
    groups = {group.id: group for group in model.groups}

    assert len(model.blocks) == 4
    assert model.metadata["flip_chip_bump_count"] == 49
    assert model.metadata["flip_chip_bump_cell_density_per_mm2"] == pytest.approx(16)
    assert model.metadata["flip_chip_bump_fill_fraction"] == pytest.approx(
        pi * (0.12 / 2) ** 2 / 0.25**2
    )
    assert model.metadata["solder_ball_count"] == 49
    assert model.metadata["solder_ball_equivalent_regions"] == 1
    assert len(groups["solder-ball"].block_ids) == 1
    assert "bga-air" not in groups
    assert "center-sball" not in groups
    assert "encapsulant" not in groups
    assert "top" not in groups
    assert model.metadata["mesh_data_included"] is False
    assert model.metadata["solver_results_included"] is False


def test_default_reference_geometry_has_expected_coordinates_and_envelope() -> None:
    parameters = FlipChipCbgaParameters()
    model = generate_flip_chip_cbga(parameters)
    blocks = {block.id: block for block in model.blocks}
    solder_regions = [
        block for block in model.blocks if block.structure_type is StructureType.SOLDER_BALL
    ]
    static_air = [
        block for block in model.blocks if block.structure_type is StructureType.STATIC_AIR
    ]

    assert blocks["substrate"].origin.model_dump() == {"x": -3.0, "y": -3.0, "z": 0.0}
    assert blocks["die"].origin.x == pytest.approx(-0.9)
    assert blocks["die"].origin.y == pytest.approx(-0.9)
    assert blocks["die"].origin.z == pytest.approx(1.25)
    bump = blocks["fc-bump-array-equivalent-1"]
    assert bump.origin.x == pytest.approx(-0.9)
    assert bump.origin.y == pytest.approx(-0.9)
    assert bump.size.x == pytest.approx(1.8)
    assert bump.size.y == pytest.approx(1.8)
    assert len(solder_regions) == 1
    assert solder_regions[0].origin.x == pytest.approx(-2.65)
    assert solder_regions[0].origin.y == pytest.approx(-2.65)
    assert solder_regions[0].size.x == pytest.approx(5.3)
    assert solder_regions[0].size.y == pytest.approx(5.3)
    assert solder_regions[0].material_id == "solder-ball-equivalent"
    assert solder_regions[0].metadata["fill_fraction"] == pytest.approx(
        pi
        * (parameters.solder_balls.diameter / 2) ** 2
        / (parameters.solder_balls.pitch_x * parameters.solder_balls.pitch_y)
    )
    expected_footprint = (
        parameters.solder_balls.columns - 1
    ) * parameters.solder_balls.pitch_x + parameters.solder_balls.diameter
    assert sum(region.size.x * region.size.y for region in solder_regions) == pytest.approx(
        expected_footprint**2
    )
    assert static_air == []
    assert parameters.solder_balls.matrix_material.id == "air"
    assert min(block.origin.z for block in model.blocks) == pytest.approx(-0.4)
    assert max(block.max_z for block in model.blocks) == pytest.approx(1.86)


def test_center_removal_is_filled_with_static_air() -> None:
    defaults = FlipChipCbgaParameters()
    depopulated = defaults.solder_balls.model_copy(
        update={
            "solder_removal_enabled": True,
            "removal_rows": 3,
            "removal_columns": 3,
        }
    )
    model = generate_flip_chip_cbga(FlipChipCbgaParameters(solder_balls=depopulated))

    assert model.metadata["solder_ball_count"] == 40
    assert "center-sball" not in {group.id for group in model.groups}
    center_air = next(block for block in model.blocks if block.id == "solder-ball-void-matrix-1")
    assert center_air.structure_type is StructureType.STATIC_AIR
    assert center_air.material_id == "air"

    assert depopulated.matrix_material.id == "air"


def test_center_solder_and_removal_generate_perimeter_air_gap_and_center_groups() -> None:
    defaults = FlipChipCbgaParameters()
    solder_style = defaults.solder_balls.model_copy(
        update={
            "solder_removal_enabled": True,
            "removal_rows": 5,
            "removal_columns": 5,
            "center_solder_enabled": True,
            "center_solder_rows": 3,
            "center_solder_columns": 3,
        }
    )

    model = generate_flip_chip_cbga(FlipChipCbgaParameters(solder_balls=solder_style))
    groups = {group.id: group for group in model.groups}
    air_blocks = [
        block for block in model.blocks if block.structure_type is StructureType.STATIC_AIR
    ]

    assert model.metadata["solder_ball_count"] == 33
    assert len(groups["solder-ball"].block_ids) == 8
    assert len(groups["center-sball"].block_ids) == 1
    assert len(air_blocks) == 4


def test_discrete_bga_elements_are_equal_volume_square_prisms_in_static_air() -> None:
    defaults = FlipChipCbgaParameters()
    discrete_balls = defaults.solder_balls.model_copy(
        update={
            "rows": 2,
            "columns": 2,
            "pitch_x": 0.5,
            "pitch_y": 0.5,
            "diameter": 0.2,
            "representation": ArrayRepresentation.DISCRETE,
        }
    )
    model = generate_flip_chip_cbga(FlipChipCbgaParameters(solder_balls=discrete_balls))
    elements = [
        block for block in model.blocks if block.structure_type is StructureType.SOLDER_BALL
    ]
    matrix_blocks = [
        block
        for block in model.blocks
        if block.structure_type is StructureType.STATIC_AIR
        and block.metadata.get("representation") == "discrete-matrix"
    ]

    expected_side = sqrt(pi) * 0.1
    assert len(elements) == 4
    assert len(matrix_blocks) == 16
    assert elements[0].size.x == pytest.approx(expected_side)
    assert elements[0].size.x * elements[0].size.y == pytest.approx(pi * 0.1**2)
    assert all(block.origin.x >= -0.5 and block.max_x <= 0.5 for block in matrix_blocks)
    assert all(block.origin.y >= -0.5 and block.max_y <= 0.5 for block in matrix_blocks)


def test_discrete_flip_chip_bumps_are_rejected() -> None:
    defaults = FlipChipCbgaParameters()
    discrete_bumps = defaults.flip_chip_bumps.model_copy(
        update={"representation": ArrayRepresentation.DISCRETE}
    )

    with pytest.raises(ValidationError, match="only support anisotropic equivalent"):
        FlipChipCbgaParameters(flip_chip_bumps=discrete_bumps)


def test_heat_slug_and_lid_form_a_contiguous_non_overlapping_top_stack() -> None:
    defaults = FlipChipCbgaParameters()
    model = generate_flip_chip_cbga(
        FlipChipCbgaParameters(
            heat_slug=defaults.heat_slug.model_copy(update={"enabled": True}),
            lid=defaults.lid.model_copy(update={"enabled": True}),
        )
    )
    top_blocks = [block for block in model.blocks if block.parent_group_id == "top"]

    assert [block.id for block in top_blocks] == [
        "die-to-slug-interface",
        "heat-slug",
        "top-to-lid-interface",
        "lid",
    ]
    assert all(left.max_z == pytest.approx(right.origin.z) for left, right in pairwise(top_blocks))


def test_optional_encapsulant_submerges_die_without_a_top_structure() -> None:
    defaults = FlipChipCbgaParameters()
    parameters = FlipChipCbgaParameters(
        encapsulant=defaults.encapsulant.model_copy(update={"enabled": True})
    )

    model = generate_flip_chip_cbga(parameters)
    encapsulant_blocks = [
        block for block in model.blocks if block.structure_type is StructureType.ENCAPSULANT
    ]
    groups = {group.id: group for group in model.groups}
    lower = [block for block in encapsulant_blocks if block.metadata["tier"] == "lower"]
    upper = [block for block in encapsulant_blocks if block.metadata["tier"] == "upper"]
    cap = next(block for block in encapsulant_blocks if block.metadata["tier"] == "cap")
    ring_area = (
        parameters.encapsulant.length * parameters.encapsulant.width
        - parameters.die.length * parameters.die.width
    )

    assert len(encapsulant_blocks) == 9
    assert groups["encapsulant"].block_ids == [block.id for block in encapsulant_blocks]
    assert model.metadata["encapsulant_block_count"] == 9
    assert sum(block.size.x * block.size.y for block in lower) == pytest.approx(ring_area)
    assert sum(block.size.x * block.size.y for block in upper) == pytest.approx(ring_area)
    assert {block.origin.z for block in lower} == {parameters.substrate.thickness}
    die_top = (
        parameters.substrate.thickness
        + parameters.flip_chip_bumps.height
        + parameters.die.thickness
    )
    assert {block.max_z for block in upper} == {die_top}
    assert cap.origin.z == pytest.approx(die_top)
    assert cap.max_z == pytest.approx(die_top + parameters.encapsulant.cover_thickness)
    assert cap.size.x * cap.size.y == pytest.approx(
        parameters.encapsulant.length * parameters.encapsulant.width
    )


def test_top_boundary_targets_the_encapsulant_cover() -> None:
    defaults = FlipChipCbgaParameters()
    parameters = FlipChipCbgaParameters(
        encapsulant=defaults.encapsulant.model_copy(update={"enabled": True}),
        environment=EnvironmentParameters(),
    )

    model = generate_flip_chip_cbga(parameters)
    boundary = next(item for item in model.boundaries if item.id == "top-surface-cooling")

    assert {target.block_id for target in boundary.targets} == {"encapsulant-cap"}


def test_lid_exposes_the_die_through_an_encapsulant_opening() -> None:
    defaults = FlipChipCbgaParameters()
    parameters = FlipChipCbgaParameters(
        encapsulant=defaults.encapsulant.model_copy(update={"enabled": True}),
        lid=defaults.lid.model_copy(update={"enabled": True}),
    )

    model = generate_flip_chip_cbga(parameters)
    blocks = {block.id: block for block in model.blocks}
    boundary = next(item for item in model.boundaries if item.id == "top-surface-cooling")

    assert "encapsulant-cap" not in blocks
    assert model.metadata["encapsulant_block_count"] == 8
    die_top = blocks["die"].max_z
    assert blocks["top-to-lid-interface"].origin.z == pytest.approx(die_top)
    assert blocks["top-to-lid-interface"].size.x == pytest.approx(parameters.die.length)
    assert blocks["top-to-lid-interface"].size.y == pytest.approx(parameters.die.width)
    assert {target.block_id for target in boundary.targets} == {"lid"}


def test_heat_slug_exposes_the_die_through_an_encapsulant_opening() -> None:
    defaults = FlipChipCbgaParameters()
    parameters = FlipChipCbgaParameters(
        encapsulant=defaults.encapsulant.model_copy(update={"enabled": True}),
        heat_slug=defaults.heat_slug.model_copy(update={"enabled": True}),
    )

    model = generate_flip_chip_cbga(parameters)
    blocks = {block.id: block for block in model.blocks}
    boundary = next(item for item in model.boundaries if item.id == "top-surface-cooling")

    assert "encapsulant-cap" not in blocks
    assert model.metadata["encapsulant_block_count"] == 8
    assert blocks["die-to-slug-interface"].origin.z == pytest.approx(blocks["die"].max_z)
    assert blocks["die-to-slug-interface"].size.x == pytest.approx(parameters.die.length)
    assert blocks["die-to-slug-interface"].size.y == pytest.approx(parameters.die.width)
    assert {target.block_id for target in boundary.targets} == {"heat-slug"}


def test_environment_parameters_generate_simulation_ready_boundaries() -> None:
    parameters = FlipChipCbgaParameters(
        environment=EnvironmentParameters(
            ambient_temperature_k=298,
            default_convection_coefficient_w_m2k=12,
            pcb_convection_coefficient_w_m2k=1800,
            top_convection_coefficient_w_m2k=25,
        )
    )

    model = generate_flip_chip_cbga(parameters)

    assert {boundary.id for boundary in model.boundaries} == {
        "pcb-side-cooling",
        "top-surface-cooling",
    }
    assert all(boundary.targets for boundary in model.boundaries)
    board = next(boundary for boundary in model.boundaries if boundary.id == "pcb-side-cooling")
    top = next(boundary for boundary in model.boundaries if boundary.id == "top-surface-cooling")
    assert board.convection_coefficient_w_m2k == pytest.approx(1800)
    assert top.convection_coefficient_w_m2k == pytest.approx(25)
