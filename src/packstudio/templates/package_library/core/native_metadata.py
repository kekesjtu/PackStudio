"""PACK grid controls and descriptive package metadata."""


def native_metadata(values, request, blocks):
    metadata = {
        f"summary.{key}": value
        for key, value in request.summary.model_dump().items()
        if value is not None
    }
    if request.template_id == "bare_die":
        length, width = values.number("die.length"), values.number("die.width")
    elif request.template_id in {"pqfp", "sop"}:
        length = values.number("package.length" if request.template_id == "pqfp" else "body.length")
        width = values.number("package.width")
    elif request.template_id in {"qfn", "pbga_wb"}:
        length, width = values.number("package.length"), values.number("package.width")
    else:
        prefix = "package" if request.template_id == "chip_array" else "substrate"
        length, width = values.number(prefix + ".length"), values.number(prefix + ".width")
    metadata.update(
        {
            "native_grid_enabled": values.boolean("grid.enabled"),
            "native_grid_density": values.text("grid.density"),
            "native_grid_length_mm": length,
            "native_grid_width_mm": width,
            "native_grid_height_mm": (
                values.number("die.thickness")
                if request.template_id == "bare_die"
                else max(b.max_z for b in blocks)
            ),
        }
    )
    if request.template_id in {"pqfp", "sop", "qfn", "pbga_wb"}:
        metadata["native_grid_length_mm"] = max(length, width)
        metadata["native_grid_width_mm"] = max(length, width)
    return metadata
