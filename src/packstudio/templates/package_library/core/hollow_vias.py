"""Two-stage hollow-via material and full-envelope homogenization."""

from math import pi, sqrt

from packstudio.domain.enums import StructureType
from packstudio.domain.materials import ConductivityTensor
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.mixtures import mix_material
from packstudio.templates.package_library.core.via_configuration import ViaConfiguration
from packstudio.templates.package_library.core.via_geometry import via_grid_drafts


def hollow_vias(values, request, metal, matrix, identifier, z, height):
    if height <= 0:
        raise ValueError("通孔高度必须大于零")
    diameter, plating = values.number("vias.diameter"), values.number("vias.plating")
    if plating > diameter / 2:
        raise ValueError("via plating must not exceed the via radius")
    fraction = 1 - ((diameter - 2 * plating) / diameter) ** 2
    via = metal.model_copy(
        update={
            "id": identifier,
            "name": identifier,
            "conductivity": ConductivityTensor.isotropic(fraction * metal.conductivity.x),
            "density": fraction * metal.density,
            "conductivity_coefficient": None,
            "conductivity_reference_temperature_c": None,
            "source": f"PACK hollow via; metal={metal.id}; shell_fraction={fraction:.16g}",
        }
    )
    rows, columns = values.integer("vias.rows"), values.integer("vias.columns")
    pitch = values.number("vias.pitch")
    if diameter > pitch:
        raise ValueError("via diameter must not exceed the pitch")
    mode = values.text("vias.modeling")
    if mode in {"discrete", "discreteCuboids"}:
        return via_grid_drafts(
            "thermal-via",
            rows,
            columns,
            pitch,
            sqrt(pi) * diameter / 2,
            z,
            height,
            material_id=identifier,
            configuration=request.vias,
            native_row_order=True,
        ), [via]
    lx, ly = (columns - 1) * pitch + diameter, (rows - 1) * pitch + diameter
    count = rows * columns - len((request.vias or ViaConfiguration()).omissions(rows, columns))
    fraction = count * pi * diameter**2 / (4 * lx * ly)
    equivalent = mix_material(
        via, via, matrix, fraction, set("xyz") if mode == "isotropicCuboid" else {"z"}
    )
    return [
        centered_draft(
            "thermal-via-equivalent",
            "Thermal vias",
            StructureType.VIA,
            (lx, ly, height),
            z,
            identifier,
            "group-vias",
            "Thermal vias",
        )
    ], [equivalent]
