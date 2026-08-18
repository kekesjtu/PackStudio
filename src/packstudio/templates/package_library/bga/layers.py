from math import pi

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.materials import ConductivityTensor, Material
from packstudio.templates.flip_chip_cbga.layer_builder import build_array_layer
from packstudio.templates.flip_chip_cbga.parameters import SolderBallParameters
from packstudio.templates.package_library.core.builds import LayerBuild
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.parameters import BgaConfiguration


def build_bga_layer(
    values: TemplateValues,
    configuration: BgaConfiguration,
    *,
    base_z: float = 0,
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
    built = build_array_layer(
        parameters=parameters,
        base_z=base_z,
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
    blocks = built.blocks
    generated_materials = built.generated_materials
    if configuration.representation.value == "equivalent":
        equivalent, fill_fraction = _bga_equivalent_material(
            built.blocks,
            built.physical_element_count,
            diameter,
            solder,
            air,
        )
        blocks = [
            block.model_copy(
                update={
                    "metadata": {
                        **block.metadata,
                        "fill_fraction": fill_fraction,
                    }
                }
            )
            if block.material_id == equivalent.id
            else block
            for block in blocks
        ]
        generated_materials = [equivalent]
    return LayerBuild(
        blocks=blocks,
        materials=[solder, air, *generated_materials],
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


def _bga_equivalent_material(
    blocks: list[AxisAlignedBlock],
    physical_count: int,
    diameter: float,
    solder: Material,
    air: Material,
) -> tuple[Material, float]:
    occupied_area = sum(
        block.size.x * block.size.y
        for block in blocks
        if block.structure_type is StructureType.SOLDER_BALL
    )
    fill_fraction = (
        physical_count * pi * (diameter / 2) ** 2 / occupied_area if occupied_area else 0
    )
    density = fill_fraction * solder.density + (1 - fill_fraction) * air.density
    heat_capacity = (
        fill_fraction * solder.density * solder.specific_heat
        + (1 - fill_fraction) * air.density * air.specific_heat
    ) / density
    conductivity_z = (
        fill_fraction * solder.conductivity.z + (1 - fill_fraction) * air.conductivity.z
    )
    return (
        Material(
            id="solder-ball-equivalent",
            name="Solder ball orthotropic equivalent",
            conductivity=ConductivityTensor(
                x=air.conductivity.x,
                y=air.conductivity.y,
                z=conductivity_z,
            ),
            density=density,
            specific_heat=heat_capacity,
            color=solder.color,
            source="Handwritten FloTHERM PACK full-array BGA equivalence",
        ),
        fill_fraction,
    )
