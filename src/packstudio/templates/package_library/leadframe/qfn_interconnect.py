"""Discrete QFN interconnects or one orthotropic envelope per side and level."""

from packstudio.templates.package_library.core.geometry import corner_draft
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.mixtures import mix_material
from packstudio.templates.package_library.leadframe.qfn_primitives import qfn_interconnect_drafts


def interconnect(values, request, count_x, count_y, pitch_x, pitch_y):
    width = values.number("leads.width")
    drafts = qfn_interconnect_drafts(
        values.number("package.length"),
        values.number("package.width"),
        count_x,
        count_y,
        pitch_x,
        pitch_y,
        width,
        values.number("leads.length"),
        values.number("leads.exposed_thickness"),
        values.number("leads.thickness"),
        values.number("leads.etch"),
        values.number("package.standoff"),
    )
    if values.text("leads.modeling") == "discreteLeads":
        return drafts, []
    materials, envelopes = [], []
    for axis, count, pitch, sides in [
        ("x", count_y, pitch_y, ("left", "right")),
        ("y", count_x, pitch_x, ("lower", "upper")),
    ]:
        if not count:
            continue
        fraction = count * width / ((count - 1) * pitch + width)
        for kind in ("lead", "solder"):
            group = "group-lead-frame" if kind == "lead" else "group-solder"
            metal = material(request.material_assignments[group], request.custom_materials)
            matrix = material(
                request.material_assignments["group-encapsulant"]
                if kind == "lead"
                else "static-air",
                request.custom_materials,
            )
            identifier = f"qfn-{kind}-{axis}"
            materials.append(
                mix_material(
                    metal.model_copy(update={"id": identifier, "name": identifier}),
                    metal,
                    matrix,
                    fraction,
                    {axis, "z"},
                )
            )
            for level in ("lead-lower", "lead-upper") if kind == "lead" else ("solder",):
                for side in sides:
                    selected = [d for d in drafts if d.id.startswith(f"{level}-{side}-")]
                    low = tuple(min(d.origin[i] for d in selected) for i in range(3))
                    size = tuple(max(d.maximum[i] for d in selected) - low[i] for i in range(3))
                    original = selected[0]
                    envelopes.append(
                        corner_draft(
                            f"{level}-{side}",
                            original.name,
                            original.structure_type,
                            low,
                            size,
                            identifier,
                            group,
                            original.group_name,
                        )
                    )
    return envelopes, materials
