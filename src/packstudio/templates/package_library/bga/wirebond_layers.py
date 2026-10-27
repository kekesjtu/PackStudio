"""WB outer traces, internal metal table and constituent-derived materials."""

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.mixtures import mix_material


def metal_rows(values, request):
    rows = values.table("metal.layers")
    if not 2 <= len(rows) <= 6:
        raise ValueError("WB 金属层表需要 2–6 层")
    rows = [row.copy() for row in rows]
    for index, key in [(0, "trace.top_thickness"), (-1, "trace.bottom_thickness")]:
        if f"pbga_wb.{key}" in request.overrides:
            rows[index]["thickness"] = values.number(key)
    height = values.number("substrate.thickness")
    rows[0]["depth"] = 0
    rows[-1]["depth"] = height - rows[-1]["thickness"]
    if any(row["depth"] + row["thickness"] > height + 1e-12 for row in rows):
        raise ValueError("WB 金属层必须位于基板范围内")
    if rows[0]["thickness"] + rows[-1]["thickness"] >= height:
        raise ValueError("metal layers must be thinner than the substrate")
    return rows


def internal_layers(values, request, rows):
    top = values.number("bga.height") + values.number("substrate.thickness")
    drafts = [
        centered_draft(
            f"trace-{i}",
            f"Trace {i}",
            StructureType.TRACE,
            (values.number("package.length"), values.number("package.width"), row["thickness"]),
            top - row["depth"] - row["thickness"],
            f"wirebond-trace-{i}",
            "group-traces",
            "Dielectric & traces",
            metadata={"disconnect_to_vias": row.get("disconnect", False)},
        )
        for i, row in enumerate(rows[1:-1], 1)
    ]
    if values.boolean("vias.enabled"):
        for index, row in enumerate(rows):
            if not row.get("disconnect"):
                continue
            length = (values.integer("vias.columns") - 1) * values.number("vias.pitch")
            width = (values.integer("vias.rows") - 1) * values.number("vias.pitch")
            margin = 3 * values.number("vias.diameter")
            drafts.append(
                centered_draft(
                    f"disconnect-{index}",
                    f"Via disconnect {index}",
                    StructureType.SUBSTRATE,
                    (length + margin, width + margin, row["thickness"]),
                    top - row["depth"] - row["thickness"],
                    request.material_assignments["group-substrate"],
                    "group-via-disconnect",
                    "Via disconnects",
                )
            )
    return drafts


def copper_materials(values, request, rows):
    metal = material(request.material_assignments["group-traces"], request.custom_materials)
    matrix = material(request.material_assignments["group-substrate"], request.custom_materials)
    entries = [
        ("wirebond-trace-top", rows[0]["coverage"]),
        ("wirebond-trace-bottom", rows[-1]["coverage"]),
        ("wirebond-die-flag", values.number("flag.coverage")),
    ]
    entries += [(f"wirebond-trace-{i}", row["coverage"]) for i, row in enumerate(rows[1:-1], 1)]
    return [
        mix_material(
            metal.model_copy(update={"id": identifier, "name": identifier}),
            metal,
            matrix,
            coverage / 100,
            set("xyz"),
        )
        for identifier, coverage in entries
    ]
