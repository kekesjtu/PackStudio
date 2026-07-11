from itertools import pairwise
from math import pi, sqrt

import pytest
from pydantic import ValidationError

from packstudio.domain.enums import StructureType
from packstudio.templates.flip_chip_cbga.generator import generate_flip_chip_cbga
from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayPattern,
    ArrayRepresentation,
    EnvironmentParameters,
    FlipChipCbgaParameters,
    VoidFillMode,
)


def test_default_model_matches_reference_tree_partition() -> None:
    model = generate_flip_chip_cbga(FlipChipCbgaParameters())
    groups = {group.id: group for group in model.groups}

    assert len(model.blocks) == 8
    assert model.metadata["flip_chip_bump_count"] == 49
    assert model.metadata["solder_ball_count"] == 49
    assert model.metadata["solder_ball_equivalent_regions"] == 5
    assert len(groups["solder-ball"].block_ids) == 4
    assert len(groups["center-sball"].block_ids) == 1
    assert model.metadata["mesh_data_included"] is False
    assert model.metadata["solver_results_included"] is False


def test_default_reference_geometry_has_expected_coordinates_and_envelope() -> None:
    parameters = FlipChipCbgaParameters()
    model = generate_flip_chip_cbga(parameters)
    blocks = {block.id: block for block in model.blocks}
    solder_regions = [
        block for block in model.blocks if block.structure_type is StructureType.SOLDER_BALL
    ]
    center_region = next(
        block for block in solder_regions if block.parent_group_id == "center-sball"
    )

    assert blocks["substrate"].origin.model_dump() == {"x": -3.0, "y": -3.0, "z": 0.0}
    assert blocks["die"].origin.x == pytest.approx(-0.9)
    assert blocks["die"].origin.y == pytest.approx(-0.9)
    assert blocks["die"].origin.z == pytest.approx(1.25)
    assert center_region.origin.x == pytest.approx(-1.2)
    assert center_region.origin.y == pytest.approx(-1.2)
    assert center_region.size.x == pytest.approx(2.4)
    assert center_region.size.y == pytest.approx(2.4)
    assert sum(region.size.x * region.size.y for region in solder_regions) == pytest.approx(
        49 * parameters.solder_balls.pitch_x * parameters.solder_balls.pitch_y
    )
    assert min(block.origin.z for block in model.blocks) == pytest.approx(-0.4)
    assert max(block.max_z for block in model.blocks) == pytest.approx(1.86)


def test_center_depopulation_can_be_omitted_or_filled_with_matrix() -> None:
    defaults = FlipChipCbgaParameters()
    depopulated = defaults.solder_balls.model_copy(
        update={
            "pattern": ArrayPattern.CENTER_DEPOPULATED,
            "void_fill": VoidFillMode.OMIT,
        }
    )
    omitted_model = generate_flip_chip_cbga(FlipChipCbgaParameters(solder_balls=depopulated))
    filled_model = generate_flip_chip_cbga(
        FlipChipCbgaParameters(
            solder_balls=depopulated.model_copy(update={"void_fill": VoidFillMode.MATRIX})
        )
    )

    assert omitted_model.metadata["solder_ball_count"] == 40
    assert "center-sball" not in {group.id for group in omitted_model.groups}
    assert len(filled_model.blocks) == len(omitted_model.blocks) + 1
    assert any(block.id == "solder-ball-void-matrix-1" for block in filled_model.blocks)


def test_discrete_elements_are_equal_volume_square_prisms() -> None:
    defaults = FlipChipCbgaParameters()
    discrete_bumps = defaults.flip_chip_bumps.model_copy(
        update={
            "rows": 2,
            "columns": 2,
            "pitch_x": 0.5,
            "pitch_y": 0.5,
            "diameter": 0.2,
            "representation": ArrayRepresentation.DISCRETE,
        }
    )
    model = generate_flip_chip_cbga(FlipChipCbgaParameters(flip_chip_bumps=discrete_bumps))
    elements = [
        block for block in model.blocks if block.structure_type is StructureType.FLIP_CHIP_BUMP
    ]
    matrix_blocks = [
        block for block in model.blocks if block.structure_type is StructureType.UNDERFILL
    ]

    expected_side = sqrt(pi) * 0.1
    assert len(elements) == 4
    assert len(matrix_blocks) == 16
    assert elements[0].size.x == pytest.approx(expected_side)
    assert elements[0].size.x * elements[0].size.y == pytest.approx(pi * 0.1**2)


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


def test_environment_parameters_generate_top_and_bottom_boundaries() -> None:
    parameters = FlipChipCbgaParameters(
        environment=EnvironmentParameters(
            ambient_temperature_k=298,
            bottom_convection_coefficient_w_m2k=10,
            top_convection_coefficient_w_m2k=20,
        )
    )

    model = generate_flip_chip_cbga(parameters)

    assert {boundary.id for boundary in model.boundaries} == {
        "bottom-convection",
        "top-convection",
    }
    assert all(boundary.targets for boundary in model.boundaries)


def test_array_outside_parent_envelope_is_rejected() -> None:
    defaults = FlipChipCbgaParameters()
    oversized = defaults.flip_chip_bumps.model_copy(update={"columns": 20})

    with pytest.raises(ValidationError, match="must fit inside the die"):
        FlipChipCbgaParameters(flip_chip_bumps=oversized)


def test_heat_slug_outside_substrate_envelope_is_rejected() -> None:
    defaults = FlipChipCbgaParameters()
    oversized_slug = defaults.heat_slug.model_copy(
        update={"enabled": True, "length": 6.5, "width": 6.5}
    )

    with pytest.raises(ValidationError, match="heat slug must fit"):
        FlipChipCbgaParameters(heat_slug=oversized_slug)
