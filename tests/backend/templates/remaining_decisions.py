"""Apply documented project geometry decisions to independent native XML evidence."""

from copy import deepcopy


def number(item, key):
    return float(item.findtext(key))


def decision_geometry(root, family):
    if family == "pqfp":
        for parent in root.iter():
            for child in list(parent):
                if child.tag == "cuboid" and child.findtext("name", "").startswith("tiebar_plt"):
                    parent.remove(child)
    if family == "sop":
        _sop_stack(root)
    if family == "pbga_wb":
        cuboids = {c.findtext("name"): c for c in root.findall(".//cuboid")}
        bottom = cuboids.get("bottom_trace", cuboids.get("bottomtrace1"))
        top = cuboids.get("toptrace1")
        if bottom is not None and top is not None:
            z = number(bottom, "position/z") + number(bottom, "size/z")
            for cuboid in root.findall(".//cuboid"):
                if cuboid.findtext("name", "").startswith("thermal_via"):
                    cuboid.find("position/z").text = str(z)
    return root


def _sop_stack(root):
    cuboids = {c.findtext("name"): c for c in root.findall(".//cuboid")}
    flag, attach, die = (cuboids[k] for k in ("die_flag", "die_attach", "die"))
    attach_z = number(flag, "position/z") + number(flag, "size/z")
    die_z = attach_z + number(attach, "size/z")
    attach.find("position/z").text = str(attach_z)
    die.find("position/z").text = str(die_z)
    for monitor in root.findall(".//monitor_point"):
        if monitor.findtext("name") == "DieJunction_Temp":
            monitor.find("position/z").text = str(die_z + 0.995 * number(die, "size/z"))
    die_top = die_z + number(die, "size/z")
    lead = cuboids["ldf_inter_right"]
    lead_top = number(lead, "position/z") + number(lead, "size/z")
    parent = next(
        p
        for p in root.iter()
        if any(c.tag == "cuboid" and c.findtext("name", "").startswith("bd_wires") for c in p)
    )
    for child in list(parent):
        if child.tag == "cuboid" and child.findtext("name", "").startswith("bdw_v"):
            parent.remove(child)
    for side in ("right", "left", "upper", "lower"):
        horizontal = cuboids["bd_wires_" + side]
        diameter = number(horizontal, "size/z")
        horizontal.find("position/z").text = str(max(die_top, lead_top) - diameter)
        if abs(die_top - lead_top) < diameter / 4:
            continue
        axis, transverse = ("x", "y") if side in {"right", "left"} else ("y", "x")
        end = number(
            cuboids["bd_wires_" + ("right" if axis == "x" else "upper")], "position/" + axis
        )
        end += number(horizontal, "size/" + axis)
        start = end if die_top > lead_top else number(die, "size/" + axis) / 2 - diameter
        vertical = deepcopy(horizontal)
        vertical.find("name").text = "bdw_v_" + side
        vertical.find("position/" + axis).text = str(
            start if side in {"right", "upper"} else -start - diameter
        )
        vertical.find("position/z").text = str(min(die_top, lead_top))
        vertical.find("size/" + axis).text = str(diameter)
        vertical.find("size/z").text = str(abs(die_top - lead_top))
        vertical.find("size/" + transverse).text = horizontal.findtext("size/" + transverse)
        parent.append(vertical)
