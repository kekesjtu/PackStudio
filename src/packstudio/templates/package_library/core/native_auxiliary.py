"""Native nonphysical grid regions and junction/case temperature monitors."""

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import Point3D, Size3D
from packstudio.domain.model import AuxiliaryGeometry


def native_auxiliary(values, request, blocks, metadata):
    if "native_grid_enabled" not in metadata:
        return []
    die = next(block for block in blocks if block.structure_type is StructureType.DIE)
    flipped = request.template_id in {"cbga_fc", "pbga_fc"} or (
        request.template_id == "bare_die"
        and (values.boolean("die.flipped") or values.boolean("bumps.enabled"))
    )
    result = [
        AuxiliaryGeometry(
            kind="monitor_point",
            name="DieJunction_Temp",
            origin=Point3D(x=0, y=0, z=die.origin.z + die.size.z * (0.005 if flipped else 0.995)),
        )
    ]
    if request.template_id == "bare_die":
        return result
    height = metadata["native_grid_height_mm"]
    result.append(
        AuxiliaryGeometry(
            kind="monitor_point", name="CaseTemp", origin=Point3D(x=0, y=0, z=0.99 * height)
        )
    )
    length = metadata["solder_ball_footprint_x_mm"]
    width = metadata["solder_ball_footprint_y_mm"]

    def region(name, length, width, z):
        return AuxiliaryGeometry(
            kind="region",
            name=name,
            origin=Point3D(x=-length / 2, y=-width / 2, z=z),
            size=Size3D(x=length, y=width, z=1),
        )

    result.append(region("z_bottom", length, width, 0))
    length, width = die.size.x, die.size.y
    if request.template_id == "chip_array":
        length, width = values.number("package.length"), values.number("package.width")
    else:
        kind = values.text("cover.type")
        prefix = {"lid": "lid", "plate": "plate", "encapsulant": "cover"}.get(kind)
        if prefix:
            length, width = values.number(prefix + ".length"), values.number(prefix + ".width")
    result.append(region("z_top", length, width, height))
    return result
