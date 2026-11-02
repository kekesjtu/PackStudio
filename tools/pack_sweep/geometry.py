"""Index FloXML cuboids by geometry and physical material properties."""

from collections import defaultdict


def geometry_index(root):
    materials = {}
    for item in root.findall("attributes/materials/*"):
        scalar = item.findtext("conductivity")
        if scalar is not None:
            tensor = [float(scalar)] * 3
        elif item.find("in_plane_conductivity") is not None:
            tensor = [float(item.findtext("in_plane_conductivity"))] * 2 + [
                float(item.findtext("normal_conductivity"))
            ]
        else:
            tensor = [float(item.findtext(f"{a}_conductivity")) for a in "xyz"]
        materials[item.findtext("name")] = (
            *tensor,
            float(item.findtext("density")),
            float(item.findtext("specific_heat")),
        )
    groups = defaultdict(list)

    def visit(geometry, offset=(0, 0, 0), inherited=None):
        for item in geometry:
            if item.tag not in {"assembly", "cuboid"}:
                continue
            origin = tuple(
                float(item.findtext(f"position/{a}", "0")) + offset[i] for i, a in enumerate("xyz")
            )
            material = item.findtext("material") or inherited
            if item.tag == "assembly":
                visit(item.find("geometry"), origin, material)
            else:
                key = tuple(round(x * 1000, 8) for x in origin) + tuple(
                    round(float(item.findtext(f"size/{a}")) * 1000, 8) for a in "xyz"
                )
                groups[key].append((item.findtext("name"), materials.get(material)))

    visit(root.find("geometry"))
    return groups
