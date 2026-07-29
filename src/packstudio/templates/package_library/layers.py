from dataclasses import dataclass
from math import ceil, sqrt

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D
from packstudio.domain.materials import Material
from packstudio.templates.flip_chip_cbga.equivalent import create_equivalent_material
from packstudio.templates.flip_chip_cbga.layer_builder import build_array_layer
from packstudio.templates.flip_chip_cbga.parameters import SolderBallParameters
from packstudio.templates.package_library.definitions import TemplateValues
from packstudio.templates.package_library.materials import material
from packstudio.templates.package_library.parameters import BgaConfiguration


@dataclass(frozen=True)
class LayerBuild:
    blocks: list[AxisAlignedBlock]
    materials: list[Material]
    group_names: dict[str, str]
    metadata: dict[str, str | int | float | bool]


def build_bga_layer(
    values: TemplateValues,
    configuration: BgaConfiguration,
    parent_length: float,
    parent_width: float,
) -> LayerBuild:
    rows = values.integer("bga.rows")
    columns = values.integer("bga.columns")
    pitch = values.number("bga.pitch")
    diameter = values.number("bga.diameter")
    height = values.number("bga.height")
    solder = material("solder-sn63")
    air = material("static-air")
    parameters = SolderBallParameters(
        rows=rows,
        columns=columns,
        pitch_x=pitch,
        pitch_y=pitch,
        diameter=diameter,
        height=height,
        representation=configuration.representation,
        element_material=solder,
        matrix_material=air,
        center_solder_enabled=configuration.center_solder_enabled,
        center_solder_rows=configuration.center_solder_rows,
        center_solder_columns=configuration.center_solder_columns,
        solder_removal_enabled=configuration.solder_removal_enabled,
        removal_rows=configuration.removal_rows,
        removal_columns=configuration.removal_columns,
        omitted_cells=configuration.omitted_cells,
    )
    if parameters.footprint_x > parent_length or parameters.footprint_y > parent_width:
        raise ValueError("BGA array must fit inside the package substrate")
    built = build_array_layer(
        parameters=parameters,
        base_z=-height,
        prefix="solder-ball",
        element_structure=StructureType.SOLDER_BALL,
        matrix_structure=StructureType.STATIC_AIR,
        group_ids={
            "default": "group-solder-ball",
            "array": "group-solder-ball",
            "perimeter": "group-solder-ball",
            "center": "group-center-solder-ball",
            "void": "group-solder-ball",
        },
    )
    return LayerBuild(
        blocks=built.blocks,
        materials=[solder, air, *built.generated_materials],
        group_names={
            "group-solder-ball": "Solder balls",
            "group-center-solder-ball": "Center solder balls",
        },
        metadata={
            "solder_ball_count": built.physical_element_count,
            "solder_ball_equivalent_regions": built.equivalent_region_count,
            "solder_ball_representation": configuration.representation.value,
            "solder_ball_footprint_x_mm": parameters.footprint_x,
            "solder_ball_footprint_y_mm": parameters.footprint_y,
        },
    )


def build_flip_chip_layer(
    values: TemplateValues,
    footprint_x: float,
    footprint_y: float,
    base_z: float,
) -> LayerBuild:
    total = values.integer("bumps.total")
    diameter = values.number("bumps.diameter")
    height = values.number("bumps.height")
    columns = max(1, ceil(sqrt(total * footprint_x / footprint_y)))
    cell_area = footprint_x * footprint_y / total
    pitch_x = footprint_x / columns
    pitch_y = cell_area / pitch_x
    solder = material("solder-pb90")
    underfill = material("underfill")
    equivalent, properties = create_equivalent_material(
        material_id="flip-chip-bumps-equivalent",
        name="Flip-chip bumps + underfill orthotropic equivalent",
        element=solder,
        matrix=underfill,
        radius=diameter / 2,
        pitch_x=pitch_x,
        pitch_y=pitch_y,
    )
    block = AxisAlignedBlock(
        id="flip-chip-bumps-equivalent",
        name="Flip-chip bumps + underfill equivalent layer",
        structure_type=StructureType.FLIP_CHIP_BUMP,
        origin=Point3D(x=-footprint_x / 2, y=-footprint_y / 2, z=base_z),
        size=Size3D(x=footprint_x, y=footprint_y, z=height),
        material_id=equivalent.id,
        parent_group_id="group-flip-chip-bumps",
        metadata={
            "representation": "equivalent",
            "tensor": "orthotropic",
            "fill_fraction": properties.fill_fraction,
            "physical_elements": total,
        },
    )
    return LayerBuild(
        blocks=[block],
        materials=[solder, underfill, equivalent],
        group_names={"group-flip-chip-bumps": "Flip-chip bumps + underfill"},
        metadata={
            "flip_chip_bump_count": total,
            "flip_chip_bump_representation": "thick_orthotropic_equivalent",
            "flip_chip_bump_footprint_x_mm": footprint_x,
            "flip_chip_bump_footprint_y_mm": footprint_y,
        },
    )
