"""PACK ball layout priorities and continuous frame equivalence."""

from math import pi, sqrt

from packstudio.domain.enums import StructureType
from packstudio.domain.materials import ConductivityTensor
from packstudio.templates.package_library.core.builds import LayerBuild
from packstudio.templates.package_library.core.geometry import centered_draft, preserve_drafts
from packstudio.templates.package_library.core.materials import material


def populated_counts(config, rows, columns):
    rp = config.populated_rows
    cp = config.populated_columns
    if rp is None:
        if config.removal_rows is None:
            raise ValueError("central removal requires both row and column counts (MEp, MDp)")
        rp = rows - config.removal_rows
    if cp is None:
        if config.removal_columns is None:
            raise ValueError("central removal requires both row and column counts (MEp, MDp)")
        cp = columns - config.removal_columns
    if not 0 <= rp <= rows or not 0 <= cp <= columns:
        raise ValueError("外围满布行列数必须位于主阵列范围内")
    return rp, cp


def depopulated_center(config):
    return (
        config.solder_removal_enabled
        if config.depopulated_center is None
        else config.depopulated_center
    )


def main_cells(config, rows, columns):
    omitted = {(c.row, c.column) for c in config.omitted_cells}
    if any(r >= rows or c >= columns for r, c in omitted):
        raise ValueError("显式去球单元超出主阵列")
    if config.solder_removal_enabled and omitted:
        return [
            (r, c) for r in range(rows) for c in range(columns) if (rows - 1 - r, c) not in omitted
        ]
    rp, cp = (
        populated_counts(config, rows, columns) if depopulated_center(config) else (rows, columns)
    )
    return [
        (r, c)
        for r in range(rows)
        for c in range(columns)
        if (not config.staggered or (r + c) % 2 == 0)
        and (
            rp == rows
            or cp == columns
            or r < rp // 2
            or r >= rows - rp // 2
            or c < cp // 2
            or c >= columns - cp // 2
        )
    ]


def wire_count(config, rows, columns):
    if config.ball_map_enabled:
        return len(config.ball_map)
    if not depopulated_center(config):
        return rows * columns
    rp, cp = populated_counts(config, rows, columns)
    return rows * columns - (rows - rp) * (columns - cp)


def build_native_solder(values, config, request, base_z=0):
    rows, columns = values.integer("bga.rows"), values.integer("bga.columns")
    pitch, diameter = values.number("bga.pitch"), values.number("bga.diameter")
    height = values.number("bga.height")
    solder = material(request.material_assignments["group-bga-solder"], request.custom_materials)
    air = material("static-air", request.custom_materials)
    drafts, materials = [], [solder, air]
    count = 0
    representation = str(config.representation)
    equivalent = representation != "discrete"
    isotropic = representation == "isotropic"
    if equivalent and (config.ball_map_enabled or config.omitted_cells):
        raise ValueError("显式去球及 Solder Ball Map 使用离散建模")

    def block(identifier, x, y, lx, ly, material_id, center=False):
        drafts.append(
            centered_draft(
                identifier,
                identifier,
                StructureType.SOLDER_BALL,
                (lx, ly, height),
                base_z,
                material_id,
                "group-center-solder-ball" if center else "group-solder-ball",
                "Center solder balls" if center else "Solder balls",
                center_x=x,
                center_y=y,
            )
        )

    def region(identifier, nr, nc, staggered, center=False):
        nonlocal count
        lx, ly = (nc - 1) * pitch + diameter, (nr - 1) * pitch + diameter
        cells = (
            [(r, c) for r in range(nr) for c in range(nc) if not staggered or (r + c) % 2 == 0]
            if center
            else main_cells(config, nr, nc)
        )
        count += len(cells)
        if not equivalent:
            side = sqrt(pi) * diameter / 2
            for r, c in cells:
                block(
                    f"{identifier}-r{r + 1}-c{c + 1}",
                    (c - (nc - 1) / 2) * pitch,
                    (r - (nr - 1) / 2) * pitch,
                    side,
                    side,
                    solder.id,
                    center,
                )
            return
        depop = depopulated_center(config) and not center
        rp, cp = populated_counts(config, nr, nc) if depop else (nr, nc)
        tx, ty = (cp / 2 - 1) * pitch + diameter, (rp / 2 - 1) * pitch + diameter
        area = lx * ly - (lx - 2 * tx) * (ly - 2 * ty) if depop else lx * ly
        n = nr * nc - (nr - rp) * (nc - cp) if depop else nr * nc
        fraction = n * pi * diameter**2 / (4 * area) * (0.5 if staggered else 1)
        density = fraction * solder.density + (1 - fraction) * air.density
        axial_conductivity = fraction * solder.conductivity.z + (1 - fraction) * air.conductivity.z
        tensor = "isotropic" if isotropic else "orthotropic"
        result = solder.model_copy(
            update={
                "source": f"PACK derived BGA; element={solder.id}; matrix={air.id}; "
                f"volume_fraction={fraction:.16g}",
                "id": "solder-ball-center-equivalent" if center else "solder-ball-equivalent",
                "name": f"Solder ball {tensor} equivalent",
                "conductivity_coefficient": None,
                "conductivity_reference_temperature_c": None,
                "conductivity": ConductivityTensor(
                    x=axial_conductivity if isotropic else air.conductivity.x,
                    y=axial_conductivity if isotropic else air.conductivity.y,
                    z=axial_conductivity,
                ),
                "density": density,
                "specific_heat": (
                    fraction * solder.density * solder.specific_heat
                    + (1 - fraction) * air.density * air.specific_heat
                )
                / density,
            }
        )
        materials.append(result)
        if not depop or rp == nr or cp == nc:
            block(identifier, 0, 0, lx, ly, result.id, center)
        else:
            if min(tx, ty, lx - 2 * tx, ly - 2 * ty) <= 0:
                raise ValueError("等效焊球边框尺寸必须大于零")
            for suffix, x, y, sx, sy in [
                ("left", -(lx - tx) / 2, 0, tx, ly),
                ("right", (lx - tx) / 2, 0, tx, ly),
                ("lower", 0, -(ly - ty) / 2, lx - 2 * tx, ty),
                ("upper", 0, (ly - ty) / 2, lx - 2 * tx, ty),
            ]:
                block(f"{identifier}-{suffix}", x, y, sx, sy, result.id, center)
        for draft in drafts:
            if draft.material_id == result.id:
                draft.metadata.update(fill_fraction=fraction, tensor=tensor)

    if config.ball_map_enabled:
        ids = [p.id for p in config.ball_map]
        if len(ids) != len(set(ids)):
            raise ValueError("Solder Ball Map 的 ID 必须唯一")
        side = sqrt(pi) * diameter / 2
        for index, point in enumerate(config.ball_map):
            block(f"solder-map-{index + 1}", point.x, point.y, side, side, solder.id)
            drafts[-1].metadata.update(native_ball_id=point.id)
        count = len(config.ball_map)
    else:
        region("solder-ball", rows, columns, config.staggered)
        if config.center_solder_enabled:
            if config.center_solder_rows is None or config.center_solder_columns is None:
                raise ValueError("central solder requires both row and column counts (MEc, MDc)")
            region(
                "center-solder-ball",
                config.center_solder_rows,
                config.center_solder_columns,
                config.center_staggered,
                True,
            )
    preserved = preserve_drafts(drafts)
    return LayerBuild(
        blocks=preserved.blocks,
        materials=materials,
        group_names=preserved.group_names,
        metadata={
            "solder_ball_count": count,
            "solder_ball_representation": representation,
            "solder_ball_footprint_x_mm": (columns - 1) * pitch + diameter,
            "solder_ball_footprint_y_mm": (rows - 1) * pitch + diameter,
        },
    )
