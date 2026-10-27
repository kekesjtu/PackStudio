"""PACK grid controls and descriptive package metadata."""


def native_metadata(values, request, blocks):
    metadata = {
        f"summary.{key}": value
        for key, value in request.summary.model_dump().items()
        if value is not None
    }
    if request.template_id not in {"bare_die", "chip_array", "cbga_fc", "pbga_fc"}:
        return metadata
    if request.template_id == "bare_die":
        length, width = values.number("die.length"), values.number("die.width")
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
    return metadata
