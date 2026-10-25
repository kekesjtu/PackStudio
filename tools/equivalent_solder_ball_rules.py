"""Hypotheses inferred from native FloXML; independent of production generators."""

import math

from tools.verify_solder_ball_arrays_floxml import predicted_cells


def material_values(element):
    if element.tag == "biaxial_material_att":
        conductivity = dict.fromkeys("xy", float(element.findtext("in_plane_conductivity")))
        conductivity["z"] = float(element.findtext("normal_conductivity"))
    elif element.tag == "isotropic_material_att":
        conductivity = dict.fromkeys("xyz", float(element.findtext("conductivity")))
    else:
        conductivity = {axis: float(element.findtext(f"{axis}_conductivity")) for axis in "xyz"}
    return {
        "rho": float(element.findtext("density")),
        "cp": float(element.findtext("specific_heat")),
        **conductivity,
    }


def fractions(values):
    md, me = int(values["MD"]), int(values["ME"])
    b, e = float(values["b"]), float(values["e"])
    lx, ly = (md - 1) * e + b, (me - 1) * e + b
    area, count = lx * ly, md * me
    tx = (float(values["MDp"]) / 2 - 1) * e + b
    ty = (float(values["MEp"]) / 2 - 1) * e + b
    if values["depop_center"] == "CHECKED":
        count -= (md - int(values["MDp"])) * (me - int(values["MEp"]))
        area -= (lx - 2 * tx) * (ly - 2 * ty)
    factor = 0.5 if values["staggered_matrix"] == "CHECKED" else 1
    main = count * factor * math.pi * b * b / (4 * area)
    cx, cy = int(values["MDc"]), int(values["MEc"])
    clx, cly = (cx - 1) * e + b, (cy - 1) * e + b
    center_factor = 0.5 if values["central_staggered_matrix"] == "CHECKED" else 1
    center = cx * cy * center_factor * math.pi * b * b / (4 * clx * cly)
    return {
        "main": main,
        "center": center,
        "Lx": lx,
        "Ly": ly,
        "Tx": tx,
        "Ty": ty,
        "Lcx": clx,
        "Lcy": cly,
        "material_area": area,
        "material_ball_count": count * factor,
    }


def mixture(solder, air, fraction, mode):
    density = fraction * solder["rho"] + (1 - fraction) * air["rho"]
    cp = (
        fraction * solder["rho"] * solder["cp"] + (1 - fraction) * air["rho"] * air["cp"]
    ) / density
    normal = fraction * solder["k"] + (1 - fraction) * air["k"]
    transverse = normal if mode == "2" else air["k"]
    return {"rho": density, "cp": cp, "x": transverse, "y": transverse, "z": normal}


def geometry(values, rows):
    b, height, pitch = float(values["b"]), float(values["A1"]), float(values["e"])
    side = b * math.sqrt(math.pi) / 2
    blocks = []

    def block(group, name, origin, size, kind):
        blocks.append({"group": group, "name": name, "origin": origin, "size": size, "kind": kind})

    def discrete(cells, md, me, group, prefix, kind):
        for i, j in cells:
            origin = (
                (i - (md - 1) / 2) * pitch - side / 2,
                (j - (me - 1) / 2) * pitch - side / 2,
                0,
            )
            block(group, f"{prefix}_{i + 1}_{j + 1}", origin, (side, side, height), kind)

    if values["csvBGA"] == "CHECKED":
        for name, x, y in rows:
            block(
                "Solder_ball", name, (x - side / 2, y - side / 2, 0), (side, side, height), "pure"
            )
        return blocks
    md, me = int(values["MD"]), int(values["ME"])
    cells, center_cells = predicted_cells(values)
    mode = values["radio_BGA_modeling"]
    if mode == "3":
        discrete(cells, md, me, "Solder_ball", "solder_ball", "pure")
    elif values["balls"]:
        discrete(cells, md, me, "Solder_ball", "solder_ball", "main")
    else:
        f = fractions(values)
        lx, ly, tx, ty = (f[key] for key in ("Lx", "Ly", "Tx", "Ty"))
        frame = (
            values["depop_center"] == "CHECKED"
            and int(values["MDp"]) < md
            and int(values["MEp"]) < me
        )
        if frame:
            inner_x = lx - 2 * tx
            definitions = [
                ((-lx / 2, -ly / 2, 0), (tx, ly, height)),
                ((lx / 2 - tx, -ly / 2, 0), (tx, ly, height)),
                ((-inner_x / 2, -ly / 2, 0), (inner_x, ty, height)),
                ((-inner_x / 2, ly / 2 - ty, 0), (inner_x, ty, height)),
            ]
            for index, (origin, size) in enumerate(definitions, 1):
                block("Solder_ball", f"solder_ball{index}", origin, size, "main")
        else:
            block("Solder_ball", "solder_ball", (-lx / 2, -ly / 2, 0), (lx, ly, height), "main")
    if values["central_balls"] == "CHECKED":
        cx, cy = int(values["MDc"]), int(values["MEc"])
        if mode == "3":
            discrete(center_cells, cx, cy, "Center_SBall", "center_sball", "pure")
        else:
            lx, ly = (cx - 1) * pitch + b, (cy - 1) * pitch + b
            block("Center_SBall", "center_sball", (-lx / 2, -ly / 2, 0), (lx, ly, height), "center")
    return blocks
